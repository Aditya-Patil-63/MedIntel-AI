"""
MedIntel AI — Database Session Management.

Provides the SQLAlchemy engine, session factory, and base class
for all ORM models. Supports SQLite and PostgreSQL (Neon).
"""

import logging
import time
from typing import Any, Dict
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger("medintel.database")


def normalize_database_url(url: str) -> str:
    """Normalize database connection string for SQLAlchemy compatibility.

    Converts 'postgres://' or 'postgresql://' to 'postgresql+psycopg2://'
    while keeping query parameters (e.g. sslmode) intact.
    """
    if not url:
        return "sqlite:///./medintel.db"
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


# Resolve normalized connection URL and dialect configuration
normalized_db_url = normalize_database_url(settings.DATABASE_URL)
is_sqlite = normalized_db_url.startswith("sqlite")
is_production = getattr(settings, "APP_ENV", "development") == "production"

engine_kwargs: Dict[str, Any] = {
    "echo": settings.DEBUG and not is_production,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production / Neon PostgreSQL connection pooling parameters
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 3,
        "max_overflow": 2,
    })

engine = create_engine(normalized_db_url, **engine_kwargs)


# Guard SQLite PRAGMA hook so it executes ONLY on SQLite connections
@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    """Set SQLite pragmas for better concurrency and referential integrity."""
    cls_module = getattr(dbapi_connection.__class__, "__module__", "").lower()
    if "sqlite" in cls_module:
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()
        except Exception:
            pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


_tables_initialized = False


def create_tables(max_retries: int = 5, retry_delay: float = 1.5) -> bool:
    """Create all database tables defined by ORM models with resilient retries.

    If database connection temporarily fails (e.g. Neon serverless compute waking up),
    retries up to max_retries before logging a warning and allowing startup to continue.
    """
    global _tables_initialized
    if _tables_initialized:
        return True

    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            _tables_initialized = True
            logger.info("Database tables initialized successfully.")
            return True
        except Exception as e:
            logger.warning(
                "Database table creation attempt %d/%d failed: %s",
                attempt, max_retries, type(e).__name__
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.warning(
        "Could not initialize database tables after %d attempts. "
        "Application startup continuing; table creation will retry lazily on demand.",
        max_retries,
    )
    return False


def ensure_tables_exist() -> None:
    """Lazy check to ensure tables exist before database queries."""
    global _tables_initialized
    if not _tables_initialized:
        create_tables(max_retries=2, retry_delay=1.0)


def get_db():  # type: ignore[no-untyped-def]
    """Dependency that provides a database session.

    Yields:
        Session: A SQLAlchemy database session that is automatically
                 closed after the request completes.
    """
    ensure_tables_exist()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
