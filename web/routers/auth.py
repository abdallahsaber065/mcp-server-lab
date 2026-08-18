"""
Authentication Router (web/routers/auth.py)
"""

import time
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_async_db
from db.models import Tenant
from db.repositories.user_repo import AsyncUserRepository
from services.auth_service import AuthService
from services.cache_service import cache_service
from web.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: Optional[str] = "tenant"


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    """Authenticate user with email and password, issuing access and refresh tokens."""
    user = await AuthService.authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token_data = {"sub": str(user.tenant_id), "email": user.email, "role": user.role, "name": user.full_name}
    access_token = AuthService.create_access_token(token_data)
    refresh_token = AuthService.create_refresh_token(token_data)

    repo = AsyncUserRepository(db)
    await repo.update_refresh_token(user.tenant_id, refresh_token)

    return {
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.tenant_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "assigned_unit_id": user.assigned_unit_id
        }
    }


@router.post("/refresh")
async def refresh_tokens(req: RefreshRequest, db: AsyncSession = Depends(get_async_db)):
    """Rotate and issue a new access token using a valid refresh token."""
    payload = await AuthService.verify_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id = payload.get("sub")
    repo = AsyncUserRepository(db)
    user = await repo.get_by_id(int(user_id))
    if not user or user.refresh_token != req.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Revoked or invalid refresh token session."
        )

    token_data = {"sub": str(user.tenant_id), "email": user.email, "role": user.role, "name": user.full_name}
    new_access_token = AuthService.create_access_token(token_data)
    new_refresh_token = AuthService.create_refresh_token(token_data)
    await repo.update_refresh_token(user.tenant_id, new_refresh_token)

    return {
        "status": "success",
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(current_user: Tenant = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    """Log out user and clear refresh token."""
    repo = AsyncUserRepository(db)
    await repo.update_refresh_token(current_user.tenant_id, None)
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/me")
async def get_current_user_profile(current_user: Tenant = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return {
        "status": "success",
        "user": {
            "id": current_user.tenant_id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role,
            "phone": current_user.phone,
            "assigned_unit_id": current_user.assigned_unit_id
        }
    }


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_async_db)):
    """Register a new user account. Role defaults to 'tenant'."""
    repo = AsyncUserRepository(db)
    existing = await repo.get_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    allowed_roles = {"tenant", "property_manager"}
    role = req.role if req.role in allowed_roles else "tenant"
    hashed_password = AuthService.hash_password(req.password)

    user = await repo.create_user(
        full_name=req.full_name,
        email=req.email,
        hashed_password=hashed_password,
        phone=req.phone,
        role=role,
    )

    token_data = {"sub": str(user.tenant_id), "email": user.email, "role": user.role, "name": user.full_name}
    access_token = AuthService.create_access_token(token_data)
    refresh_token = AuthService.create_refresh_token(token_data)
    await repo.update_refresh_token(user.tenant_id, refresh_token)

    return {
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.tenant_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "assigned_unit_id": user.assigned_unit_id
        }
    }


@router.get("/demo-accounts")
async def list_demo_accounts():
    """Return pre-configured demonstration accounts for 1-click login."""
    return {
        "status": "success",
        "accounts": [
            {
                "role": "executive_admin",
                "label": "Executive Admin",
                "email": "admin@cornerstonerealty.eg",
                "password": "AdminPass123!",
                "description": "Full access to HITL Approval Queue, Failure Tickets, and Tool Matrix."
            },
            {
                "role": "property_manager",
                "label": "Property Manager",
                "email": "abdallahsaber065@gmail.com",
                "password": "ManagerPass123!",
                "description": "Operations management, commercial leases, and autonomous state graphs."
            },
            {
                "role": "tenant",
                "label": "Registered Tenant",
                "email": "tarek.mahdy@cairomed.org",
                "password": "TenantPass123!",
                "description": "Tenant portal, active lease overview, maintenance tickets, and AI concierge."
            }
        ]
    }
