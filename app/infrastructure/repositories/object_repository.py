from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.database.models import DetectedObjectORM
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

object_repository = ObjectRepository()
