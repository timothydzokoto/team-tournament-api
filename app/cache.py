import redis
import json
import os
from typing import Any, Optional
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def _json_default(value: Any) -> Any:
    """Convert non-JSON-native objects into serializable payloads."""
    if isinstance(value, (datetime, date)):
        return {"__type__": "datetime", "value": value.isoformat()}

    # SQLAlchemy model instance support: cache column values only.
    table = getattr(value, "__table__", None)
    if table is not None and hasattr(table, "columns"):
        return {column.name: getattr(value, column.name) for column in table.columns}

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _json_object_hook(payload: dict[str, Any]) -> Any:
    """Restore tagged JSON values back to Python objects."""
    if payload.get("__type__") == "datetime":
        return datetime.fromisoformat(payload["value"])
    return payload

def cache_set(key: str, value: Any, expiry: int = 300) -> None:
    """Set a value in cache with expiration"""
    try:
        redis_client.setex(key, expiry, json.dumps(value, default=_json_default))
    except (redis.ConnectionError, TypeError, ValueError):
        # Silently skip caching when Redis is unavailable or value is not JSON serializable
        pass

def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache"""
    try:
        data = redis_client.get(key)
        return json.loads(data, object_hook=_json_object_hook) if data else None
    except (redis.ConnectionError, json.JSONDecodeError, TypeError, ValueError):
        return None

def cache_delete(key: str) -> None:
    """Delete a key from cache"""
    try:
        redis_client.delete(key)
    except redis.ConnectionError:
        pass

def cache_clear_pattern(pattern: str) -> None:
    """Clear all keys matching a pattern"""
    try:
        keys_to_delete = list(redis_client.scan_iter(match=pattern, count=1000))
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
    except redis.ConnectionError:
        pass


def cache_get_namespace_version(namespace: str) -> int:
    """Get a cache namespace version used for O(1) invalidation."""
    try:
        version = redis_client.get(f"cache_ns:{namespace}:v")
        return int(version) if version is not None else 1
    except (redis.ConnectionError, TypeError, ValueError):
        return 1


def cache_bump_namespace_version(namespace: str) -> None:
    """Invalidate all versioned keys in a namespace by bumping its version."""
    try:
        redis_client.incr(f"cache_ns:{namespace}:v")
    except redis.ConnectionError:
        pass
