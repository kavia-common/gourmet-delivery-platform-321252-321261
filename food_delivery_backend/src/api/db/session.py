from collections.abc import Generator
import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.settings import get_settings

# Lazily initialized engine and sessionmaker.
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def _build_engine() -> Engine:
    """
    Create a SQLAlchemy Engine.

    Behavior:
    - Prefer PostgreSQL using environment/Settings.
    - If database configuration is missing or invalid, gracefully fall back to a local SQLite file DB
      so the service can still boot and expose health/docs routes. This ensures port readiness even
      when the database container/env is not yet wired.
    """
    settings = get_settings()
    try:
        db_url = settings.build_database_url()
        # PostgreSQL path (or any SQLAlchemy URL from env)
        return create_engine(db_url, pool_pre_ping=True)
    except Exception as e:
        # Fallback: local SQLite database to keep the app bootable.
        # This is safe for demo/preview; real deployments should provide PostgreSQL env.
        fallback_url = os.getenv("FALLBACK_SQLITE_URL", "sqlite:///./app.db")
        # Note: For SQLite we need check_same_thread=False for usage across threads in ASGI.
        is_sqlite = fallback_url.startswith("sqlite://")
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        print(f"[db.session] Warning: PostgreSQL configuration missing or invalid ({e}). "
              f"Falling back to SQLite at {fallback_url}.")
        return create_engine(fallback_url, connect_args=connect_args, pool_pre_ping=True)


def _ensure_engine_and_sessionmaker() -> None:
    """Ensure module-level Engine and SessionLocal exist (lazy init)."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _build_engine()
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session and ensures cleanup."""
    _ensure_engine_and_sessionmaker()
    assert _SessionLocal is not None  # for type checkers
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Return the SQLAlchemy engine (used by startup migrations/metadata create)."""
    _ensure_engine_and_sessionmaker()
    assert _engine is not None
    return _engine
