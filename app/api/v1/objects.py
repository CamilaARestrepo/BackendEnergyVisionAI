from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.object_repository import object_repository
from app.domain.schemas.object_schema import DetectedObjectSchema, DetectedObjectUpdate
from pydantic import BaseModel

router = APIRouter(prefix="/objects", tags=["Object History"])

class PaginatedObjectResponse(BaseModel):
    items: List[DetectedObjectSchema]
    total: int
    page: int
    page_size: int
    pages: int

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
