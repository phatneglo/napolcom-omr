"""
API router for v1 endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, templates, regions, training, processing, pages, dashboard

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(regions.router, prefix="/templates/{template_id}/regions", tags=["regions"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(processing.router, prefix="/processing", tags=["processing"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Don't include page routes here - they're added directly to the main app
