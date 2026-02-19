import redis
import json
import os
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def cache_set(key: str, value: Any, expiry: int = 300) -> None:
    """Set a value in cache with expiration"""
    try:
        redis_client.setex(key, expiry, json.dumps(value))
    except (redis.ConnectionError, TypeError, ValueError):
        # Silently skip caching when Redis is unavailable or value is not JSON serializable
        pass

def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache"""
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
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
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except redis.ConnectionError:
        pass 
