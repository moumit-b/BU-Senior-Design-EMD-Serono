"""
Database Manager

Supports both PostgreSQL (Supabase — shared across machines) and SQLite
(local fallback when SUPABASE_DB_URL is not set).

Set SUPABASE_DB_URL in .env to enable cross-machine persistence.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event, Engine, text
from sqlalchemy.orm import sessionmaker, Session

from .db_models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager supporting PostgreSQL (Supabase) and SQLite.

    When SUPABASE_DB_URL is set: uses PostgreSQL for cross-machine access.
    Otherwise: falls back to local SQLite for development.
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        self._db_path = db_path
        self._database_url: Optional[str] = os.getenv("SUPABASE_DB_URL")
        self._using_postgres: bool = bool(self._database_url)
        self._engine: Optional[Engine] = None
        self._session_maker: Optional[sessionmaker] = None

        if not self._using_postgres:
            # Ensure local data directory exists for SQLite fallback
            data_dir = Path(db_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)

    def _configure_sqlite(self, dbapi_conn, connection_record):
        """Configure SQLite connection for optimal performance."""
        dbapi_conn.execute("PRAGMA foreign_keys = ON")
        dbapi_conn.execute("PRAGMA journal_mode = WAL")
        dbapi_conn.execute("PRAGMA cache_size = -10000")
        dbapi_conn.execute("PRAGMA synchronous = NORMAL")

    def initialize(self) -> None:
        """Initialize database connection and create schema."""
        if self._engine is not None:
            return

        if self._using_postgres:
            try:
                self._engine = create_engine(
                    self._database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    pool_size=5,
                    max_overflow=10,
                    echo=False,
                )
                # Enable pgvector extension if available
                try:
                    with self._engine.connect() as conn:
                        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                        conn.commit()
                except Exception:
                    pass  # pgvector may already exist or not be available

                # Verify the connection is actually reachable before proceeding
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

            except Exception as pg_err:
                logger.warning(
                    "Supabase/PostgreSQL unreachable (%s: %s) — falling back to local SQLite.",
                    type(pg_err).__name__,
                    pg_err,
                )
                print(
                    f"[database] WARNING: PostgreSQL unavailable ({type(pg_err).__name__}). "
                    "Using local SQLite fallback."
                )
                self._engine = None
                self._using_postgres = False
                if not Path(self._db_path).parent.exists():
                    Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

        if not self._using_postgres and self._engine is None:
            from sqlalchemy.pool import StaticPool
            self._engine = create_engine(
                f"sqlite:///{self._db_path}",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False,
            )
            event.listen(self._engine, "connect", self._configure_sqlite)

        self._session_maker = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

        Base.metadata.create_all(self._engine)

    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic commit/rollback."""
        if self._session_maker is None:
            self.initialize()

        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_maker = None

    def reset_database(self) -> None:
        """Drop all tables and recreate schema. WARNING: deletes all data."""
        if self._engine is not None:
            Base.metadata.drop_all(self._engine)
            Base.metadata.create_all(self._engine)

    @property
    def is_initialized(self) -> bool:
        return self._engine is not None

    @property
    def backend(self) -> str:
        return "postgresql" if self._using_postgres else "sqlite"

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
