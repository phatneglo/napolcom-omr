"""
Database base models for SQLAlchemy
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.SQLITE_DATABASE_URL}",
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}
)

# Create async session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

# Create base class
Base = declarative_base()
