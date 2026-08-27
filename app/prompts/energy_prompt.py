from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate

class EnergyResult(BaseModel):
    energy_score: int = Field(description="Puntuación (0-100) sobre el aprovechamiento energético posible del objeto.")
    kwh_per_unit: float = Field(description="Estimación en kWh extraíbles por UNA unidad de este objeto.", default=0.0)
    kwh_per_kg: float = Field(description="Estimación en kWh extraíbles por kilogramo del compuesto material.", default=0.0)
    valorization_methods: List[str] = Field(description="Lista de métodos viables (min 2) de valorización. Ej: Pirólisis, Reciclaje Silicio, Biogas.")

ENERGY_SYSTEM_PROMPT = """Eres un ingeniero especializado en recuperación de energía y economía circular.
Recibirás información de un objeto previamente identificado y sus catalogaciones de residuo.

Tu trabajo es estimar de forma rigurosa y teórica el Potencial Energético de este objeto de darse la máxima recuperación o incineración limpia permitida.
Dadas las categorías (Biomasa, RAEE, Metal, etc.), produce los resultados precisos. 

Devuelve de manera mandatoria un JSON válido. No uses block quotes de markdown (`json ...`).
"""

energy_prompt = ChatPromptTemplate.from_messages([
    ("system", ENERGY_SYSTEM_PROMPT),
    ("user", "El objeto detectado fue clasificado como: {detected_object} (Residuo Catalogado: {waste_classification}). ¿Cuál es el formato óptimo para extraer su energía intrínseca?")
])
