from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.object_repository import object_repository
from app.domain.schemas.object_schema import DetectedObjectSchema, DetectedObjectUpdate
from pydantic import BaseModel, Field

router = APIRouter(prefix="/objects", tags=["Object History"])

class PaginatedObjectResponse(BaseModel):
    items: List[DetectedObjectSchema]
    total: int
    page: int
    page_size: int
    pages: int

class CategoryStat(BaseModel):
    category: str
    count: int

class RecentScan(BaseModel):
    id: int
    object_name: str
    object_category: str
    image_path: str
    created_at: datetime
    energy_score: Optional[int] = None
    is_hazardous: bool = False

class ObjectStatsResponse(BaseModel):
    total_scans: int
    avg_energy_score: Optional[float] = None
    avg_confidence: Optional[float] = None
    hazardous_count: int
    categories_count: int
    total_kwh: Optional[float] = None
    top_categories: List[CategoryStat] = Field(default_factory=list)
    recent: List[RecentScan] = Field(default_factory=list)

@router.get("", response_model=PaginatedObjectResponse)
async def list_objects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Devuelve listado paginado filtrable."""
    filters = {}
    if category: filters["object_category"] = category
    if provider: filters["ai_provider"] = provider
    
    total, items = await object_repository.list_paginated(db, page, page_size, **filters)
    pages = (total + page_size - 1) // page_size
    
    return PaginatedObjectResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )

@router.get("/stats", response_model=ObjectStatsResponse)
async def get_object_stats(db: AsyncSession = Depends(get_db_session)):
    """Resumen agregado del historial para el mini dashboard del scanner."""
    stats = await object_repository.get_stats(db)
    recent = [
        RecentScan(
            id=obj.id,
            object_name=obj.object_name,
            object_category=obj.object_category,
            image_path=obj.image_path,
            created_at=obj.created_at,
            energy_score=obj.energy_data.energy_score if obj.energy_data else None,
            is_hazardous=bool(obj.energy_data.is_hazardous) if obj.energy_data else False,
        )
        for obj in stats["recent"]
    ]
    return ObjectStatsResponse(
        total_scans=stats["total_scans"],
        avg_energy_score=stats["avg_energy_score"],
        avg_confidence=stats["avg_confidence"],
        hazardous_count=stats["hazardous_count"],
        categories_count=stats["categories_count"],
        total_kwh=stats["total_kwh"],
        top_categories=[CategoryStat(**c) for c in stats["top_categories"]],
        recent=recent,
    )

@router.get("/{id}", response_model=DetectedObjectSchema)
async def get_object(id: int, db: AsyncSession = Depends(get_db_session)):
    obj = await object_repository.get_by_id_with_energy(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objeto no encontrado.")
    return obj

@router.patch("/{id}", response_model=DetectedObjectSchema)
async def update_object(id: int, payload: DetectedObjectUpdate, db: AsyncSession = Depends(get_db_session)):
    obj = await object_repository.get_by_id_with_energy(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objeto no encontrado.")
    
    obj = await object_repository.update(db, obj, payload)
    return obj

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(id: int, db: AsyncSession = Depends(get_db_session)):
    deleted = await object_repository.delete(db, id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objeto no encontrado.")
