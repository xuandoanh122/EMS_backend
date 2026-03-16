"""
Bootstrap routes - for initializing the first admin user.
These routes should be disabled after the first admin is created.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Use bcrypt directly instead of passlib to avoid compatibility issues
import bcrypt

from app.modules.auth.entity import User, UserRole
from app.core.database import AsyncSession, get_async_session
from app.core.response import APIResponse
from sqlalchemy import select


router = APIRouter(prefix="/init", tags=["Bootstrap"])

# Secret key for bootstrap endpoint - should be set via environment variable
BOOTSTRAP_SECRET = os.getenv("BOOTSTRAP_SECRET", "ems-bootstrap-secret-key-change-me")


class BootstrapRequest(BaseModel):
    secret: str = Field(..., description="Bootstrap secret key")
    username: str = Field(..., min_length=3, max_length=255, description="Username (nên sử dụng email)")
    password: str = Field(..., min_length=6, max_length=128)


class BootstrapResponse(BaseModel):
    id: int
    username: str
    role: str
    message: str


@router.post(
    "/admin", 
    status_code=status.HTTP_201_CREATED,
    summary="Bootstrap first admin user"
)
async def bootstrap_admin(
    data: BootstrapRequest,
    session: AsyncSession = Depends(get_async_session),
) -> BootstrapResponse:
    """
    Create the first admin user.
    
    This endpoint is intended for initial system setup only.
    It should be disabled or protected after the first admin is created.
    
    Required: Set BOOTSTRAP_SECRET environment variable for security.
    """
    
    # Verify bootstrap secret
    if data.secret != BOOTSTRAP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bootstrap secret"
        )
    
    # Check if admin already exists
    result = await session.execute(
        select(User).where(User.role == UserRole.ADMIN)
    )
    existing_admin = result.scalars().first()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists. Use /auth/users endpoint to manage users."
        )
    
    # Check if username is taken
    result = await session.execute(
        select(User).where(User.username == data.username)
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{data.username}' is already taken"
        )
    
    # Hash password using bcrypt directly (avoid passlib compatibility issues)
    password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create admin user
    admin = User(
        username=data.username,
        password_hash=password_hash,
        role=UserRole.ADMIN,
        is_active=True,
    )
    
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    
    return APIResponse.created(
        data=BootstrapResponse(
            id=admin.id,
            username=admin.username,
            role=admin.role.value,
            message="Admin user created successfully"
        ).model_dump(),
        detail="Admin user created successfully"
    )


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Check if system is initialized"
)
async def check_init_status(
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Check if admin user has been created."""
    
    result = await session.execute(
        select(User).where(User.role == UserRole.ADMIN)
    )
    admin_exists = result.scalars().first() is not None
    
    return APIResponse.success(
        data={
            "initialized": admin_exists,
            "message": "System is ready" if admin_exists else "System needs initialization"
        },
        detail="Init status"
    )
