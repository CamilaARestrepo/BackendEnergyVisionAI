"""
Utilidades para procesamiento y validación de imágenes.

Incluye:
- Validación profunda de formato vía magic bytes (python-magic)
- Redimensionamiento automático antes de enviar a modelos de IA
- Conversión a base64
"""

import base64
import hashlib
from io import BytesIO
from typing import Tuple

from PIL import Image

from app.utils.exceptions import ImageValidationError
from app.utils.logger import logger

# Intentar importar python-magic (requiere libmagic instalado en el sistema)
# Fallback: validación manual por firma de bytes si libmagic no está disponible
try:
    import magic as _magic

    _MAGIC_AVAILABLE = True
except (ImportError, OSError):
    _magic = None  # type: ignore[assignment]
    _MAGIC_AVAILABLE = False
    logger.warning(
        "python-magic / libmagic no disponible. "
        "Se usará validación por magic bytes manual. "
        "Instala libmagic para validación más robusta: brew install libmagic"
    )

# Magic bytes (firmas) de los formatos de imagen soportados
_IMAGE_MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],  # RIFF????WEBP — verificamos RIFF + posición 8
}

# MIME types aceptados por el sistema
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Tamaño máximo de salida para el modelo de IA (en píxeles, lado mayor)
AI_MAX_IMAGE_DIMENSION = 1024


def _detect_mime_from_bytes(data: bytes) -> str | None:
    """
    Detecta el MIME type de una imagen inspeccionando sus magic bytes manualmente.

    Returns:
        MIME type detectado o None si no coincide con ningún formato conocido.
    """
    header = data[:12]
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image_magic_bytes(data: bytes) -> str:
    """
    Valida el archivo usando magic bytes (no el Content-Type del header HTTP).

    Usa python-magic (libmagic) si está disponible. De lo contrario, utiliza
    inspección manual de firmas de bytes como fallback seguro.

    Args:
        data: Raw bytes del archivo subido.

    Returns:
        El MIME type real detectado del archivo.

    Raises:
        ImageValidationError: Si el archivo no es una imagen soportada.
    """
    if _MAGIC_AVAILABLE and _magic is not None:
        # Ruta preferida: python-magic con libmagic
        try:
            detected_mime = _magic.from_buffer(data[:4096], mime=True)
        except Exception as e:
            raise ImageValidationError(f"No se pudo determinar el tipo de archivo: {e}") from e
    else:
        # Fallback: inspección manual de magic bytes
        detected_mime = _detect_mime_from_bytes(data)

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise ImageValidationError(
            f"Formato de imagen no soportado. Detectado: '{detected_mime}'. "
            f"Se permiten: {', '.join(sorted(ALLOWED_MIME_TYPES))}."
        )

    return detected_mime


def resize_image_for_ai(data: bytes, max_dimension: int = AI_MAX_IMAGE_DIMENSION) -> Tuple[bytes, str]:
    """
    Redimensiona la imagen para optimizar el envío a modelos de IA.

    Si alguna dimensión supera `max_dimension`, la imagen se escala proporcionalmente.
    Si ya es suficientemente pequeña, se retorna sin cambios.

    Args:
        data: Raw bytes de la imagen original.
        max_dimension: Tamaño máximo (en píxeles) del lado más largo. Default: 1024.

    Returns:
        Tupla (bytes_de_imagen_procesada, mime_type_real).

    Raises:
        ImageValidationError: Si la imagen no puede ser procesada por Pillow.
    """
    try:
        img = Image.open(BytesIO(data))
        original_format = img.format or "JPEG"
        original_size = img.size

        # Convertir modos especiales a RGB para compatibilidad universal
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Solo redimensionar si es necesario
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
            logger.info(
                f"Imagen redimensionada: {original_size} → {img.size} "
                f"(max dimension: {max_dimension}px)"
            )
        else:
            logger.info(f"Imagen dentro de límite: {img.size}, no requiere resize.")

        # Re-serializar
        output = BytesIO()
        save_format = original_format if original_format in ("JPEG", "PNG", "WEBP") else "JPEG"
        
        save_kwargs: dict = {}
        if save_format == "JPEG":
            save_kwargs["quality"] = 90
            save_kwargs["optimize"] = True
            # JPEG no soporta transparencia
            if img.mode == "RGBA":
                img = img.convert("RGB")

        img.save(output, format=save_format, **save_kwargs)
        processed_bytes = output.getvalue()

        mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
        mime_type = mime_map.get(save_format, "image/jpeg")

        return processed_bytes, mime_type

    except ImageValidationError:
        raise
    except Exception as e:
        raise ImageValidationError(f"No se pudo procesar la imagen: {e}") from e


def image_bytes_to_base64(data: bytes) -> str:
    """Convierte raw bytes a string base64 UTF-8."""
    return base64.b64encode(data).decode("utf-8")


def compute_sha256(data: bytes) -> str:
    """Calcula el hash SHA-256 del contenido en bytes de la imagen."""
    return hashlib.sha256(data).hexdigest()
