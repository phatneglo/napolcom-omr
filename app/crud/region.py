"""
Region CRUD operations
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.region import FormRegion
from app.schemas.region import RegionCreate, RegionUpdate


class CRUDRegion(CRUDBase[FormRegion, RegionCreate, RegionUpdate]):
    """
    CRUD operations for form regions
    """
    
    async def get_by_template(
        self, db: AsyncSession, *, template_id: int
    ) -> List[FormRegion]:
        """
        Get all regions for a template
        """
        query = select(FormRegion).where(FormRegion.template_id == template_id)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_by_template_and_type(
        self, db: AsyncSession, *, template_id: int, region_type: str
    ) -> List[FormRegion]:
        """
        Get regions for a template by type
        """
        query = select(FormRegion).where(
            FormRegion.template_id == template_id,
            FormRegion.region_type == region_type
        )
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_by_template_and_field_name(
        self, db: AsyncSession, *, template_id: int, field_name: str
    ) -> Optional[FormRegion]:
        """
        Get a specific region by template and field name
        """
        query = select(FormRegion).where(
            FormRegion.template_id == template_id,
            FormRegion.field_name == field_name
        )
        result = await db.execute(query)
        return result.scalars().first()


# Create instance for use in endpoints
region = CRUDRegion(FormRegion)
