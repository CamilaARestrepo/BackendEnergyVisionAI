from fastapi import APIRouter
from app.api.v1 import settings
from app.api.v1 import scan
from app.api.v1 import objects
from app.api.v1 import export

api_router = APIRouter()
api_router.include_router(settings.router)
api_router.include_router(scan.router)
api_router.include_router(objects.router)
api_router.include_router(export.router)
