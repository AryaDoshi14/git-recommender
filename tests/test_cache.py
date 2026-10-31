"""Tests for core/cache.py."""

import time
from core.cache import InMemoryCache


def test_in_memory_cache_basic_and_ttl():
    """Test get, set, and TTL expiration in InMemoryCache."""
    cache = InMemoryCache()

    # Basic get and set
    cache.set("foo", "bar")
    assert cache.get("foo") == "bar"
    assert cache.get("nonexistent") is None

    # Expiry test
    cache.set("temp", "val", ttl=1)
    assert cache.get("temp") == "val"
    time.sleep(1.1)
    assert cache.get("temp") is None


def test_in_memory_cache_mget_mset():
    """Test mget and mset operations."""
    cache = InMemoryCache()
    cache.mset({"k1": "v1", "k2": "v2", "k3": "v3"}, ttl=10)

    res = cache.mget(["k1", "k3", "missing"])
    assert res == {"k1": "v1", "k3": "v3"}
