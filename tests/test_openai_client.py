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


class TestResizeImageBytes:
    """Tests para la función _resize_image_bytes."""
    
    def test_small_image_not_resized(self):
        """Una imagen pequeña no se redimensiona."""
        # Crear una imagen pequeña de prueba
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='red')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f, format='PNG')
            temp_path = f.name
        
        try:
            result = _resize_image_bytes(temp_path, max_side=2048)
            assert isinstance(result, bytes)
            assert len(result) > 0
            
            # Verificar que la imagen resultante no excede el tamaño máximo
            result_img = Image.open(io.BytesIO(result))
            assert max(result_img.size) <= 2048
        finally:
            os.unlink(temp_path)
    
    def test_large_image_resized(self):
        """Una imagen grande se redimensiona correctamente."""
        from PIL import Image
        import io
        
        # Crear una imagen grande
        img = Image.new('RGB', (4000, 3000), color='blue')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f, format='PNG')
            temp_path = f.name
        
        try:
            result = _resize_image_bytes(temp_path, max_side=1024)
            result_img = Image.open(io.BytesIO(result))
            
            # Verificar que se redimensionó correctamente
            assert max(result_img.size) <= 1024
            # Verificar que mantiene la proporción
            assert result_img.size[0] == 1024 or result_img.size[1] == 1024
        finally:
            os.unlink(temp_path)
    
    def test_invalid_image_raises_error(self):
        """Lanza FileProcessingError con archivo no válido."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b"not a valid image")
            temp_path = f.name
        
        try:
            with pytest.raises(FileProcessingError):
                _resize_image_bytes(temp_path)
        finally:
            os.unlink(temp_path)


class TestExecuteWithRetry:
    """Tests para la función _execute_with_retry."""
    
    def test_success_on_first_try(self):
        """Retorna resultado si la primera ejecución es exitosa."""
        from openai_client import _execute_with_retry
        
        mock_func = MagicMock(return_value="success")
        result = _execute_with_retry(mock_func, max_retries=3)
        
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_retries_on_rate_limit(self):
        """Reintenta con backoff en rate limit."""
        from openai_client import _execute_with_retry
        from openai import RateLimitError
        
        # Simular que falla 2 veces y luego tiene éxito
        mock_func = MagicMock(side_effect=[
            RateLimitError("Rate limit", response=MagicMock(), body=None),
            RateLimitError("Rate limit", response=MagicMock(), body=None),
            "success"
        ])
        
        with patch('openai_client.time.sleep'):  # No esperar realmente
            result = _execute_with_retry(mock_func, max_retries=3)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_raises_after_max_retries(self):
        """Lanza excepción después de máximo de reintentos."""
        from openai_client import _execute_with_retry
        from openai import RateLimitError
        
        mock_func = MagicMock(side_effect=RateLimitError(
            "Rate limit", response=MagicMock(), body=None
        ))
        
        with patch('openai_client.time.sleep'):
            with pytest.raises(RateLimitError):
                _execute_with_retry(mock_func, max_retries=2)
        
        assert mock_func.call_count == 3  # Intento inicial + 2 reintentos
    
    def test_api_error_not_retried(self):
        """Los errores de API genéricos no se reintentan."""
        from openai_client import _execute_with_retry
        from openai import APIError
        
        mock_func = MagicMock(side_effect=APIError(
            "API Error", request=MagicMock(), body=None
        ))
        
        with pytest.raises(APIError):
            _execute_with_retry(mock_func, max_retries=3)
        
        mock_func.assert_called_once()


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
