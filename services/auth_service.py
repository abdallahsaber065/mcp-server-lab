"""
Authentication & JWT Token Service (services/auth_service.py)
"""

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import Tenant
from db.repositories.user_repo import AsyncUserRepository, UserRepository
from services.cache_service import cache_service

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cornerstone_dev_secret_key_change_in_production_991283")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class AuthService:
    """Handles password hashing, token issuance, verification, and rotation."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt if available, else SHA256-PBKDF2."""
        try:
            pwd_bytes = password.encode("utf-8")
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")
        except Exception:
            salt = uuid.uuid4().hex
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return f"pbkdf2${salt}${dk.hex()}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        if not hashed_password:
            return False
        try:
            if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
                return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
            elif hashed_password.startswith("pbkdf2$"):
                parts = hashed_password.split("$")
                salt = parts[1]
                target_hex = parts[2]
                dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
                return dk.hex() == target_hex
            return plain_password == hashed_password  # Fallback for plain test strings
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access"
        })
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "refresh"
        })
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    async def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and verify a JWT token, ensuring it is not blacklisted."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            if jti and await cache_service.is_token_blacklisted(jti):
                return None
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[Tenant]:
        repo = AsyncUserRepository(session)
        user = await repo.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not AuthService.verify_password(password, user.hashed_password or ""):
            return None
        return user
