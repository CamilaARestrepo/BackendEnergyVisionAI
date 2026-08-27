import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.database.session import get_db_session
from app.infrastructure.database.models import DetectedObjectORM

router = APIRouter(prefix="/export", tags=["Data Export"])

@router.get("")
async def export_data(
    format: str = Query("csv", description="Formato de exportación: 'csv' o 'json'"),
    db: AsyncSession = Depends(get_db_session)
):
    """Descarga todo el historial reportable."""
    stmt = select(DetectedObjectORM).options(selectinload(DetectedObjectORM.energy_data))
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    if format == "json":
        data = []
        for r in records:
            d = {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "name": r.object_name,
                "category": r.object_category,
                "energy_score": r.energy_data.energy_score if r.energy_data else None,
                "ler_code": r.energy_data.ler_code if r.energy_data else None,
                "ai_provider": r.ai_provider
            }
            data.append(d)
        return JSONResponse(content=data)
        
    elif format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Fecha", "Nombre", "Categoria", "Material", "LER", "Energy Score", "AI Provider"])
        
        for r in records:
            ler = r.energy_data.ler_code if r.energy_data else ""
            score = r.energy_data.energy_score if r.energy_data else ""
            
            writer.writerow([
                r.id, 
                r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                r.object_name,
                r.object_category,
                r.object_material or "",
                ler,
                score,
                r.ai_provider
            ])
            
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vision_ai_export.csv"}
        )
        
    raise HTTPException(400, "Formato no soportado.")
