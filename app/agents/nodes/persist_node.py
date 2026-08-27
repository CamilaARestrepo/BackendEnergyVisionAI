import json
import os
import base64
import hashlib
from app.agents.state import AgentState
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories.object_repository import object_repository
from app.config import settings


async def persist_node(state: AgentState) -> dict:
    if state.get("errors"):
        return {}

    obj_data = state.get("detected_object")
    waste_data = state.get("waste_classification")
    energy_data = state.get("energy_data")

    if not obj_data:
        return {"errors": ["No hay datos del objeto listos para persistir."]}


    try:
        # ── 1. Hash e imagen ya calculados por validate_image_node ────────────
        b64 = state.get("image_base64", "")
        # Usar hash pre-calculado en validate_image_node (sobre imagen post-resize)
        img_hash = state.get("image_hash") or hashlib.sha256(b64.encode("utf-8")).hexdigest()

        # Detectar extensión real desde mime type
        mime = state.get("image_mime_type", "image/jpeg")
        ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
        ext = ext_map.get(mime, "jpg")
        filename = f"{img_hash}.{ext}"

        uploads_dir = settings.UPLOADS_DIR
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, filename)
        img_url_path = f"/uploads/{filename}"

        # Escribir archivo solo si no existe ya (idempotencia)
        if not os.path.exists(file_path):
            img_bytes = base64.b64decode(b64)
            with open(file_path, "wb") as f:
                f.write(img_bytes)

        # ── 2. Persistir en BD ─────────────────────────────────────────────────
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.infrastructure.database.models import EnergyDataORM

            # Idempotencia: si el hash ya existe, verificar/actualizar energy_data y retornar
            existing = await object_repository.get_by_hash(db, img_hash)
            if existing:
                # Upsert energy_data para el objeto existente
                if energy_data or waste_data:
                    result = await db.execute(
                        select(EnergyDataORM).where(EnergyDataORM.object_id == existing.id)
                    )
                    existing_energy = result.scalar_one_or_none()

                    if existing_energy:
                        # Actualizar registro existente
                        existing_energy.energy_score = energy_data.get("energy_score", 0) if energy_data else existing_energy.energy_score
                        existing_energy.kwh_per_unit = energy_data.get("kwh_per_unit", 0.0) if energy_data else existing_energy.kwh_per_unit
                        existing_energy.kwh_per_kg = energy_data.get("kwh_per_kg", 0.0) if energy_data else existing_energy.kwh_per_kg
                        existing_energy.valorization_methods = json.dumps(
                            energy_data.get("valorization_methods", []) if energy_data else [],
                            ensure_ascii=False,
                        )
                        existing_energy.waste_hierarchy_level = waste_data.get("waste_hierarchy_level") if waste_data else existing_energy.waste_hierarchy_level
                        existing_energy.ler_code = waste_data.get("ler_code") if waste_data else existing_energy.ler_code
                        existing_energy.is_hazardous = waste_data.get("is_hazardous", False) if waste_data else existing_energy.is_hazardous
                        existing_energy.processing_notes = waste_data.get("processing_notes") if waste_data else existing_energy.processing_notes
                        await db.commit()
                    else:
                        # No existía energy_data para este objeto — insertarlo ahora
                        energy_db = EnergyDataORM(
                            object_id=existing.id,
                            energy_score=energy_data.get("energy_score", 0) if energy_data else 0,
                            kwh_per_unit=energy_data.get("kwh_per_unit", 0.0) if energy_data else 0.0,
                            kwh_per_kg=energy_data.get("kwh_per_kg", 0.0) if energy_data else 0.0,
                            valorization_methods=json.dumps(
                                energy_data.get("valorization_methods", []) if energy_data else [],
                                ensure_ascii=False,
                            ),
                            waste_hierarchy_level=waste_data.get("waste_hierarchy_level") if waste_data else None,
                            ler_code=waste_data.get("ler_code") if waste_data else None,
                            is_hazardous=waste_data.get("is_hazardous", False) if waste_data else False,
                            processing_notes=waste_data.get("processing_notes") if waste_data else None,
                        )
                        db.add(energy_db)
                        await db.commit()

                return {"db_record_id": existing.id}

            creation_dict = {
                "object_name": obj_data.get("name", "Unknown"),
                "object_category": obj_data.get("category", "Unknown"),
                "object_material": obj_data.get("material"),
                "object_brand": obj_data.get("brand"),
                "object_condition": obj_data.get("condition"),
                "confidence_score": obj_data.get("confidence_score", 0.0),
                "description": obj_data.get("description"),
                "reuse_suggestions": json.dumps(obj_data.get("reuse_suggestions", []), ensure_ascii=False),
                "ai_provider": obj_data.get("ai_provider", "unknown"),
                "ai_model": obj_data.get("ai_model", "unknown"),
                "image_path": img_url_path,
                "image_hash": img_hash,
            }

            db_obj = await object_repository.create(db, creation_dict)

            # ── 3. Upsert datos energéticos ────────────────────────────────────
            if energy_data or waste_data:
                result = await db.execute(
                    select(EnergyDataORM).where(EnergyDataORM.object_id == db_obj.id)
                )
                existing_energy = result.scalar_one_or_none()

                if existing_energy:
                    existing_energy.energy_score = energy_data.get("energy_score", 0) if energy_data else existing_energy.energy_score
                    existing_energy.kwh_per_unit = energy_data.get("kwh_per_unit", 0.0) if energy_data else existing_energy.kwh_per_unit
                    existing_energy.kwh_per_kg = energy_data.get("kwh_per_kg", 0.0) if energy_data else existing_energy.kwh_per_kg
                    existing_energy.valorization_methods = json.dumps(
                        energy_data.get("valorization_methods", []) if energy_data else [],
                        ensure_ascii=False,
                    )
                    existing_energy.waste_hierarchy_level = waste_data.get("waste_hierarchy_level") if waste_data else existing_energy.waste_hierarchy_level
                    existing_energy.ler_code = waste_data.get("ler_code") if waste_data else existing_energy.ler_code
                    existing_energy.is_hazardous = waste_data.get("is_hazardous", False) if waste_data else existing_energy.is_hazardous
                    existing_energy.processing_notes = waste_data.get("processing_notes") if waste_data else existing_energy.processing_notes
                else:
                    energy_db = EnergyDataORM(
                        object_id=db_obj.id,
                        energy_score=energy_data.get("energy_score", 0) if energy_data else 0,
                        kwh_per_unit=energy_data.get("kwh_per_unit", 0.0) if energy_data else 0.0,
                        kwh_per_kg=energy_data.get("kwh_per_kg", 0.0) if energy_data else 0.0,
                        valorization_methods=json.dumps(
                            energy_data.get("valorization_methods", []) if energy_data else [],
                            ensure_ascii=False,
                        ),
                        waste_hierarchy_level=waste_data.get("waste_hierarchy_level") if waste_data else None,
                        ler_code=waste_data.get("ler_code") if waste_data else None,
                        is_hazardous=waste_data.get("is_hazardous", False) if waste_data else False,
                        processing_notes=waste_data.get("processing_notes") if waste_data else None,
                    )
                    db.add(energy_db)

                await db.commit()

            return {"db_record_id": db_obj.id}

    except Exception as e:
        import traceback
        return {"errors": [f"Error persistiendo a base de datos: {str(e)}\n{traceback.format_exc()}"]}
