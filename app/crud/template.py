"""
Template CRUD operations
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.template import FormTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate


class CRUDTemplate(CRUDBase[FormTemplate, TemplateCreate, TemplateUpdate]):
    """
    CRUD operations for form templates
    """
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[FormTemplate]:
        """
        Get a template by name
        """
        query = select(FormTemplate).where(FormTemplate.name == name)
        result = await db.execute(query)
        return result.scalars().first()
        
    async def get_multi_with_search(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[FormTemplate]:
        """
        Get multiple templates with search filter
        """
        query = select(FormTemplate)
        
        if search:
            query = query.where(
                FormTemplate.name.ilike(f"%{search}%") | 
                FormTemplate.description.ilike(f"%{search}%")
            )
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


# Create instance for use in endpoints
template = CRUDTemplate(FormTemplate)
