"""
Model CRUD operations
"""
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.model import TrainedModel
from app.schemas.model import ModelCreate


class CRUDModel(CRUDBase[TrainedModel, ModelCreate, ModelCreate]):
    """
    CRUD operations for trained models
    """
    
    async def get_by_template(
        self, db: AsyncSession, *, template_id: int, skip: int = 0, limit: int = 100
    ) -> List[TrainedModel]:
        """
        Get models for a template
        """
        query = select(TrainedModel).where(
            TrainedModel.template_id == template_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_by_dataset(
        self, db: AsyncSession, *, dataset_id: int
    ) -> List[TrainedModel]:
        """
        Get models trained on a dataset
        """
        query = select(TrainedModel).where(TrainedModel.dataset_id == dataset_id)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_by_name(
        self, db: AsyncSession, *, name: str
    ) -> Optional[TrainedModel]:
        """
        Get a model by name
        """
        query = select(TrainedModel).where(TrainedModel.model_name == name)
        result = await db.execute(query)
        return result.scalars().first()
        
    async def count_by_template(
        self, db: AsyncSession, *, template_id: int
    ) -> int:
        """
        Count models for a template
        """
        query = select(
            func.count(TrainedModel.id)
        ).where(
            TrainedModel.template_id == template_id
        )
        result = await db.execute(query)
        return result.scalar_one()


# Create instance for use in endpoints
model = CRUDModel(TrainedModel)
