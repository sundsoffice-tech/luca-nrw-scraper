# -*- coding: utf-8 -*-
"""
Tests for caching improvements: AI result cache, domain rating cache, lazy loading.
"""

import hashlib
import os
import sys
import time
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import cache classes
from cache import (
    AIResultCache,
    DomainRatingCache,
    get_ai_result_cache,
    get_domain_rating_cache,
)


def test_ai_result_cache_basic():
    """Test basic AI result cache operations."""
    cache = AIResultCache(ttl_seconds=60)
    
    # Test cache miss
    content_hash = hashlib.md5(b"test content").hexdigest()
    assert cache.get_result("analyze_content", content_hash) is None
    
    # Test cache set and get
    result = {"score": 0.85, "category": "candidate"}
    cache.set_result("analyze_content", content_hash, result)
    cached_result = cache.get_result("analyze_content", content_hash)
    assert cached_result == result
    
    # Test has_cached
    assert cache.has_cached("analyze_content", content_hash) is True
    assert cache.has_cached("extract_contacts", content_hash) is False


def test_ai_result_cache_ttl():
    """Test AI result cache TTL expiration."""
    cache = AIResultCache(ttl_seconds=1)
    
    content_hash = hashlib.md5(b"test content").hexdigest()
    result = {"score": 0.85}
    cache.set_result("analyze_content", content_hash, result)
    
    # Should be cached immediately
    assert cache.get_result("analyze_content", content_hash) == result
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Should be expired
    assert cache.get_result("analyze_content", content_hash) is None


def test_ai_result_cache_size_limit():
    """Test AI result cache size limit and eviction."""
    cache = AIResultCache(ttl_seconds=60)
    cache._cache.max_size = 5  # Set small limit for testing
    
    # Add entries up to limit
    for i in range(5):
        content_hash = hashlib.md5(f"content{i}".encode()).hexdigest()
        cache.set_result("test", content_hash, {"index": i})
    
    # All should be cached
    assert cache._cache.size() == 5
    
    # Add one more - should evict oldest
    content_hash = hashlib.md5(b"content5").hexdigest()
    cache.set_result("test", content_hash, {"index": 5})
    
    # Size should still be at limit
    assert cache._cache.size() == 5


def test_ai_result_cache_stats():
    """Test AI result cache statistics."""
    cache = AIResultCache(ttl_seconds=60)
    
    for i in range(3):
        content_hash = hashlib.md5(f"content{i}".encode()).hexdigest()
        cache.set_result("test", content_hash, {"index": i})
    
    stats = cache.stats()
    assert stats["size"] == 3
    assert stats["max_size"] == 5000
    assert stats["ttl_seconds"] == 60


def test_domain_rating_cache_basic():
    """Test basic domain rating cache operations."""
    cache = DomainRatingCache(ttl_seconds=60)
    
    # Test cache miss
    assert cache.get_score("example.com", "portal_reputation") is None
    
    # Test cache set and get
    cache.set_score("example.com", 8.5, "portal_reputation")
    assert cache.get_score("example.com", "portal_reputation") == 8.5
    
    # Test different score types
    cache.set_score("example.com", 7.2, "quality")
    assert cache.get_score("example.com", "quality") == 7.2
    assert cache.get_score("example.com", "portal_reputation") == 8.5
    
    # Test has_cached
    assert cache.has_cached("example.com", "portal_reputation") is True
    assert cache.has_cached("example.com", "unknown") is False


def test_domain_rating_cache_ttl():
    """Test domain rating cache TTL expiration."""
    cache = DomainRatingCache(ttl_seconds=1)
    
    cache.set_score("example.com", 8.5)
    assert cache.get_score("example.com") == 8.5
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Should be expired
    assert cache.get_score("example.com") is None


def test_domain_rating_cache_stats():
    """Test domain rating cache statistics."""
    cache = DomainRatingCache(ttl_seconds=60)
    
    cache.set_score("example.com", 8.5)
    cache.set_score("test.org", 7.0)
    cache.set_score("sample.net", 9.0, "quality")
    
    stats = cache.stats()
    assert stats["size"] == 3
    assert stats["max_size"] == 10000


def test_get_ai_result_cache_singleton():
    """Test that get_ai_result_cache returns singleton."""
    cache1 = get_ai_result_cache()
    cache2 = get_ai_result_cache()
    assert cache1 is cache2


def test_get_domain_rating_cache_singleton():
    """Test that get_domain_rating_cache returns singleton."""
    cache1 = get_domain_rating_cache()
    cache2 = get_domain_rating_cache()
    assert cache1 is cache2


def test_lazy_loading_dorks():
    """Test lazy loading of dorks."""
    from dorks_extended import get_all_dorks
    
    # First call should load and cache
    dorks1 = get_all_dorks()
    assert isinstance(dorks1, list)
    assert len(dorks1) > 0
    
    # Second call should return cached result (same object)
    dorks2 = get_all_dorks()
    assert dorks1 is dorks2  # Should be same cached object


def test_lazy_loading_ai_config():
    """Test lazy loading of AI config."""
    from adaptive_system import get_ai_config
    
    # First call should load and cache
    config1 = get_ai_config()
    assert isinstance(config1, dict)
    assert "default_model" in config1
    
    # Second call should return cached result (same object)
    config2 = get_ai_config()
    assert config1 is config2  # Should be same cached object


def test_ai_result_cache_clear():
    """Test clearing AI result cache."""
    cache = AIResultCache(ttl_seconds=60)
    
    content_hash = hashlib.md5(b"test").hexdigest()
    cache.set_result("test", content_hash, {"result": "value"})
    assert cache.get_result("test", content_hash) is not None
    
    cache.clear()
    assert cache.get_result("test", content_hash) is None
    assert cache.stats()["size"] == 0


def test_domain_rating_cache_clear():
    """Test clearing domain rating cache."""
    cache = DomainRatingCache(ttl_seconds=60)
    
    cache.set_score("example.com", 8.5)
    assert cache.get_score("example.com") is not None
    
    cache.clear()
    assert cache.get_score("example.com") is None
    assert cache.stats()["size"] == 0


if __name__ == "__main__":
    # Run tests manually
    print("Running cache improvement tests...")
    
    test_ai_result_cache_basic()
    print("✓ AI result cache basic operations")
    
    test_ai_result_cache_ttl()
    print("✓ AI result cache TTL expiration")
    
    test_ai_result_cache_size_limit()
    print("✓ AI result cache size limit")
    
    test_ai_result_cache_stats()
    print("✓ AI result cache statistics")
    
    test_domain_rating_cache_basic()
    print("✓ Domain rating cache basic operations")
    
    test_domain_rating_cache_ttl()
    print("✓ Domain rating cache TTL expiration")
    
    test_domain_rating_cache_stats()
    print("✓ Domain rating cache statistics")
    
    test_get_ai_result_cache_singleton()
    print("✓ AI result cache singleton")
    
    test_get_domain_rating_cache_singleton()
    print("✓ Domain rating cache singleton")
    
    test_lazy_loading_dorks()
    print("✓ Lazy loading dorks")
    
    test_lazy_loading_ai_config()
    print("✓ Lazy loading AI config")
    
    test_ai_result_cache_clear()
    print("✓ AI result cache clear")
    
    test_domain_rating_cache_clear()
    print("✓ Domain rating cache clear")
    
    print("\nAll cache improvement tests passed! ✓")
