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
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import List, Optional

import streamlit as st

from openai_client import chat_completion
from dotenv import load_dotenv

# Prompt del sistema que define las reglas de generación de CV para el modelo de IA
SYSTEM_PROMPT = """## System Prompt (pégalo como "System" en tu GPT)

Eres un generador de CVs en HTML. Tu única salida debe ser **un documento HTML completo** y **auto-contenido** (con `<!DOCTYPE html>`, `<html>`, `<head>`, `<style>`, `<body>`) que respete **exactamente** la estructura, clases y estilos del **template base** incluido al final de este mensaje. Tu función es transformar un brief o prompt del usuario en un CV profesional y listo para imprimir, adaptado a su perfil y objetivo.

### Reglas obligatorias

1. **Salida única y exclusiva:** devuelve **solo** el HTML final. No incluyas comentarios, explicaciones, instrucciones, ni texto fuera del HTML. No uses emojis.
2. **Template inalterable:** conserva **idénticos** el layout, nombres de clases CSS, media queries y reglas de impresión del template. Puedes:

   * Reemplazar contenido textual.
   * Actualizar enlaces (`tel:`, `mailto:`, `https://`).
   * Cambiar `src` de imágenes (avatar/QR) por rutas proporcionadas o placeholders.
   * Opcionalmente actualizar `--accent` (variable CSS) a un color pedido por el usuario.
     Está **prohibido** eliminar secciones, renombrar clases o reescribir el CSS.
3. **Idioma y tono:** usa el idioma del usuario (por defecto español neutro). Redacción concisa, orientada a impacto y legible por ATS.
4. **Estructura de contenido:**

   * Encabezado: nombre, tagline/perfil corto, datos de contacto (ubicación, teléfono, correo, LinkedIn, sitio, otros).
   * Foto/QR: si el usuario no da imagen/QR, deja `src="avatar.png"` / `src="qr.png"` como placeholder y `alt` descriptivo.
   * Columnas:

     * **Izquierda:** Perfil (resumen), Certificaciones (bullets), Habilidades (como “pills”), Idiomas (bullets con nivel), Membresías/Reconocimientos (bullets).
     * **Derecha:** Experiencia (entradas cronológicas recientes→antiguas), Educación (entradas).
5. **Formato de entradas (Experiencia/Educación):**

   * `<article class="entry">`

     * `<h3>`: cargo o título del programa.
     * `<div class="meta">` con **ubicación** y **rango de fechas** (mes abreviado y año, en minúsculas, p. ej. `sep 2022 – presente`). Usa guion en (–) en el rango. Localiza meses al idioma del usuario.
     * `<p>`: logros y alcance. Escribe en estilo resultado→métrica→medio (si hay datos). Usa verbos de acción. Evita jerga innecesaria.
6. **Normalización de datos si faltan campos:**

   * Si faltan teléfono, correo, links o imágenes: coloca placeholders plausibles y consistentes, sin inventar datos personales sensibles.
   * Si no hay experiencia formal: prioriza proyectos, freelance, prácticas, voluntariado o cursos con entregables.
   * Si el usuario da bullets sueltos, conviértelos a redacción fluida o bullets compactos según la sección.
7. **Medición e impacto:**

   * Cuando el usuario provea métricas, inclúyelas. Si no hay, evita inventarlas.
   * Puedes estimar **rango cualitativo** (“reducción significativa”, “mejora sustancial”) solo si el usuario no quiere números.
8. **Adaptación al objetivo:**

   * Ajusta tagline, resumen y orden de secciones según objetivo (p. ej., “Data Analyst”, “Calidad”, “Operaciones”, “PM”).
   * Destaca habilidades y proyectos relevantes al rol objetivo y al mercado/país indicado.
9. **Accesibilidad y ATS:**

   * Mantén texto plano semántico (sin tablas para contenido). Evita símbolos crípticos.
   * Usa `alt` descriptivo en imágenes.
10. **Validación final antes de entregar:**

    * HTML bien formado y listo para impresión A4 (el template ya lo soporta).
    * Sin texto marcador tipo “lorem ipsum” salvo que el usuario lo pida.
    * Enlaces `mailto:`/`tel:` y URLs con protocolo (`https://`).
    * Fechas ordenadas de reciente a antiguo en Experiencia.

### Mapeo desde el prompt del usuario

* **Identidad:** nombre, titular/tagline, ubicación.
* **Contacto:** teléfono, email, LinkedIn, web, portfolio, GitHub.
* **Resumen/Perfil:** 3–5 líneas con rol objetivo + años de experiencia + áreas clave + herramientas/metodologías.
* **Habilidades técnicas:** máximo 20 “pills” priorizadas para el rol objetivo.
* **Experiencia:** para cada empleo: cargo, empresa, país/ciudad, fechas (mes/año), 1–3 impactos medibles.
* **Educación:** título/programa, institución, año/rango.
* **Certificaciones:** nombre, institución, credencial/año si existe.
* **Idiomas:** nivel claro (nativo, avanzado, intermedio, básico).
* **Membresías/Reconocimientos:** bullets breves.

### Placeholders por defecto si faltan datos

* Avatar: `src="avatar.png"`, alt genérico.
* QR/Link: `src="qr.png"` si se solicita.
* Teléfono: `tel:+0000000000`
* Correo: `mailto:nombre.apellido@email.com`
* LinkedIn: `https://www.linkedin.com/in/usuario`
* Sitio: `https://example.com`

### Preferencias tipográficas y estilo

* Mantén frases cortas, con sustantivos concretos y verbos de impacto.
* Evita párrafos densos; 1–3 oraciones por entrada.
* No repitas la misma métrica/beneficio en varias entradas.

---

### TEMPLATE BASE (usa este HTML tal cual y solo reemplaza contenido y, si aplica, `--accent`)

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>CV – {{NOMBRE_COMPLETO}}</title>
<style>
  :root{
    --accent:#0b3a6e; /* puedes adaptar si el usuario lo pide */
    --text:#1e1f23;
    --muted:#555;
    --rule:#e4e7ec;
  }
  body{
    font-family:"Segoe UI",Helvetica,Arial,sans-serif;
    color:var(--text);
    line-height:1.55;
    margin:0;
    background:#fff;
  }
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline}
  .page{max-width:1000px;margin:48px auto;padding:0 24px;}
  .header{
    display:grid;
    grid-template-columns:1fr 180px;
    gap:24px;
    padding-bottom:18px;
    border-bottom:3px solid var(--accent);
  }
  .name{
    font-size:34px;
    font-weight:800;
    margin:0 0 6px 0;
    color:var(--accent);
  }
  .tagline{
    font-size:18px;
    margin:0 0 14px 0;
    color:#1f2d3a;
    font-weight:600;
  }
  .contact p{
    margin:4px 0;
    color:var(--muted);
    font-size:15px;
  }
  .contact span{margin-right:8px;font-weight:600;}
  .photo-box { display:flex; flex-direction:column; align-items:center; gap:10px; }
  .avatar { width:160px; height:160px; object-fit:cover; border-radius:10px; border:3px solid #dfe5ee; box-shadow:0 2px 8px rgba(13,25,44,.06); }
  .qr { width:90px; height:90px; object-fit:contain; border:2px solid #e4e7ec; border-radius:6px; background:white; box-shadow:0 1px 6px rgba(0,0,0,.08); }
  .columns{ display:grid; grid-template-columns:300px 1fr; gap:32px; margin-top:28px; }
  .left{ border-right:1px solid var(--rule); padding-right:24px; }
  .right{ padding-left:4px; }
  .section-title{ font-size:15px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; color:var(--accent); margin:22px 0 8px 0; border-bottom:1px solid var(--rule); padding-bottom:6px; }
  .list{ margin:8px 0 0 0; padding-left:18px; }
  .list li{ margin:6px 0; }
  .entry{ margin:16px 0 18px 0; }
  .entry h3{ font-size:17px; margin:0 0 4px 0; color:#0d2f58; }
  .entry .meta{ font-size:13px; color:var(--muted); margin-bottom:6px; }
  .entry p{ margin:0; }
  .pill{ display:inline-block; font-size:12px; border:1px solid var(--rule); border-radius:999px; padding:6px 10px; margin:5px 6px 0 0; background:#fafbfd; }
  .summary{ margin:6px 0 10px 0; font-size:14px; }
  @media(max-width:820px){
    .columns{ grid-template-columns:1fr; }
    .left{ border-right:none; padding-right:0; border-bottom:1px solid var(--rule); padding-bottom:16px; margin-bottom:12px; }
    .header{ grid-template-columns:1fr 140px; }
    .avatar{ width:140px; height:140px; }
    .qr{ width:80px; height:80px; }
  }
  @media print {
    @page { size: A4 portrait; margin: 1.3cm; }
    body { background:#fff; color:#000; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
    .page { margin:0; padding:0; max-width:100%; }
    .header { grid-template-columns:1fr 130px; border-bottom:2px solid #003366; margin-bottom:6px; padding-bottom:6px; page-break-after:avoid; page-break-inside:avoid; }
    .photo-box { gap:6px; }
    .avatar { width:110px; height:110px; }
    .qr { width:70px; height:70px; }
    h1, h2, h3, .section-title { page-break-after:avoid; page-break-inside:avoid; break-after:avoid; break-inside:avoid; }
    .entry, ul, p { page-break-inside:avoid; break-inside:avoid; }
    .columns { grid-template-columns:260px 1fr; gap:18px; page-break-inside:auto; break-inside:auto; }
    .name { font-size:28px; line-height:1.15; }
    .tagline { font-size:15px; margin-bottom:8px; }
    .contact p { font-size:12px; margin:2px 0; }
    .summary, .entry p, .list li { font-size:12px; }
    .pill { font-size:10px; padding:3px 7px; }
    a[href^="http"]:after { content:""; }
    .section-title { margin-top:12px; margin-bottom:4px; padding-bottom:3px; font-size:13px; }
    .entry { margin:10px 0 12px 0; }
    .left, .right { break-inside:avoid; page-break-inside:avoid; }
    html { zoom:0.95; }
  }
</style>
</head>
<body>
  <main class="page">
    <header class="header">
      <div>
        <h1 class="name">{{NOMBRE_COMPLETO}}</h1>
        <p class="tagline">{{TAGLINE}}</p>
        <div class="contact">
          <p>📍 <span>Ubicación:</span> {{UBICACION}}</p>
          <p>📞 <span>Teléfono:</span> <a href="tel:{{TEL_LINK}}">{{TEL_TEXTO}}</a></p>
          <p>✉️ <span>Correo:</span> <a href="mailto:{{EMAIL}}">{{EMAIL}}</a></p>
          <p>💼 <span>LinkedIn:</span> <a href="{{LINKEDIN_URL}}">{{LINKEDIN_TEXTO}}</a></p>
          <p>🌐 <span>Sitio web:</span> <a href="{{WEB_URL}}">{{WEB_TEXTO}}</a></p>
          <p>🗂 <span>Portfolio:</span> <a href="{{PORTFOLIO_URL}}">{{PORTFOLIO_TEXTO}}</a></p>
        </div>
      </div>
      <div class="photo-box">
        <img class="avatar" src="{{AVATAR_SRC}}" alt="{{AVATAR_ALT}}" />
        <img class="qr" src="{{QR_SRC}}" alt="{{QR_ALT}}" />
      </div>
    </header>

    <section class="columns">
      <aside class="left">
        <h2 class="section-title">Perfil</h2>
        <p class="summary">{{RESUMEN}}</p>

        <h2 class="section-title">Certificaciones</h2>
        <ul class="list">
          {{#each CERTIFICACIONES}}
          <li>{{this}}</li>
          {{/each}}
        </ul>

        <h2 class="section-title">Habilidades técnicas</h2>
        <div>
          {{#each HABILIDADES}}
          <div class="pill">{{this}}</div>
          {{/each}}
        </div>

        <h2 class="section-title">Idiomas</h2>
        <ul class="list">
          {{#each IDIOMAS}}
          <li>{{this}}</li>
          {{/each}}
        </ul>

        <h2 class="section-title">Membresías y reconocimientos</h2>
        <ul class="list">
          {{#each MEMBRESIAS}}
          <li>{{this}}</li>
          {{/each}}
        </ul>
      </aside>

      <section class="right">
        <h2 class="section-title">Experiencia</h2>
        {{#each EXPERIENCIA}}
        <article class="entry">
          <h3>{{CARGO}} — {{EMPRESA}}</h3>
          <div class="meta">{{UBICACION}} · {{FECHA_INICIO}} – {{FECHA_FIN}}</div>
          <p>{{DESCRIPCION}}</p>
        </article>
        {{/each}}

        <h2 class="section-title">Educación</h2>
        {{#each EDUCACION}}
        <article class="entry">
          <h3>{{TITULO}} — {{INSTITUCION}}</h3>
          <div class="meta">{{FECHAS}}</div>
        </article>
        {{/each}}
      </section>
    </section>
  </main>
</body>
</html>
```
"""

# Constantes de configuración
DEFAULT_ACCENT = "#0b3a6e"  # Color azul oscuro por defecto para el acento del CV
DEFAULT_MODEL = "gpt-4.1-mini"  # Modelo de OpenAI predeterminado
AVAILABLE_MODELS: List[str] = [
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-4o-mini",
    "gpt-4o",
]
ENV_VAR_NAME = "OPENAI_API_KEY"  # Nombre de la variable de entorno para la API key

# Cargar variables de entorno desde archivo .env
load_dotenv()


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
    
    La aplicación consta de:
    - Sidebar con configuración del modelo y parámetros
    - Área principal con campos de entrada (brief, imágenes, archivos)
    - Botón de generación que invoca el modelo de IA
    - Vista previa del CV generado
    - Botón de descarga del HTML resultante
    
    Raises:
        Exception: Si hay errores en la comunicación con OpenAI
        
    Note:
        Requiere que OPENAI_API_KEY esté definida en las variables de entorno
        o en un archivo .env en el directorio del proyecto.
    """
    # Configuración de la página de Streamlit
    st.set_page_config(page_title="Generador de CV HTML", layout="wide")
    st.title("Generador de CV HTML con OpenAI")
    st.write(
        "Escribe un brief con el perfil, experiencia y objetivos. El modelo entregará un CV HTML listo para imprimir basándose en el template provisto."
    )

    # Sidebar con opciones de configuración
    with st.sidebar:
        st.header("Configuración")
    model = st.selectbox("Modelo", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(DEFAULT_MODEL))
    accent = st.color_picker("Color de acento", DEFAULT_ACCENT)
    max_tokens = st.slider("Tokens máximos de salida", min_value=1024, max_value=8000, value=6000, step=256)
    
    # Verificar si la API key está configurada
    if os.getenv(ENV_VAR_NAME):
      st.success("Clave de API detectada en el entorno.")
    else:
      st.error(f"No se encontró {ENV_VAR_NAME} en el entorno ni en el archivo .env.")

    # Campo de texto para el brief del CV
    brief = st.text_area(
        "Brief del CV",
        height=320,
        placeholder="Ejemplo: Perfil senior de analítica de datos con 8 años en retail, habilidades en SQL, Python, Power BI...",
    )
    
    # Sección de carga de imágenes (avatar y QR)
    col_avatar, col_qr = st.columns(2)
    with col_avatar:
        avatar_upload = st.file_uploader(
            "Foto (opcional)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
            help="Se usará para reemplazar el avatar del template.",
            key="avatar_uploader",
        )
    with col_qr:
        qr_upload = st.file_uploader(
            "QR de LinkedIn (opcional)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
            help="Se mostrará en el espacio del código QR.",
            key="qr_uploader",
        )

    # Archivos adicionales de contexto
    uploaded_files = st.file_uploader(
        "Adjunta archivos de referencia (opcional)",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        accept_multiple_files=True,
        help="Se enviarán como contexto adicional al modelo.",
        key="context_files",
    )
    
    # Opción para incluir el color de acento en el prompt
    include_accent_hint = st.checkbox(
        "Incluir el color seleccionado en el prompt", value=True, help="Añade una instrucción explícita para cambiar --accent."
    )

    # Botón para generar el CV
    generate = st.button("Generar CV", type="primary")

    # Proceso de generación cuando se presiona el botón
    if generate:
        # Validar que se haya ingresado un brief
        if not brief.strip():
            st.warning("Ingresa un brief para generar el CV.")
            return

        # Obtener la API key
        api_key = os.getenv(ENV_VAR_NAME)
        if not api_key:
            st.error("Define la API Key en el archivo .env o en la variable de entorno OPENAI_API_KEY.")
            return

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
        temp_paths: List[str] = []
        try:
            temp_paths = persist_uploaded_files(files_for_context)
            user_content = build_content(brief, accent, include_accent_hint, bool(avatar_upload), bool(qr_upload))
            with st.spinner("Generando CV..."):
                response = chat_completion(
                    system_prompt=SYSTEM_PROMPT,
                    user_content=user_content,
                    files=temp_paths or None,
                    model=model,
                    max_output_tokens=max_tokens,
                    api_key=api_key,
                )
        except Exception as exc:  # pragma: no cover - Streamlit handler
            st.error(f"Error al generar el CV: {exc}")
            return
        finally:
            # Limpiar archivos temporales
            for path in temp_paths:
                try:
                    os.unlink(path)
                except OSError:
                    pass

        # Aplicar las imágenes al HTML y guardar en sesión
        html_response = apply_image_overrides(response, avatar_data_uri, qr_data_uri)
        st.session_state["cv_html"] = html_response

    # Mostrar el CV generado si existe en la sesión
    if "cv_html" in st.session_state:
        html = st.session_state["cv_html"]
        # Vista previa del CV en un iframe
        st.components.v1.html(html, height=900, scrolling=True)
        # Botón para descargar el HTML
        st.download_button("Descargar HTML", data=html, file_name="cv.html", mime="text/html")
        # Botón para limpiar el resultado
        if st.button("Limpiar resultado"):
            st.session_state.pop("cv_html", None)


if __name__ == "__main__":
    main()
