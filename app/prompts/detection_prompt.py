from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate

class DetectionResult(BaseModel):
    name: str = Field(description="Nombre preciso del objeto principal detectado en la imagen.")
    category: str = Field(description="Categoría general del objeto (Ej: RAEE, Biomasa, Metal, Plástico, Mueble).")
    material: Optional[str] = Field(description="Material principal deducido (Ej: Silicio, Madera, Aluminio).")
    brand: Optional[str] = Field(description="Marca visible o deducida del objeto, null si no tiene.")
    condition: str = Field(description="Estado del objeto: funcional, dañado, obsoleto o desconocido.")
    confidence_score: float = Field(description="Nivel de confianza de 0.0 a 1.0 (float) de tu evaluación.")

DETECTION_SYSTEM_PROMPT = """Eres un sistema experto en visión artificial para control de residuos y comunidades energéticas.
Tu único objetivo es identificar precisamenente EL OBJETO PRINCIPAL en la imagen. No te dejes distraer por el fondo o elementos incidentales.
Si hay múltiples objetos, céntrate sólo en el más grande o evidente que parezca residuo u objeto recuperable.

Devuelve de manera mandatoria un objeto en formato JSON, sin markdown, estrictamente en las reglas solicitadas y con un alto confidence score numérico.

Si la imagen no tiene ningún objeto reconocible o es caótica y oscura, asume un objeto desconocido y devuelve un confidence < 0.3.
"""

detection_prompt = ChatPromptTemplate.from_messages([
    ("system", DETECTION_SYSTEM_PROMPT),
    ("user", [
        {"type": "text", "text": "Identifica el objeto principal de la siguiente imagen y sus posibles atributos de material y estado."},
        {"type": "image_url", "image_url": {"url": "data:{mime_type};base64,{image_base64}"}}
    ])
])
