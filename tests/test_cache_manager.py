"""
Tests for cache_manager.py
--------------------------
Validates caching functionality and TTL behavior.
"""

import pytest
import time
from cache_manager import (
    SimpleCache,
    generate_cache_key,
    get_cached,
    set_cached,
    clear_cache,
    get_cache_stats,
)


def test_simple_cache_set_and_get():
    """Cache should store and retrieve values."""
    cache = SimpleCache()
    cache.set("test_key", "test_value")
    
    result = cache.get("test_key")
    assert result == "test_value"


def test_simple_cache_expiration():
    """Cache entries should expire after TTL."""
    cache = SimpleCache()
    cache.set("test_key", "test_value", ttl=1)
    
    # Value should be available immediately
    assert cache.get("test_key") == "test_value"
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Value should be expired
    assert cache.get("test_key") is None


def test_simple_cache_lru_eviction():
    """Cache should evict oldest items when full."""
    cache = SimpleCache(max_size=3)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # Cache is full, adding one more should evict oldest
    cache.set("key4", "value4")
    
    # key1 should be evicted
    assert cache.get("key1") is None
    # Others should still be present
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


def test_generate_cache_key_consistency():
    """Cache key generation should be consistent for same inputs."""
    key1 = generate_cache_key("arg1", "arg2", kwarg1="value1")
    key2 = generate_cache_key("arg1", "arg2", kwarg1="value1")
    
    assert key1 == key2


def test_generate_cache_key_uniqueness():
    """Different inputs should generate different cache keys."""
    key1 = generate_cache_key("arg1", "arg2")
    key2 = generate_cache_key("arg1", "arg3")
    
    assert key1 != key2


def test_global_cache_operations():
    """Global cache functions should work correctly."""
    clear_cache()
    
    # Set a value
    set_cached("global_test_key", "global_test_value", ttl=10)
    
    # Retrieve it
    result = get_cached("global_test_key")
    assert result == "global_test_value"
    
    # Check stats
    stats = get_cache_stats()
    assert stats["size"] >= 1
    
    # Clear cache
    clear_cache()
    stats = get_cache_stats()
    assert stats["size"] == 0


def test_cache_handles_complex_data():
    """Cache should handle complex data structures."""
    cache = SimpleCache()
    
    complex_data = {
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "number": 42
    }
    
    cache.set("complex_key", complex_data)
    result = cache.get("complex_key")
    
    assert result == complex_data
