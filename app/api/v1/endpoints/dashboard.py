"""
Dashboard API endpoints
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.crud.template import template
from app.crud.dataset import dataset
from app.crud.model import model
from app.crud.form import form

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get dashboard statistics
    """
    # Get counts
    templates_count = await template.count(db)
    datasets_count = await dataset.count(db)
    models_count = await model.count(db)
    forms_count = await form.count(db)
    
    # Get recent forms
    recent_forms = await form.get_latest(db, limit=5)
    
    # Generate sample activity data
    activity_data = {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "datasets": [
            {
                "label": "Forms Processed",
                "data": [65, 59, 80, 81, 56, 55, 40],
                "borderColor": "rgb(54, 162, 235)",
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "tension": 0.4,
                "fill": True
            }
        ]
    }
    
    # Queue statistics (sample data)
    active_jobs = 2
    pending_jobs = 3
    completed_jobs = 45
    
    # Format the response
    response = {
        "templates_count": templates_count,
        "datasets_count": datasets_count,
        "models_count": models_count,
        "forms_count": forms_count,
        "recent_forms": [
            {
                "id": form.id,
                "template_id": form.template_id,
                "template_name": "Template Name",  # In a real implementation, we would fetch this
                "processed_at": form.processed_at.isoformat(),
                "confidence_score": form.confidence_score or 0.0,
                "status": "completed"
            }
            for form in recent_forms
        ],
        "activity_data": activity_data,
        "active_jobs": active_jobs,
        "pending_jobs": pending_jobs,
        "completed_jobs": completed_jobs
    }
    
    return response
