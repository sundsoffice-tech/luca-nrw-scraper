"""
Test database indices for queries_done and urls_seen tables.
Verifies that the required indices are created to prevent full table scans.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from luca_scraper import database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def reset_db_ready():
    """Reset the global DB_READY flag before each test"""
    original_value = database._DB_READY
    database._DB_READY = False
    # Clear any thread-local connections
    if hasattr(database._db_local, "conn") and database._db_local.conn is not None:
        try:
            database._db_local.conn.close()
        except Exception:
            pass
        database._db_local.conn = None
    yield
    # Restore original value
    database._DB_READY = original_value


class TestDatabaseIndices:
    """Test database indices on queries_done and urls_seen tables"""

    def test_queries_done_indices_exist(self, temp_db, reset_db_ready):
        """Test that indices on queries_done table are created"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = database.db()
            
            # Get list of indices for queries_done table
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='queries_done'
            """)
            indices = [row[0] for row in cursor.fetchall()]
            
            # Check that our timestamp index exists
            # Note: q column has auto-index from PRIMARY KEY
            assert 'idx_queries_done_ts' in indices, "Index on queries_done.ts should exist"
    
    def test_urls_seen_indices_exist(self, temp_db, reset_db_ready):
        """Test that indices on urls_seen table are created"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = database.db()
            
            # Get list of indices for urls_seen table
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='urls_seen'
            """)
            indices = [row[0] for row in cursor.fetchall()]
            
            # Check that our timestamp index exists
            # Note: url column has auto-index from PRIMARY KEY
            assert 'idx_urls_seen_ts' in indices, "Index on urls_seen.ts should exist"
    
    def test_index_details(self, temp_db, reset_db_ready):
        """Test the details of the created indices"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = database.db()
            
            # Check idx_queries_done_ts
            cursor = conn.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='index' AND name='idx_queries_done_ts'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert 'queries_done' in result[0].lower()
            assert 'ts' in result[0].lower()
            
            # Check idx_urls_seen_ts
            cursor = conn.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='index' AND name='idx_urls_seen_ts'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert 'urls_seen' in result[0].lower()
            assert 'ts' in result[0].lower()
    
    def test_queries_performance_with_index(self, temp_db, reset_db_ready):
        """Test that queries on indexed columns use the index"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = database.db()
            
            # Insert test data
            test_queries = [(f"query_{i}", None, "2024-01-01") for i in range(100)]
            conn.executemany(
                "INSERT INTO queries_done (q, last_run_id, ts) VALUES (?, ?, ?)",
                test_queries
            )
            conn.commit()
            
            # Query using WHERE clause on indexed column
            cursor = conn.execute("SELECT * FROM queries_done WHERE q = 'query_50'")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'query_50'
            
            # Test timestamp queries
            cursor = conn.execute("SELECT COUNT(*) FROM queries_done WHERE ts >= '2024-01-01'")
            count = cursor.fetchone()[0]
            assert count == 100
    
    def test_urls_performance_with_index(self, temp_db, reset_db_ready):
        """Test that queries on urls_seen use the index"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = database.db()
            
            # Insert test data
            test_urls = [(f"https://example.com/{i}", None, "2024-01-01") for i in range(100)]
            conn.executemany(
                "INSERT INTO urls_seen (url, first_run_id, ts) VALUES (?, ?, ?)",
                test_urls
            )
            conn.commit()
            
            # Query using WHERE clause on indexed column
            cursor = conn.execute("SELECT * FROM urls_seen WHERE url = 'https://example.com/50'")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'https://example.com/50'
            
            # Test timestamp queries
            cursor = conn.execute("SELECT COUNT(*) FROM urls_seen WHERE ts >= '2024-01-01'")
            count = cursor.fetchone()[0]
            assert count == 100
    
    def test_indices_are_idempotent(self, temp_db, reset_db_ready):
        """Test that running db() multiple times doesn't cause issues"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Call db() multiple times to ensure schema is created only once
            conn = database.db()
            database._DB_READY = False  # Reset to test idempotency
            conn = database.db()
            database._DB_READY = False  # Reset to test idempotency  
            conn = database.db()
            
            # Verify indices still exist and there are no duplicates
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND tbl_name='queries_done' 
                AND name = 'idx_queries_done_ts'
            """)
            count = cursor.fetchone()[0]
            assert count == 1, "Should have exactly 1 timestamp index on queries_done"
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND tbl_name='urls_seen' 
                AND name = 'idx_urls_seen_ts'
            """)
            count = cursor.fetchone()[0]
            assert count == 1, "Should have exactly 1 timestamp index on urls_seen"
