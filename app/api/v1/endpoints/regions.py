"""
Region management endpoints
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.region import Region, RegionCreate, RegionUpdate
from app.crud.region import region
from app.services.template_service import create_region, get_regions_by_template

router = APIRouter()


@router.get("", response_model=List[Region])
async def read_regions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int = Path(...),
) -> Any:
    """
    Get all regions for a template
    """
    return await get_regions_by_template(db, template_id)


@router.post("", response_model=Region, status_code=status.HTTP_201_CREATED)
async def create_region_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int = Path(...),
    region_in: RegionCreate,
) -> Any:
    """
    Create a new region for a template
    """
    # Ensure template_id in path matches the one in payload
    if region_in.template_id != template_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template ID in path and payload do not match"
        )
    
    return await create_region(db, region_in)


@router.get("/{region_id}", response_model=Region)
async def read_region(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int = Path(...),
    region_id: int = Path(...),
) -> Any:
    """
    Get a specific region by ID
    """
    region_obj = await region.get(db, id=region_id)
    if not region_obj or region_obj.template_id != template_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with ID {region_id} not found in template {template_id}"
        )
    return region_obj


@router.put("/{region_id}", response_model=Region)
async def update_region_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int = Path(...),
    region_id: int = Path(...),
    region_in: RegionUpdate,
) -> Any:
    """
    Update a region
    """
    region_obj = await region.get(db, id=region_id)
    if not region_obj or region_obj.template_id != template_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with ID {region_id} not found in template {template_id}"
        )
    
    region_obj = await region.update(db, db_obj=region_obj, obj_in=region_in)
    return region_obj


@router.delete("/{region_id}")
async def delete_region(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int = Path(...),
    region_id: int = Path(...),
) -> Any:
    """
    Delete a region
    """
    region_obj = await region.get(db, id=region_id)
    if not region_obj or region_obj.template_id != template_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with ID {region_id} not found in template {template_id}"
        )
    
    await region.remove(db, id=region_id)
    return {"success": True}
