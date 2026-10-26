from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, distinct
from sqlalchemy.orm import selectinload
from app.infrastructure.database.models import DetectedObjectORM, EnergyDataORM
from app.infrastructure.repositories.base_repository import BaseRepository
from app.domain.schemas.object_schema import DetectedObjectCreate, DetectedObjectUpdate

class ObjectRepository(BaseRepository[DetectedObjectORM, DetectedObjectCreate, DetectedObjectUpdate]):
    def __init__(self):
        super().__init__(DetectedObjectORM)

    async def get_by_id_with_energy(self, db: AsyncSession, id: int) -> Optional[DetectedObjectORM]:
        """Obtiene el objeto detectado con sus datos energéticos mapeados."""
        stmt = select(self.model).options(selectinload(self.model.energy_data)).filter(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_hash(self, db: AsyncSession, image_hash: str) -> Optional[DetectedObjectORM]:
        """Verifica existencia de fichero para evitar iteraciones de LLM repetitivas."""
        result = await db.execute(select(self.model).filter(self.model.image_hash == image_hash))
        return result.scalars().first()

    async def list_paginated(self, db: AsyncSession, page: int = 1, page_size: int = 20, **filters) -> tuple[int, List[DetectedObjectORM]]:
        """Devuelve listado de objetos con limit e información total para UX Paginator."""
        skip = (page - 1) * page_size
        total = await self.count(db, **filters)
        
        stmt = select(self.model).options(selectinload(self.model.energy_data))
        for key, value in filters.items():
            if value is not None:
                stmt = stmt.filter(getattr(self.model, key) == value)
                
        stmt = stmt.order_by(self.model.created_at.desc()).offset(skip).limit(page_size)
        result = await db.execute(stmt)
        data = result.scalars().all()
        return total, list(data)

    async def get_stats(self, db: AsyncSession) -> dict:
        """Agregados para el panel resumen del scanner: totales, promedios y últimos escaneos."""
        agg = await db.execute(
            select(
                func.count(DetectedObjectORM.id),
                func.avg(DetectedObjectORM.confidence_score),
                func.avg(EnergyDataORM.energy_score),
                func.sum(case((EnergyDataORM.is_hazardous.is_(True), 1), else_=0)),
                func.count(distinct(DetectedObjectORM.object_category)),
                func.sum(EnergyDataORM.kwh_per_unit),
            )
            .select_from(DetectedObjectORM)
            .outerjoin(EnergyDataORM)
        )
        total, avg_confidence, avg_energy, hazardous, categories, total_kwh = agg.one()

        cat_result = await db.execute(
            select(DetectedObjectORM.object_category, func.count(DetectedObjectORM.id).label("count"))
            .group_by(DetectedObjectORM.object_category)
            .order_by(func.count(DetectedObjectORM.id).desc())
            .limit(4)
        )
        top_categories = [{"category": cat, "count": count} for cat, count in cat_result.all()]

        recent_result = await db.execute(
            select(DetectedObjectORM)
            .options(selectinload(DetectedObjectORM.energy_data))
            .order_by(DetectedObjectORM.created_at.desc())
            .limit(4)
        )
        recent = list(recent_result.scalars().all())

        return {
            "total_scans": total or 0,
            "avg_energy_score": avg_energy,
            "avg_confidence": avg_confidence,
            "hazardous_count": hazardous or 0,
            "categories_count": categories or 0,
            "total_kwh": total_kwh,
            "top_categories": top_categories,
            "recent": recent,
        }

object_repository = ObjectRepository()
