from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate

class WasteResult(BaseModel):
    waste_hierarchy_level: str = Field(description="Nivel aplicable: reutilización, reparación, reciclaje, valorización energética, disposición final.")
    ler_code: str = Field(description="Código exacto (6 dígitos) de la Lista Europea de Residuos (LER). Si no estás seguro, provee el más cercano.")
    is_hazardous: bool = Field(description="Boolean True si el material porta nivel de peligrosidad intrínseco. False en caso contrario.")
    processing_notes: Optional[str] = Field(description="Nota breve para tratar el objeto.")

WASTE_SYSTEM_PROMPT = """Eres un experto en normativa medioambiental europea, economía circular y gestión de componentes industriales y de consumo.
Dada la identificación de un objeto, aplícale las reglas estrictas de la jerarquía LER y clasifica si representa riesgo ecológico.
Tu respuesta debe ser JSON determinista, evitando bloques de texto fuera del output.
"""

waste_prompt = ChatPromptTemplate.from_messages([
    ("system", WASTE_SYSTEM_PROMPT),
    ("user", "El objeto detectado fue clasificado como: {detected_object} de material {material} en estado {condition}. ¿Cómo lo clasificamos a nivel código LER europeo y peligrosidad?")
])
