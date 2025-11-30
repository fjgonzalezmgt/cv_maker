"""
Cliente de OpenAI para procesamiento de imágenes y archivos.

Este módulo proporciona funcionalidades para interactuar con la API de OpenAI,
incluyendo el procesamiento y envío de imágenes y archivos, así como la generación
de respuestas mediante modelos de chat.

Autor: Francisco González
Fecha: Noviembre 2025
Organización: Quality Analytics
"""

from __future__ import annotations

import base64
import io
import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional, Union

from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from PIL import Image

from config import (
    ENV_VAR_API_KEY,
    MAX_FILE_BYTES,
    MAX_IMAGE_SIDE,
    JPEG_QUALITY,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    API_TIMEOUT,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configurar logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Extensiones de imagen soportadas y sus tipos MIME correspondientes
IMAGE_EXTS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

# Configuración de reintentos
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # segundos, se usa exponential backoff


class OpenAIClientError(Exception):
    """Excepción base para errores del cliente OpenAI."""
    pass


class APIKeyMissingError(OpenAIClientError):
    """Error cuando no se encuentra la API key."""
    pass


class FileProcessingError(OpenAIClientError):
    """Error al procesar archivos."""
    pass


def _resize_image_bytes(path: str, max_side: int = MAX_IMAGE_SIDE, quality: int = JPEG_QUALITY) -> bytes:
    """
    Redimensiona una imagen y la convierte a JPEG optimizado.
    
    Esta función toma una imagen de cualquier formato soportado, la convierte a RGB,
    y la redimensiona si es necesario para que su lado más grande no exceda max_side.
    Finalmente, la guarda como JPEG optimizado con la calidad especificada.
    
    Args:
        path: Ruta al archivo de imagen a procesar.
        max_side: Tamaño máximo permitido para el lado más largo (default: 2048).
        quality: Calidad de compresión JPEG 1-100 (default: 85).
    
    Returns:
        bytes: Los bytes de la imagen procesada en formato JPEG.
    
    Raises:
        FileProcessingError: Si hay un error al procesar la imagen.
    """
    logger.debug(f"Procesando imagen: {path}")
    
    try:
        im = Image.open(path).convert("RGB")
        w, h = im.size
        logger.debug(f"Tamaño original: {w}x{h}")
        
        if max(w, h) > max_side:
            scale = max_side / float(max(w, h))
            new_w, new_h = int(w * scale), int(h * scale)
            im = im.resize((new_w, new_h))
            logger.debug(f"Redimensionada a: {new_w}x{new_h}")
        
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality, optimize=True)
        result = buf.getvalue()
        logger.debug(f"Imagen convertida a JPEG: {len(result):,} bytes")
        return result
        
    except Exception as e:
        logger.error(f"Error al procesar imagen {path}: {e}")
        raise FileProcessingError(f"No se pudo procesar la imagen: {path}") from e


def _guess_mime(path: str) -> str:
    """
    Determina el tipo MIME basándose en la extensión del archivo.
    
    Args:
        path: Ruta al archivo cuyo tipo MIME se desea determinar.
    
    Returns:
        El tipo MIME del archivo.
    """
    ext = os.path.splitext(path.lower())[1]
    
    if ext in IMAGE_EXTS:
        return IMAGE_EXTS[ext]
    if ext == ".pdf":
        return "application/pdf"
    return "application/octet-stream"


def _file_to_content_items(path: str, max_bytes: int = MAX_FILE_BYTES) -> List[dict]:
    """
    Convierte un archivo a items de contenido para la API de OpenAI.
    
    Esta función procesa archivos de diferentes tipos:
    - Imágenes: redimensiona automáticamente y retorna como 'input_image'
    - Otros archivos: codifica en base64 y retorna como 'input_file'
    
    Args:
        path: Ruta al archivo a procesar.
        max_bytes: Tamaño máximo permitido en bytes (default: 8 MB).
    
    Returns:
        Lista de items de contenido para la API.
    
    Raises:
        FileNotFoundError: Si el archivo no existe.
        FileProcessingError: Si hay un error al procesar el archivo.
    """
    logger.debug(f"Procesando archivo: {path}")
    
    if not os.path.exists(path):
        logger.error(f"Archivo no encontrado: {path}")
        raise FileNotFoundError(f"El archivo no existe: {path}")
    
    mime = _guess_mime(path)
    ext = os.path.splitext(path)[1].lower()
    
    # Procesar imágenes
    if ext in IMAGE_EXTS:
        logger.debug("Procesando como imagen")
        data = _resize_image_bytes(path)
        b64 = base64.b64encode(data).decode("ascii")
        return [{"type": "input_image", "image_url": f"data:{mime};base64,{b64}"}]
    
    # Procesar otros archivos
    logger.debug("Procesando como archivo genérico")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except IOError as e:
        logger.error(f"Error al leer archivo {path}: {e}")
        raise FileProcessingError(f"No se pudo leer el archivo: {path}") from e
    
    truncated = False
    original_size = len(raw)
    
    if original_size > max_bytes:
        raw = raw[:max_bytes]
        truncated = True
        logger.warning(f"Archivo truncado: {original_size:,} -> {max_bytes:,} bytes")
    
    b64 = base64.b64encode(raw).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    
    items: List[dict] = [
        {
            "type": "input_file",
            "filename": os.path.basename(path),
            "file_data": data_url,
        }
    ]
    
    if truncated:
        items.append({
            "type": "input_text",
            "text": f"⚠️ Advertencia: '{os.path.basename(path)}' truncado de {original_size:,} a {max_bytes:,} bytes.",
        })
    
    logger.debug(f"Archivo procesado: {len(items)} items de contenido")
    return items


def create_openai_client(
    api_key: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    timeout: float = API_TIMEOUT,
) -> OpenAI:
    """
    Crea y retorna un cliente de OpenAI configurado.
    
    Args:
        api_key: API key de OpenAI. Si es None, se usa la variable de entorno.
        organization: ID de la organización de OpenAI (opcional).
        project: ID del proyecto de OpenAI (opcional).
        timeout: Tiempo máximo de espera en segundos (default: 120).
    
    Returns:
        Cliente de OpenAI configurado.
    
    Raises:
        APIKeyMissingError: Si no se encuentra la API key.
    """
    logger.debug("Creando cliente OpenAI")
    
    resolved_api_key = api_key or os.getenv(ENV_VAR_API_KEY)
    
    if not resolved_api_key:
        logger.error("API key no encontrada")
        raise APIKeyMissingError(
            f"No se encontró la API key. Define {ENV_VAR_API_KEY} en el entorno o archivo .env"
        )
    
    # Log ofuscado de la API key para debugging
    key_preview = f"{resolved_api_key[:8]}...{resolved_api_key[-4:]}" if len(resolved_api_key) > 12 else "***"
    logger.debug(f"Usando API key: {key_preview}")
    
    client = OpenAI(
        api_key=resolved_api_key,
        organization=organization,
        project=project,
        timeout=timeout,
    )
    
    logger.debug("Cliente OpenAI creado exitosamente")
    return client


def _execute_with_retry(func, max_retries: int = MAX_RETRIES):
    """
    Ejecuta una función con reintentos y backoff exponencial.
    
    Args:
        func: Función a ejecutar.
        max_retries: Número máximo de reintentos.
    
    Returns:
        Resultado de la función.
    
    Raises:
        La última excepción si todos los reintentos fallan.
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except RateLimitError as e:
            last_exception = e
            if attempt < max_retries:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"Rate limit alcanzado. Reintentando en {delay}s... (intento {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                logger.error("Rate limit: máximo de reintentos alcanzado")
        except APIConnectionError as e:
            last_exception = e
            if attempt < max_retries:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"Error de conexión. Reintentando en {delay}s... (intento {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                logger.error("Error de conexión: máximo de reintentos alcanzado")
        except APIError as e:
            # Para otros errores de API, no reintentar
            logger.error(f"Error de API: {e}")
            raise
    
    raise last_exception


def chat_completion(
    system_prompt: str,
    user_content: Union[str, List[str]],
    *,
    files: Optional[List[str]] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_output_tokens: Optional[int] = None,
    stream: bool = False,
    extra_messages: Optional[List[dict]] = None,
    max_file_bytes: int = MAX_FILE_BYTES,
    reasoning: Optional[Dict[str, Any]] = None,
    text: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    timeout: float = API_TIMEOUT,
) -> Union[str, Iterable[str]]:
    """
    Realiza una consulta a la API de OpenAI usando Responses API.
    
    Esta es la función principal del módulo que permite interactuar con los modelos de
    chat de OpenAI. Soporta el envío de texto, imágenes y archivos, así como streaming.
    
    Args:
        system_prompt: Prompt del sistema que define el comportamiento del modelo.
        user_content: Contenido del mensaje del usuario (string o lista).
        files: Lista de rutas de archivos a adjuntar (opcional).
        model: Modelo de OpenAI a utilizar (default: gpt-4.1-mini).
        temperature: Control de aleatoriedad 0-2 (default: 0.2).
        max_output_tokens: Máximo de tokens en respuesta (opcional).
        stream: Si True, retorna generador con respuesta en tiempo real.
        extra_messages: Mensajes adicionales para la conversación (opcional).
        max_file_bytes: Tamaño máximo de archivos (default: 8 MB).
        reasoning: Parámetros de razonamiento del modelo (opcional).
        text: Parámetros de generación de texto (opcional).
        api_key: API key de OpenAI (opcional, usa entorno si no se provee).
        organization: ID de organización (opcional).
        project: ID de proyecto (opcional).
        timeout: Timeout en segundos (default: 120).
    
    Returns:
        String con respuesta completa, o generador si stream=True.
    
    Raises:
        ValueError: Si no hay contenido para enviar.
        OpenAIClientError: Si hay errores de configuración.
        APIError: Si hay errores en la comunicación con OpenAI.
    """
    logger.info(f"Iniciando chat_completion - Modelo: {model}")
    logger.debug(f"Temperatura: {temperature}, Max tokens: {max_output_tokens}, Stream: {stream}")
    
    # Crear cliente
    openai_api = create_openai_client(api_key, organization, project, timeout)
    
    # Preparar contenido del usuario
    if isinstance(user_content, list):
        user_text = "\n\n".join([u for u in user_content if u])
        logger.debug(f"Contenido: lista de {len(user_content)} elementos")
    else:
        user_text = user_content or ""
        logger.debug(f"Contenido: string de {len(user_text)} caracteres")
    
    user_content_items: List[dict] = []
    if user_text:
        user_content_items.append({"type": "input_text", "text": user_text})
    
    # Agregar archivos
    if files:
        logger.info(f"Procesando {len(files)} archivos adjuntos")
        for f in files:
            try:
                user_content_items.extend(_file_to_content_items(f, max_bytes=max_file_bytes))
            except (FileNotFoundError, FileProcessingError) as e:
                logger.warning(f"Omitiendo archivo {f}: {e}")
    
    # Construir mensajes de entrada
    input_messages: List[dict] = []
    
    if system_prompt:
        input_messages.append({
            "role": "developer",
            "content": [{"type": "input_text", "text": system_prompt}],
        })
    
    if user_content_items:
        input_messages.append({"role": "user", "content": user_content_items})
    
    if extra_messages:
        input_messages.extend(extra_messages)
        logger.debug(f"Añadidos {len(extra_messages)} mensajes adicionales")
    
    if not input_messages:
        raise ValueError("Se requiere al menos un contenido para enviar a la API")
    
    logger.debug(f"Total de mensajes a enviar: {len(input_messages)}")
    
    # Preparar parámetros de la API
    api_params = {
        "model": model,
        "input": input_messages,
    }
    
    if temperature is not None:
        api_params["temperature"] = temperature
    if max_output_tokens is not None:
        api_params["max_output_tokens"] = max_output_tokens
    if reasoning is not None:
        api_params["reasoning"] = reasoning
    if text is not None:
        api_params["text"] = text
    
    # Ejecutar solicitud
    if stream:
        logger.info("Iniciando respuesta en streaming")
        api_params["stream"] = True
        
        def _make_stream_request():
            return openai_api.responses.create(**api_params)
        
        events = _execute_with_retry(_make_stream_request)
        
        def _gen():
            for ev in events:
                if ev.type == "response.output_text.delta":
                    yield ev.delta
                elif ev.type == "response.error":
                    logger.error(f"Error en streaming: {ev.error}")
                    raise OpenAIClientError(str(ev.error))
            logger.info("Streaming completado")
        
        return _gen()
    
    # Solicitud sin streaming
    logger.info("Realizando solicitud a OpenAI API")
    
    def _make_request():
        return openai_api.responses.create(**api_params)
    
    resp = _execute_with_retry(_make_request)
    output = (getattr(resp, "output_text", "") or "").strip()
    
    logger.info(f"Respuesta recibida: {len(output):,} caracteres")
    return output