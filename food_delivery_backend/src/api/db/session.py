from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.settings import get_settings

settings = get_settings()

_engine = create_engine(
    settings.build_database_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def get_engine():
    """Return the SQLAlchemy engine (used by startup migrations/metadata create)."""
    return _engine
