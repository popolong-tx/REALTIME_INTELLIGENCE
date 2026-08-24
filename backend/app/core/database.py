from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLite needs a thread override; production database drivers must not receive
# SQLite-only connection arguments.
engine_options = {"echo": settings.DEBUG}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(settings.DATABASE_URL, **engine_options)


# Enable WAL mode for better concurrency (SQLite specific)
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Simple in-memory cache (replaces Redis for local development)
class SimpleCache:
    """Simple in-memory cache for development."""

    def __init__(self):
        self._cache = {}

    def get(self, key: str):
        """Get value from cache."""
        return self._cache.get(key)

    def set(self, key: str, value, expire: int = None):
        """Set value in cache."""
        self._cache[key] = value

    def delete(self, key: str):
        """Delete value from cache."""
        self._cache.pop(key, None)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._cache

    def clear(self):
        """Clear all cache."""
        self._cache.clear()


# Global cache instance
cache = SimpleCache()


def get_db() -> Generator:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    import app.models.intelligence_monitoring  # noqa: F401
    import app.models.platform_operations  # noqa: F401
    import app.models.training  # noqa: F401
    import app.models.user_config  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def check_cache_connection() -> bool:
    """Check if cache is healthy."""
    try:
        cache.set("health_check", "ok")
        result = cache.get("health_check")
        cache.delete("health_check")
        return result == "ok"
    except Exception:
        return False
