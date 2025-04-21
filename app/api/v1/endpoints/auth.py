"""
Authentication endpoints
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, User as UserSchema
from app.services.auth_service import (
    authenticate_user,
    create_user_tokens,
    get_current_user,
    get_current_active_superuser
)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user_obj = await authenticate_user(db, form_data.username, form_data.password)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return create_user_tokens(user_obj.id)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Refresh access token
    """
    return create_user_tokens(current_user.id)


@router.post("/register", response_model=UserSchema)
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate
) -> Any:
    """
    Register a new user
    """
    # Check if user already exists
    user_obj = await user.get_by_username(db, username=user_in.username)
    if user_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    user_obj = await user.get_by_email(db, email=user_in.email)
    if user_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user_obj = await user.create(db, obj_in=user_in)
    return user_obj


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user
    """
    return current_user
