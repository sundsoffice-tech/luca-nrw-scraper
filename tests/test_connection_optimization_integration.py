"""
Integration test to verify the SQLite connection optimization.

This test demonstrates that the optimization actually reduces
the number of connection operations in a realistic scenario.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch
import sqlite3

from luca_scraper.database import (
    close_db,
    upsert_lead_sqlite,
    lead_exists_sqlite,
    mark_url_seen_sqlite,
    is_url_seen_sqlite,
    get_lead_count_sqlite,
)


def test_connection_optimization_integration():
    """
    Integration test to verify connection reuse reduces overhead.
    
    This simulates a typical scraping session where multiple
    operations are performed sequentially.
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
        
        CREATE TABLE IF NOT EXISTS urls_seen(
            url TEXT PRIMARY KEY,
            first_run_id INTEGER,
            ts TEXT
        );
    """)
    conn.commit()
    conn.close()
    
    try:
        with patch("luca_scraper.database.DB_PATH", db_path):
            # Clean up any existing connection
            close_db()
            
            # Track sqlite3.connect calls
            original_connect = sqlite3.connect
            connect_count = [0]
            
            def counting_connect(*args, **kwargs):
                connect_count[0] += 1
                return original_connect(*args, **kwargs)
            
            with patch("sqlite3.connect", side_effect=counting_connect):
                # Reset connection
                close_db()
                
                # Simulate a scraping session with 10 operations
                for i in range(10):
                    # Insert a lead
                    lead_data = {
                        "name": f"User {i}",
                        "email": f"user{i}@example.com",
                        "telefon": f"123456789{i}",
                    }
                    lead_id, created = upsert_lead_sqlite(lead_data)
                    
                    # Check if lead exists
                    exists = lead_exists_sqlite(email=f"user{i}@example.com")
                    assert exists is True
                    
                    # Mark URL as seen
                    mark_url_seen_sqlite(f"https://example.com/{i}")
                    
                    # Check if URL is seen
                    is_seen = is_url_seen_sqlite(f"https://example.com/{i}")
                    assert is_seen is True
                
                # Get final count
                count = get_lead_count_sqlite()
                assert count == 10
                
                # The optimization should result in only 1 connection
                # (all operations reuse the same thread-local connection)
                print(f"Number of sqlite3.connect calls: {connect_count[0]}")
                assert connect_count[0] == 1, (
                    f"Expected 1 connection, got {connect_count[0]}. "
                    "Connection reuse optimization may not be working correctly."
                )
                
                # Clean up
                close_db()
    
    finally:
        # Cleanup
        if db_path.exists():
            db_path.unlink()


if __name__ == "__main__":
    test_connection_optimization_integration()
    print("✅ Integration test passed! Connection optimization is working correctly.")
