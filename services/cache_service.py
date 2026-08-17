"""
Async Redis Cache Service with In-Memory Fallback (services/cache_service.py)
Provides high-performance distributed caching, token revocation blacklist, and rate limiting.
"""

import os
import json
import time
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger("services.cache")

REDIS_URL = os.getenv("REDIS_URL")


class CacheService:
    """Async Redis caching client with automatic in-memory fallback."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or REDIS_URL
        self._redis = None
        self._in_memory: Dict[str, Dict[str, Any]] = {}
        self._is_redis_available = False

    async def connect(self):
        """Attempt to connect to Redis, or activate in-memory fallback."""
        if self.redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                await self._redis.ping()
                self._is_redis_available = True
                logger.info("Connected to Redis at %s", self.redis_url.split("@")[-1])
                return
            except Exception as e:
                logger.warning("Redis unavailable (%s), falling back to in-memory cache.", e)
        self._is_redis_available = False
        self._redis = None

    async def get(self, key: str) -> Optional[str]:
        if self._is_redis_available and self._redis:
            try:
                return await self._redis.get(key)
            except Exception:
                pass
        
        # In-memory fallback with TTL check
        item = self._in_memory.get(key)
        if item:
            if item["expires_at"] and time.time() > item["expires_at"]:
                del self._in_memory[key]
                return None
            return item["value"]
        return None

    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        if self._is_redis_available and self._redis:
            try:
                if expire_seconds:
                    await self._redis.setex(key, expire_seconds, value)
                else:
                    await self._redis.set(key, value)
                return True
            except Exception:
                pass

        # In-memory fallback
        expires_at = time.time() + expire_seconds if expire_seconds else None
        self._in_memory[key] = {"value": value, "expires_at": expires_at}
        return True

    async def delete(self, key: str) -> bool:
        if self._is_redis_available and self._redis:
            try:
                await self._redis.delete(key)
                return True
            except Exception:
                pass
        self._in_memory.pop(key, None)
        return True

    async def get_json(self, key: str) -> Optional[Any]:
        val = await self.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return None
        return None

    async def set_json(self, key: str, data: Any, expire_seconds: Optional[int] = None) -> bool:
        return await self.set(key, json.dumps(data), expire_seconds)

    async def blacklist_token(self, jti: str, expire_seconds: int) -> bool:
        """Add a revoked JWT token identifier to the blacklist."""
        return await self.set(f"auth:blacklist:{jti}", "1", expire_seconds)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a JWT token has been explicitly revoked."""
        val = await self.get(f"auth:blacklist:{jti}")
        return val is not None


# Global singleton instance
cache_service = CacheService()
