import json
from typing import Any

import redis

from shared.config import get_settings

settings = get_settings()


class RedisCache:
    """Redis cache wrapper for task outputs."""

    def __init__(self, url: str, default_ttl: int = 3600) -> None:
        self.client = redis.from_url(url, decode_responses=True)
        self.default_ttl = default_ttl

    def _task_key(self, task_uuid: str) -> str:
        """Generate cache key for task."""
        return f"task:{task_uuid}"

    def get(self, task_uuid: str) -> dict[str, Any] | None:
        """Get cached task output."""
        data = self.client.get(self._task_key(task_uuid))
        if data:
            return json.loads(data)  # type: ignore[no-any-return]
        return None

    def get_raw(self, key: str) -> dict[str, Any] | None:
        """Get cached value by raw key."""
        data = self.client.get(key)
        if data:
            return json.loads(data)  # type: ignore[no-any-return]
        return None

    def set(
        self,
        task_uuid: str,
        output: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache task output with TTL."""
        self.client.set(
            self._task_key(task_uuid),
            json.dumps(output),
            ex=ttl or self.default_ttl,
        )

    def set_raw(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache value by raw key with TTL."""
        self.client.set(
            key,
            json.dumps(value),
            ex=ttl or self.default_ttl,
        )

    def delete(self, task_uuid: str) -> None:
        """Remove task from cache."""
        self.client.delete(self._task_key(task_uuid))

    def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False


# Singleton cache instance
cache = RedisCache(
    url=settings.redis_url,
    default_ttl=settings.cache_ttl_seconds,
)
