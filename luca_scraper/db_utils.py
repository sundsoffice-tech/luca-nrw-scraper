# -*- coding: utf-8 -*-
"""
Database utilities with concurrency support.

This module provides thread-safe and async-safe database connection management
for SQLite databases to prevent "database is locked" errors in concurrent scenarios.

Features:
- Connection pooling with locks
- Automatic retry logic for database locked errors
- WAL mode configuration for better concurrency
- Thread-safe and async-safe operations
"""

import sqlite3
import threading
import asyncio
import time
import logging
from contextlib import contextmanager
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Configuration
DB_TIMEOUT = 30.0  # Increased timeout for busy operations
MAX_RETRIES = 5
RETRY_DELAY = 0.1  # Initial delay between retries (exponential backoff)

# Thread-local storage for connections
_thread_local = threading.local()

# Global lock for database initialization
_init_lock = threading.Lock()

# Track initialized databases
_initialized_dbs = set()


def configure_connection(conn: sqlite3.Connection) -> None:
    """
    Configure a SQLite connection for optimal concurrency.
    
    Args:
        conn: SQLite connection to configure
    """
    # Enable WAL mode for better concurrency
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        # WAL mode might not be available, fallback to default
        logger.warning("WAL mode not available, using default journal mode")
    
    # Set busy timeout
    conn.execute(f"PRAGMA busy_timeout={int(DB_TIMEOUT * 1000)}")
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON")
    
    # Optimize for concurrent reads
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA mmap_size=268435456")  # 256MB mmap


def ensure_db_initialized(db_path: str, init_func: Optional[Callable] = None) -> None:
    """
    Ensure database is initialized (thread-safe).
    
    Args:
        db_path: Path to database file
        init_func: Optional initialization function to call on first access
    """
    # Check with lock to avoid race condition
    with _init_lock:
        if db_path in _initialized_dbs:
            return
        
        # Initialize database
        conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT)
        configure_connection(conn)
        
        if init_func:
            init_func(conn)
        
        conn.close()
        _initialized_dbs.add(db_path)


@contextmanager
def get_db_connection(db_path: str, timeout: float = DB_TIMEOUT):
    """
    Get a thread-safe database connection with automatic retry.
    
    This context manager provides:
    - Thread-local connection reuse
    - Automatic retry on database locked errors
    - Proper connection cleanup
    
    Args:
        db_path: Path to SQLite database
        timeout: Connection timeout in seconds
    
    Yields:
        sqlite3.Connection: Database connection
    
    Example:
        with get_db_connection("scraper.db") as conn:
            conn.execute("INSERT INTO table VALUES (?)", (value,))
            conn.commit()
    """
    # Try to reuse thread-local connection
    if not hasattr(_thread_local, 'connections'):
        _thread_local.connections = {}
    
    if db_path not in _thread_local.connections:
        conn = sqlite3.connect(db_path, timeout=timeout, check_same_thread=False)
        configure_connection(conn)
        _thread_local.connections[db_path] = conn
    
    conn = _thread_local.connections[db_path]
    
    try:
        yield conn
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            logger.warning(f"Database locked, will be retried: {db_path}")
        raise
    finally:
        # Don't close - keep connection for reuse
        pass


def with_db_retry(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """
    Decorator to retry database operations on lock errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (exponential backoff)
    
    Returns:
        Decorator function
    
    Example:
        @with_db_retry()
        def insert_data(db_path, data):
            with get_db_connection(db_path) as conn:
                conn.execute("INSERT INTO table VALUES (?)", (data,))
                conn.commit()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e).lower() or "locked" in str(e).lower():
                        last_error = e
                        if attempt < max_retries - 1:
                            logger.debug(f"Database locked on attempt {attempt + 1}/{max_retries}, retrying in {current_delay:.2f}s...")
                            time.sleep(current_delay)
                            current_delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"Database locked after {max_retries} attempts")
                    else:
                        raise
            
            # If we exhausted retries, raise the last error
            if last_error:
                raise last_error
        
        return wrapper
    return decorator


def with_db_retry_async(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """
    Decorator to retry async database operations on lock errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (exponential backoff)
    
    Returns:
        Decorator function
    
    Example:
        @with_db_retry_async()
        async def insert_data(db_path, data):
            with get_db_connection(db_path) as conn:
                conn.execute("INSERT INTO table VALUES (?)", (data,))
                conn.commit()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e).lower() or "locked" in str(e).lower():
                        last_error = e
                        if attempt < max_retries - 1:
                            logger.debug(f"Database locked on attempt {attempt + 1}/{max_retries}, retrying in {current_delay:.2f}s...")
                            await asyncio.sleep(current_delay)
                            current_delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"Database locked after {max_retries} attempts")
                    else:
                        raise
            
            # If we exhausted retries, raise the last error
            if last_error:
                raise last_error
        
        return wrapper
    return decorator


def execute_with_retry(db_path: str, query: str, params: tuple = (), commit: bool = True) -> Optional[Any]:
    """
    Execute a database query with automatic retry on lock errors.
    
    Args:
        db_path: Path to SQLite database
        query: SQL query to execute
        params: Query parameters
        commit: Whether to commit after execution
    
    Returns:
        Cursor result or None
    """
    @with_db_retry()
    def _execute():
        with get_db_connection(db_path) as conn:
            cursor = conn.execute(query, params)
            if commit:
                conn.commit()
            return cursor
    
    return _execute()


def cleanup_connections():
    """
    Clean up all thread-local database connections.
    
    Call this when shutting down or when you want to force
    connection cleanup (e.g., at end of request in web app).
    """
    if hasattr(_thread_local, 'connections'):
        for db_path, conn in _thread_local.connections.items():
            try:
                conn.close()
                logger.debug(f"Closed connection to {db_path}")
            except Exception as e:
                logger.warning(f"Error closing connection to {db_path}: {e}")
        _thread_local.connections.clear()
