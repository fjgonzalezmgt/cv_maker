"""
Tests para el módulo app.

Estos tests verifican las funciones auxiliares de la aplicación Streamlit.
No prueban la interfaz de usuario directamente.
"""

import os
# Importar funciones del módulo app
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (apply_image_overrides, build_content, file_to_data_uri,
                 load_system_prompt, persist_uploaded_files,
                 validate_accent_color, validate_html_response,
                 validate_latex_response)


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
        assert "Perfil de prueba" in result
    
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
        assert "Perfil con espacios" in result
    
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


class TestValidateHtmlResponse:
    """Tests para la función validate_html_response."""
    
    def test_valid_html(self):
        """Retorna True para HTML válido con DOCTYPE."""
        html = "<!DOCTYPE html><html><head></head><body></body></html>"
        assert validate_html_response(html) is True
    
    def test_valid_html_with_whitespace(self):
        """Retorna True para HTML con espacios en blanco al inicio."""
        html = "   \n\n<!DOCTYPE html><html><head></head><body></body></html>"
        assert validate_html_response(html) is True
    
    def test_valid_html_case_insensitive(self):
        """Retorna True independientemente de mayúsculas/minúsculas."""
        html = "<!doctype HTML><html><head></head><body></body></html>"
        assert validate_html_response(html) is True
    
    def test_invalid_html_no_doctype(self):
        """Retorna False para HTML sin DOCTYPE."""
        html = "<html><head></head><body></body></html>"
        assert validate_html_response(html) is False
    
    def test_invalid_empty_string(self):
        """Retorna False para string vacío."""
        assert validate_html_response("") is False
    
    def test_invalid_none(self):
        """Retorna False para None (aunque no debería recibir None)."""
        assert validate_html_response(None) is False
    
    def test_invalid_text_response(self):
        """Retorna False para respuesta de texto que no es HTML."""
        assert validate_html_response("Lo siento, no puedo generar el CV.") is False


class TestValidateAccentColor:
    """Tests para la función validate_accent_color."""
    
    def test_valid_color_lowercase(self):
        """Retorna True para color hexadecimal válido en minúsculas."""
        assert validate_accent_color("#0b3a6e") is True
    
    def test_valid_color_uppercase(self):
        """Retorna True para color hexadecimal válido en mayúsculas."""
        assert validate_accent_color("#0B3A6E") is True
    
    def test_valid_color_mixed_case(self):
        """Retorna True para color hexadecimal con mayúsculas mezcladas."""
        assert validate_accent_color("#AbCdEf") is True
    
    def test_invalid_color_no_hash(self):
        """Retorna False para color sin #."""
        assert validate_accent_color("0b3a6e") is False
    
    def test_invalid_color_short(self):
        """Retorna False para color demasiado corto."""
        assert validate_accent_color("#fff") is False
    
    def test_invalid_color_too_long(self):
        """Retorna False para color demasiado largo."""
        assert validate_accent_color("#0b3a6e00") is False
    
    def test_invalid_color_non_hex(self):
        """Retorna False para caracteres no hexadecimales."""
        assert validate_accent_color("#ghijkl") is False
    
    def test_invalid_empty_string(self):
        """Retorna False para string vacío."""
        assert validate_accent_color("") is False


class TestLoadSystemPrompt:
    """Tests para la función load_system_prompt."""
    
    def test_loads_prompt_successfully(self):
        """Carga el prompt del sistema correctamente."""
        prompt = load_system_prompt()
        # Verificar que se cargó contenido
        assert len(prompt) > 0
        # Verificar que contiene contenido esperado
        assert "HTML" in prompt or "CV" in prompt

    def test_loads_latex_prompt_successfully(self):
        """Carga el prompt LaTeX del sistema correctamente."""
        prompt = load_system_prompt("LaTeX")
        assert len(prompt) > 0
        assert "LaTeX" in prompt or "documentclass" in prompt

    def test_loads_html_prompt_by_default(self):
        """Carga el prompt HTML por defecto."""
        prompt = load_system_prompt("HTML")
        assert len(prompt) > 0
        assert "HTML" in prompt


class TestValidateLatexResponse:
    """Tests para la función validate_latex_response."""

    def test_valid_latex(self):
        """Retorna True para LaTeX válido con documentclass."""
        latex = "\\documentclass[9pt,a4paper]{article}\n\\begin{document}\nHola\n\\end{document}"
        assert validate_latex_response(latex) is True

    def test_valid_latex_with_comments(self):
        """Retorna True para LaTeX con comentarios antes de documentclass."""
        latex = "%% Mi CV\n% Compilar con xelatex\n\\documentclass{article}\n\\begin{document}\n\\end{document}"
        assert validate_latex_response(latex) is True

    def test_valid_latex_with_whitespace(self):
        """Retorna True para LaTeX con espacios en blanco al inicio."""
        latex = "   \n\n\\documentclass{article}\n\\begin{document}\n\\end{document}"
        assert validate_latex_response(latex) is True

    def test_invalid_latex_no_documentclass(self):
        """Retorna False para LaTeX sin documentclass."""
        latex = "\\begin{document}\nHola\n\\end{document}"
        assert validate_latex_response(latex) is False

    def test_invalid_empty_string(self):
        """Retorna False para string vacío."""
        assert validate_latex_response("") is False

    def test_invalid_none(self):
        """Retorna False para None."""
        assert validate_latex_response(None) is False

    def test_invalid_html_response(self):
        """Retorna False para respuesta HTML."""
        assert validate_latex_response("<!DOCTYPE html><html></html>") is False

    def test_invalid_text_response(self):
        """Retorna False para texto plano."""
        assert validate_latex_response("Lo siento, no puedo generar el CV.") is False


class TestBuildContentLatex:
    """Tests para build_content con formato LaTeX."""

    def test_latex_no_avatar_hint(self):
        """No incluye hint de avatar en formato LaTeX."""
        result = build_content(
            brief="Perfil",
            accent="#000000",
            include_accent_hint=False,
            has_avatar=True,
            has_qr=False,
            output_format="LaTeX",
        )
        assert "avatar.png" not in result

    def test_latex_no_qr_hint(self):
        """No incluye hint de QR en formato LaTeX."""
        result = build_content(
            brief="Perfil",
            accent="#000000",
            include_accent_hint=False,
            has_avatar=False,
            has_qr=True,
            output_format="LaTeX",
        )
        assert "qr.png" not in result

    def test_html_includes_avatar_hint(self):
        """Incluye hint de avatar en formato HTML."""
        result = build_content(
            brief="Perfil",
            accent="#000000",
            include_accent_hint=False,
            has_avatar=True,
            has_qr=False,
            output_format="HTML",
        )
        assert "avatar.png" in result
