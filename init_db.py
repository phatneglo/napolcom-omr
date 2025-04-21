"""
Database initialization script
"""
import os
import asyncio
import argparse
import logging

from app.db.init_db import init_db
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def init():
    """
    Initialize the database
    """
    logger.info("Initializing database...")
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(settings.SQLITE_DATABASE_URL), exist_ok=True)
    
    # Initialize database
    await init_db()
    
    logger.info("Database initialization complete")


def main():
    """
    Command-line entry point
    """
    parser = argparse.ArgumentParser(description='Initialize the database')
    parser.add_argument('--reset', action='store_true', help='Reset the database if it exists')
    
    args = parser.parse_args()
    
    # Reset database if requested
    if args.reset and os.path.exists(settings.SQLITE_DATABASE_URL):
        logger.warning(f"Deleting existing database: {settings.SQLITE_DATABASE_URL}")
        os.remove(settings.SQLITE_DATABASE_URL)
    
    # Run the initialization
    asyncio.run(init())


if __name__ == "__main__":
    main()
