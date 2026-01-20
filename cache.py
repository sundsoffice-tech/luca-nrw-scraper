# -*- coding: utf-8 -*-
"""
Cache module for query results and URL seen-set tracking.
Implements TTL-based caching for cost and performance optimization.
"""

import time
from collections import OrderedDict
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
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
    
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
        
        # Move to end (LRU)
        self._cache.move_to_end(key)
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
            self._cache.popitem(last=False)
        
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
        expired_keys = [
            k for k, (v, ts) in self._cache.items()
            if now - ts > self.ttl
        ]
        for k in expired_keys:
            del self._cache[k]
    
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
        expired_urls = [
            url for url, ts in self._seen.items()
            if now - ts > self.ttl
        ]
        for url in expired_urls:
            del self._seen[url]
    
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


class AIResultCache:
    """
    Cache for AI query results (e.g., content analysis, contact extraction).
    Caches expensive AI API calls to reduce costs and latency.
    """
    
    def __init__(self, ttl_seconds: int = 604800):  # 7 days default
        """
        Initialize AI result cache.
        
        Args:
            ttl_seconds: Time to live for cache entries (default 7 days)
        """
        self._cache = TTLCache(ttl_seconds=ttl_seconds, max_size=5000)
    
    def get_result(self, query_type: str, content_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get cached AI result.
        
        Args:
            query_type: Type of query (e.g., "analyze_content", "extract_contacts")
            content_hash: Hash of the input content
        
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = f"{query_type}:{content_hash}"
        return self._cache.get(cache_key)
    
    def set_result(self, query_type: str, content_hash: str, result: Dict[str, Any]):
        """
        Cache AI result.
        
        Args:
            query_type: Type of query
            content_hash: Hash of the input content
            result: AI query result to cache
        """
        cache_key = f"{query_type}:{content_hash}"
        self._cache.set(cache_key, result)
    
    def has_cached(self, query_type: str, content_hash: str) -> bool:
        """
        Check if result is cached.
        
        Args:
            query_type: Type of query
            content_hash: Hash of the input content
        
        Returns:
            True if cached result exists and is not expired
        """
        cache_key = f"{query_type}:{content_hash}"
        return self._cache.has(cache_key)
    
    def clear(self):
        """Clear all cached AI results."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats()


class DomainRatingCache:
    """
    Cache for domain/host ratings and scores.
    Reduces redundant scoring calculations for frequently accessed domains.
    """
    
    def __init__(self, ttl_seconds: int = 86400):  # 24 hours default
        """
        Initialize domain rating cache.
        
        Args:
            ttl_seconds: Time to live for cache entries (default 24 hours)
        """
        self._cache = TTLCache(ttl_seconds=ttl_seconds, max_size=10000)
    
    def get_score(self, domain: str, score_type: str = "default") -> Optional[float]:
        """
        Get cached domain score.
        
        Args:
            domain: Domain name
            score_type: Type of score (e.g., "portal_reputation", "quality")
        
        Returns:
            Cached score or None if not found/expired
        """
        cache_key = f"{domain}:{score_type}"
        return self._cache.get(cache_key)
    
    def set_score(self, domain: str, score: float, score_type: str = "default"):
        """
        Cache domain score.
        
        Args:
            domain: Domain name
            score: Score value
            score_type: Type of score
        """
        cache_key = f"{domain}:{score_type}"
        self._cache.set(cache_key, score)
    
    def has_cached(self, domain: str, score_type: str = "default") -> bool:
        """
        Check if domain score is cached.
        
        Args:
            domain: Domain name
            score_type: Type of score
        
        Returns:
            True if cached score exists and is not expired
        """
        cache_key = f"{domain}:{score_type}"
        return self._cache.has(cache_key)
    
    def clear(self):
        """Clear all cached domain scores."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats()


# Global cache instances
_QUERY_CACHE: Optional[QueryCache] = None
_URL_SEEN_SET: Optional[URLSeenSet] = None
_AI_RESULT_CACHE: Optional[AIResultCache] = None
_DOMAIN_RATING_CACHE: Optional[DomainRatingCache] = None


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


def get_ai_result_cache(ttl_seconds: int = 604800) -> AIResultCache:
    """Get or create global AI result cache."""
    global _AI_RESULT_CACHE
    if _AI_RESULT_CACHE is None:
        _AI_RESULT_CACHE = AIResultCache(ttl_seconds=ttl_seconds)
    return _AI_RESULT_CACHE


def get_domain_rating_cache(ttl_seconds: int = 86400) -> DomainRatingCache:
    """Get or create global domain rating cache."""
    global _DOMAIN_RATING_CACHE
    if _DOMAIN_RATING_CACHE is None:
        _DOMAIN_RATING_CACHE = DomainRatingCache(ttl_seconds=ttl_seconds)
    return _DOMAIN_RATING_CACHE
