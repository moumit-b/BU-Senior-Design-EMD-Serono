"""
SQLite Database Manager

Provides connection pooling, session management, and schema initialization
for the persistent context layer.
"""

import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .db_models import Base


class DatabaseManager:
    """
    SQLite database manager for persistent context storage.

    Features:
    - Connection pooling
    - Schema auto-creation
    - Context manager support
    - Thread-safe operations
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._engine: Optional[Engine] = None
        self._session_maker: Optional[sessionmaker] = None
        self._ensure_data_directory()

    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    def _configure_sqlite(self, dbapi_conn, connection_record):
        """Configure SQLite connection for optimal performance."""
        # Enable foreign keys
        dbapi_conn.execute("PRAGMA foreign_keys = ON")
        # Use WAL mode for better concurrency
        dbapi_conn.execute("PRAGMA journal_mode = WAL")
        # Increase cache size (10MB)
        dbapi_conn.execute("PRAGMA cache_size = -10000")
        # Synchronous mode for better performance
        dbapi_conn.execute("PRAGMA synchronous = NORMAL")

    def initialize(self) -> None:
        """
        Initialize database connection and create schema.

        Creates tables if they don't exist.
        """
        if self._engine is not None:
            return

        # Create engine with connection pooling
        self._engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # Use static pool for SQLite
            echo=False,  # Set to True for SQL debugging
        )

        # Configure SQLite for optimal performance
        event.listen(self._engine, "connect", self._configure_sqlite)

        # Create session maker
        self._session_maker = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

        # Create tables
        Base.metadata.create_all(self._engine)

    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session with automatic cleanup.

        Usage:
            with db_manager.get_session() as session:
                session.query(SessionRecord).all()

        Yields:
            SQLAlchemy session
        """
        if self._session_maker is None:
            self.initialize()

        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
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
        """
        Drop all tables and recreate schema.

        WARNING: This deletes all data! Use only for testing.
        """
        if self._engine is not None:
            Base.metadata.drop_all(self._engine)
            Base.metadata.create_all(self._engine)

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._engine is not None

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
