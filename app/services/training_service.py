"""
Model training service
"""
import os
import asyncio
import uuid
import json
from typing import Dict, Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.template import template as template_crud
from app.crud.dataset import dataset as dataset_crud
from app.crud.model import model as model_crud
from app.models.model import TrainedModel
from app.schemas.model import ModelCreate, ModelTrainingTask, ModelTrainingStatus


# Keep track of running tasks
active_training_tasks = {}


async def create_model(
    db: AsyncSession, model_in: ModelCreate
) -> ModelTrainingTask:
    """
    Create a new model and start training task
    """
    # Check if template exists
    template = await template_crud.get(db, id=model_in.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {model_in.template_id} not found"
        )
    
    # Check if dataset exists
    dataset = await dataset_crud.get(db, id=model_in.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {model_in.dataset_id} not found"
        )
    
    # Check if model with same name already exists
    existing = await model_crud.get_by_name(db, name=model_in.model_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model with name '{model_in.model_name}' already exists"
        )
    
    # Create model path
    model_id = str(uuid.uuid4())
    model_path = os.path.join(settings.MODELS_DIR, model_id)
    os.makedirs(model_path, exist_ok=True)
    
    # Create model record
    model_obj = TrainedModel(
        template_id=model_in.template_id,
        dataset_id=model_in.dataset_id,
        model_name=model_in.model_name,
        model_path=model_path,
        config_params=model_in.training_params
    )
    db.add(model_obj)
    await db.commit()
    await db.refresh(model_obj)
    
    # Save configuration
    config_path = os.path.join(model_path, "config.json")
    with open(config_path, "w") as f:
        json.dump({
            "template_id": model_in.template_id,
            "dataset_id": model_in.dataset_id,
            "model_name": model_in.model_name,
            "training_params": model_in.training_params
        }, f, indent=2)
    
    # Start training task
    task_id = await start_training_task(model_obj.id, model_in)
    
    return ModelTrainingTask(
        model_id=model_obj.id,
        status="queued",
        task_id=task_id,
        estimated_completion_time="30 minutes"  # Placeholder
    )


async def start_training_task(model_id: int, model_in: ModelCreate) -> str:
    """
    Start a background task to train a model
    """
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # In a real implementation, this would use something like Celery
    # For this sample, we'll use asyncio to simulate a background task
    epochs = model_in.training_params.get("epochs", 100)
    active_training_tasks[task_id] = {
        "model_id": model_id,
        "status": "running",
        "progress": 0.0,
        "current_epoch": 0,
        "total_epochs": epochs,
        "metrics": {
            "train_loss": [],
            "val_loss": [],
            "mAP50": []
        },
        "config": model_in
    }
    
    # Start the task
    asyncio.create_task(train_model(task_id, model_id, model_in))
    
    return task_id


async def train_model(
    task_id: str, model_id: int, model_in: ModelCreate
) -> None:
    """
    Train a model
    """
    try:
        # This is a simplified implementation - in a real system, this would
        # train an actual YOLO v8 model based on the parameters
        
        epochs = model_in.training_params.get("epochs", 100)
        
        # Simulate training with a sleep
        for epoch in range(epochs):
            # Update task status
            active_training_tasks[task_id]["current_epoch"] = epoch + 1
            active_training_tasks[task_id]["progress"] = (epoch + 1) / epochs
            
            # Simulate metrics
            train_loss = 1.0 - (epoch / epochs) * 0.7
            val_loss = 1.0 - (epoch / epochs) * 0.6
            mAP50 = (epoch / epochs) * 0.9
            
            active_training_tasks[task_id]["metrics"]["train_loss"].append(train_loss)
            active_training_tasks[task_id]["metrics"]["val_loss"].append(val_loss)
            active_training_tasks[task_id]["metrics"]["mAP50"].append(mAP50)
            
            await asyncio.sleep(0.5)
        
        # Update task status
        active_training_tasks[task_id]["status"] = "completed"
        active_training_tasks[task_id]["progress"] = 1.0
        
        # In a real implementation, we would update the model record with final metrics
        
    except Exception as e:
        # Update task status
        active_training_tasks[task_id]["status"] = "failed"
        active_training_tasks[task_id]["error"] = str(e)


async def get_training_task_status(task_id: str) -> ModelTrainingStatus:
    """
    Get the status of a training task
    """
    if task_id not in active_training_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    task = active_training_tasks[task_id]
    
    return ModelTrainingStatus(
        status=task["status"],
        progress=task["progress"],
        current_epoch=task["current_epoch"],
        total_epochs=task["total_epochs"],
        metrics=task["metrics"],
        eta=f"{(task['total_epochs'] - task['current_epoch']) * 0.5:.1f} seconds"
    )
