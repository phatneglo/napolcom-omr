"""
Synthetic data generation service
"""
import os
import asyncio
import uuid
from typing import Dict, Any, Optional
import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.template import template as template_crud
from app.crud.region import region as region_crud
from app.crud.dataset import dataset as dataset_crud
from app.models.dataset import TrainingDataset
from app.schemas.dataset import DatasetCreate, DatasetGenerationTask


# Keep track of running tasks
active_generation_tasks = {}


async def create_dataset(
    db: AsyncSession, dataset_in: DatasetCreate
) -> DatasetGenerationTask:
    """
    Create a new dataset and start generation task
    """
    # Check if template exists
    template = await template_crud.get(db, id=dataset_in.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {dataset_in.template_id} not found"
        )
    
    # Check if dataset with same name already exists
    existing = await dataset_crud.get_by_name(db, name=dataset_in.dataset_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset with name '{dataset_in.dataset_name}' already exists"
        )
    
    # Create dataset path
    dataset_id = str(uuid.uuid4())
    dataset_path = os.path.join(settings.DATASETS_DIR, dataset_id)
    os.makedirs(dataset_path, exist_ok=True)
    
    # Create dataset record
    dataset_obj = TrainingDataset(
        template_id=dataset_in.template_id,
        dataset_name=dataset_in.dataset_name,
        dataset_path=dataset_path
    )
    db.add(dataset_obj)
    await db.commit()
    await db.refresh(dataset_obj)
    
    # Save configuration
    config_path = os.path.join(dataset_path, "config.json")
    with open(config_path, "w") as f:
        json.dump({
            "template_id": dataset_in.template_id,
            "dataset_name": dataset_in.dataset_name,
            "num_samples": dataset_in.num_samples,
            "variation_params": dataset_in.variation_params
        }, f, indent=2)
    
    # Start generation task
    task_id = await start_generation_task(dataset_obj.id, dataset_in)
    
    return DatasetGenerationTask(
        dataset_id=dataset_obj.id,
        status="queued",
        task_id=task_id,
        estimated_completion_time="10 minutes"  # Placeholder
    )


async def start_generation_task(dataset_id: int, dataset_in: DatasetCreate) -> str:
    """
    Start a background task to generate synthetic data
    """
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # In a real implementation, this would use something like Celery
    # For this sample, we'll use asyncio to simulate a background task
    active_generation_tasks[task_id] = {
        "dataset_id": dataset_id,
        "status": "running",
        "progress": 0.0,
        "config": dataset_in
    }
    
    # Start the task
    asyncio.create_task(generate_synthetic_data(task_id, dataset_id, dataset_in))
    
    return task_id


async def generate_synthetic_data(
    task_id: str, dataset_id: int, dataset_in: DatasetCreate
) -> None:
    """
    Generate synthetic data for a dataset
    """
    try:
        # This is a simplified implementation - in a real system, this would
        # generate actual synthetic training data based on the parameters
        
        # Simulate work with a sleep
        for i in range(10):
            active_generation_tasks[task_id]["progress"] = i / 10.0
            await asyncio.sleep(1)
        
        # Update task status
        active_generation_tasks[task_id]["status"] = "completed"
        active_generation_tasks[task_id]["progress"] = 1.0
        
    except Exception as e:
        # Update task status
        active_generation_tasks[task_id]["status"] = "failed"
        active_generation_tasks[task_id]["error"] = str(e)


async def get_generation_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a generation task
    """
    if task_id not in active_generation_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return active_generation_tasks[task_id]
