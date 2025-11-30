"""
Tests para el módulo app.

Estos tests verifican las funciones auxiliares de la aplicación Streamlit.
No prueban la interfaz de usuario directamente.
"""

import tempfile
import os
from pathlib import Path
from io import BytesIO
from unittest.mock import MagicMock

import pytest


# Importar funciones del módulo app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (
    build_content,
    persist_uploaded_files,
    file_to_data_uri,
    apply_image_overrides,
)


class TestBuildContent:
    """Tests para la función build_content."""
    
    def test_basic_brief(self):
        """Retorna el brief básico sin modificaciones."""
        result = build_content(
            brief="Perfil de prueba",
            accent="#000000",
            include_accent_hint=False,
            has_avatar=False,
            has_qr=False,
        )
        assert result == "Perfil de prueba"
    
    def test_with_accent_hint(self):
        """Incluye el color de acento cuando se solicita."""
        result = build_content(
            brief="Perfil de prueba",
            accent="#ff0000",
            include_accent_hint=True,
            has_avatar=False,
            has_qr=False,
        )
        assert "Perfil de prueba" in result
        assert "#ff0000" in result
        assert "Color de acento" in result
    
    def test_with_avatar(self):
        """Incluye mensaje sobre avatar cuando hay foto."""
        result = build_content(
            brief="Perfil de prueba",
            accent="#000000",
            include_accent_hint=False,
            has_avatar=True,
            has_qr=False,
        )
        assert "avatar.png" in result
    
    def test_with_qr(self):
        """Incluye mensaje sobre QR cuando se proporciona."""
        result = build_content(
            brief="Perfil de prueba",
            accent="#000000",
            include_accent_hint=False,
            has_avatar=False,
            has_qr=True,
        )
        assert "qr.png" in result
    
    def test_strips_whitespace(self):
        """Elimina espacios en blanco del brief."""
        result = build_content(
            brief="  Perfil con espacios  ",
            accent="#000000",
            include_accent_hint=False,
            has_avatar=False,
            has_qr=False,
        )
        assert result == "Perfil con espacios"
    
    def test_all_options(self):
        """Incluye todas las opciones cuando están habilitadas."""
        result = build_content(
            brief="Perfil completo",
            accent="#123456",
            include_accent_hint=True,
            has_avatar=True,
            has_qr=True,
        )
        assert "Perfil completo" in result
        assert "#123456" in result
        assert "avatar.png" in result
        assert "qr.png" in result


class TestPersistUploadedFiles:
    """Tests para la función persist_uploaded_files."""
    
    def test_empty_list(self):
        """Retorna lista vacía para entrada vacía."""
        result = persist_uploaded_files([])
        assert result == []
    
    def test_single_file(self):
        """Guarda un archivo correctamente."""
        # Crear un mock de archivo uploadado
        mock_file = MagicMock()
        mock_file.name = "test.txt"
        mock_file.getbuffer.return_value = b"contenido de prueba"
        
        result = persist_uploaded_files([mock_file])
        
        assert len(result) == 1
        assert os.path.exists(result[0])
        
        # Verificar contenido
        with open(result[0], "rb") as f:
            assert f.read() == b"contenido de prueba"
        
        # Limpiar
        os.unlink(result[0])
    
    def test_multiple_files(self):
        """Guarda múltiples archivos correctamente."""
        mock_files = []
        for i in range(3):
            mock_file = MagicMock()
            mock_file.name = f"test{i}.txt"
            mock_file.getbuffer.return_value = f"contenido {i}".encode()
            mock_files.append(mock_file)
        
        result = persist_uploaded_files(mock_files)
        
        assert len(result) == 3
        for path in result:
            assert os.path.exists(path)
            os.unlink(path)
    
    def test_preserves_extension(self):
        """Preserva la extensión del archivo original."""
        mock_file = MagicMock()
        mock_file.name = "imagen.png"
        mock_file.getbuffer.return_value = b"fake image data"
        
        result = persist_uploaded_files([mock_file])
        
        assert result[0].endswith(".png")
        os.unlink(result[0])


class TestFileToDataUri:
    """Tests para la función file_to_data_uri."""
    
    def test_returns_none_for_non_image(self):
        """Retorna None para archivos no-imagen."""
        mock_file = MagicMock()
        mock_file.type = "application/pdf"
        mock_file.name = "documento.pdf"
        
        result = file_to_data_uri(mock_file)
        assert result is None
    
    def test_returns_none_for_empty_file(self):
        """Retorna None para archivos vacíos."""
        mock_file = MagicMock()
        mock_file.type = "image/png"
        mock_file.name = "imagen.png"
        mock_file.getvalue.return_value = b""
        
        result = file_to_data_uri(mock_file)
        assert result is None
    
    def test_returns_data_uri_for_image(self):
        """Retorna Data URI correcto para imágenes."""
        mock_file = MagicMock()
        mock_file.type = "image/png"
        mock_file.name = "imagen.png"
        mock_file.getvalue.return_value = b"fake png data"
        
        result = file_to_data_uri(mock_file)
        
        assert result is not None
        assert result.startswith("data:image/png;base64,")


class TestApplyImageOverrides:
    """Tests para la función apply_image_overrides."""
    
    def test_no_changes_without_uris(self):
        """No modifica el HTML si no hay URIs."""
        html = '<img src="avatar.png" /><img src="qr.png" />'
        result = apply_image_overrides(html, None, None)
        assert result == html
    
    def test_replaces_avatar(self):
        """Reemplaza el placeholder de avatar."""
        html = '<img src="avatar.png" alt="foto" />'
        result = apply_image_overrides(html, "data:image/png;base64,ABC", None)
        assert 'src="data:image/png;base64,ABC"' in result
        assert 'src="avatar.png"' not in result
    
    def test_replaces_qr(self):
        """Reemplaza el placeholder de QR."""
        html = '<img src="qr.png" alt="codigo" />'
        result = apply_image_overrides(html, None, "data:image/png;base64,XYZ")
        assert 'src="data:image/png;base64,XYZ"' in result
        assert 'src="qr.png"' not in result
    
    def test_replaces_both(self):
        """Reemplaza ambos placeholders."""
        html = '<img src="avatar.png" /><img src="qr.png" />'
        result = apply_image_overrides(
            html,
            "data:image/png;base64,AVATAR",
            "data:image/png;base64,QR",
        )
        assert 'src="data:image/png;base64,AVATAR"' in result
        assert 'src="data:image/png;base64,QR"' in result
    
    def test_handles_single_quotes(self):
        """Maneja comillas simples en atributos src."""
        html = "<img src='avatar.png' />"
        result = apply_image_overrides(html, "data:image/png;base64,TEST", None)
        assert "data:image/png;base64,TEST" in result
    
    def test_replaces_only_first_occurrence(self):
        """Solo reemplaza la primera ocurrencia de cada placeholder."""
        html = '<img src="avatar.png" /><img src="avatar.png" />'
        result = apply_image_overrides(html, "data:image/png;base64,NEW", None)
        # Debería haber un reemplazo y uno sin cambiar
        assert result.count("data:image/png;base64,NEW") == 1
        assert result.count('src="avatar.png"') == 1
