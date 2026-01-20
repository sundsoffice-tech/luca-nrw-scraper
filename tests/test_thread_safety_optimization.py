"""
Test thread safety with the connection optimization.

Verifies that each thread gets its own connection and operations
don't interfere with each other.
"""

import pytest
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch
import sqlite3
import time

from luca_scraper.database import (
    db,
    close_db,
    upsert_lead_sqlite,
    lead_exists_sqlite,
    get_lead_count_sqlite,
)


def test_thread_local_connections():
    """
    Test that each thread gets its own connection.
    
    This ensures the thread-local storage is working correctly
    after removing the close() calls.
    """
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    # Initialize schema
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        PRAGMA journal_mode = WAL;
        
        CREATE TABLE IF NOT EXISTS leads(
            id INTEGER PRIMARY KEY,
            name TEXT,
            rolle TEXT,
            email TEXT,
            telefon TEXT,
            quelle TEXT,
            score INT
        );
    """)
    conn.commit()
    conn.close()
    
    try:
        with patch("luca_scraper.database.DB_PATH", db_path):
            # Track connection objects per thread
            thread_connections = {}
            lock = threading.Lock()
            
            def worker(thread_id):
                """Worker function that operates on database"""
                # Get connection for this thread
                conn = db()
                
                # Store the connection object
                with lock:
                    thread_connections[thread_id] = id(conn)
                
                # Perform some operations
                for i in range(5):
                    lead_data = {
                        "name": f"Thread {thread_id} User {i}",
                        "email": f"thread{thread_id}_user{i}@example.com",
                    }
                    upsert_lead_sqlite(lead_data)
                    time.sleep(0.01)  # Small delay to allow thread interleaving
                
                # Verify connection is the same throughout
                conn_after = db()
                assert id(conn) == id(conn_after), "Connection changed within thread!"
            
            # Create and run multiple threads
            threads = []
            for i in range(3):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            # Wait for all threads to complete
            for t in threads:
                t.join()
            
            # Verify each thread had a different connection
            connection_ids = list(thread_connections.values())
            assert len(set(connection_ids)) == 3, (
                f"Expected 3 different connections, got {len(set(connection_ids))}. "
                "Thread-local storage may not be working correctly."
            )
            
            # Verify all leads were inserted
            count = get_lead_count_sqlite()
            assert count == 15, f"Expected 15 leads, got {count}"
    
    finally:
        # Cleanup
        close_db()
        if db_path.exists():
            db_path.unlink()


def test_concurrent_reads_and_writes():
    """
    Test concurrent reads and writes with connection reuse.
    
    Ensures that the optimization doesn't cause database locks
    or race conditions.
    """
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    # Initialize schema
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        PRAGMA journal_mode = WAL;
        
        CREATE TABLE IF NOT EXISTS leads(
            id INTEGER PRIMARY KEY,
            name TEXT,
            rolle TEXT,
            email TEXT,
            telefon TEXT,
            quelle TEXT,
            score INT
        );
    """)
    conn.commit()
    conn.close()
    
    try:
        with patch("luca_scraper.database.DB_PATH", db_path):
            errors = []
            
            def writer(start_id):
                """Writer thread"""
                try:
                    for i in range(10):
                        lead_data = {
                            "name": f"User {start_id + i}",
                            "email": f"user{start_id + i}@example.com",
                        }
                        upsert_lead_sqlite(lead_data)
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)
            
            def reader():
                """Reader thread"""
                try:
                    for _ in range(10):
                        count = get_lead_count_sqlite()
                        # Count should be between 0 and 30
                        assert 0 <= count <= 30
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple writer and reader threads
            threads = []
            
            # 3 writer threads
            for i in range(3):
                t = threading.Thread(target=writer, args=(i * 10,))
                threads.append(t)
            
            # 2 reader threads
            for _ in range(2):
                t = threading.Thread(target=reader)
                threads.append(t)
            
            # Start all threads
            for t in threads:
                t.start()
            
            # Wait for completion
            for t in threads:
                t.join()
            
            # Check for errors
            if errors:
                raise errors[0]
            
            # Verify final count
            count = get_lead_count_sqlite()
            assert count == 30, f"Expected 30 leads, got {count}"
    
    finally:
        # Cleanup
        close_db()
        if db_path.exists():
            db_path.unlink()


if __name__ == "__main__":
    test_thread_local_connections()
    print("✅ Thread-local connections test passed!")
    
    test_concurrent_reads_and_writes()
    print("✅ Concurrent reads/writes test passed!")
    
    print("\n✅ All thread safety tests passed!")
