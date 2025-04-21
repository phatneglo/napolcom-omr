"""
Main FastAPI application
"""
import os
import logging
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.api.v1.endpoints import pages
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import get_db
from app.services.auth_service import get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for NAPOLCOM OMR Form Processing System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Set up CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # If no origins specified, allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include web page routes separately (without the API prefix)
app.include_router(pages.router)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application")
    await init_db()
    
    # Ensure required directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMPLATES_DIR, exist_ok=True)
    os.makedirs(settings.MODELS_DIR, exist_ok=True)
    os.makedirs(settings.DATASETS_DIR, exist_ok=True)
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    
    logger.info("Application startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")
