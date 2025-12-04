# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.1.0] - 2025-12-04

### Añadido
- Archivo `prompts/system_prompt.md` para separar el prompt del sistema del código
- Configuración `MAX_BRIEF_LENGTH` para limitar longitud del brief
- Configuración `SYSTEM_PROMPT_PATH` para ruta configurable del prompt
- Mensajes de error más descriptivos para rate limit, conexión y timeout
- Context manager `temp_uploaded_files` para gestión segura de archivos temporales
- Función `validate_html_response` para validar HTML generado
- Función `validate_accent_color` para validar colores hexadecimales
- Función `load_system_prompt` para cargar el prompt desde archivo
- Tests para `_execute_with_retry` en `test_openai_client.py`
- Tests para `_resize_image_bytes` en `test_openai_client.py`
- Cache del cliente OpenAI usando `@st.cache_resource`
- Logging de métricas (tokens, tiempo de respuesta)

### Cambiado
- `SYSTEM_PROMPT` movido de `app.py` a archivo externo
- Mejorado manejo de errores con mensajes específicos por tipo
- Refactorizada limpieza de archivos temporales usando context manager

### Corregido
- Validación de longitud máxima del brief antes de enviar a API
- Validación del formato de color de acento

## [1.0.0] - 2025-11-01

### Añadido
- Versión inicial del generador de CV
- Interfaz web con Streamlit
- Generación de HTML usando OpenAI GPT-4
- Soporte para foto de perfil y código QR
- Color de acento personalizable
- Archivos de contexto adicionales
- Suite de pruebas con pytest
- Documentación completa en README
- Configuración centralizada en `config.py`
- Reintentos automáticos con backoff exponencial
