"""
Nodo de validación de imagen del pipeline LangGraph.

Responsabilidades:
- Decodificar el base64 recibido
- Validar el tipo real usando magic bytes (no el header HTTP)
- Redimensionar la imagen a 1024x1024 máx para optimizar tokens de IA
- Recalcular el hash SHA-256 post-resize para idempotencia correcta
"""

import base64

from app.agents.state import AgentState
from app.utils.exceptions import ImageValidationError
from app.utils.image_utils import validate_image_magic_bytes, resize_image_for_ai, compute_sha256
from app.utils.logger import logger


async def validate_image_node(state: AgentState) -> dict:
    """Valida y pre-procesa la imagen antes de enviarla al modelo de IA."""
    if state.get("errors"):
        return {}  # bypass en cadena de errores

    b64 = state.get("image_base64")
    if not b64:
        return {"errors": ["No se proporcionó imagen válida en base64."]}

    # 1. Decodificar base64
    try:
        raw_bytes = base64.b64decode(b64)
    except Exception:
        return {"errors": ["El formato base64 de la imagen es inválido."]}

    # 2. Validar magic bytes (no confiar en el Content-Type del header HTTP)
    try:
        real_mime = validate_image_magic_bytes(raw_bytes)
    except ImageValidationError as e:
        return {"errors": [str(e)]}

    # 3. Redimensionar imagen para optimizar envío a IA (máx 1024x1024)
    try:
        processed_bytes, processed_mime = resize_image_for_ai(raw_bytes)
    except ImageValidationError as e:
        return {"errors": [str(e)]}

    # 4. Recalcular base64 y hash con la imagen ya procesada
    processed_b64 = base64.b64encode(processed_bytes).decode("utf-8")
    image_hash = compute_sha256(processed_bytes)

    logger.info(
        f"Imagen validada: mime={processed_mime}, "
        f"tamaño_original={len(raw_bytes):,}B, "
        f"tamaño_procesado={len(processed_bytes):,}B, "
        f"hash={image_hash[:12]}..."
    )

    return {
        "image_base64": processed_b64,
        "image_mime_type": processed_mime,
        "image_hash": image_hash,
        "errors": [],
    }
