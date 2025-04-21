"""
Database initialization and migration
"""
import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.db.base import engine, Base
from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_password_hash

# Import all models to ensure they are registered with Base
from app.models.user import User
from app.models.template import FormTemplate
from app.models.region import FormRegion
from app.models.dataset import TrainingDataset
from app.models.model import TrainedModel
from app.models.form import ProcessedForm
from app.models.permission import Permission

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Initialize database with tables and initial data
    """
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Check if database was just created
        db_path = settings.SQLITE_DATABASE_URL
        db_exists = os.path.exists(db_path) and os.path.getsize(db_path) > 0
        
        # If new database, create admin user
        if not db_exists:
            await create_initial_data()
            
        logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def create_initial_data() -> None:
    """
    Create initial data - admin user
    """
    async for db in get_db():
        # Check if admin user exists
        admin = await db.execute(
            text("SELECT * FROM users WHERE username = 'admin'")
        )
        admin = admin.first()
        
        if not admin:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@napolcom.example",
                hashed_password=get_password_hash("admin"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            await db.commit()
            
            # Create admin permissions
            admin_permission = Permission(
                user_id=admin_user.id,
                permission_type="admin"
            )
            db.add(admin_permission)
            await db.commit()
            
            logger.info("Created admin user")
