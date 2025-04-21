"""
Dataset CRUD operations
"""
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.dataset import TrainingDataset
from app.schemas.dataset import DatasetCreate


class CRUDDataset(CRUDBase[TrainingDataset, DatasetCreate, DatasetCreate]):
    """
    CRUD operations for training datasets
    """
    
    async def get_by_template(
        self, db: AsyncSession, *, template_id: int, skip: int = 0, limit: int = 100
    ) -> List[TrainingDataset]:
        """
        Get datasets for a template
        """
        query = select(TrainingDataset).where(
            TrainingDataset.template_id == template_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_by_name(
        self, db: AsyncSession, *, name: str
    ) -> Optional[TrainingDataset]:
        """
        Get a dataset by name
        """
        query = select(TrainingDataset).where(TrainingDataset.dataset_name == name)
        result = await db.execute(query)
        return result.scalars().first()
        
    async def count_by_template(
        self, db: AsyncSession, *, template_id: int
    ) -> int:
        """
        Count datasets for a template
        """
        query = select(
            func.count(TrainingDataset.id)
        ).where(
            TrainingDataset.template_id == template_id
        )
        result = await db.execute(query)
        return result.scalar_one()


# Create instance for use in endpoints
dataset = CRUDDataset(TrainingDataset)
