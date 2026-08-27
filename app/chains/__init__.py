"""
Módulo de chains de LangChain para EnergyVision AI.

Las chains encapsulan la lógica de invocación del LLM,
separándola de los nodos del grafo LangGraph que actúan como coordinadores.

Chains disponibles:
  - detection_chain: Identifica el objeto principal en una imagen
  - waste_chain: Clasifica el residuo según jerarquía LER europea
  - energy_chain: Calcula el potencial energético del objeto
"""

from app.chains.detection_chain import detection_chain, DetectionChain
from app.chains.waste_chain import waste_chain, WasteChain
from app.chains.energy_chain import energy_chain, EnergyChain

__all__ = [
    "detection_chain",
    "waste_chain",
    "energy_chain",
    "DetectionChain",
    "WasteChain",
    "EnergyChain",
]
