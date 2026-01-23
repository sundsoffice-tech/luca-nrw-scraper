"""
Tests for cache module (TTL cache, URL seen set, query cache).
"""

import time
import pytest

from cache import TTLCache, URLSeenSet, QueryCache


class TestTTLCache:
    """Test TTL cache functionality."""
    
    def test_basic_get_set(self):
        """Test basic get/set operations."""
        cache = TTLCache(ttl_seconds=10, max_size=100)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Non-existent key
        assert cache.get("nonexistent") is None
    
    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = TTLCache(ttl_seconds=1, max_size=100)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_size_limit(self):
        """Test that cache evicts oldest when at capacity."""
        cache = TTLCache(ttl_seconds=100, max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # All should exist
        assert cache.size() == 3
        
        # Add one more (should evict oldest)
        cache.set("key4", "value4")
        
        # Should still be 3
        assert cache.size() == 3
        
        # key1 should be evicted
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"
    
    def test_clear_expired(self):
        """Test clearing expired entries."""
        cache = TTLCache(ttl_seconds=1, max_size=100)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        time.sleep(1.1)
        
        cache.set("key3", "value3")  # Fresh entry
        
        cache.clear_expired()
        
        # key1 and key2 should be gone, key3 should remain
        assert cache.size() == 1
        assert cache.get("key3") == "value3"
    
    def test_stats(self):
        """Test cache statistics."""
        cache = TTLCache(ttl_seconds=10, max_size=100)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = cache.stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 10
    
    def test_auto_cleanup(self):
        """Test automatic cleanup of expired entries."""
        # Use a short TTL and very short cleanup interval
        cache = TTLCache(ttl_seconds=1, max_size=100, cleanup_interval=1)
        
        # Add some entries
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.size() == 2
        
        # Wait for entries to expire
        time.sleep(1.1)
        
        # Force a time-based cleanup by waiting for cleanup interval
        time.sleep(0.1)
        
        # Access cache to trigger auto-cleanup
        cache.get("any_key")
        
        # All expired entries should be cleared
        assert cache.size() == 0
    
    def test_cleanup_interval_stats(self):
        """Test that cleanup interval is included in stats."""
        cache = TTLCache(ttl_seconds=10, max_size=100, cleanup_interval=60)
        
        stats = cache.stats()
        
        assert stats["cleanup_interval"] == 60
        assert "seconds_since_cleanup" in stats


class TestURLSeenSet:
    """Test URL seen set functionality."""
    
    def test_add_and_has(self):
        """Test adding and checking URLs."""
        seen = URLSeenSet(ttl_seconds=10)
        
        # First add should return True (newly added)
        assert seen.add("https://example.com/page1") is True
        
        # Second add should return False (already exists)
        assert seen.add("https://example.com/page1") is False
        
        # Check if URL is seen
        assert seen.has("https://example.com/page1") is True
        assert seen.has("https://example.com/page2") is False
    
    def test_ttl_expiration(self):
        """Test that URLs expire after TTL."""
        seen = URLSeenSet(ttl_seconds=1)
        
        seen.add("https://example.com/page1")
        assert seen.has("https://example.com/page1") is True
        
        # Wait for expiration
        time.sleep(1.1)
        assert seen.has("https://example.com/page1") is False
    
    def test_clear_expired(self):
        """Test clearing expired URLs."""
        seen = URLSeenSet(ttl_seconds=1)
        
        seen.add("https://example.com/page1")
        seen.add("https://example.com/page2")
        
        time.sleep(1.1)
        
        seen.add("https://example.com/page3")  # Fresh
        
        seen.clear_expired()
        
        # page1 and page2 should be gone, page3 should remain
        assert seen.size() == 1
        assert seen.has("https://example.com/page3") is True
    
    def test_stats(self):
        """Test seen set statistics."""
        seen = URLSeenSet(ttl_seconds=10)
        
        seen.add("https://example.com/page1")
        seen.add("https://example.com/page2")
        
        stats = seen.stats()
        
        assert stats["size"] == 2
        assert stats["ttl_seconds"] == 10


class TestQueryCache:
    """Test query cache functionality."""
    
    def test_cache_and_retrieve(self):
        """Test caching and retrieving query results."""
        cache = QueryCache(ttl_seconds=10)
        
        results = [
            {"url": "https://example.com/1", "title": "Result 1"},
            {"url": "https://example.com/2", "title": "Result 2"},
        ]
        
        cache.set_results("test query", results, source="google")
        
        cached = cache.get_results("test query", source="google")
        assert cached is not None
        assert len(cached) == 2
        assert cached[0]["url"] == "https://example.com/1"
    
    def test_cache_with_different_sources(self):
        """Test that same query with different sources are cached separately."""
        cache = QueryCache(ttl_seconds=10)
        
        google_results = [{"url": "https://google-result.com"}]
        ddg_results = [{"url": "https://ddg-result.com"}]
        
        cache.set_results("same query", google_results, source="google")
        cache.set_results("same query", ddg_results, source="ddg")
        
        # Should get different results for different sources
        google_cached = cache.get_results("same query", source="google")
        ddg_cached = cache.get_results("same query", source="ddg")
        
        assert google_cached[0]["url"] == "https://google-result.com"
        assert ddg_cached[0]["url"] == "https://ddg-result.com"
    
    def test_has_cached(self):
        """Test checking if query is cached."""
        cache = QueryCache(ttl_seconds=10)
        
        results = [{"url": "https://example.com"}]
        
        assert cache.has_cached("test query", source="google") is False
        
        cache.set_results("test query", results, source="google")
        
        assert cache.has_cached("test query", source="google") is True
    
    def test_ttl_expiration(self):
        """Test that cached queries expire after TTL."""
        cache = QueryCache(ttl_seconds=1)
        
        results = [{"url": "https://example.com"}]
        cache.set_results("test query", results, source="google")
        
        assert cache.has_cached("test query", source="google") is True
        
        # Wait for expiration
        time.sleep(1.1)
        
        assert cache.has_cached("test query", source="google") is False
        assert cache.get_results("test query", source="google") is None
    
    def test_auto_cleanup(self):
        """Test that QueryCache automatically cleans up expired entries."""
        # Use short TTL and cleanup interval
        cache = QueryCache(ttl_seconds=1, cleanup_interval=1)
        
        results = [{"url": "https://example.com"}]
        cache.set_results("query1", results, source="google")
        cache.set_results("query2", results, source="ddg")
        
        stats = cache.stats()
        assert stats["size"] == 2
        
        # Wait for entries to expire and cleanup interval to pass
        time.sleep(1.5)
        
        # Access cache to trigger auto-cleanup
        cache.get_results("nonexistent", "any")
        
        # All expired entries should be cleared
        stats = cache.stats()
        assert stats["size"] == 0
