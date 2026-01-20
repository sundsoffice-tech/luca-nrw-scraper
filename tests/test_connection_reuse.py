"""
Test SQLite connection reuse optimization.

This test verifies that SQLite connections are properly reused
across multiple function calls, eliminating unnecessary overhead.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sqlite3

from luca_scraper.database import (
    db,
    close_db,
    upsert_lead_sqlite,
    lead_exists_sqlite,
    is_url_seen_sqlite,
    mark_url_seen_sqlite,
    is_query_done_sqlite,
    mark_query_done_sqlite,
    start_scraper_run_sqlite,
    finish_scraper_run_sqlite,
    get_lead_count_sqlite,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
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
        
        CREATE TABLE IF NOT EXISTS runs(
            id INTEGER PRIMARY KEY,
            started_at TEXT,
            finished_at TEXT,
            status TEXT,
            links_checked INTEGER,
            leads_new INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS queries_done(
            q TEXT PRIMARY KEY,
            last_run_id INTEGER,
            ts TEXT
        );
        
        CREATE TABLE IF NOT EXISTS urls_seen(
            url TEXT PRIMARY KEY,
            first_run_id INTEGER,
            ts TEXT
        );
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


class TestConnectionReuse:
    """Test that database connections are properly reused"""
    
    def test_db_connection_is_cached(self, temp_db):
        """Test that db() returns the same connection object"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Reset any existing connection
            close_db()
            
            # Get connection twice
            conn1 = db()
            conn2 = db()
            
            # Should return the exact same object
            assert conn1 is conn2
            
            # Cleanup
            close_db()
    
    def test_upsert_lead_reuses_connection(self, temp_db):
        """Test that upsert_lead_sqlite reuses the connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Get initial connection
            conn_before = db()
            
            # Call upsert_lead_sqlite
            lead_data = {
                "name": "Test User",
                "email": "test@example.com",
                "telefon": "123456789",
            }
            lead_id, created = upsert_lead_sqlite(lead_data)
            
            # Get connection after
            conn_after = db()
            
            # Should be the same connection object
            assert conn_before is conn_after
            assert created is True
            
            # Verify connection is still usable
            cursor = conn_after.execute("SELECT COUNT(*) FROM leads")
            count = cursor.fetchone()[0]
            assert count == 1
            
            # Cleanup
            close_db()
    
    def test_lead_exists_reuses_connection(self, temp_db):
        """Test that lead_exists_sqlite reuses the connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Insert a test lead
            lead_data = {
                "name": "Test User",
                "email": "test@example.com",
            }
            upsert_lead_sqlite(lead_data)
            
            # Get connection
            conn_before = db()
            
            # Call lead_exists_sqlite
            exists = lead_exists_sqlite(email="test@example.com")
            
            # Get connection after
            conn_after = db()
            
            # Should be the same connection
            assert conn_before is conn_after
            assert exists is True
            
            # Cleanup
            close_db()
    
    def test_url_tracking_reuses_connection(self, temp_db):
        """Test that URL tracking functions reuse the connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Get initial connection
            conn_before = db()
            
            # Mark URL as seen
            mark_url_seen_sqlite("https://example.com/1")
            
            # Get connection after mark
            conn_after_mark = db()
            assert conn_before is conn_after_mark
            
            # Check if URL is seen
            is_seen = is_url_seen_sqlite("https://example.com/1")
            
            # Get connection after check
            conn_after_check = db()
            assert conn_before is conn_after_check
            assert is_seen is True
            
            # Cleanup
            close_db()
    
    def test_query_tracking_reuses_connection(self, temp_db):
        """Test that query tracking functions reuse the connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Get initial connection
            conn_before = db()
            
            # Mark query as done
            mark_query_done_sqlite("test query")
            
            # Get connection after mark
            conn_after_mark = db()
            assert conn_before is conn_after_mark
            
            # Check if query is done
            is_done = is_query_done_sqlite("test query")
            
            # Get connection after check
            conn_after_check = db()
            assert conn_before is conn_after_check
            assert is_done is True
            
            # Cleanup
            close_db()
    
    def test_scraper_run_tracking_reuses_connection(self, temp_db):
        """Test that scraper run tracking functions reuse the connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Get initial connection
            conn_before = db()
            
            # Start scraper run
            run_id = start_scraper_run_sqlite()
            
            # Get connection after start
            conn_after_start = db()
            assert conn_before is conn_after_start
            
            # Finish scraper run
            finish_scraper_run_sqlite(run_id, links_checked=10, leads_new=5)
            
            # Get connection after finish
            conn_after_finish = db()
            assert conn_before is conn_after_finish
            
            # Cleanup
            close_db()
    
    def test_get_lead_count_reuses_connection(self, temp_db):
        """Test that get_lead_count_sqlite reuses the connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Insert test leads
            upsert_lead_sqlite({"name": "User 1", "email": "user1@example.com"})
            upsert_lead_sqlite({"name": "User 2", "email": "user2@example.com"})
            
            # Get connection
            conn_before = db()
            
            # Get lead count
            count = get_lead_count_sqlite()
            
            # Get connection after
            conn_after = db()
            
            # Should be the same connection
            assert conn_before is conn_after
            assert count == 2
            
            # Cleanup
            close_db()
    
    def test_multiple_operations_reuse_single_connection(self, temp_db):
        """Test that multiple operations in sequence reuse the same connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Get initial connection
            conn_initial = db()
            
            # Perform multiple operations
            run_id = start_scraper_run_sqlite()
            mark_url_seen_sqlite("https://example.com/1", run_id)
            mark_query_done_sqlite("test query", run_id)
            upsert_lead_sqlite({"name": "Test", "email": "test@example.com"})
            exists = lead_exists_sqlite(email="test@example.com")
            count = get_lead_count_sqlite()
            finish_scraper_run_sqlite(run_id, links_checked=1, leads_new=1)
            
            # Get final connection
            conn_final = db()
            
            # All operations should have used the same connection
            assert conn_initial is conn_final
            assert exists is True
            assert count == 1
            
            # Cleanup
            close_db()
    
    def test_close_db_cleans_up_connection(self, temp_db):
        """Test that close_db properly closes and clears the connection"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Get a connection
            conn1 = db()
            assert conn1 is not None
            
            # Close it
            close_db()
            
            # Get another connection - should be a new one
            conn2 = db()
            assert conn2 is not None
            # After closing, db() creates a new connection
            # We can't directly compare objects, but we can verify it's functional
            
            # Verify the new connection works
            cursor = conn2.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            # Cleanup
            close_db()
    
    def test_close_db_is_safe_when_no_connection(self):
        """Test that close_db doesn't error when there's no connection"""
        # This should not raise an error
        close_db()
        close_db()  # Multiple calls should be safe


class TestConnectionPerformance:
    """Test the performance benefits of connection reuse"""
    
    def test_no_unnecessary_reconnects(self, temp_db):
        """Test that we don't reconnect unnecessarily"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            close_db()
            
            # Mock sqlite3.connect to count calls
            original_connect = sqlite3.connect
            connect_count = [0]
            
            def counting_connect(*args, **kwargs):
                connect_count[0] += 1
                return original_connect(*args, **kwargs)
            
            with patch("sqlite3.connect", side_effect=counting_connect):
                # Reset connection state
                close_db()
                
                # Perform multiple operations
                upsert_lead_sqlite({"name": "User 1", "email": "user1@example.com"})
                upsert_lead_sqlite({"name": "User 2", "email": "user2@example.com"})
                lead_exists_sqlite(email="user1@example.com")
                get_lead_count_sqlite()
                
                # Should have connected only once (for the first db() call)
                assert connect_count[0] == 1
            
            # Cleanup
            close_db()
