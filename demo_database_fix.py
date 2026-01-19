#!/usr/bin/env python3
"""
Demonstration script to show the fix for "Cannot operate on a closed database" error.

This script shows the connection validation logic that prevents the
"Cannot operate on a closed database" error.
"""

import sqlite3
import tempfile
from pathlib import Path
import threading

print("=" * 70)
print("Demonstration: Database Connection Validation Fix")
print("=" * 70)
print()

# Create a temporary database for this demo
with tempfile.TemporaryDirectory() as tmpdir:
    db_path = Path(tmpdir) / "demo.db"
    print(f"Using temporary database: {db_path}")
    print()
    
    # Simulate the fixed db() function behavior
    class DatabaseModule:
        def __init__(self):
            self._db_local = threading.local()
            self._DB_READY = False
            self._DB_READY_LOCK = threading.Lock()
        
        def _ensure_schema(self, con):
            """Create basic schema."""
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    telefon TEXT,
                    quelle TEXT,
                    score INTEGER
                )
            """)
            con.commit()
        
        def db(self):
            """
            Thread-safe database connection WITH VALIDATION FIX.
            This is the fixed version that checks if connection is still open.
            """
            # Check if connection exists AND is still open/valid
            if hasattr(self._db_local, "conn") and self._db_local.conn is not None:
                try:
                    # Test if connection is still open/valid by executing a simple query
                    self._db_local.conn.execute("SELECT 1")
                except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                    # Connection is closed or broken - reset it
                    self._db_local.conn = None
                    print("    [FIX] Detected closed connection, will recreate")
            
            if not hasattr(self._db_local, "conn") or self._db_local.conn is None:
                self._db_local.conn = sqlite3.connect(str(db_path), check_same_thread=False)
                self._db_local.conn.row_factory = sqlite3.Row
                print("    [INFO] Created new connection")
            
            # Initialize schema if not already done (thread-safe)
            if not self._DB_READY:
                with self._DB_READY_LOCK:
                    if not self._DB_READY:
                        self._ensure_schema(self._db_local.conn)
                        self._DB_READY = True
            
            return self._db_local.conn
    
    db_module = DatabaseModule()
    
    print("Step 1: Get initial connection from db()")
    con1 = db_module.db()
    print(f"  ✓ Got connection: {con1}")
    
    # Verify it works
    cursor = con1.cursor()
    cursor.execute("SELECT 1 as test")
    result = cursor.fetchone()
    print(f"  ✓ Connection works, test query result: {result[0]}")
    
    print()
    print("Step 2: Close the connection (simulating external close like LearningEngine)")
    con1.close()
    print("  ✓ Connection closed")
    
    print()
    print("Step 3: Call db() again - should detect closed connection and recreate")
    print("  (Without the fix, this would return the closed connection and crash)")
    
    con2 = db_module.db()
    print(f"  ✓ Got connection: {con2}")
    
    print()
    print("Step 4: Verify new connection works")
    cursor2 = con2.cursor()
    cursor2.execute("SELECT 1 as test")
    result2 = cursor2.fetchone()
    print(f"  ✓ New connection works! Test query result: {result2[0]}")
    
    print()
    print("Step 5: Insert test data")
    cursor2.execute("""
        INSERT INTO leads (name, email, telefon, quelle, score)
        VALUES (?, ?, ?, ?, ?)
    """, ("Test Lead", "test@example.com", "+49123456789", "demo", 5))
    con2.commit()
    print("  ✓ Successfully inserted test lead")
    
    print()
    print("Step 6: Verify data")
    cursor2.execute("SELECT COUNT(*) FROM leads")
    count = cursor2.fetchone()[0]
    print(f"  ✓ Lead count in database: {count}")
    
    print()
    print("=" * 70)
    print("SUCCESS! The fix correctly handles closed connections")
    print("=" * 70)
    print()
    print("What this fix prevents:")
    print("  • 'sqlite3.ProgrammingError: Cannot operate on a closed database'")
    print("  • Scraper crashes when LearningEngine closes connections")
    print("  • Failed database operations due to stale connections")
    print()
    print("How it works:")
    print("  • db() validates cached connection before returning it")
    print("  • Uses 'SELECT 1' query to test if connection is still open")
    print("  • If connection is closed, creates a new one automatically")
    print("  • Preserves thread-safety and existing behavior")
    print()
    print("Implementation in luca_scraper/database.py:")
    print("  Lines 38-45: Connection validation with try/except")
    print("  Catches: sqlite3.ProgrammingError, sqlite3.OperationalError")

