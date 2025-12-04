"""
Generador de CV en HTML con OpenAI

Este módulo proporciona una aplicación Streamlit para generar currículums vitae
profesionales en formato HTML utilizando modelos de lenguaje de OpenAI.

Autor: Francisco Gonzalez
Fecha: Noviembre 2025
Versión: 1.0

Características principales:
    - Generación de CV en HTML basado en un brief descriptivo
    - Soporte para modelos GPT-4 y GPT-4o de OpenAI
    - Personalización del color de acento del CV
    - Carga de foto de perfil y código QR
    - Vista previa en tiempo real del CV generado
    - Descarga del HTML resultante

Dependencias:
    - streamlit: Framework web para la interfaz de usuario
    - openai: Cliente para la API de OpenAI
    - python-dotenv: Gestión de variables de entorno

Uso:
    $ streamlit run app.py
    
Variables de entorno requeridas:
    OPENAI_API_KEY: Clave de API de OpenAI
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import List, Optional

import re
import time as time_module
from contextlib import contextmanager

import streamlit as st
from dotenv import load_dotenv
from openai import RateLimitError, APIConnectionError, APITimeoutError

from openai_client import chat_completion, OpenAIClientError
from config import (
    ENV_VAR_API_KEY,
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    DEFAULT_ACCENT_COLOR,
    DEFAULT_MAX_TOKENS,
    MIN_TOKENS,
    MAX_TOKENS,
    TOKEN_STEP,
    PAGE_TITLE,
    BRIEF_TEXT_AREA_HEIGHT,
    PREVIEW_IFRAME_HEIGHT,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_CONTEXT_EXTENSIONS,
    MESSAGES,
    LOG_LEVEL,
    LOG_FORMAT,
    MAX_BRIEF_LENGTH,
    HEX_COLOR_PATTERN,
    SYSTEM_PROMPT_PATH,
)

# Configurar logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde archivo .env
load_dotenv()


def load_system_prompt() -> str:
    """
    Carga el prompt del sistema desde un archivo externo.
    
    Lee el contenido del archivo de prompt del sistema definido en SYSTEM_PROMPT_PATH.
    Si el archivo no existe o hay un error, registra el error y retorna un string vacío.
    
    Returns:
        String con el contenido del prompt del sistema
    """
    prompt_path = Path(__file__).parent / SYSTEM_PROMPT_PATH
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
            logger.debug(f"Prompt del sistema cargado: {len(content):,} caracteres")
            return content
    except FileNotFoundError:
        logger.error(f"Archivo de prompt no encontrado: {prompt_path}")
        return ""
    except IOError as e:
        logger.error(f"Error al leer prompt del sistema: {e}")
        return ""


def validate_html_response(html: str) -> bool:
    """
    Valida que la respuesta del modelo sea HTML válido.
    
    Verifica que el string comience con la declaración DOCTYPE de HTML5.
    
    Args:
        html: String con el HTML generado por el modelo
        
    Returns:
        True si el HTML es válido, False en caso contrario
    """
    if not html:
        return False
    return html.strip().lower().startswith("<!doctype html")


def validate_accent_color(color: str) -> bool:
    """
    Valida que el color de acento sea un hexadecimal válido.
    
    Args:
        color: String con el color en formato hexadecimal (#RRGGBB)
        
    Returns:
        True si el color es válido, False en caso contrario
    """
    return bool(re.match(HEX_COLOR_PATTERN, color))


@contextmanager
def temp_uploaded_files(files: list):
    """
    Context manager para gestión segura de archivos temporales.
    
    Guarda los archivos cargados en ubicaciones temporales y garantiza
    su eliminación al finalizar, incluso si ocurre una excepción.
    
    Args:
        files: Lista de objetos UploadedFile de Streamlit
        
    Yields:
        Lista de rutas absolutas a los archivos temporales creados
        
    Example:
        >>> with temp_uploaded_files(uploaded_files) as paths:
        ...     process_files(paths)
        # Los archivos se eliminan automáticamente al salir del bloque
    """
    paths = persist_uploaded_files(files)
    try:
        yield paths
    finally:
        for path in paths:
            try:
                os.unlink(path)
                logger.debug(f"Archivo temporal eliminado: {path}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar archivo temporal {path}: {e}")


def build_content(brief: str, accent: str, include_accent_hint: bool, has_avatar: bool, has_qr: bool) -> str:
    """
    Construye el contenido del prompt para el modelo de IA.
    
    Combina el brief del usuario con instrucciones adicionales sobre el color
    de acento y los archivos adjuntos (avatar y QR).
    
    Args:
        brief: Descripción del perfil profesional proporcionada por el usuario
        accent: Color hexadecimal para el acento del CV (ej: "#0b3a6e")
        include_accent_hint: Si se debe incluir la instrucción del color en el prompt
        has_avatar: Indica si se proporcionó una foto de perfil
        has_qr: Indica si se proporcionó un código QR
        
    Returns:
        String con el prompt completo para enviar al modelo
        
    Example:
        >>> build_content("Analista de datos con 5 años...", "#0b3a6e", True, True, False)
        'Analista de datos con 5 años...\\n\\nColor de acento preferido: #0b3a6e...'
    """
    parts = [brief.strip()]
    if include_accent_hint and accent:
        parts.append(f"Color de acento preferido: {accent}")
    if has_avatar:
        parts.append("Se proporcionó una foto para el avatar; conserva el atributo src=\"avatar.png\" en el HTML.")
    if has_qr:
        parts.append("Se proporcionó un código QR de LinkedIn; conserva el atributo src=\"qr.png\" en el HTML.")
    return "\n\n".join(parts)


def persist_uploaded_files(files: List) -> List[str]:
    """
    Guarda archivos cargados en ubicaciones temporales del sistema.
    
    Toma los archivos subidos por el usuario y los guarda en archivos temporales
    en el disco para que puedan ser procesados por el cliente de OpenAI.
    
    Args:
        files: Lista de objetos UploadedFile de Streamlit
        
    Returns:
        Lista de rutas absolutas a los archivos temporales creados
        
    Note:
        Los archivos temporales no se eliminan automáticamente. El llamador
        es responsable de eliminarlos después de usarlos.
    """
    temp_paths: List[str] = []
    for file in files:
        suffix = Path(file.name).suffix or ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.getbuffer())
            temp_paths.append(tmp.name)
    return temp_paths


def file_to_data_uri(file) -> Optional[str]:
    """
    Convierte un archivo cargado a un Data URI en base64.
    
    Toma un archivo de imagen y lo convierte a un formato Data URI que puede
    ser incrustado directamente en el HTML generado.
    
    Args:
        file: Objeto UploadedFile de Streamlit que contiene una imagen
        
    Returns:
        String con el Data URI (ej: "data:image/png;base64,iVBORw0KG...")
        o None si el archivo no es una imagen válida
        
    Example:
        >>> data_uri = file_to_data_uri(avatar_file)
        >>> # "data:image/png;base64,iVBORw0KGgoAAAANSU..."
    """
    mime = file.type or mimetypes.guess_type(file.name)[0] or "image/png"
    if not mime.startswith("image/"):
        return None
    data = file.getvalue()
    if not data:
        return None
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def apply_image_overrides(html: str, avatar_uri: Optional[str], qr_uri: Optional[str]) -> str:
    """
    Reemplaza las referencias de imágenes placeholder en el HTML con Data URIs reales.
    
    Sustituye los placeholders "avatar.png" y "qr.png" en el HTML generado
    con los Data URIs de las imágenes reales proporcionadas por el usuario.
    
    Args:
        html: String con el código HTML generado por el modelo
        avatar_uri: Data URI de la foto de perfil (opcional)
        qr_uri: Data URI del código QR (opcional)
        
    Returns:
        HTML actualizado con las imágenes incrustadas
        
    Note:
        Solo se realiza un reemplazo por imagen para evitar modificaciones
        no deseadas en otros lugares del HTML.
    """
    updated = html
    if avatar_uri:
        updated = updated.replace('src="avatar.png"', f'src="{avatar_uri}"', 1)
        updated = updated.replace("src='avatar.png'", f"src='{avatar_uri}'", 1)
    if qr_uri:
        updated = updated.replace('src="qr.png"', f'src="{qr_uri}"', 1)
        updated = updated.replace("src='qr.png'", f"src='{qr_uri}'", 1)
    return updated


def main() -> None:
    """
    Función principal que ejecuta la aplicación Streamlit.
    
    Configura la interfaz de usuario, maneja la entrada del usuario,
    realiza la llamada al modelo de OpenAI y muestra los resultados.
    """
    # Configuración de la página de Streamlit
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Título y descripción
    st.title("🎯 Generador de CV HTML con OpenAI")
    st.markdown(
        """Escribe un **brief** con tu perfil, experiencia y objetivos profesionales. 
        El modelo generará un CV HTML profesional listo para imprimir."""
    )

    # =========================================================================
    # SIDEBAR - Configuración
    # =========================================================================
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Estado de la API key
        api_key = os.getenv(ENV_VAR_API_KEY)
        if api_key:
            st.success(MESSAGES["api_key_found"])
        else:
            st.error(MESSAGES["api_key_missing"])
        
        st.divider()
        
        # Selección de modelo
        model = st.selectbox(
            "🤖 Modelo",
            AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(DEFAULT_MODEL),
            help="Selecciona el modelo de OpenAI a utilizar.",
        )
        
        # Color de acento
        accent = st.color_picker(
            "🎨 Color de acento",
            DEFAULT_ACCENT_COLOR,
            help="Color principal para títulos y acentos del CV.",
        )
        
        # Tokens máximos
        max_tokens = st.slider(
            "📊 Tokens máximos",
            min_value=MIN_TOKENS,
            max_value=MAX_TOKENS,
            value=DEFAULT_MAX_TOKENS,
            step=TOKEN_STEP,
            help="Límite de tokens para la respuesta del modelo.",
        )
        
        # Opción para incluir el color de acento en el prompt
        include_accent_hint = st.checkbox(
            "Incluir color en el prompt",
            value=True,
            help="Añade instrucción explícita para usar el color seleccionado.",
        )
        
        st.divider()
        
        # Información del proyecto
        st.markdown("""        
        **📚 Guía rápida:**
        1. Escribe tu perfil profesional
        2. (Opcional) Sube foto y QR
        3. Haz clic en "Generar CV"
        4. Descarga el HTML resultante
        """)

    # =========================================================================
    # ÁREA PRINCIPAL - Entrada de datos
    # =========================================================================
    
    # Campo de texto para el brief del CV
    brief = st.text_area(
        "📝 Brief del CV",
        height=BRIEF_TEXT_AREA_HEIGHT,
        placeholder=MESSAGES["brief_placeholder"],
        help="Describe tu perfil, experiencia, habilidades y objetivo profesional.",
    )
    
    # Sección de carga de imágenes (avatar y QR)
    st.subheader("📷 Imágenes (opcional)")
    col_avatar, col_qr = st.columns(2)
    
    with col_avatar:
        avatar_upload = st.file_uploader(
            "Foto de perfil",
            type=SUPPORTED_IMAGE_EXTENSIONS,
            accept_multiple_files=False,
            help="Imagen cuadrada recomendada (400x400 px o mayor).",
            key="avatar_uploader",
        )
        if avatar_upload:
            st.image(avatar_upload, caption="Vista previa", width=150)
    
    with col_qr:
        qr_upload = st.file_uploader(
            "Código QR (LinkedIn/Portfolio)",
            type=SUPPORTED_IMAGE_EXTENSIONS,
            accept_multiple_files=False,
            help="Código QR que enlace a tu perfil profesional.",
            key="qr_uploader",
        )
        if qr_upload:
            st.image(qr_upload, caption="Vista previa", width=100)

    # Archivos adicionales de contexto (colapsable)
    with st.expander("📎 Archivos de referencia adicionales", expanded=False):
        uploaded_files = st.file_uploader(
            "Adjunta documentos de apoyo",
            type=SUPPORTED_CONTEXT_EXTENSIONS,
            accept_multiple_files=True,
            help="CVs anteriores, certificados, etc. Se usan como contexto.",
            key="context_files",
        )
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} archivo(s) adjunto(s)")

    # =========================================================================
    # GENERACIÓN DEL CV
    # =========================================================================
    
    # Botón para generar el CV
    col_btn, col_status = st.columns([1, 3])
    with col_btn:
        generate = st.button(MESSAGES["generate_button"], type="primary", use_container_width=True)

    # Proceso de generación cuando se presiona el botón
    if generate:
        # Validar que se haya ingresado un brief
        if not brief.strip():
            st.warning(MESSAGES["brief_empty_warning"])
            logger.warning("Intento de generación sin brief")
            return

        # Validar longitud del brief
        if len(brief) > MAX_BRIEF_LENGTH:
            st.warning(MESSAGES["brief_too_long_warning"].format(MAX_BRIEF_LENGTH))
            logger.warning(f"Brief demasiado largo: {len(brief):,} caracteres")
            return

        # Validar color de acento
        if not validate_accent_color(accent):
            st.warning(MESSAGES["invalid_color_warning"])
            logger.warning(f"Color de acento inválido: {accent}")
            return

        # Validar API key
        if not api_key:
            st.error(MESSAGES["api_key_missing"])
            logger.error("API key no configurada")
            return

        # Cargar el prompt del sistema
        system_prompt = load_system_prompt()
        if not system_prompt:
            st.error(MESSAGES["prompt_load_error"].format("Archivo no encontrado"))
            logger.error("No se pudo cargar el prompt del sistema")
            return

        logger.info(f"Iniciando generación de CV - Modelo: {model}")

        # Convertir imágenes a Data URIs
        avatar_data_uri = file_to_data_uri(avatar_upload) if avatar_upload else None
        qr_data_uri = file_to_data_uri(qr_upload) if qr_upload else None

        # Preparar lista de archivos para enviar como contexto
        files_for_context: List = list(uploaded_files) if uploaded_files else []
        if avatar_upload:
            files_for_context.append(avatar_upload)
        if qr_upload:
            files_for_context.append(qr_upload)

        # Generar el CV usando el modelo de OpenAI
        try:
            with temp_uploaded_files(files_for_context) as temp_paths:
                user_content = build_content(brief, accent, include_accent_hint, bool(avatar_upload), bool(qr_upload))
                
                # Barra de progreso
                progress_bar = st.progress(0, text=MESSAGES["generating"])
                progress_bar.progress(30, text="🔄 Enviando solicitud a OpenAI...")
                
                # Medir tiempo de respuesta
                start_time = time_module.time()
                
                response = chat_completion(
                    system_prompt=system_prompt,
                    user_content=user_content,
                    files=temp_paths or None,
                    model=model,
                    max_output_tokens=max_tokens,
                    api_key=api_key,
                )
                
                elapsed_time = time_module.time() - start_time
                logger.info(f"Tiempo de respuesta de OpenAI: {elapsed_time:.2f}s")
                
                progress_bar.progress(80, text="📝 Procesando respuesta...")
                
                # Validar que la respuesta sea HTML válido
                if not validate_html_response(response):
                    st.error(MESSAGES["invalid_html_warning"])
                    logger.error("La respuesta del modelo no es HTML válido")
                    progress_bar.empty()
                    return
                
                # Aplicar las imágenes al HTML
                html_response = apply_image_overrides(response, avatar_data_uri, qr_data_uri)
                st.session_state["cv_html"] = html_response
                
                progress_bar.progress(100, text="✅ ¡CV generado exitosamente!")
                logger.info(f"CV generado exitosamente: {len(html_response):,} caracteres")
                
                # Limpiar la barra de progreso después de un momento
                time_module.sleep(1)
                progress_bar.empty()
                
                st.success("✅ CV generado exitosamente. Revisa el resultado abajo.")
                
        except RateLimitError as exc:
            st.error(MESSAGES["rate_limit_error"])
            logger.error(f"Rate limit error: {exc}")
            return
        except APIConnectionError as exc:
            st.error(MESSAGES["connection_error"])
            logger.error(f"Connection error: {exc}")
            return
        except APITimeoutError as exc:
            st.error(MESSAGES["timeout_error"])
            logger.error(f"Timeout error: {exc}")
            return
        except OpenAIClientError as exc:
            st.error(MESSAGES["generation_error"].format(str(exc)))
            logger.error(f"Error de cliente OpenAI: {exc}")
            return
        except Exception as exc:
            st.error(MESSAGES["generation_error"].format(str(exc)))
            logger.exception(f"Error inesperado durante la generación: {exc}")
            return

    # =========================================================================
    # VISTA PREVIA Y DESCARGA
    # =========================================================================
    
    if "cv_html" in st.session_state:
        html = st.session_state["cv_html"]
        
        st.divider()
        st.subheader("👁️ Vista Previa del CV")
        
        # Vista previa del CV en un iframe
        st.components.v1.html(html, height=PREVIEW_IFRAME_HEIGHT, scrolling=True)
        
        # Botones de acción
        col_download, col_clear, col_info = st.columns([1, 1, 2])
        
        with col_download:
            st.download_button(
                MESSAGES["download_button"],
                data=html,
                file_name="cv.html",
                mime="text/html",
                use_container_width=True,
            )
        
        with col_clear:
            if st.button(MESSAGES["clear_button"], use_container_width=True):
                st.session_state.pop("cv_html", None)
                st.rerun()
        
        with col_info:
            st.caption(f"📄 Tamaño del HTML: {len(html):,} caracteres")


if __name__ == "__main__":
    main()
