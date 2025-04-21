"""
Form CRUD operations
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.form import ProcessedForm
from app.schemas.form import FormCreate


class CRUDForm(CRUDBase[ProcessedForm, FormCreate, FormCreate]):
    """
    CRUD operations for processed forms
    """
    
    async def get_by_template(
        self, db: AsyncSession, *, template_id: int, skip: int = 0, limit: int = 100
    ) -> List[ProcessedForm]:
        """
        Get forms for a template
        """
        query = select(ProcessedForm).where(
            ProcessedForm.template_id == template_id
        ).order_by(
            ProcessedForm.processed_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_by_model(
        self, db: AsyncSession, *, model_id: int, skip: int = 0, limit: int = 100
    ) -> List[ProcessedForm]:
        """
        Get forms processed by a model
        """
        query = select(ProcessedForm).where(
            ProcessedForm.model_id == model_id
        ).order_by(
            ProcessedForm.processed_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_by_date_range(
        self, db: AsyncSession, *, 
        date_from: datetime, 
        date_to: datetime,
        skip: int = 0, 
        limit: int = 100
    ) -> List[ProcessedForm]:
        """
        Get forms processed within a date range
        """
        query = select(ProcessedForm).where(
            ProcessedForm.processed_at >= date_from,
            ProcessedForm.processed_at <= date_to
        ).order_by(
            ProcessedForm.processed_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_latest(
        self, db: AsyncSession, *, limit: int = 10
    ) -> List[ProcessedForm]:
        """
        Get the most recently processed forms
        """
        query = select(ProcessedForm).order_by(
            ProcessedForm.processed_at.desc()
        ).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def count_by_template(
        self, db: AsyncSession, *, template_id: int
    ) -> int:
        """
        Count forms for a template
        """
        query = select(
            func.count(ProcessedForm.id)
        ).where(
            ProcessedForm.template_id == template_id
        )
        result = await db.execute(query)
        return result.scalar_one()


# Create instance for use in endpoints
form = CRUDForm(ProcessedForm)
