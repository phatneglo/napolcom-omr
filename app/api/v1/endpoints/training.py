"""
Training endpoints for datasets and models
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.dataset import Dataset, DatasetCreate, DatasetList, DatasetGenerationTask
from app.schemas.model import Model, ModelCreate, ModelList, ModelTrainingTask, ModelTrainingStatus
from app.crud.dataset import dataset
from app.crud.model import model
from app.services.synthetic_data_service import create_dataset, get_generation_task_status
from app.services.training_service import create_model, get_training_task_status

router = APIRouter()


# Dataset endpoints
@router.get("/datasets", response_model=DatasetList)
async def read_datasets(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    template_id: Optional[int] = None,
) -> Any:
    """
    Get all datasets with pagination and optional template filter
    """
    skip = (page - 1) * limit
    
    if template_id:
        # Get datasets for a specific template
        items = await dataset.get_by_template(
            db, template_id=template_id, skip=skip, limit=limit
        )
        total = await dataset.count_by_template(db, template_id=template_id)
    else:
        # Get all datasets
        items = await dataset.get_multi(db, skip=skip, limit=limit)
        total = await dataset.count(db)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/generate", response_model=DatasetGenerationTask, status_code=status.HTTP_202_ACCEPTED)
async def generate_dataset(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dataset_in: DatasetCreate,
) -> Any:
    """
    Generate a new synthetic dataset
    """
    return await create_dataset(db, dataset_in)


@router.get("/datasets/{dataset_id}", response_model=Dataset)
async def read_dataset(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dataset_id: int,
) -> Any:
    """
    Get a specific dataset by ID
    """
    dataset_obj = await dataset.get(db, id=dataset_id)
    if not dataset_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found"
        )
    return dataset_obj


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dataset_id: int,
) -> Any:
    """
    Delete a dataset
    """
    dataset_obj = await dataset.get(db, id=dataset_id)
    if not dataset_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found"
        )
    
    await dataset.remove(db, id=dataset_id)
    return {"success": True}


@router.get("/generation/{task_id}")
async def read_generation_task_status(
    *,
    current_user: User = Depends(get_current_user),
    task_id: str,
) -> Any:
    """
    Get the status of a dataset generation task
    """
    return await get_generation_task_status(task_id)


# Model endpoints
@router.get("/models", response_model=ModelList)
async def read_models(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    template_id: Optional[int] = None,
) -> Any:
    """
    Get all models with pagination and optional template filter
    """
    skip = (page - 1) * limit
    
    if template_id:
        # Get models for a specific template
        items = await model.get_by_template(
            db, template_id=template_id, skip=skip, limit=limit
        )
        total = await model.count_by_template(db, template_id=template_id)
    else:
        # Get all models
        items = await model.get_multi(db, skip=skip, limit=limit)
        total = await model.count(db)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/models", response_model=ModelTrainingTask, status_code=status.HTTP_202_ACCEPTED)
async def train_model_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    model_in: ModelCreate,
) -> Any:
    """
    Train a new model
    """
    return await create_model(db, model_in)


@router.get("/models/{model_id}", response_model=Model)
async def read_model(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    model_id: int,
) -> Any:
    """
    Get a specific model by ID
    """
    model_obj = await model.get(db, id=model_id)
    if not model_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {model_id} not found"
        )
    return model_obj


@router.get("/models/{model_id}/status", response_model=ModelTrainingStatus)
async def read_model_status(
    *,
    current_user: User = Depends(get_current_user),
    model_id: int,
    task_id: str,
) -> Any:
    """
    Get the training status of a model
    """
    return await get_training_task_status(task_id)


@router.delete("/models/{model_id}")
async def delete_model(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    model_id: int,
) -> Any:
    """
    Delete a model
    """
    model_obj = await model.get(db, id=model_id)
    if not model_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {model_id} not found"
        )
    
    await model.remove(db, id=model_id)
    return {"success": True}
