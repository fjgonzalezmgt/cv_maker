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
import os
from typing import Any, Dict, Iterable, List, Optional, Union

from openai import OpenAI
from PIL import Image

# Extensiones de imagen soportadas y sus tipos MIME correspondientes
IMAGE_EXTS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _resize_image_bytes(path: str, max_side: int = 2048, quality: int = 85) -> bytes:
    """
    Redimensiona una imagen y la convierte a JPEG optimizado.
    
    Esta función toma una imagen de cualquier formato soportado, la convierte a RGB,
    y la redimensiona si es necesario para que su lado más grande no exceda max_side.
    Finalmente, la guarda como JPEG optimizado con la calidad especificada.
    
    Args:
        path (str): Ruta al archivo de imagen a procesar.
        max_side (int, optional): Tamaño máximo permitido para el lado más largo.
            Por defecto es 2048 píxeles.
        quality (int, optional): Calidad de compresión JPEG (1-100).
            Por defecto es 85.
    
    Returns:
        bytes: Los bytes de la imagen procesada en formato JPEG.
    
    Raises:
        FileNotFoundError: Si el archivo no existe.
        PIL.UnidentifiedImageError: Si el archivo no es una imagen válida.
    
    Example:
        >>> image_bytes = _resize_image_bytes("foto.png", max_side=1024, quality=90)
        >>> len(image_bytes)
        125432
    """
    print(f"[DEBUG] _resize_image_bytes: Procesando imagen {path}")
    im = Image.open(path).convert("RGB")
    w, h = im.size
    print(f"[DEBUG] _resize_image_bytes: Tamaño original {w}x{h}")
    if max(w, h) > max_side:
        scale = max_side / float(max(w, h))
        im = im.resize((int(w * scale), int(h * scale)))
        print(f"[DEBUG] _resize_image_bytes: Redimensionada a {int(w * scale)}x{int(h * scale)}")
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    print(f"[DEBUG] _resize_image_bytes: Imagen convertida a JPEG, tamaño: {len(buf.getvalue())} bytes")
    return buf.getvalue()


def _guess_mime(path: str) -> str:
    """
    Determina el tipo MIME basándose en la extensión del archivo.
    
    Esta función analiza la extensión del archivo y retorna el tipo MIME correspondiente.
    Soporta imágenes (.png, .jpg, .jpeg, .webp), archivos PDF, y archivos genéricos.
    
    Args:
        path (str): Ruta al archivo cuyo tipo MIME se desea determinar.
    
    Returns:
        str: El tipo MIME del archivo. Posibles valores:
            - "image/png" para archivos .png
            - "image/jpeg" para archivos .jpg y .jpeg
            - "image/webp" para archivos .webp
            - "application/pdf" para archivos .pdf
            - "application/octet-stream" para cualquier otro tipo
    
    Example:
        >>> _guess_mime("documento.pdf")
        'application/pdf'
        >>> _guess_mime("foto.jpg")
        'image/jpeg'
    """
    ext = os.path.splitext(path.lower())[1]
    print(f"[DEBUG] _guess_mime: Archivo {path}, extensión: {ext}")
    if ext in IMAGE_EXTS:
        mime = IMAGE_EXTS[ext]
        print(f"[DEBUG] _guess_mime: Es imagen, MIME: {mime}")
        return mime
    if ext == ".pdf":
        print(f"[DEBUG] _guess_mime: Es PDF")
        return "application/pdf"
    print(f"[DEBUG] _guess_mime: Tipo genérico application/octet-stream")
    return "application/octet-stream"


def _file_to_content_items(path: str, max_bytes: int = 8_000_000) -> List[dict]:
    """
    Convierte un archivo a items de contenido para la API de OpenAI.
    
    Esta función procesa archivos de diferentes tipos:
    - Imágenes: redimensiona automáticamente y retorna como 'input_image'
    - Otros archivos: codifica en base64 y retorna como 'input_file'
    
    Si el archivo excede el tamaño máximo, se trunca y se añade un mensaje de advertencia.
    
    Args:
        path (str): Ruta al archivo a procesar.
        max_bytes (int, optional): Tamaño máximo permitido en bytes.
            Por defecto es 8,000,000 bytes (8 MB).
    
    Returns:
        List[dict]: Lista de items de contenido para la API. Puede contener:
            - Para imágenes: dict con type="input_image" y image_url en formato data URL
            - Para otros archivos: dict con type="input_file", filename, y file_data
            - Si se trunca: item adicional con type="input_text" con advertencia
    
    Raises:
        FileNotFoundError: Si el archivo especificado no existe.
    
    Example:
        >>> items = _file_to_content_items("documento.pdf")
        >>> len(items)
        1
        >>> items[0]["type"]
        'input_file'
    """
    print(f"[DEBUG] _file_to_content_items: Procesando archivo {path}")
    if not os.path.exists(path):
        print(f"[ERROR] _file_to_content_items: Archivo no existe: {path}")
        raise FileNotFoundError(path)
    
    mime = _guess_mime(path)
    ext = os.path.splitext(path)[1].lower()
    
    if ext in IMAGE_EXTS:
        print(f"[DEBUG] _file_to_content_items: Procesando como imagen")
        data = _resize_image_bytes(path)
        b64 = base64.b64encode(data).decode("ascii")
        print(f"[DEBUG] _file_to_content_items: Base64 length: {len(b64)}")
        return [{"type": "input_image", "image_url": f"data:{mime};base64,{b64}"}]
    
    print(f"[DEBUG] _file_to_content_items: Procesando como archivo genérico")
    with open(path, "rb") as f:
        raw = f.read()
    
    print(f"[DEBUG] _file_to_content_items: Tamaño archivo: {len(raw)} bytes")
    truncated = False
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
        truncated = True
        print(f"[DEBUG] _file_to_content_items: Archivo truncado a {max_bytes} bytes")
    
    b64 = base64.b64encode(raw).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    print(f"[DEBUG] _file_to_content_items: Base64 length: {len(b64)}")
    
    items: List[dict] = [
        {
            "type": "input_file",
            "filename": os.path.basename(path),
            "file_data": data_url,
        }
    ]
    
    if truncated:
        items.append(
            {
                "type": "input_text",
                "text": (
                    f"Advertencia: '{os.path.basename(path)}' truncado a {max_bytes} bytes "
                    "máximos para el envío."
                ),
            }
        )
    
    print(f"[DEBUG] _file_to_content_items: Retornando {len(items)} items de contenido")
    return items


def create_openai_client(
    api_key: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    timeout: float = 60.0,
) -> OpenAI:
    """
    Crea y retorna un cliente de OpenAI configurado.
    
    Esta función inicializa un cliente de la API de OpenAI con las credenciales proporcionadas.
    Si no se proporciona una API key explícitamente, intenta obtenerla de la variable de
    entorno OPENAI_API_KEY.
    
    Args:
        api_key (Optional[str], optional): API key de OpenAI. Si es None, se usa
            la variable de entorno OPENAI_API_KEY. Por defecto es None.
        organization (Optional[str], optional): ID de la organización de OpenAI.
            Por defecto es None.
        project (Optional[str], optional): ID del proyecto de OpenAI.
            Por defecto es None.
        timeout (float, optional): Tiempo máximo de espera en segundos para las
            peticiones a la API. Por defecto es 60.0 segundos.
    
    Returns:
        OpenAI: Cliente de OpenAI configurado y listo para usar.
    
    Raises:
        RuntimeError: Si no se encuentra la API key ni en los parámetros ni en
            las variables de entorno.
    
    Example:
        >>> client = create_openai_client(api_key="sk-...")
        >>> # O usando variable de entorno
        >>> client = create_openai_client()
    """
    print(f"[DEBUG] create_openai_client: Creando cliente OpenAI")
    
    # Obtener API key
    if api_key:
        resolved_api_key = api_key
        print(f"[DEBUG] create_openai_client: Usando API key proporcionada (longitud: {len(resolved_api_key)})")
    else:
        resolved_api_key = os.getenv("OPENAI_API_KEY")
        if resolved_api_key:
            print(f"[DEBUG] create_openai_client: Usando API key de variable de entorno (longitud: {len(resolved_api_key)})")
        else:
            print(f"[ERROR] create_openai_client: No se encontró API key")
            raise RuntimeError("Falta la variable de entorno OPENAI_API_KEY. Añádela en .env o exporta la variable.")
    
    # Crear cliente con API key
    print(f"[DEBUG] create_openai_client: Instanciando OpenAI(api_key=...)")
    openai_api = OpenAI(api_key=resolved_api_key)
    print(f"[DEBUG] create_openai_client: Cliente creado exitosamente")
    return openai_api


def chat_completion(
    system_prompt: str,
    user_content: Union[str, List[str]],
    *,
    files: Optional[List[str]] = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_output_tokens: Optional[int] = None,
    stream: bool = False,
    extra_messages: Optional[List[dict]] = None,
    max_file_bytes: int = 8_000_000,
    reasoning: Optional[Dict[str, Any]] = None,
    text: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    timeout: float = 60.0,
) -> Union[str, Iterable[str]]:
    """
    Realiza una consulta a la API de OpenAI usando Responses API.
    
    Esta es la función principal del módulo que permite interactuar con los modelos de
    chat de OpenAI. Soporta el envío de texto, imágenes y archivos, así como streaming
    de respuestas.
    
    Args:
        system_prompt (str): Prompt del sistema que define el comportamiento del modelo.
            Se envía con rol 'developer'.
        user_content (Union[str, List[str]]): Contenido del mensaje del usuario.
            Puede ser un string único o una lista de strings que se concatenarán.
        files (Optional[List[str]], optional): Lista de rutas de archivos a adjuntar
            al mensaje. Soporta imágenes y PDFs. Por defecto es None.
        model (str, optional): Identificador del modelo de OpenAI a utilizar.
            Por defecto es "gpt-4.1-mini".
        temperature (float, optional): Controla la aleatoriedad de las respuestas.
            Valores más bajos (cercanos a 0) hacen respuestas más deterministas.
            Por defecto es 0.2.
        max_output_tokens (Optional[int], optional): Número máximo de tokens en la
            respuesta. Si es None, usa el límite por defecto del modelo.
            Por defecto es None.
        stream (bool, optional): Si es True, retorna un generador que produce la
            respuesta en tiempo real. Si es False, espera la respuesta completa.
            Por defecto es False.
        extra_messages (Optional[List[dict]], optional): Mensajes adicionales para
            incluir en la conversación (historial de chat). Por defecto es None.
        max_file_bytes (int, optional): Tamaño máximo permitido para archivos adjuntos
            en bytes. Por defecto es 8,000,000 (8 MB).
        reasoning (Optional[Dict[str, Any]], optional): Parámetros de configuración
            para el razonamiento del modelo. Por defecto es None.
        text (Optional[Dict[str, Any]], optional): Parámetros de configuración
            para la generación de texto. Por defecto es None.
        api_key (Optional[str], optional): API key de OpenAI. Si es None, se usa
            la variable de entorno. Por defecto es None.
        organization (Optional[str], optional): ID de organización de OpenAI.
            Por defecto es None.
        project (Optional[str], optional): ID de proyecto de OpenAI.
            Por defecto es None.
        timeout (float, optional): Tiempo máximo de espera en segundos.
            Por defecto es 60.0.
    
    Returns:
        Union[str, Iterable[str]]: Si stream=False, retorna un string con la respuesta
            completa. Si stream=True, retorna un generador que produce fragmentos de
            texto a medida que se generan.
    
    Raises:
        ValueError: Si no se proporciona contenido para enviar a la API.
        RuntimeError: Si ocurre un error durante la comunicación con la API.
        FileNotFoundError: Si alguno de los archivos especificados no existe.
    
    Example:
        >>> # Uso básico
        >>> respuesta = chat_completion(
        ...     system_prompt="Eres un asistente útil",
        ...     user_content="¿Qué es Python?"
        ... )
        
        >>> # Con archivos adjuntos
        >>> respuesta = chat_completion(
        ...     system_prompt="Analiza estas imágenes",
        ...     user_content="Describe lo que ves",
        ...     files=["imagen1.jpg", "imagen2.png"]
        ... )
        
        >>> # Con streaming
        >>> for fragmento in chat_completion(
        ...     system_prompt="Eres un poeta",
        ...     user_content="Escribe un poema",
        ...     stream=True
        ... ):
        ...     print(fragmento, end="")
    """
    print(f"[DEBUG] chat_completion: Iniciando")
    print(f"[DEBUG] chat_completion: Modelo: {model}, Temperatura: {temperature}")
    print(f"[DEBUG] chat_completion: Max tokens: {max_output_tokens}, Stream: {stream}")
    
    # Crear cliente
    print(f"[DEBUG] chat_completion: Creando cliente OpenAI")
    openai_api = create_openai_client(api_key, organization, project, timeout)
    
    # Preparar contenido del usuario
    print(f"[DEBUG] chat_completion: Preparando contenido del usuario")
    if isinstance(user_content, list):
        user_text = "\n\n".join([u for u in user_content if u])
        print(f"[DEBUG] chat_completion: user_content es lista, combinando {len(user_content)} elementos")
    else:
        user_text = user_content or ""
        print(f"[DEBUG] chat_completion: user_content es string, longitud: {len(user_text)}")
    
    user_content_items: List[dict] = []
    if user_text:
        user_content_items.append({"type": "input_text", "text": user_text})
        print(f"[DEBUG] chat_completion: Añadido texto de usuario")
    
    # Agregar archivos
    if files:
        print(f"[DEBUG] chat_completion: Procesando {len(files)} archivos")
        for f in files:
            print(f"[DEBUG] chat_completion: Procesando archivo: {f}")
            user_content_items.extend(_file_to_content_items(f, max_bytes=max_file_bytes))
    else:
        print(f"[DEBUG] chat_completion: No hay archivos adjuntos")
    
    # Construir mensajes de entrada
    print(f"[DEBUG] chat_completion: Construyendo mensajes de entrada")
    input_messages: List[dict] = []
    if system_prompt:
        input_messages.append(
            {
                "role": "developer",
                "content": [{"type": "input_text", "text": system_prompt}],
            }
        )
        print(f"[DEBUG] chat_completion: Añadido system prompt (developer role)")
    if user_content_items:
        input_messages.append({"role": "user", "content": user_content_items})
        print(f"[DEBUG] chat_completion: Añadido mensaje de usuario con {len(user_content_items)} items")
    if extra_messages:
        input_messages.extend(extra_messages)
        print(f"[DEBUG] chat_completion: Añadidos {len(extra_messages)} mensajes extra")
    
    if not input_messages:
        print(f"[ERROR] chat_completion: No hay mensajes para enviar")
        raise ValueError("Se requiere al menos un contenido para enviar a la API")
    
    print(f"[DEBUG] chat_completion: Total mensajes a enviar: {len(input_messages)}")
    
    # Preparar parámetros de la API
    api_params = {
        "model": model,
        "input": input_messages,
    }
    
    # Añadir parámetros opcionales solo si se proporcionan
    if temperature is not None:
        api_params["temperature"] = temperature
    if max_output_tokens is not None:
        api_params["max_output_tokens"] = max_output_tokens
    if reasoning is not None:
        api_params["reasoning"] = reasoning
        print(f"[DEBUG] chat_completion: Parámetro reasoning: {reasoning}")
    if text is not None:
        api_params["text"] = text
        print(f"[DEBUG] chat_completion: Parámetro text: {text}")
    
    print(f"[DEBUG] chat_completion: Parámetros API preparados: {list(api_params.keys())}")
    
    # Ejecutar solicitud
    try:
        if stream:
            print(f"[DEBUG] chat_completion: Iniciando streaming")
            api_params["stream"] = True
            events = openai_api.responses.create(**api_params)
            
            def _gen():
                print(f"[DEBUG] chat_completion: Generador de streaming iniciado")
                for ev in events:
                    if ev.type == "response.output_text.delta":
                        yield ev.delta
                    elif ev.type == "response.error":
                        print(f"[ERROR] chat_completion: Error en evento: {ev.error}")
                        raise RuntimeError(str(ev.error))
                print(f"[DEBUG] chat_completion: Streaming completado")
            return _gen()
        
        print(f"[DEBUG] chat_completion: Realizando llamada a API (no-stream)")
        resp = openai_api.responses.create(**api_params)
        print(f"[DEBUG] chat_completion: Respuesta recibida")
        output = (getattr(resp, "output_text", "") or "").strip()
        print(f"[DEBUG] chat_completion: Output length: {len(output)}")
        return output
    except Exception as e:
        print(f"[ERROR] chat_completion: Excepción capturada: {type(e).__name__}: {str(e)}")
        raise