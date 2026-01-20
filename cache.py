# -*- coding: utf-8 -*-
"""
Cache module for query results and URL seen-set tracking.
Implements TTL-based caching for cost and performance optimization.
"""

import os
import time
from typing import Any, Dict, List, Optional, Set


class TTLCache:
    """
    Simple TTL (Time To Live) cache with size limits.
    Items expire after a specified time period.
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10000):
        """
        Initialize TTL cache.
        
        Args:
            ttl_seconds: Time to live for cache entries in seconds
            max_size: Maximum number of entries before eviction
        """
        self.ttl = ttl_seconds
        self.max_size = max_size
        # Python 3.7+ dicts maintain insertion order
        self._cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None
        
        # Move to end (for LRU behavior - dicts maintain insertion order since Python 3.7)
        # Re-insert to move to end
        self._cache[key] = self._cache.pop(key)
        return value
    
    def set(self, key: str, value: Any):
        """
        Set value in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            # Pop the first item (oldest in insertion order)
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        
        self._cache[key] = (value, time.time())
    
    def has(self, key: str) -> bool:
        """
        Check if key exists and is not expired.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists and not expired
        """
        return self.get(key) is not None
    
    def clear_expired(self):
        """Remove all expired entries."""
        now = time.time()
        # Use dict comprehension for more efficient bulk deletion
        self._cache = {
            k: v for k, v in self._cache.items()
            if now - v[1] <= self.ttl
        }
    
    def clear(self):
        """Clear all entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        expired = sum(1 for _, ts in self._cache.values() if now - ts > self.ttl)
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl,
            "expired_entries": expired,
        }


class URLSeenSet:
    """
    Set for tracking seen URLs with TTL expiration.
    Used to avoid re-fetching the same URLs within a time window.
    """
    
    def __init__(self, ttl_seconds: int = 604800):  # 7 days default
        """
        Initialize URL seen set.
        
        Args:
            ttl_seconds: Time to live for entries (default 7 days)
        """
        self.ttl = ttl_seconds
        self._seen: Dict[str, float] = {}
    
    def add(self, url: str) -> bool:
        """
        Add URL to seen set.
        
        Args:
            url: URL to add
        
        Returns:
            True if URL was newly added, False if already existed
        """
        if self.has(url):
            return False
        
        self._seen[url] = time.time()
        return True
    
    def has(self, url: str) -> bool:
        """
        Check if URL has been seen (and not expired).
        
        Args:
            url: URL to check
        
        Returns:
            True if URL has been seen and not expired
        """
        if url not in self._seen:
            return False
        
        # Check if expired
        if time.time() - self._seen[url] > self.ttl:
            del self._seen[url]
            return False
        
        return True
    
    def clear_expired(self):
        """Remove all expired entries."""
        now = time.time()
        # Use dict comprehension for more efficient bulk deletion
        self._seen = {
            url: ts for url, ts in self._seen.items()
            if now - ts <= self.ttl
        }
    
    def clear(self):
        """Clear all entries."""
        self._seen.clear()
    
    def size(self) -> int:
        """Get current size."""
        return len(self._seen)
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics."""
        now = time.time()
        expired = sum(1 for ts in self._seen.values() if now - ts > self.ttl)
        return {
            "size": len(self._seen),
            "ttl_seconds": self.ttl,
            "expired_entries": expired,
        }


class QueryCache:
    """
    Cache for search query results.
    Stores query results with TTL to avoid redundant searches.
    """
    
    def __init__(self, ttl_seconds: int = 86400):  # 24 hours default
        """
        Initialize query cache.
        
        Args:
            ttl_seconds: Time to live for cache entries (default 24 hours)
        """
        self._cache = TTLCache(ttl_seconds=ttl_seconds, max_size=1000)
    
    def get_results(self, query: str, source: str = "") -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results for a query.
        
        Args:
            query: Search query
            source: Source (e.g., "google", "ddg")
        
        Returns:
            Cached results or None if not found/expired
        """
        cache_key = f"{source}:{query}" if source else query
        return self._cache.get(cache_key)
    
    def set_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        source: str = ""
    ):
        """
        Cache results for a query.
        
        Args:
            query: Search query
            results: Search results to cache
            source: Source (e.g., "google", "ddg")
        """
        cache_key = f"{source}:{query}" if source else query
        self._cache.set(cache_key, results)
    
    def has_cached(self, query: str, source: str = "") -> bool:
        """
        Check if query has cached results.
        
        Args:
            query: Search query
            source: Source (e.g., "google", "ddg")
        
        Returns:
            True if cached results exist and are not expired
        """
        cache_key = f"{source}:{query}" if source else query
        return self._cache.has(cache_key)
    
    def clear(self):
        """Clear all cached queries."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats()


_AI_RESPONSE_CACHE: Optional[TTLCache] = None
_DOMAIN_RATING_CACHE: Optional[TTLCache] = None
_QUERY_CACHE: Optional[QueryCache] = None
_URL_SEEN_SET: Optional[URLSeenSet] = None


def get_query_cache(ttl_seconds: int = 86400) -> QueryCache:
    """Get or create global query cache."""
    global _QUERY_CACHE
    if _QUERY_CACHE is None:
        _QUERY_CACHE = QueryCache(ttl_seconds=ttl_seconds)
    return _QUERY_CACHE


def get_url_seen_set(ttl_seconds: int = 604800) -> URLSeenSet:
    """Get or create global URL seen set."""
    global _URL_SEEN_SET
    if _URL_SEEN_SET is None:
        _URL_SEEN_SET = URLSeenSet(ttl_seconds=ttl_seconds)
    return _URL_SEEN_SET


def get_ai_response_cache(
    ttl_seconds: Optional[int] = None,
    max_size: int = 1500,
) -> TTLCache:
    """
    Get or create global AI response cache.

    Args:
        ttl_seconds: TTL for cached AI responses
        max_size: Max number of cached items
    """
    global _AI_RESPONSE_CACHE
    if ttl_seconds is None:
        ttl_seconds = int(os.getenv("AI_RESPONSE_CACHE_TTL", "1800"))
    if _AI_RESPONSE_CACHE is None:
        _AI_RESPONSE_CACHE = TTLCache(ttl_seconds=ttl_seconds, max_size=max_size)
    return _AI_RESPONSE_CACHE


def get_domain_rating_cache(
    ttl_seconds: Optional[int] = None,
    max_size: int = 5000,
) -> TTLCache:
    """
    Get or create global domain rating cache (e.g., domain priority scores).

    Args:
        ttl_seconds: TTL for cached ratings
        max_size: Max number of cached domains
    """
    global _DOMAIN_RATING_CACHE
    if ttl_seconds is None:
        ttl_seconds = int(os.getenv("DOMAIN_RATING_CACHE_TTL", "43200"))
    if _DOMAIN_RATING_CACHE is None:
        _DOMAIN_RATING_CACHE = TTLCache(ttl_seconds=ttl_seconds, max_size=max_size)
    return _DOMAIN_RATING_CACHE
