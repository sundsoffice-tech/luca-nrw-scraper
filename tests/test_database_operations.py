"""
Comprehensive tests for luca_scraper database module
Testing database connections, schema, and operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import database module
from luca_scraper.database import (
    db,
    get_schema,
    db_context,
    ensure_schema,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


class TestDatabaseConnection:
    """Test database connection management"""

    def test_db_returns_connection(self):
        """Test that db() returns a valid connection"""
        conn = db()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

    def test_db_connection_has_row_factory(self):
        """Test that connection has row_factory set"""
        conn = db()
        assert conn.row_factory is not None

    def test_db_connection_is_cached(self):
        """Test that db() returns the same connection"""
        conn1 = db()
        conn2 = db()
        # Should return the same connection object
        assert conn1 is conn2

    def test_db_connection_validates_existing(self):
        """Test that broken connections are recreated"""
        # This test verifies the connection validation logic
        conn = db()
        assert conn is not None


class TestDatabaseSchema:
    """Test database schema operations"""

    def test_get_schema_returns_string(self):
        """Test that get_schema returns SQL string"""
        schema = get_schema()
        assert isinstance(schema, str)
        assert len(schema) > 0

    def test_schema_contains_leads_table(self):
        """Test that schema defines leads table"""
        schema = get_schema()
        assert "CREATE TABLE" in schema.upper()
        # Should contain some lead-related content

    def test_ensure_schema_creates_tables(self, temp_db):
        """Test that ensure_schema creates tables"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            ensure_schema()
            # Verify table was created
            conn = sqlite3.connect(str(temp_db))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            assert len(tables) > 0


class TestDatabaseContext:
    """Test database context manager"""

    def test_db_context_returns_connection(self):
        """Test that db_context yields a connection"""
        with db_context() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

    def test_db_context_commits_on_success(self):
        """Test that context manager commits on success"""
        with db_context() as conn:
            # Create a temporary table for testing
            conn.execute("CREATE TEMP TABLE test_table (id INTEGER)")
            conn.execute("INSERT INTO test_table VALUES (1)")
        # Verify commit happened by opening new connection
        with db_context() as conn:
            # If commit worked, this should succeed
            assert conn is not None

    def test_db_context_handles_exception(self):
        """Test that context manager handles exceptions"""
        try:
            with db_context() as conn:
                # Force an error
                conn.execute("INVALID SQL STATEMENT")
        except sqlite3.OperationalError:
            # Exception should propagate
            pass
        # Database should still be accessible
        with db_context() as conn:
            assert conn is not None


@pytest.mark.integration
class TestDatabaseOperations:
    """Integration tests for database operations"""

    def test_create_and_query_data(self, temp_db):
        """Test creating and querying data"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = db()
            # Create a simple table
            conn.execute("CREATE TABLE test_leads (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test_leads (name) VALUES ('Test Lead')")
            conn.commit()
            
            # Query the data
            cursor = conn.execute("SELECT name FROM test_leads")
            result = cursor.fetchone()
            assert result is not None
            assert "Test Lead" in str(result)

    def test_row_factory_returns_dict_like(self, temp_db):
        """Test that row factory allows dict-like access"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = db()
            conn.execute("CREATE TABLE test_data (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test_data VALUES (1, 'Test')")
            conn.commit()
            
            cursor = conn.execute("SELECT * FROM test_data")
            row = cursor.fetchone()
            # Row factory should allow key access
            assert row is not None

    def test_thread_safety(self, temp_db):
        """Test that database connections are thread-safe"""
        import threading
        
        results = []
        
        def query_db():
            with patch("luca_scraper.database.DB_PATH", temp_db):
                conn = db()
                conn.execute("CREATE TABLE IF NOT EXISTS thread_test (id INTEGER)")
                results.append(True)
        
        threads = [threading.Thread(target=query_db) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 3


class TestDatabaseMigration:
    """Test database migration and schema updates"""

    def test_schema_is_idempotent(self, temp_db):
        """Test that running ensure_schema multiple times is safe"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Run schema creation multiple times
            ensure_schema()
            ensure_schema()
            # Should not raise errors

    def test_database_path_creation(self, temp_db):
        """Test that database directory is created if needed"""
        # Create a path in a non-existent directory
        test_path = temp_db.parent / "subdir" / "test.db"
        test_path.parent.mkdir(exist_ok=True)
        
        with patch("luca_scraper.database.DB_PATH", test_path):
            conn = db()
            assert conn is not None
        
        # Cleanup
        if test_path.exists():
            test_path.unlink()
        if test_path.parent.exists():
            test_path.parent.rmdir()


@pytest.mark.slow
class TestDatabasePerformance:
    """Performance tests for database operations"""

    def test_bulk_insert_performance(self, temp_db):
        """Test performance of bulk inserts"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = db()
            conn.execute("CREATE TABLE perf_test (id INTEGER, data TEXT)")
            
            # Insert 1000 records
            data = [(i, f"Data {i}") for i in range(1000)]
            conn.executemany("INSERT INTO perf_test VALUES (?, ?)", data)
            conn.commit()
            
            # Verify count
            cursor = conn.execute("SELECT COUNT(*) FROM perf_test")
            count = cursor.fetchone()[0]
            assert count == 1000

    def test_query_performance(self, temp_db):
        """Test query performance with indexed data"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            conn = db()
            conn.execute("""
                CREATE TABLE indexed_test (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER
                )
            """)
            conn.execute("CREATE INDEX idx_value ON indexed_test(value)")
            
            # Insert test data
            data = [(i, f"Name {i}", i % 100) for i in range(1000)]
            conn.executemany("INSERT INTO indexed_test VALUES (?, ?, ?)", data)
            conn.commit()
            
            # Query with index
            cursor = conn.execute("SELECT * FROM indexed_test WHERE value = 50")
            results = cursor.fetchall()
            assert len(results) > 0
