"""
MedIntel AI — Database Session Management.

Provides the SQLAlchemy engine, session factory, and base class
for all ORM models. Uses SQLite as the initial database.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Create engine — SQLite needs check_same_thread=False for FastAPI
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)


# Enable WAL mode and foreign keys for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    """Set SQLite pragmas for better concurrency and referential integrity."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


def get_db():  # type: ignore[no-untyped-def]
    """Dependency that provides a database session.

    Yields:
        Session: A SQLAlchemy database session that is automatically
                 closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables defined by ORM models.

    This should be called once at application startup or via a
    migration script. In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
