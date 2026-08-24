import json
from typing import Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SimpleCacheManager:
    """Simple in-memory cache manager (no Redis dependency)."""

    def __init__(self):
        self._cache = {}
        self._expiry = {}

    def _clean_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, exp_time in self._expiry.items()
            if exp_time and exp_time < now
        ]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._clean_expired()
        value = self._cache.get(key)
        if value is not None:
            try:
                return json.loads(value) if isinstance(value, str) else value
            except (json.JSONDecodeError, TypeError):
                return value
        return None

    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """Set value in cache."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            self._cache[key] = value
            if expire:
                self._expiry[key] = datetime.utcnow() + timedelta(seconds=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        self._clean_expired()
        return key in self._cache

    def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern."""
        self._clean_expired()
        if pattern == "*":
            return list(self._cache.keys())
        # Simple pattern matching
        import fnmatch
        return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]

    def flush_db(self) -> bool:
        """Flush all cache."""
        self._cache.clear()
        self._expiry.clear()
        return True

    def get_stock_cache_key(self, symbol: str, data_type: str) -> str:
        """Generate cache key for stock data."""
        return f"stock:{symbol}:{data_type}"

    def get_user_cache_key(self, user_id: str, data_type: str) -> str:
        """Generate cache key for user data."""
        return f"user:{user_id}:{data_type}"

    def get_model_cache_key(self, model_id: str, data_type: str) -> str:
        """Generate cache key for model data."""
        return f"model:{model_id}:{data_type}"


# Global cache instance
cache = SimpleCacheManager()
