"""
Form processing endpoints
"""
from typing import Any, Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.form import Form, FormCreate, FormList, FormProcessingTask
from app.crud.form import form
from app.services.inference_service import process_form, get_processing_task_status

router = APIRouter()


@router.get("/forms", response_model=FormList)
async def read_forms(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    template_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Any:
    """
    Get all processed forms with pagination and filters
    """
    skip = (page - 1) * limit
    
    if template_id:
        # Get forms for a specific template
        items = await form.get_by_template(
            db, template_id=template_id, skip=skip, limit=limit
        )
        total = await form.count_by_template(db, template_id=template_id)
    elif date_from and date_to:
        # Get forms within a date range
        items = await form.get_by_date_range(
            db, date_from=date_from, date_to=date_to, skip=skip, limit=limit
        )
        # For simplicity, not implementing count for date range
        total = len(items)
    else:
        # Get all forms
        items = await form.get_multi(db, skip=skip, limit=limit)
        total = await form.count(db)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/forms", response_model=FormProcessingTask, status_code=status.HTTP_202_ACCEPTED)
async def process_form_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    form_in: FormCreate,
    file: UploadFile = File(...),
) -> Any:
    """
    Process a new form
    """
    return await process_form(db, form_in, file)


@router.get("/forms/{form_id}", response_model=Form)
async def read_form(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    form_id: int,
) -> Any:
    """
    Get a specific form by ID
    """
    form_obj = await form.get(db, id=form_id)
    if not form_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found"
        )
    return form_obj


@router.get("/forms/{form_id}/download")
async def download_form_results(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    form_id: int,
    format: str = Query("json", regex="^(csv|json|xlsx)$"),
) -> Any:
    """
    Download form results in the specified format
    """
    form_obj = await form.get(db, id=form_id)
    if not form_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found"
        )
    
    # In a real implementation, this would generate a file in the requested format
    # For this sample, we'll just return a placeholder response
    return {
        "message": f"Download form {form_id} results in {format} format",
        "extracted_data": form_obj.extracted_data
    }


@router.delete("/forms/{form_id}")
async def delete_form(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    form_id: int,
) -> Any:
    """
    Delete a form
    """
    form_obj = await form.get(db, id=form_id)
    if not form_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found"
        )
    
    await form.remove(db, id=form_id)
    return {"success": True}


@router.get("/forms/{form_id}/image")
async def get_form_image(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    form_id: int,
) -> Any:
    """
    Get the original image of a processed form
    """
    form_obj = await form.get(db, id=form_id)
    if not form_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found"
        )
    
    # Return the image file
    return FileResponse(form_obj.image_path)


@router.get("/tasks/{task_id}")
async def read_processing_task_status(
    *,
    current_user: User = Depends(get_current_user),
    task_id: str,
) -> Any:
    """
    Get the status of a form processing task
    """
    return await get_processing_task_status(task_id)
