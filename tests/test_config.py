"""
Tests para el módulo de configuración.

Verifica que todas las constantes estén definidas correctamente
y tengan los tipos esperados.
"""

import pytest
from config import (
    ENV_VAR_API_KEY,
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    DEFAULT_MAX_TOKENS,
    MIN_TOKENS,
    MAX_TOKENS,
    TOKEN_STEP,
    DEFAULT_TEMPERATURE,
    API_TIMEOUT,
    MAX_FILE_BYTES,
    MAX_IMAGE_SIDE,
    JPEG_QUALITY,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_CONTEXT_EXTENSIONS,
    DEFAULT_ACCENT_COLOR,
    PAGE_TITLE,
    BRIEF_TEXT_AREA_HEIGHT,
    PREVIEW_IFRAME_HEIGHT,
    LOG_LEVEL,
    LOG_FORMAT,
    MESSAGES,
)


class TestOpenAIConfig:
    """Tests para configuración de OpenAI."""
    
    def test_env_var_name_is_string(self):
        """ENV_VAR_API_KEY debe ser un string no vacío."""
        assert isinstance(ENV_VAR_API_KEY, str)
        assert len(ENV_VAR_API_KEY) > 0
    
    def test_default_model_in_available(self):
        """El modelo por defecto debe estar en la lista de disponibles."""
        assert DEFAULT_MODEL in AVAILABLE_MODELS
    
    def test_available_models_not_empty(self):
        """Debe haber al menos un modelo disponible."""
        assert len(AVAILABLE_MODELS) > 0
    
    def test_token_limits_valid(self):
        """Los límites de tokens deben ser coherentes."""
        assert MIN_TOKENS > 0
        assert MAX_TOKENS > MIN_TOKENS
        assert MIN_TOKENS <= DEFAULT_MAX_TOKENS <= MAX_TOKENS
        assert TOKEN_STEP > 0
    
    def test_temperature_in_range(self):
        """La temperatura debe estar entre 0 y 2."""
        assert 0 <= DEFAULT_TEMPERATURE <= 2
    
    def test_timeout_positive(self):
        """El timeout debe ser positivo."""
        assert API_TIMEOUT > 0


class TestFileConfig:
    """Tests para configuración de archivos."""
    
    def test_max_file_bytes_positive(self):
        """El tamaño máximo de archivo debe ser positivo."""
        assert MAX_FILE_BYTES > 0
    
    def test_max_image_side_positive(self):
        """El tamaño máximo de imagen debe ser positivo."""
        assert MAX_IMAGE_SIDE > 0
    
    def test_jpeg_quality_in_range(self):
        """La calidad JPEG debe estar entre 1 y 100."""
        assert 1 <= JPEG_QUALITY <= 100
    
    def test_image_extensions_not_empty(self):
        """Debe haber extensiones de imagen soportadas."""
        assert len(SUPPORTED_IMAGE_EXTENSIONS) > 0
        assert "png" in SUPPORTED_IMAGE_EXTENSIONS
        assert "jpg" in SUPPORTED_IMAGE_EXTENSIONS
    
    def test_context_extensions_include_images(self):
        """Las extensiones de contexto deben incluir imágenes."""
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            assert ext in SUPPORTED_CONTEXT_EXTENSIONS


class TestUIConfig:
    """Tests para configuración de UI."""
    
    def test_accent_color_is_hex(self):
        """El color de acento debe ser hexadecimal válido."""
        assert DEFAULT_ACCENT_COLOR.startswith("#")
        assert len(DEFAULT_ACCENT_COLOR) == 7
    
    def test_page_title_not_empty(self):
        """El título de página no debe estar vacío."""
        assert len(PAGE_TITLE) > 0
    
    def test_dimensions_positive(self):
        """Las dimensiones de UI deben ser positivas."""
        assert BRIEF_TEXT_AREA_HEIGHT > 0
        assert PREVIEW_IFRAME_HEIGHT > 0


class TestLoggingConfig:
    """Tests para configuración de logging."""
    
    def test_log_level_valid(self):
        """El nivel de log debe ser válido."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert LOG_LEVEL in valid_levels
    
    def test_log_format_not_empty(self):
        """El formato de log no debe estar vacío."""
        assert len(LOG_FORMAT) > 0


class TestMessages:
    """Tests para mensajes de UI."""
    
    def test_messages_dict_not_empty(self):
        """El diccionario de mensajes no debe estar vacío."""
        assert len(MESSAGES) > 0
    
    def test_required_messages_exist(self):
        """Los mensajes requeridos deben existir."""
        required_keys = [
            "api_key_found",
            "api_key_missing",
            "brief_placeholder",
            "brief_empty_warning",
            "generating",
            "generation_error",
            "download_button",
            "clear_button",
            "generate_button",
        ]
        for key in required_keys:
            assert key in MESSAGES, f"Falta el mensaje: {key}"
            assert len(MESSAGES[key]) > 0, f"Mensaje vacío: {key}"
