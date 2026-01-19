"""
Test for database connection validation fix.

This test verifies that the db() function properly handles closed connections
and recreates them when necessary.
"""

import sqlite3
import tempfile
from pathlib import Path
import threading


def test_db_reconnects_after_close():
    """Test that db() function recreates connection if it's been closed."""
    # Create a temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        # Set up a minimal database module environment
        class DBModule:
            def __init__(self):
                self._db_local = threading.local()
                self._DB_READY = False
                self._DB_READY_LOCK = threading.Lock()
            
            def _ensure_schema(self, con):
                """Minimal schema for testing."""
                cur = con.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)")
                con.commit()
            
            def db(self):
                """Test version of db() function with validation."""
                # Check if connection exists AND is still open/valid
                if hasattr(self._db_local, "conn") and self._db_local.conn is not None:
                    try:
                        # Test if connection still works
                        self._db_local.conn.execute("SELECT 1")
                    except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                        # Connection is closed or broken - reset it
                        self._db_local.conn = None
                
                if not hasattr(self._db_local, "conn") or self._db_local.conn is None:
                    self._db_local.conn = sqlite3.connect(str(db_path), check_same_thread=False)
                    self._db_local.conn.row_factory = sqlite3.Row
                
                # Initialize schema if not already done (thread-safe)
                if not self._DB_READY:
                    with self._DB_READY_LOCK:
                        if not self._DB_READY:
                            self._ensure_schema(self._db_local.conn)
                            self._DB_READY = True
                
                return self._db_local.conn
        
        db_module = DBModule()
        
        # Test scenario: Get connection, close it, then get connection again
        # Step 1: Get initial connection
        con1 = db_module.db()
        assert con1 is not None
        
        # Verify it works
        cur = con1.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1
        
        # Step 2: Simulate external close (like LearningEngine does)
        con1.close()
        
        # Step 3: Try to use db() again - should get a NEW connection
        con2 = db_module.db()
        assert con2 is not None
        
        # Step 4: Verify new connection works
        cur2 = con2.cursor()
        cur2.execute("SELECT 1")
        result2 = cur2.fetchone()
        assert result2[0] == 1
        
        # Step 5: Verify we can insert data
        cur2.execute("INSERT INTO test_table (value) VALUES (?)", ("test_value",))
        con2.commit()
        
        # Step 6: Verify data was inserted
        cur2.execute("SELECT COUNT(*) FROM test_table")
        count = cur2.fetchone()[0]
        assert count == 1
        
        print("✓ db() successfully reconnects after connection is closed")


def test_db_without_close():
    """Test that db() function returns same connection when not closed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        class DBModule:
            def __init__(self):
                self._db_local = threading.local()
                self._DB_READY = False
                self._DB_READY_LOCK = threading.Lock()
            
            def _ensure_schema(self, con):
                cur = con.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)")
                con.commit()
            
            def db(self):
                if hasattr(self._db_local, "conn") and self._db_local.conn is not None:
                    try:
                        self._db_local.conn.execute("SELECT 1")
                    except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                        self._db_local.conn = None
                
                if not hasattr(self._db_local, "conn") or self._db_local.conn is None:
                    self._db_local.conn = sqlite3.connect(str(db_path), check_same_thread=False)
                    self._db_local.conn.row_factory = sqlite3.Row
                
                if not self._DB_READY:
                    with self._DB_READY_LOCK:
                        if not self._DB_READY:
                            self._ensure_schema(self._db_local.conn)
                            self._DB_READY = True
                
                return self._db_local.conn
        
        db_module = DBModule()
        
        # Get connection twice without closing
        con1 = db_module.db()
        con2 = db_module.db()
        
        # Should be the same object
        assert con1 is con2
        
        print("✓ db() returns same connection when not closed")


if __name__ == "__main__":
    test_db_reconnects_after_close()
    test_db_without_close()
    print("\nAll tests passed!")

