from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.infrastructure.database.models import AISettingsORM
from app.infrastructure.repositories.base_repository import BaseRepository
from app.domain.schemas.settings_schema import AISettingsSchema, SettingsUpdate
from app.utils.security import security_service

class SettingsRepository(BaseRepository[AISettingsORM, AISettingsSchema, SettingsUpdate]):
    def __init__(self):
        super().__init__(AISettingsORM)

    async def get_active_provider(self, db: AsyncSession) -> Optional[AISettingsORM]:
        """Obtiene el proveedor actualmente configurado como activo."""
        result = await db.execute(select(self.model).filter(self.model.is_active == True))
        return result.scalars().first()

    async def set_active_provider(self, db: AsyncSession, provider_name: str) -> None:
        """Marca un proveedor como activo y desactiva el resto automáticamente."""
        await db.execute(update(self.model).values(is_active=False))
        await db.execute(update(self.model).filter(self.model.provider_name == provider_name).values(is_active=True))
        await db.commit()

    async def update_or_create(self, db: AsyncSession, obj_in: SettingsUpdate) -> AISettingsORM:
        """Actualiza o crea la configuración del proveedor en la base de datos cifrando la pass."""
        result = await db.execute(select(self.model).filter(self.model.provider_name == obj_in.provider_name))
        existing_provider = result.scalars().first()

        data_dict = obj_in.model_dump(exclude_unset=True)
        if obj_in.api_key is not None:
            data_dict["api_key"] = security_service.encrypt_api_key(obj_in.api_key)
        
        if existing_provider:
            for key, value in data_dict.items():
                setattr(existing_provider, key, value)
            db.add(existing_provider)
            await db.commit()
            await db.refresh(existing_provider)
            return existing_provider
        else:
            new_provider = self.model(**data_dict)
            db.add(new_provider)
            await db.commit()
            await db.refresh(new_provider)
            return new_provider

settings_repository = SettingsRepository()
