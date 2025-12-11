"""
Redis caching layer for AI Agent Platform
Performance optimization, session management, and distributed caching
"""

import redis
import json
import pickle
from typing import Any, Optional, Dict, List
import asyncio
from datetime import datetime, timedelta
import logging
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis-based caching system"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 password: Optional[str] = None, decode_responses: bool = True):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )

        # Separate client for binary data
        self.redis_binary = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False
        )

        self._test_connection()

    def _test_connection(self):
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            logger.info("Redis connection established")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Using fallback mode.")
            self.redis_client = None
            self.redis_binary = None

    def _make_key(self, prefix: str, key: str) -> str:
        """Create a namespaced key"""
        return f"ai_agent:{prefix}:{key}"

    def _hash_key(self, key: str) -> str:
        """Hash long keys to avoid Redis key length limits"""
        if len(key) > 250:
            return hashlib.md5(key.encode()).hexdigest()
        return key

    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  prefix: str = "default") -> bool:
        """Set a cache value"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))

            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)

            if ttl:
                return bool(self.redis_client.setex(cache_key, ttl, serialized))
            else:
                return bool(self.redis_client.set(cache_key, serialized))
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def get(self, key: str, prefix: str = "default") -> Optional[Any]:
        """Get a cache value"""
        if not self.redis_client:
            return None

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))
            value = self.redis_client.get(cache_key)

            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def delete(self, key: str, prefix: str = "default") -> bool:
        """Delete a cache key"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))
            return bool(self.redis_client.delete(cache_key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str, prefix: str = "default") -> bool:
        """Check if a key exists"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))
            return bool(self.redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def expire(self, key: str, ttl: int, prefix: str = "default") -> bool:
        """Set expiration on a key"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))
            return bool(self.redis_client.expire(cache_key, ttl))
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False

    async def incr(self, key: str, prefix: str = "default") -> Optional[int]:
        """Increment a numeric value"""
        if not self.redis_client:
            return None

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))
            return self.redis_client.incr(cache_key)
        except Exception as e:
            logger.error(f"Redis incr error: {e}")
            return None

    # Session management
    async def set_session(self, session_id: str, data: Dict, ttl: int = 3600) -> bool:
        """Store session data"""
        return await self.set(session_id, data, ttl=ttl, prefix="session")

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data"""
        return await self.get(session_id, prefix="session")

    async def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        return await self.delete(session_id, prefix="session")

    # User-specific caching
    async def cache_user_data(self, user_id: str, key: str, data: Any, ttl: int = 300) -> bool:
        """Cache user-specific data"""
        cache_key = f"{user_id}:{key}"
        return await self.set(cache_key, data, ttl=ttl, prefix="user")

    async def get_user_data(self, user_id: str, key: str) -> Optional[Any]:
        """Get cached user-specific data"""
        cache_key = f"{user_id}:{key}"
        return await self.get(cache_key, prefix="user")

    # Task result caching
    async def cache_task_result(self, task_id: str, result: Dict, ttl: int = 3600) -> bool:
        """Cache task execution results"""
        return await self.set(task_id, result, ttl=ttl, prefix="task_result")

    async def get_task_result(self, task_id: str) -> Optional[Dict]:
        """Get cached task result"""
        return await self.get(task_id, prefix="task_result")

    # API response caching
    async def cache_api_response(self, endpoint: str, params: Dict, response: Any, ttl: int = 300) -> bool:
        """Cache API responses"""
        # Create a hash of endpoint + params for cache key
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        cache_key = hashlib.md5(key_data.encode()).hexdigest()
        return await self.set(cache_key, response, ttl=ttl, prefix="api")

    async def get_api_response(self, endpoint: str, params: Dict) -> Optional[Any]:
        """Get cached API response"""
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        cache_key = hashlib.md5(key_data.encode()).hexdigest()
        return await self.get(cache_key, prefix="api")

    # Rate limiting
    async def check_rate_limit(self, identifier: str, limit: int, window: int) -> tuple[bool, int]:
        """Check if rate limit is exceeded. Returns (allowed, remaining_requests)"""
        if not self.redis_client:
            return True, limit  # Allow if Redis is down

        try:
            key = f"ratelimit:{identifier}"
            current = await self.incr(key)

            if current == 1:
                # First request, set expiration
                await self.expire(key, window)

            remaining = max(0, limit - current)
            allowed = current <= limit

            return allowed, remaining
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True, limit

    # Binary data storage (for files, images, etc.)
    async def set_binary(self, key: str, data: bytes, ttl: Optional[int] = None,
                        prefix: str = "binary") -> bool:
        """Store binary data"""
        if not self.redis_binary:
            return False

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))

            if ttl:
                return bool(self.redis_binary.setex(cache_key, ttl, data))
            else:
                return bool(self.redis_binary.set(cache_key, data))
        except Exception as e:
            logger.error(f"Redis binary set error: {e}")
            return False

    async def get_binary(self, key: str, prefix: str = "binary") -> Optional[bytes]:
        """Retrieve binary data"""
        if not self.redis_binary:
            return None

        try:
            cache_key = self._make_key(prefix, self._hash_key(key))
            return self.redis_binary.get(cache_key)
        except Exception as e:
            logger.error(f"Redis binary get error: {e}")
            return None

    # Cache statistics
    async def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self.redis_client.dbsize(),
                "uptime_days": info.get("uptime_in_days", 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"status": "error", "error": str(e)}

    # Cache warming
    async def warm_cache(self, data_dict: Dict[str, Any], prefix: str = "default", ttl: int = 3600):
        """Warm cache with multiple key-value pairs"""
        for key, value in data_dict.items():
            await self.set(key, value, ttl=ttl, prefix=prefix)

    # Cache invalidation patterns
    async def invalidate_pattern(self, pattern: str, prefix: str = "default") -> int:
        """Invalidate all keys matching a pattern"""
        if not self.redis_client:
            return 0

        try:
            full_pattern = self._make_key(prefix, pattern)
            keys = self.redis_client.keys(full_pattern + "*")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
            return 0

    async def clear_user_cache(self, user_id: str) -> int:
        """Clear all cached data for a user"""
        return await self.invalidate_pattern(f"{user_id}:*", prefix="user")

    async def clear_api_cache(self) -> int:
        """Clear all API response cache"""
        return await self.invalidate_pattern("*", prefix="api")

# Global cache instance
cache = RedisCache()

# Decorators for caching
def cached(ttl: int = 300, prefix: str = "default"):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Try to get from cache first
            cached_result = await cache.get(cache_key, prefix=prefix)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl, prefix=prefix)
            return result

        return wrapper
    return decorator

def cache_on_user(ttl: int = 300):
    """Decorator to cache function results per user"""
    def decorator(func):
        @wraps(func)
        async def wrapper(user_id: str, *args, **kwargs):
            cache_key = f"{user_id}:{func.__name__}"
            cached_result = await cache.get_user_data(user_id, func.__name__)
            if cached_result is not None:
                return cached_result

            result = await func(user_id, *args, **kwargs)
            await cache.cache_user_data(user_id, func.__name__, result, ttl=ttl)
            return result

        return wrapper
    return decorator