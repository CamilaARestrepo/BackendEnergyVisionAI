# -*- coding: utf-8 -*-
"""
Verificación de la caché RAG por hash (cortocircuito en validate_image_node).

- Caso 1: imagen duplicada + force=False → cached=True, db_record_id set, sin invocar LLM.
- Caso 2: imagen nueva (no existe en BD) → cached=False.
- Caso 3: imagen duplicada + force=True → cached=False (re-análisis forzado).

Usa un mock de object_repository.get_by_hash para evitar conexión real a BD.
"""
import sys
import io
import asyncio
import os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Agregar la raíz del backend al path (para importar app.*)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Imagen PNG 1x1 válida (mínima) para pasar magic bytes + Pillow
IMG_PNG_1x1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)

from app.utils.exceptions import ImageValidationError  # noqa
from app.agents.nodes.validate_image_node import validate_image_node
from app.infrastructure.repositories.object_repository import object_repository


class FakeORM:
    def __init__(self, rid):
        self.id = rid


async def run_case(name, force, patch, expect_cached):
    state = {
        "image_base64": IMG_PNG_1x1,
        "image_mime_type": "image/png",
        "image_hash": None,
        "force": force,
        "errors": [],
    }
    original = object_repository.get_by_hash
    if patch:
        async def fake_get_by_hash(db, image_hash):
            return FakeORM(42)
        object_repository.get_by_hash = fake_get_by_hash
    try:
        result = await validate_image_node(state)
        cached = result.get("cached")
        record_id = result.get("db_record_id")
        errors = result.get("errors", [])
        ok = cached == expect_cached and not errors
        status = "PASS" if ok else "FAIL"
        print(f"{status} | {name}: cached={cached}, record={record_id}, errors={errors}")
    finally:
        object_repository.get_by_hash = original


async def main():
    print("=== Verificación caché RAG por hash ===")
    await run_case("Caso 1: duplicada + force=False → cached", False, True, True)
    await run_case("Caso 2: no existe (sin patch) → cached=False", False, False, False)
    await run_case("Caso 3: duplicada + force=True → re-analiza", True, True, False)


if __name__ == "__main__":
    asyncio.run(main())
    print("=== Fin ===")