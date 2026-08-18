"""
FastAPI Dependencies & Security Guards (web/deps.py)
"""

from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Tenant
from db.repositories.user_repo import AsyncUserRepository
from db.session import get_async_db
from services.auth_service import AuthService
from services.cache_service import CacheService, cache_service

bearer_scheme = HTTPBearer(auto_error=False)


async def get_redis() -> CacheService:
    """Dependency providing the async Redis cache service."""
    return cache_service


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> Tenant:
    """Enforce authentication via Bearer token and return active Tenant/User."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await AuthService.verify_token(auth.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    repo = AsyncUserRepository(db)
    user = await repo.get_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled.")

    return user


async def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[Tenant]:
    """Return current user if token is present and valid, otherwise None."""
    if not auth or not auth.credentials:
        return None
    try:
        return await get_current_user(auth, db)
    except HTTPException:
        return None


def require_roles(allowed_roles: List[str]) -> Callable:
    """Dependency factory restricting endpoint access to specific roles."""
    async def role_checker(current_user: Tenant = Depends(get_current_user)) -> Tenant:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Your role: '{current_user.role}'."
            )
        return current_user
    return role_checker


async def get_optional_user(request, db: AsyncSession) -> Optional[Tenant]:
    """Extract current user from raw Request Authorization header. Returns None if no valid token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        payload = await AuthService.verify_token(token)
        if not payload or payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        repo = AsyncUserRepository(db)
        user = await repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None
