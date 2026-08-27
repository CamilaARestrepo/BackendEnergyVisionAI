"""
Excepciones de dominio personalizadas para EnergyVision AI.

Estas excepciones son lanzadas por la capa de dominio/aplicación y luego
mapeadas a respuestas HTTP por el handler global en app/main.py.
"""


class EnergyVisionBaseError(Exception):
    """Clase base de la que heredan todas las excepciones del dominio."""

    status_code: int = 500
    default_message: str = "Error interno del servidor."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class ProviderNotFoundError(EnergyVisionBaseError):
    """El proveedor de IA solicitado no está registrado en el factory."""

    status_code = 400
    default_message = "Proveedor de IA no encontrado."


class MissingAPIKeyError(EnergyVisionBaseError):
    """El proveedor activo no tiene una API key configurada."""

    status_code = 503
    default_message = "El proveedor de IA activo no tiene una clave API configurada."


class ProviderNotConfiguredError(EnergyVisionBaseError):
    """No hay ningún proveedor de IA activo configurado en el sistema."""

    status_code = 503
    default_message = "No hay proveedor de IA activo. Configure uno en Ajustes."


class ImageValidationError(EnergyVisionBaseError):
    """La imagen enviada no supera las validaciones de formato o tamaño."""

    status_code = 400
    default_message = "La imagen no es válida."


class ImageTooLargeError(EnergyVisionBaseError):
    """La imagen excede el tamaño máximo permitido."""

    status_code = 413
    default_message = "La imagen excede el tamaño máximo de 10 MB."


class DuplicateImageError(EnergyVisionBaseError):
    """La imagen ya fue procesada anteriormente (mismo SHA-256)."""

    status_code = 200  # No es un error real, se retorna el registro existente
    default_message = "La imagen ya fue analizada previamente."


class AIInferenceError(EnergyVisionBaseError):
    """Error durante la inferencia del modelo de IA (nodo del grafo falló)."""

    status_code = 422
    default_message = "Error durante el análisis de IA."


class ObjectNotFoundError(EnergyVisionBaseError):
    """El objeto solicitado no existe en la base de datos."""

    status_code = 404
    default_message = "Objeto no encontrado."
