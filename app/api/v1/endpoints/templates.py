"""
Template management endpoints
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.template import Template, TemplateCreate, TemplateUpdate, TemplateList
from app.crud.template import template
from app.services.template_service import create_template, upload_template_image

router = APIRouter()


@router.get("", response_model=TemplateList)
async def read_templates(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
) -> Any:
    """
    Get all templates with pagination and search
    """
    skip = (page - 1) * limit
    
    # Get templates
    items = await template.get_multi_with_search(
        db, skip=skip, limit=limit, search=search
    )
    
    # Get total count
    total = await template.count(db)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("", response_model=Template, status_code=status.HTTP_201_CREATED)
async def create_template_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_in: TemplateCreate,
) -> Any:
    """
    Create a new template
    """
    return await create_template(db, template_in)


@router.get("/{template_id}", response_model=Template)
async def read_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
) -> Any:
    """
    Get a specific template by ID
    """
    template_obj = await template.get(db, id=template_id)
    if not template_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )
    return template_obj


@router.put("/{template_id}", response_model=Template)
async def update_template_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
    template_in: TemplateUpdate,
) -> Any:
    """
    Update a template
    """
    template_obj = await template.get(db, id=template_id)
    if not template_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )
    
    template_obj = await template.update(db, db_obj=template_obj, obj_in=template_in)
    return template_obj


@router.delete("/{template_id}")
async def delete_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
) -> Any:
    """
    Delete a template
    """
    template_obj = await template.get(db, id=template_id)
    if not template_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )
    
    await template.remove(db, id=template_id)
    return {"success": True}


@router.post("/{template_id}/upload-image")
async def upload_template_image_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
    file: UploadFile = File(...),
) -> Any:
    """
    Upload an image for a template
    """
    file_path = await upload_template_image(db, template_id, file)
    return {"file_path": file_path}
