"""
cache_manager.py — Simple in-memory caching with LRU eviction
------------------------------------------------------------
Provides fast caching for API responses and statute lookups to reduce
redundant external API calls and computation.
"""

from functools import lru_cache
from typing import Optional, Dict, Any
import hashlib
import json
import time
import logging

logger = logging.getLogger(__name__)

# ============================================================
# CACHE CONFIGURATION
# ============================================================

CACHE_TTL_SECONDS = 3600  # 1 hour default TTL
MAX_CACHE_SIZE = 1000  # Maximum number of cached items


class CacheEntry:
    """Cache entry with TTL support."""
    
    def __init__(self, value: Any, ttl: int = CACHE_TTL_SECONDS):
        self.value = value
        self.expires_at = time.time() + ttl
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > self.expires_at


class SimpleCache:
    """Simple in-memory cache with TTL and LRU eviction."""
    
    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._access_order = []
    
    def _evict_if_needed(self):
        """Evict oldest items if cache is full."""
        if len(self._cache) >= self._max_size:
            # Remove oldest accessed item
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                self._cache.pop(oldest_key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        if entry.is_expired():
            # Remove expired entry
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None
        
        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: int = CACHE_TTL_SECONDS):
        """Set value in cache with TTL."""
        self._evict_if_needed()
        self._cache[key] = CacheEntry(value, ttl)
        
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Global cache instance
_global_cache = SimpleCache()


# ============================================================
# CACHE KEY GENERATION
# ============================================================

def generate_cache_key(*args, **kwargs) -> str:
    """Generate a unique cache key from arguments."""
    # Create a deterministic key from arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


# ============================================================
# PUBLIC API
# ============================================================

def get_cached(key: str) -> Optional[Any]:
    """Get value from global cache."""
    value = _global_cache.get(key)
    if value is not None:
        logger.debug(f"Cache hit for key: {key[:8]}...")
    return value


def set_cached(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS):
    """Set value in global cache."""
    _global_cache.set(key, value, ttl)
    logger.debug(f"Cache set for key: {key[:8]}... (TTL: {ttl}s)")


def clear_cache():
    """Clear all cached data."""
    _global_cache.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics."""
    return {
        "size": _global_cache.size(),
        "max_size": _global_cache._max_size
    }


# ============================================================
# DECORATOR FOR CACHING FUNCTION RESULTS
# ============================================================

def cached(ttl: int = CACHE_TTL_SECONDS):
    """Decorator to cache function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = get_cached(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Compute and cache result
            result = func(*args, **kwargs)
            set_cached(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
