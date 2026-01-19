"""
Integration test for database connection validation fix with actual module.

This test verifies that the luca_scraper.database.db() function properly
handles closed connections when used with LearningEngine.
"""

import tempfile
from pathlib import Path
import sys
import os
import sqlite3

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_db_reconnection_simple():
    """Simple test to verify the db() function handles closed connections."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temporary database
        db_path = Path(tmpdir) / "test_luca.db"
        
        # Import only the database module directly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "database",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "luca_scraper", "database.py")
        )
        database = importlib.util.module_from_spec(spec)
        
        # Override the database path before loading
        database.DB_PATH = db_path
        database._DB_READY = False
        
        # Now load the module
        spec.loader.exec_module(database)
        
        # Step 1: Get initial connection
        con1 = database.db()
        print(f"✓ Got initial connection: {con1}")
        
        # Verify it works
        cur1 = con1.cursor()
        cur1.execute("SELECT 1")
        result = cur1.fetchone()
        assert result[0] == 1
        print("✓ Initial connection works")
        
        # Step 2: Close the connection (simulating what LearningEngine does)
        con1.close()
        print("✓ Closed connection")
        
        # Step 3: Try to get connection again - should recreate it
        con2 = database.db()
        print(f"✓ Got new connection after close: {con2}")
        
        # Step 4: Verify the new connection works
        cur2 = con2.cursor()
        cur2.execute("SELECT 1")
        result2 = cur2.fetchone()
        assert result2[0] == 1
        print("✓ New connection works after close")
        
        # Step 5: Verify we can insert data
        cur2.execute("""
            INSERT INTO leads (name, email, telefon, quelle, score) 
            VALUES (?, ?, ?, ?, ?)
        """, ("Test Lead", "test@example.com", "+49123456789", "test", 5))
        con2.commit()
        print("✓ Successfully inserted test lead")
        
        # Step 6: Verify data was inserted
        cur2.execute("SELECT COUNT(*) FROM leads")
        count = cur2.fetchone()[0]
        assert count == 1
        print(f"✓ Verified lead count: {count}")
        
        print("\n✅ All integration tests passed!")
        print("✅ db() correctly handles closed connections")


if __name__ == "__main__":
    test_db_reconnection_simple()

