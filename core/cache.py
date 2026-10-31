"""Caching abstraction layer supporting Upstash Redis REST or in-memory dict with TTL.

Callers interact with get, set, mget, and mset without needing to know which backend is active.
"""

import json
import logging
import time
from threading import Lock
from typing import Any, Dict, List, Optional
import requests

from core.config import UPSTASH_REDIS_REST_TOKEN, UPSTASH_REDIS_REST_URL

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Thread-safe in-memory cache with timestamp-based TTL expiry."""

    def __init__(self) -> None:
        self._store: Dict[str, tuple[Any, Optional[float]]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            val, expires_at = entry
            if expires_at is not None and time.time() > expires_at:
                del self._store[key]
                return None
            return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = (time.time() + ttl) if ttl is not None else None
        with self._lock:
            self._store[key] = (value, expires_at)

    def mget(self, keys: List[str]) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        now = time.time()
        with self._lock:
            for k in keys:
                entry = self._store.get(k)
                if entry is not None:
                    val, expires_at = entry
                    if expires_at is not None and now > expires_at:
                        del self._store[k]
                    else:
                        results[k] = val
        return results

    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        expires_at = (time.time() + ttl) if ttl is not None else None
        with self._lock:
            for k, v in mapping.items():
                self._store[k] = (v, expires_at)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


class UpstashRedisCache:
    """Upstash Redis REST client using requests."""

    def __init__(self, rest_url: str, token: str) -> None:
        self.url = rest_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._fallback = InMemoryCache()

    def _execute(self, command: List[Any]) -> Any:
        try:
            resp = requests.post(
                self.url,
                headers=self.headers,
                json=command,
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("result")
        except Exception as e:
            logger.warning("Upstash Redis error: %s. Using in-memory fallback.", e)
        return None

    def get(self, key: str) -> Optional[Any]:
        raw = self._execute(["GET", key])
        if raw is not None:
            try:
                return json.loads(raw)
            except Exception:
                return raw
        return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        # Also set in fallback in case Upstash is temporarily unreachable
        self._fallback.set(key, value, ttl)
        serialized = json.dumps(value)
        if ttl is not None:
            self._execute(["SET", key, serialized, "EX", ttl])
        else:
            self._execute(["SET", key, serialized])

    def mget(self, keys: List[str]) -> Dict[str, Any]:
        if not keys:
            return {}
        raw_list = self._execute(["MGET"] + keys)
        results: Dict[str, Any] = {}
        if isinstance(raw_list, list) and len(raw_list) == len(keys):
            for k, raw in zip(keys, raw_list):
                if raw is not None:
                    try:
                        results[k] = json.loads(raw)
                    except Exception:
                        results[k] = raw
            return results
        # Fallback if Upstash failed
        return self._fallback.mget(keys)

    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        if not mapping:
            return
        self._fallback.mset(mapping, ttl)
        if ttl is not None:
            # Upstash pipeline for commands with TTL
            pipeline_commands = [
                ["SET", k, json.dumps(v), "EX", ttl] for k, v in mapping.items()
            ]
            try:
                requests.post(
                    f"{self.url}/pipeline",
                    headers=self.headers,
                    json=pipeline_commands,
                    timeout=5,
                )
            except Exception as e:
                logger.warning("Upstash Redis pipeline error: %s", e)
        else:
            cmd = ["MSET"]
            for k, v in mapping.items():
                cmd.extend([k, json.dumps(v)])
            self._execute(cmd)


# Initialize active cache instance
if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
    _CACHE_INSTANCE = UpstashRedisCache(UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN)
else:
    _CACHE_INSTANCE = InMemoryCache()


def get(key: str) -> Optional[Any]:
    """Retrieve an item from cache by key. Returns None if key not found or expired."""
    return _CACHE_INSTANCE.get(key)


def set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Store an item in cache with an optional TTL in seconds."""
    _CACHE_INSTANCE.set(key, value, ttl)


def mget(keys: List[str]) -> Dict[str, Any]:
    """Retrieve multiple items from cache. Returns a dict of key -> value for hits."""
    return _CACHE_INSTANCE.mget(keys)


def mset(mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
    """Store multiple key-value pairs in cache with an optional TTL in seconds."""
    _CACHE_INSTANCE.mset(mapping, ttl)
