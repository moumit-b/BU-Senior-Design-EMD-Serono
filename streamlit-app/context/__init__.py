"""
Context Management Package

Persistent context layer implementing the "Session-as-Database" pattern
from MIT Recursive Language Models research to solve context rot.

Components:
- database: SQLite connection manager
- db_models: SQLAlchemy data models
- session_db: Persistent session manager (replaces in-memory)
- vector_store: ChromaDB for semantic search
- memory_retriever: Query interface for agents to access session history
"""

from .database import DatabaseManager
from .session_db import PersistentSessionManager
from .vector_store import VectorStore
from .memory_retriever import MemoryRetriever

__all__ = [
    "DatabaseManager",
    "PersistentSessionManager",
    "VectorStore",
    "MemoryRetriever",
]
