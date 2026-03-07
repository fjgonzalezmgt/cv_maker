"""
Configuración centralizada para el Generador de CV.

Este módulo contiene todas las constantes y configuraciones del proyecto,
facilitando el mantenimiento y la personalización.

Autor: Francisco González
Fecha: Noviembre 2025
"""

from typing import List

# =============================================================================
# CONFIGURACIÓN DE OPENAI
# =============================================================================

# Nombre de la variable de entorno para la API key
ENV_VAR_API_KEY: str = "OPENAI_API_KEY"

# Modelo predeterminado de OpenAI
DEFAULT_MODEL: str = "gpt-5.4"

# Modelos disponibles para selección
AVAILABLE_MODELS: List[str] = [
    "gpt-5.4",
    "gpt-5.2",
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-4o-mini",
    "gpt-4o",
]

# Configuración de tokens
DEFAULT_MAX_TOKENS: int = 6000
MIN_TOKENS: int = 1024
MAX_TOKENS: int = 8000
TOKEN_STEP: int = 256

# Temperatura por defecto para generación
DEFAULT_TEMPERATURE: float = 0.2

# Timeout para llamadas a la API (segundos)
API_TIMEOUT: float = 120.0

# =============================================================================
# CONFIGURACIÓN DE ARCHIVOS
# =============================================================================

# Tamaño máximo de archivo en bytes (8 MB)
MAX_FILE_BYTES: int = 8_000_000

# Tamaño máximo para redimensionar imágenes (píxeles)
MAX_IMAGE_SIDE: int = 2048

# Calidad de compresión JPEG
JPEG_QUALITY: int = 85

# Extensiones de imagen soportadas
SUPPORTED_IMAGE_EXTENSIONS: List[str] = ["png", "jpg", "jpeg", "webp"]

# Extensiones de archivos de contexto soportadas
SUPPORTED_CONTEXT_EXTENSIONS: List[str] = ["png", "jpg", "jpeg", "webp", "pdf"]

# =============================================================================
# CONFIGURACIÓN DE UI
# =============================================================================

# Color de acento por defecto (azul oscuro)
DEFAULT_ACCENT_COLOR: str = "#0b3a6e"

# Idiomas disponibles para el CV
AVAILABLE_LANGUAGES: List[str] = ["Español", "English"]
DEFAULT_LANGUAGE: str = "Español"

# Título de la página
PAGE_TITLE: str = "Generador de CV HTML"

# Altura del área de texto para el brief
BRIEF_TEXT_AREA_HEIGHT: int = 320

# Altura del iframe de vista previa
PREVIEW_IFRAME_HEIGHT: int = 900

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

# Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: str = "INFO"

# Formato de logging
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =============================================================================
# CONFIGURACIÓN DE VALIDACIÓN
# =============================================================================

# Longitud máxima del brief en caracteres
MAX_BRIEF_LENGTH: int = 15000

# Patrón de validación de color hexadecimal
HEX_COLOR_PATTERN: str = r"^#[0-9A-Fa-f]{6}$"

# =============================================================================
# RUTAS DE ARCHIVOS
# =============================================================================

# Ruta al archivo del prompt del sistema
SYSTEM_PROMPT_PATH: str = "prompts/system_prompt.md"

# =============================================================================
# MENSAJES DE UI
# =============================================================================

MESSAGES = {
    "api_key_found": "✅ Clave de API detectada en el entorno.",
    "api_key_missing": "❌ No se encontró OPENAI_API_KEY en el entorno ni en el archivo .env.",
    "brief_placeholder": "Ejemplo: Perfil senior de analítica de datos con 8 años en retail, habilidades en SQL, Python, Power BI...",
    "brief_empty_warning": "⚠️ Ingresa un brief para generar el CV.",
    "brief_or_files_required": "⚠️ Debes ingresar un brief o adjuntar al menos un documento de referencia.",
    "brief_too_long_warning": "⚠️ El brief es demasiado largo. Máximo {} caracteres.",
    "invalid_color_warning": "⚠️ Color de acento inválido. Usa formato hexadecimal (#RRGGBB).",
    "invalid_html_warning": "⚠️ La respuesta del modelo no es HTML válido. Intenta de nuevo.",
    "generating": "🔄 Generando CV...",
    "generation_error": "❌ Error al generar el CV: {}",
    "rate_limit_error": "⏳ Demasiadas solicitudes. Por favor espera un momento e intenta de nuevo.",
    "connection_error": "🌐 Error de conexión. Verifica tu conexión a internet.",
    "timeout_error": "⏱️ La solicitud tardó demasiado. Intenta con un brief más corto o menos archivos.",
    "download_button": "📥 Descargar HTML",
    "clear_button": "🗑️ Limpiar resultado",
    "generate_button": "🚀 Generar CV",
    "prompt_load_error": "❌ No se pudo cargar el prompt del sistema: {}",
}
