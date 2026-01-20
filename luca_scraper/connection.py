"""
LUCA NRW Scraper - Database Connection Management
==================================================
SQLite Connection Handling, Context Managers und Thread-Sicherheit.

This module provides:
- Thread-safe database connection management
- Context managers for transactions
- Connection validation and reconnection logic
"""

import logging
import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager

# Import DB_PATH and DATABASE_BACKEND from config
from .config import DB_PATH as _DB_PATH_STR, DATABASE_BACKEND

# Convert to Path object
DB_PATH = Path(_DB_PATH_STR)

# Thread-local storage for database connections
_db_local = threading.local()

# Global flag for schema initialization with thread lock
_DB_READY = False
_DB_READY_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


def db() -> sqlite3.Connection:
    """
    Thread-safe database connection.
    
    Returns a connection with row factory set.
    Ensures schema is initialized on first access.
    Validates that cached connection is still open before returning it.
    
    Note: When DATABASE_BACKEND is 'django', this function raises NotImplementedError.
    Use Django ORM directly instead.
    """
    if DATABASE_BACKEND == 'django':
        raise NotImplementedError(
            "db() function is not available when using Django ORM backend. "
            "Use Django ORM directly via the Lead model."
        )
    
    global _DB_READY
    
    # Check if connection exists AND is still open/valid
    if hasattr(_db_local, "conn") and _db_local.conn is not None:
        try:
            # Test if connection is still open/valid by executing a simple query
            _db_local.conn.execute("SELECT 1")
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            # Connection is closed or broken - reset it
            _db_local.conn = None
    
    if not hasattr(_db_local, "conn") or _db_local.conn is None:
        _db_local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _db_local.conn.row_factory = sqlite3.Row
    
    # Initialize schema if not already done (thread-safe)
    if not _DB_READY:
        with _DB_READY_LOCK:
            # Double-check pattern to avoid multiple initializations
            if not _DB_READY:
                from .schema import _ensure_schema
                _ensure_schema(_db_local.conn)
                
                # Dashboard schema initialization removed - migrated to Django CRM
                # See docs/FLASK_TO_DJANGO_MIGRATION.md for migration details
                
                _DB_READY = True
    
    return _db_local.conn


def init_db():
    """
    Explicit database initializer.
    
    Opens connection, ensures schema exists, then closes.
    Kept for backward compatibility.
    """
    con = db()
    con.close()
    # Reset the thread-local connection
    if hasattr(_db_local, "conn"):
        _db_local.conn = None


@contextmanager
def transaction():
    """
    Context manager for database transactions.
    
    Usage:
        with transaction() as conn:
            conn.execute("INSERT INTO ...")
    
    Commits on success, rolls back on exception.
    """
    conn = db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


__all__ = [
    'DB_PATH',
    'db',
    'init_db',
    'transaction',
]
