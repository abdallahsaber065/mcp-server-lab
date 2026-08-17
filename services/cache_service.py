"""
Async Redis Cache Service with In-Memory Fallback & Namespacing (services/cache_service.py)
Provides high-performance distributed caching, token revocation blacklist, and rate limiting with key prefixing for shared Redis environments.
"""

import os
import json
import time
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger("services.cache")

REDIS_URL = os.getenv("REDIS_URL")
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "cornerstone:")


class CacheService:
    """Async Redis caching client with automatic in-memory fallback and namespace key scoping."""

    def __init__(self, redis_url: Optional[str] = None, prefix: Optional[str] = None):
        self.redis_url = redis_url or REDIS_URL
        self.prefix = prefix if prefix is not None else REDIS_KEY_PREFIX
        self._redis = None
        self._in_memory: Dict[str, Dict[str, Any]] = {}
        self._is_redis_available = False

    def _scoped_key(self, key: str) -> str:
        """Prepend namespace prefix to prevent collision in shared Redis instances."""
        if self.prefix and not key.startswith(self.prefix):
            return f"{self.prefix}{key}"
        return key

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
                logger.info(
                    "Connected to Redis (Namespace Prefix: '%s') at %s",
                    self.prefix,
                    self.redis_url.split("@")[-1]
                )
                return
            except Exception as e:
                logger.warning("Redis unavailable (%s), falling back to in-memory cache.", e)
        self._is_redis_available = False
        self._redis = None

    async def get(self, key: str) -> Optional[str]:
        scoped = self._scoped_key(key)
        if self._is_redis_available and self._redis:
            try:
                return await self._redis.get(scoped)
            except Exception:
                pass
        
        # In-memory fallback with TTL check
        item = self._in_memory.get(scoped)
        if item:
            if item["expires_at"] and time.time() > item["expires_at"]:
                del self._in_memory[scoped]
                return None
            return item["value"]
        return None

    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        scoped = self._scoped_key(key)
        if self._is_redis_available and self._redis:
            try:
                if expire_seconds:
                    await self._redis.setex(scoped, expire_seconds, value)
                else:
                    await self._redis.set(scoped, value)
                return True
            except Exception:
                pass

        # In-memory fallback
        expires_at = time.time() + expire_seconds if expire_seconds else None
        self._in_memory[scoped] = {"value": value, "expires_at": expires_at}
        return True

    async def delete(self, key: str) -> bool:
        scoped = self._scoped_key(key)
        if self._is_redis_available and self._redis:
            try:
                await self._redis.delete(scoped)
                return True
            except Exception:
                pass
        self._in_memory.pop(scoped, None)
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
        """Add a revoked JWT token identifier to the blacklist with namespace."""
        return await self.set(f"auth:blacklist:{jti}", "1", expire_seconds)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a JWT token has been explicitly revoked."""
        val = await self.get(f"auth:blacklist:{jti}")
        return val is not None


# Global singleton instance
cache_service = CacheService()
