"""
Template management service
"""
import os
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.template import template as template_crud
from app.crud.region import region as region_crud
from app.models.template import FormTemplate
from app.models.region import FormRegion
from app.schemas.template import TemplateCreate, TemplateUpdate
from app.schemas.region import RegionCreate, RegionUpdate


async def create_template(
    db: AsyncSession, template_in: TemplateCreate
) -> FormTemplate:
    """
    Create a new form template
    """
    # Check if a template with this name already exists
    existing = await template_crud.get_by_name(db, name=template_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template_in.name}' already exists"
        )
    
    # Create the template
    template = await template_crud.create(db, obj_in=template_in)
    
    # Create a directory for this template's files
    template_dir = os.path.join(settings.TEMPLATES_DIR, str(template.id))
    os.makedirs(template_dir, exist_ok=True)
    
    return template


async def upload_template_image(
    db: AsyncSession, template_id: int, file: UploadFile
) -> str:
    """
    Upload an image for a template
    """
    # Check if template exists
    template = await template_crud.get(db, id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )
    
    # Check file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create template directory if it doesn't exist
    template_dir = os.path.join(settings.TEMPLATES_DIR, str(template_id))
    os.makedirs(template_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(template_dir, "template.jpg")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    return file_path


async def get_template_image_path(template_id: int) -> Optional[str]:
    """
    Get the path to a template's image
    """
    file_path = os.path.join(settings.TEMPLATES_DIR, str(template_id), "template.jpg")
    if os.path.exists(file_path):
        return file_path
    return None


async def create_region(
    db: AsyncSession, region_in: RegionCreate
) -> FormRegion:
    """
    Create a new region for a template
    """
    # Check if template exists
    template = await template_crud.get(db, id=region_in.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {region_in.template_id} not found"
        )
    
    # Check if region with same field name already exists
    existing = await region_crud.get_by_template_and_field_name(
        db, template_id=region_in.template_id, field_name=region_in.field_name
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Region with field name '{region_in.field_name}' already exists for this template"
        )
    
    # Create the region
    region = await region_crud.create(db, obj_in=region_in)
    
    return region


async def get_regions_by_template(
    db: AsyncSession, template_id: int
) -> List[FormRegion]:
    """
    Get all regions for a template
    """
    # Check if template exists
    template = await template_crud.get(db, id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )
    
    # Get regions
    regions = await region_crud.get_by_template(db, template_id=template_id)
    
    return regions
