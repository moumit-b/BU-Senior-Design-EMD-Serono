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

# Maintain direct access to DatabaseManager as it's lightweight
from .database import DatabaseManager

# Use lazy loading for heavy components (VectorStore, PersistentSessionManager)
# by only importing them when needed.

def get_persistent_session_manager():
    from .session_db import PersistentSessionManager
    return PersistentSessionManager

def get_vector_store():
    from .vector_store import VectorStore
    return VectorStore

def get_memory_retriever():
    from .memory_retriever import MemoryRetriever
    return MemoryRetriever

# Note: Directly importing these from other modules will still work, 
# but they are no longer exported at the package level to prevent 
# accidental global loading.

__all__ = [
    "DatabaseManager",
    "get_persistent_session_manager",
    "get_vector_store",
    "get_memory_retriever",
]
