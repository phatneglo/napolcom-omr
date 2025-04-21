"""
Authentication service
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud.user import user as user_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """
    Authenticate a user with username and password
    """
    user = await user_crud.authenticate(db, username=username, password=password)
    return user


def create_user_tokens(user_id: int) -> Token:
    """
    Create access and refresh tokens for a user
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user_id, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 2)
    refresh_token = create_refresh_token(
        subject=user_id, expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    )


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current user from the token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Check if token is a refresh token
        if payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is not valid for authentication",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise credentials_exception
        
    user = await user_crud.get(db, id=int(user_id))
    if user is None:
        raise credentials_exception
        
    if not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current user and verify that they are a superuser
    """
    if not user_crud.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    return current_user
