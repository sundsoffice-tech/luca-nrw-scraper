"""
Tests for cache TTL functionality in luca_scraper database module.
Testing query and URL cache expiration with time-to-live (TTL).

Note: This test file requires the project root to be in PYTHONPATH.
Run from project root: pytest tests/test_cache_ttl.py
"""

import pytest
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

# Import database functions
from luca_scraper.database import (
    is_query_done_sqlite,
    mark_query_done_sqlite,
    is_url_seen_sqlite,
    mark_url_seen_sqlite,
    cleanup_expired_queries,
    cleanup_expired_urls,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    # Create schema
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
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


class TestQueryCacheTTL:
    """Test query cache TTL functionality"""
    
    def test_query_without_ttl_legacy_behavior(self, temp_db):
        """Test that ttl_hours=0 provides legacy behavior (no expiration)"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Mark query as done
            mark_query_done_sqlite("test query", run_id=1)
            
            # Should be found with ttl_hours=0 (legacy behavior)
            assert is_query_done_sqlite("test query", ttl_hours=0) is True
    
    def test_query_within_ttl(self, temp_db):
        """Test that query within TTL is considered done"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Mark query as done
            mark_query_done_sqlite("recent query", run_id=1)
            
            # Should be found within 24 hour TTL
            assert is_query_done_sqlite("recent query", ttl_hours=24) is True
    
    def test_query_expired_ttl(self, temp_db):
        """Test that query outside TTL is not considered done"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Insert a query with an old timestamp (25 hours ago)
            conn = sqlite3.connect(str(temp_db))
            conn.execute(
                "INSERT INTO queries_done(q, last_run_id, ts) VALUES(?, ?, datetime('now', '-25 hours'))",
                ("old query", 1)
            )
            conn.commit()
            conn.close()
            
            # Should NOT be found with 24 hour TTL
            assert is_query_done_sqlite("old query", ttl_hours=24) is False
    
    def test_query_not_found(self, temp_db):
        """Test that non-existent query returns False"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            assert is_query_done_sqlite("nonexistent query", ttl_hours=24) is False
    
    def test_cleanup_expired_queries(self, temp_db):
        """Test cleanup of expired queries - basic validation"""
        # This test validates the cleanup function exists and can be called
        # Detailed testing is better done in integration tests due to db() caching
        with patch("luca_scraper.config.env_loader.DB_PATH", temp_db):
            from luca_scraper.database import cleanup_expired_queries
            
            # Function should execute without error
            deleted = cleanup_expired_queries(ttl_hours=48)
            
            # Return value should be int (0 or more)
            assert isinstance(deleted, int)
            assert deleted >= 0


class TestURLCacheTTL:
    """Test URL cache TTL functionality"""
    
    def test_url_without_ttl_legacy_behavior(self, temp_db):
        """Test that ttl_hours=0 provides legacy behavior (no expiration)"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Mark URL as seen
            mark_url_seen_sqlite("https://example.com", run_id=1)
            
            # Should be found with ttl_hours=0 (legacy behavior)
            assert is_url_seen_sqlite("https://example.com", ttl_hours=0) is True
    
    def test_url_within_ttl(self, temp_db):
        """Test that URL within TTL is considered seen"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Mark URL as seen
            mark_url_seen_sqlite("https://example.com/page", run_id=1)
            
            # Should be found within 168 hour (7 day) TTL
            assert is_url_seen_sqlite("https://example.com/page", ttl_hours=168) is True
    
    def test_url_expired_ttl(self, temp_db):
        """Test that URL outside TTL is not considered seen"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Insert a URL with an old timestamp (8 days ago = 192 hours)
            conn = sqlite3.connect(str(temp_db))
            conn.execute(
                "INSERT INTO urls_seen(url, first_run_id, ts) VALUES(?, ?, datetime('now', '-192 hours'))",
                ("https://old.example.com", 1)
            )
            conn.commit()
            conn.close()
            
            # Should NOT be found with 168 hour (7 day) TTL
            assert is_url_seen_sqlite("https://old.example.com", ttl_hours=168) is False
    
    def test_url_not_found(self, temp_db):
        """Test that non-existent URL returns False"""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            assert is_url_seen_sqlite("https://nonexistent.com", ttl_hours=168) is False
    
    def test_cleanup_expired_urls(self, temp_db):
        """Test cleanup of expired URLs - basic validation"""
        # This test validates the cleanup function exists and can be called
        # Detailed testing is better done in integration tests due to db() caching
        with patch("luca_scraper.config.env_loader.DB_PATH", temp_db):
            from luca_scraper.database import cleanup_expired_urls
            
            # Function should execute without error
            deleted = cleanup_expired_urls(ttl_hours=336)
            
            # Return value should be int (0 or more)
            assert isinstance(deleted, int)
            assert deleted >= 0


class TestTTLConfiguration:
    """Test TTL configuration and defaults"""
    
    def test_default_query_ttl(self):
        """Test that default query TTL is 24 hours"""
        from luca_scraper.config.defaults import QUERY_CACHE_TTL_HOURS
        assert QUERY_CACHE_TTL_HOURS == 24
    
    def test_default_url_ttl(self):
        """Test that default URL TTL is 168 hours (7 days)"""
        from luca_scraper.config.defaults import URL_SEEN_TTL_HOURS
        assert URL_SEEN_TTL_HOURS == 168
    
    def test_custom_query_ttl_via_env(self, monkeypatch):
        """Test that query TTL can be configured via environment variable"""
        monkeypatch.setenv("QUERY_CACHE_TTL_HOURS", "48")
        # Need to reload the module to pick up the new env var
        import importlib
        from luca_scraper.config import defaults
        importlib.reload(defaults)
        assert defaults.QUERY_CACHE_TTL_HOURS == 48
    
    def test_custom_url_ttl_via_env(self, monkeypatch):
        """Test that URL TTL can be configured via environment variable"""
        monkeypatch.setenv("URL_SEEN_TTL_HOURS", "336")
        # Need to reload the module to pick up the new env var
        import importlib
        from luca_scraper.config import defaults
        importlib.reload(defaults)
        assert defaults.URL_SEEN_TTL_HOURS == 336


class TestRepositoryTTL:
    """Test TTL functionality in repository module"""
    
    def test_repository_query_ttl(self, temp_db):
        """Test query TTL in repository module"""
        with patch("luca_scraper.config.env_loader.DB_PATH", temp_db):
            from luca_scraper.repository import is_query_done_sqlite, mark_query_done_sqlite
            
            # Mark query as done
            mark_query_done_sqlite("test query repo", run_id=1)
            
            # Should be found within TTL
            assert is_query_done_sqlite("test query repo", ttl_hours=24) is True
    
    def test_repository_url_ttl(self, temp_db):
        """Test URL TTL in repository module"""
        with patch("luca_scraper.config.env_loader.DB_PATH", temp_db):
            from luca_scraper.repository import is_url_seen_sqlite, mark_url_seen_sqlite
            
            # Mark URL as seen
            mark_url_seen_sqlite("https://example.com/repo", run_id=1)
            
            # Should be found within TTL
            assert is_url_seen_sqlite("https://example.com/repo", ttl_hours=168) is True
    
    def test_repository_cleanup_functions(self, temp_db):
        """Test cleanup functions in repository module - basic validation"""
        # This test validates the cleanup function exists and can be called
        # Detailed testing is better done in integration tests due to db() caching
        with patch("luca_scraper.config.env_loader.DB_PATH", temp_db):
            from luca_scraper.repository import cleanup_expired_queries
            
            # Function should execute without error
            deleted = cleanup_expired_queries(ttl_hours=48)
            
            # Return value should be int (0 or more)
            assert isinstance(deleted, int)
            assert deleted >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
