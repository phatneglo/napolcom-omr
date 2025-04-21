"""
Configuration settings for the NAPOLCOM OMR Processing System
"""
from typing import List, Optional, Union
import os
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NAPOLCOM OMR Processing System"
    
    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Security
    SECRET_KEY: str = "napolcom_omr_secret_key_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    SQLITE_DATABASE_URL: str = "app.db"
    DATABASE_DIR: str = "data/db"
    
    # File storage
    UPLOAD_DIR: str = "data/uploads"
    TEMPLATES_DIR: str = "data/templates"
    MODELS_DIR: str = "data/models"
    DATASETS_DIR: str = "data/datasets"
    RESULTS_DIR: str = "data/results"
    
    # Processing parameters
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.5
    DEFAULT_IMAGE_SIZE: int = 1280
    
    # Debug settings
    DEBUG: bool = True
    WORKERS_COUNT: int = 1
    
    # File size limits
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    
    class Config:
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.DATABASE_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TEMPLATES_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(settings.DATASETS_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)

# Set database path
settings.SQLITE_DATABASE_URL = os.path.join(settings.DATABASE_DIR, settings.SQLITE_DATABASE_URL)
