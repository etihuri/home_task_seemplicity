from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from shared.cache import RedisCache, cache
from shared.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cache() -> RedisCache:
    """Return the Redis cache instance."""
    return cache


# Annotated types for dependency injection
DbSession = Annotated[Session, Depends(get_db)]
Cache = Annotated[RedisCache, Depends(get_cache)]
