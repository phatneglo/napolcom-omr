"""
User CRUD operations
"""
from typing import Any, Dict, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for users
    """
    
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        Get a user by username
        """
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalars().first()
        
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()
        
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password
        """
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
        
    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user, hashing the password if provided
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
            
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
        
    async def authenticate(
        self, db: AsyncSession, *, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user with username and password
        """
        user = await self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
        
    def is_active(self, user: User) -> bool:
        """
        Check if a user is active
        """
        return user.is_active
        
    def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser
        """
        return user.is_superuser


# Create instance for use in endpoints
user = CRUDUser(User)
