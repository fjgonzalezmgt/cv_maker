"""
Tests para el módulo openai_client.

Estos tests verifican las funciones auxiliares del cliente de OpenAI
sin hacer llamadas reales a la API.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from openai_client import (
    _guess_mime,
    _resize_image_bytes,
    _file_to_content_items,
    create_openai_client,
    OpenAIClientError,
    APIKeyMissingError,
    FileProcessingError,
)


class TestGuessMime:
    """Tests para la función _guess_mime."""
    
    def test_png_mime(self):
        """Detecta correctamente archivos PNG."""
        assert _guess_mime("foto.png") == "image/png"
        assert _guess_mime("FOTO.PNG") == "image/png"
    
    def test_jpg_mime(self):
        """Detecta correctamente archivos JPG/JPEG."""
        assert _guess_mime("foto.jpg") == "image/jpeg"
        assert _guess_mime("foto.jpeg") == "image/jpeg"
    
    def test_webp_mime(self):
        """Detecta correctamente archivos WebP."""
        assert _guess_mime("foto.webp") == "image/webp"
    
    def test_pdf_mime(self):
        """Detecta correctamente archivos PDF."""
        assert _guess_mime("documento.pdf") == "application/pdf"
    
    def test_unknown_mime(self):
        """Retorna octet-stream para tipos desconocidos."""
        assert _guess_mime("archivo.xyz") == "application/octet-stream"
        assert _guess_mime("archivo") == "application/octet-stream"
    
    def test_path_with_directories(self):
        """Funciona con rutas que incluyen directorios."""
        assert _guess_mime("/path/to/foto.png") == "image/png"
        assert _guess_mime("C:\\Users\\foto.jpg") == "image/jpeg"


class TestFileToContentItems:
    """Tests para la función _file_to_content_items."""
    
    def test_file_not_found(self):
        """Lanza FileNotFoundError si el archivo no existe."""
        with pytest.raises(FileNotFoundError):
            _file_to_content_items("/ruta/inexistente/archivo.txt")
    
    def test_text_file_content(self):
        """Procesa correctamente archivos de texto."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Contenido de prueba")
            temp_path = f.name
        
        try:
            items = _file_to_content_items(temp_path)
            assert len(items) == 1
            assert items[0]["type"] == "input_file"
            assert "filename" in items[0]
            assert "file_data" in items[0]
        finally:
            os.unlink(temp_path)
    
    def test_truncation_warning(self):
        """Añade advertencia cuando se trunca el archivo."""
        # Crear un archivo temporal grande
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(b"X" * 1000)  # 1000 bytes
            temp_path = f.name
        
        try:
            # Usar un límite muy pequeño para forzar truncamiento
            items = _file_to_content_items(temp_path, max_bytes=100)
            assert len(items) == 2  # archivo + advertencia
            assert items[1]["type"] == "input_text"
            assert "Advertencia" in items[1]["text"]
        finally:
            os.unlink(temp_path)


class TestCreateOpenAIClient:
    """Tests para la función create_openai_client."""
    
    def test_missing_api_key_raises_error(self):
        """Lanza APIKeyMissingError si no hay API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Asegurar que no hay variable de entorno
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            
            with pytest.raises(APIKeyMissingError):
                create_openai_client()
    
    def test_api_key_from_parameter(self):
        """Usa la API key del parámetro si se proporciona."""
        with patch('openai_client.OpenAI') as mock_openai:
            mock_openai.return_value = MagicMock()
            client = create_openai_client(api_key="sk-test-key-12345")
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args[1]
            assert call_kwargs["api_key"] == "sk-test-key-12345"
    
    def test_api_key_from_environment(self):
        """Usa la API key del entorno si no se proporciona parámetro."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key-67890"}):
            with patch('openai_client.OpenAI') as mock_openai:
                mock_openai.return_value = MagicMock()
                client = create_openai_client()
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs["api_key"] == "sk-env-key-67890"


class TestCustomExceptions:
    """Tests para las excepciones personalizadas."""
    
    def test_openai_client_error_inheritance(self):
        """OpenAIClientError hereda de Exception."""
        assert issubclass(OpenAIClientError, Exception)
    
    def test_api_key_missing_error_inheritance(self):
        """APIKeyMissingError hereda de OpenAIClientError."""
        assert issubclass(APIKeyMissingError, OpenAIClientError)
    
    def test_file_processing_error_inheritance(self):
        """FileProcessingError hereda de OpenAIClientError."""
        assert issubclass(FileProcessingError, OpenAIClientError)
    
    def test_exception_message(self):
        """Las excepciones pueden tener mensajes personalizados."""
        error = APIKeyMissingError("API key no encontrada")
        assert str(error) == "API key no encontrada"
