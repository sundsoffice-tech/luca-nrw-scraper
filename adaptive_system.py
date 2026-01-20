# -*- coding: utf-8 -*-
"""
Adaptive System Integration Module
Provides high-level interface for the phase-based adaptive search system.

Integrates with Django ai_config app when available for DB-driven AI configuration.
Falls back gracefully to default constants when Django is not available.
"""

import os
from typing import Dict, List, Optional, Tuple
import logging

from metrics import get_metrics_store, MetricsStore
from adaptive_dorks import AdaptiveDorkSelector
from wasserfall import WasserfallManager
from cache import get_query_cache, get_url_seen_set, QueryCache, URLSeenSet
from reporting import ReportGenerator

# Optional Django ai_config integration
# Falls back gracefully when Django is not available or configured
try:
    from telis_recruitment.ai_config.loader import (
        get_ai_config as _get_ai_config_django,
        get_prompt,
        log_usage,
        check_budget
    )
    AI_CONFIG_AVAILABLE = True
except (ImportError, Exception):
    AI_CONFIG_AVAILABLE = False
    # Fallback defaults when ai_config is not available
    def _get_ai_config_django():
        return {
            'temperature': 0.3,
            'top_p': 1.0,
            'max_tokens': 4000,
            'learning_rate': 0.01,
            'daily_budget': 5.0,
            'monthly_budget': 150.0,
            'confidence_threshold': 0.35,
            'retry_limit': 2,
            'timeout_seconds': 30,
            'default_provider': 'OpenAI',
            'default_model': 'gpt-4o-mini',
        }
    
    def get_prompt(slug: str):
        return None
    
    def log_usage(*args, **kwargs):
        pass
    
    def check_budget():
        return True, {
            'daily_spent': 0.0,
            'daily_budget': 5.0,
            'daily_remaining': 5.0,
            'monthly_spent': 0.0,
            'monthly_budget': 150.0,
            'monthly_remaining': 150.0,
        }

logger = logging.getLogger(__name__)


# Cached AI config loader (lazy loading)
_AI_CONFIG_CACHE: Optional[Dict] = None


def get_ai_config() -> Dict:
    """
    Get AI configuration with lazy loading and caching.
    Only loads the config once on first access.
    
    Returns:
        AI configuration dictionary
    """
    global _AI_CONFIG_CACHE
    if _AI_CONFIG_CACHE is None:
        _AI_CONFIG_CACHE = _get_ai_config_django()
        if AI_CONFIG_AVAILABLE:
            logger.info(f"AI config loaded and cached: "
                       f"provider={_AI_CONFIG_CACHE.get('default_provider')}, "
                       f"model={_AI_CONFIG_CACHE.get('default_model')}")
    return _AI_CONFIG_CACHE


class AdaptiveSearchSystem:
    """
    High-level interface for the adaptive search system.
    Coordinates metrics, dork selection, wasserfall modes, and caching.
    
    Integrates with Django ai_config app when available for configuration management.
    """
    
    def __init__(
        self,
        all_dorks: List[str],
        metrics_db_path: str = "metrics.db",
        query_cache_ttl: int = 86400,  # 24 hours
        url_seen_ttl: int = 604800,  # 7 days
        initial_mode: str = "conservative",
    ):
        """
        Initialize the adaptive search system.
        
        Args:
            all_dorks: List of all available dork queries
            metrics_db_path: Path to metrics database
            query_cache_ttl: TTL for query cache in seconds (default 24h)
            url_seen_ttl: TTL for URL seen set in seconds (default 7d)
            initial_mode: Initial Wasserfall mode
        """
        # Load AI configuration (from Django DB if available, else defaults)
        self.ai_config = get_ai_config()
        if AI_CONFIG_AVAILABLE:
            logger.info(f"Adaptive system using AI config from Django DB: "
                       f"provider={self.ai_config.get('default_provider')}, "
                       f"model={self.ai_config.get('default_model')}")
        else:
            logger.info("Adaptive system using fallback AI config (Django not available)")
        
        # Initialize components
        self.metrics = get_metrics_store(metrics_db_path)
        self.dork_selector = AdaptiveDorkSelector(
            self.metrics,
            all_dorks,
            explore_rate=0.15,
        )
        self.wasserfall = WasserfallManager(
            self.metrics,
            initial_mode=initial_mode,
        )
        self.query_cache = get_query_cache(ttl_seconds=query_cache_ttl)
        self.url_seen = get_url_seen_set(ttl_seconds=url_seen_ttl)
        self.reporter = ReportGenerator(self.metrics)
        
        # Runtime state
        self.run_count = 0
    
    def select_dorks_for_run(self) -> List[Dict[str, str]]:
        """
        Select dorks for this run based on current Wasserfall mode.
        
        Returns:
            List of selected dork info dicts
        """
        mode = self.wasserfall.get_current_mode()
        
        # Determine number of dorks based on mode
        num_dorks = mode.dork_slots_max
        
        # Update explore rate from mode
        self.dork_selector.explore_rate = mode.explore_rate
        
        # Select dorks
        selected = self.dork_selector.select_dorks(
            num_dorks=num_dorks,
            google_ratio=0.25,
            force_update=True,
        )
        
        # Log selection
        self.reporter.log_dork_selection(selected, mode.name)
        
        return selected
    
    def should_fetch_url(self, url: str) -> Tuple[bool, str]:
        """
        Check if URL should be fetched.
        
        Args:
            url: URL to check
        
        Returns:
            (should_fetch, reason) tuple
        """
        # Check if already seen
        if self.url_seen.has(url):
            return False, "already_seen"
        
        # Check host backoff
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        host_metrics = self.metrics.get_host_metrics(host)
        
        if host_metrics.is_backedoff():
            return False, "host_backedoff"
        
        return True, ""
    
    def mark_url_seen(self, url: str):
        """Mark URL as seen."""
        self.url_seen.add(url)
    
    def get_cached_query_results(
        self,
        query: str,
        source: str
    ) -> Optional[List[Dict]]:
        """
        Get cached results for a query.
        
        Args:
            query: Search query
            source: Source ("google" or "ddg")
        
        Returns:
            Cached results or None
        """
        return self.query_cache.get_results(query, source)
    
    def cache_query_results(
        self,
        query: str,
        source: str,
        results: List[Dict]
    ):
        """
        Cache results for a query.
        
        Args:
            query: Search query
            source: Source ("google" or "ddg")
            results: Search results to cache
        """
        self.query_cache.set_results(query, results, source)
    
    def record_query_execution(self, dork: str):
        """Record that a query was executed."""
        self.metrics.record_query(dork)
    
    def record_serp_results(self, dork: str, count: int):
        """Record SERP hits for a dork."""
        self.metrics.record_serp_hits(dork, count)
    
    def record_url_fetched(self, dork: str, url: str):
        """Record that a URL was fetched."""
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        self.metrics.record_url_fetch(dork, host)
    
    def record_lead_found(self, dork: str):
        """Record that a lead was found."""
        self.metrics.record_lead_found(dork)
    
    def record_lead_kept(self, dork: str):
        """Record that a lead was kept after dropper."""
        self.metrics.record_lead_kept(dork)
    
    def record_accepted_lead(self, dork: str):
        """Record that a lead was accepted (final)."""
        self.metrics.record_accepted_lead(dork)
    
    def record_lead_dropped(self, url: str, reason: str):
        """
        Record that a lead was dropped.
        
        Args:
            url: URL of dropped lead
            reason: Drop reason
        """
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        self.metrics.record_drop(host, reason)
        
        # Check if host should be backed off
        host_metrics = self.metrics.get_host_metrics(host)
        if host_metrics.should_backoff():
            self.metrics.set_host_backoff(host)
    
    def complete_run(self):
        """
        Complete a run and update system state.
        Should be called at the end of each scraping run.
        """
        # Persist metrics
        self.metrics.persist()
        
        # Increment run counter
        self.run_count += 1
        self.wasserfall.increment_run()
        
        # Check for mode transition
        transition = self.wasserfall.check_and_transition()
        if transition:
            print(f"Wasserfall mode transition: {transition['from_mode']} -> {transition['to_mode']}")
            print(f"Reason: {transition['reason']}")
            print(f"Phone find rate: {transition['phone_find_rate']:.2%}")
    
    def get_rate_limits(self) -> Dict[str, int]:
        """
        Get current rate limits based on Wasserfall mode.
        
        Returns:
            Dict with rate limit info
        """
        mode = self.wasserfall.get_current_mode()
        return {
            "ddg_bucket_rate": mode.ddg_bucket_rate,
            "google_bucket_rate": mode.google_bucket_rate,
            "worker_parallelism": mode.worker_parallelism,
        }
    
    def generate_report(
        self,
        output_format: str = "json",
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Generate a comprehensive report.
        
        Args:
            output_format: "json" or "csv"
            output_path: Optional path to save report
        
        Returns:
            Report data
        """
        return self.reporter.generate_weekly_report(
            output_format=output_format,
            output_path=output_path
        )
    
    def get_status(self) -> Dict:
        """
        Get current system status.
        
        Returns:
            Status dict with key metrics
        """
        return {
            "run_count": self.run_count,
            "wasserfall": self.wasserfall.get_status(),
            "dork_pools": self.dork_selector.get_pool_info(),
            "query_cache": self.query_cache.stats(),
            "url_seen": self.url_seen.stats(),
            "phone_find_rate": self.metrics.calculate_phone_find_rate(),
            "backedoff_hosts": len(self.metrics.get_backedoff_hosts()),
        }
    
    def cleanup_caches(self):
        """Clean up expired cache entries."""
        self.query_cache.clear()
        self.url_seen.clear_expired()


def create_system_from_env(all_dorks: List[str]) -> AdaptiveSearchSystem:
    """
    Create adaptive system from environment variables.
    
    Args:
        all_dorks: List of all available dorks
    
    Returns:
        Configured AdaptiveSearchSystem
    """
    metrics_db = os.getenv("METRICS_DB", "metrics.db")
    query_cache_ttl = int(os.getenv("QUERY_CACHE_TTL", "86400"))  # 24h
    url_seen_ttl = int(os.getenv("URL_SEEN_TTL", "604800"))  # 7d
    initial_mode = os.getenv("WASSERFALL_MODE", "conservative")
    
    return AdaptiveSearchSystem(
        all_dorks=all_dorks,
        metrics_db_path=metrics_db,
        query_cache_ttl=query_cache_ttl,
        url_seen_ttl=url_seen_ttl,
        initial_mode=initial_mode,
    )
