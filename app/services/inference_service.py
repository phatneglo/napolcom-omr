"""
Form processing inference service
"""
import os
import asyncio
import uuid
import json
from typing import Dict, Any, Optional
import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.template import template as template_crud
from app.crud.model import model as model_crud
from app.crud.form import form as form_crud
from app.models.form import ProcessedForm
from app.schemas.form import FormCreate, FormProcessingTask


# Keep track of running tasks
active_processing_tasks = {}


async def process_form(
    db: AsyncSession, form_in: FormCreate, file: UploadFile
) -> FormProcessingTask:
    """
    Process a form image
    """
    # Check if template exists
    template = await template_crud.get(db, id=form_in.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {form_in.template_id} not found"
        )
    
    # Check if model exists
    model = await model_crud.get(db, id=form_in.model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {form_in.model_id} not found"
        )
    
    # Check file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create upload directory if it doesn't exist
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    upload_dir = os.path.join(settings.UPLOAD_DIR, today)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    filename = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Create form record
    form_obj = ProcessedForm(
        template_id=form_in.template_id,
        model_id=form_in.model_id,
        image_path=file_path
    )
    db.add(form_obj)
    await db.commit()
    await db.refresh(form_obj)
    
    # Start processing task
    task_id = await start_processing_task(form_obj.id, form_in, file_path)
    
    return FormProcessingTask(
        form_id=form_obj.id,
        status="queued",
        task_id=task_id
    )


async def start_processing_task(form_id: int, form_in: FormCreate, file_path: str) -> str:
    """
    Start a background task to process a form
    """
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # In a real implementation, this would use something like Celery
    # For this sample, we'll use asyncio to simulate a background task
    active_processing_tasks[task_id] = {
        "form_id": form_id,
        "status": "running",
        "progress": 0.0,
        "config": form_in,
        "file_path": file_path
    }
    
    # Start the task
    asyncio.create_task(process_form_image(task_id, form_id, form_in, file_path))
    
    return task_id


async def process_form_image(
    task_id: str, form_id: int, form_in: FormCreate, file_path: str
) -> None:
    """
    Process a form image
    """
    try:
        # This is a simplified implementation - in a real system, this would
        # use the OMR processing pipeline to extract data from the form
        
        # Simulate processing with a sleep
        await asyncio.sleep(3)
        
        # Generate sample results
        results = {
            "booklet_number": "123456",
            "date_of_exam": "04/15/2025",
            "date_of_birth": "01/01/1990",
            "surname": "SMITH",
            "first_name": "JOHN",
            "middle_name": "DOE",
            "set_type": "A",
            "application_number": "12345678901",
            "answers": {
                "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
                # ... more answers
            }
        }
        
        # In a real implementation, we would update the form record with the results
        async with AsyncSession(bind=None) as db:
            form_obj = await form_crud.get(db, id=form_id)
            if form_obj:
                form_obj.extracted_data = results
                form_obj.confidence_score = 0.95
                db.add(form_obj)
                await db.commit()
        
        # Update task status
        active_processing_tasks[task_id]["status"] = "completed"
        active_processing_tasks[task_id]["progress"] = 1.0
        active_processing_tasks[task_id]["results"] = results
        
    except Exception as e:
        # Update task status
        active_processing_tasks[task_id]["status"] = "failed"
        active_processing_tasks[task_id]["error"] = str(e)


async def get_processing_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a processing task
    """
    if task_id not in active_processing_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return active_processing_tasks[task_id]
