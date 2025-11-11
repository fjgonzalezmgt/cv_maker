from __future__ import annotations

import base64
import io
import os
from typing import Any, Dict, Iterable, List, Optional, Union

from openai import OpenAI
from PIL import Image

IMAGE_EXTS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _resize_image_bytes(path: str, max_side: int = 2048, quality: int = 85) -> bytes:
    """Redimensiona una imagen y la convierte a JPEG optimizado."""
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
    """Determina el tipo MIME basándose en la extensión del archivo."""
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
    Convierte un archivo a items de contenido para la API.
    - Imágenes: redimensiona y retorna input_image
    - Otros: codifica en base64 y retorna input_file
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
    Crea y retorna un cliente de OpenAI.
    Si no se proporciona api_key, intenta obtenerla de la variable de entorno OPENAI_API_KEY.
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
    
    Args:
        system_prompt: Prompt del sistema (rol developer)
        user_content: Contenido del usuario (str o lista de strings)
        files: Lista de rutas de archivos a adjuntar
        model: Modelo a usar
        temperature: Temperatura de generación
        max_output_tokens: Máximo de tokens de salida
        stream: Si debe hacer streaming
        extra_messages: Mensajes adicionales para incluir
        max_file_bytes: Tamaño máximo de archivo en bytes
        reasoning: Parámetros de razonamiento
        text: Parámetros de texto
        api_key: API key de OpenAI
        organization: ID de organización
        project: ID de proyecto
        timeout: Timeout en segundos
        
    Returns:
        String con la respuesta o generador para streaming
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