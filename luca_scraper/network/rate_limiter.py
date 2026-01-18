# -*- coding: utf-8 -*-
"""
Rate limiter and retry logic for network requests.
Tracks retry attempts and determines which HTTP status codes should trigger retries.
"""

import os
import time
from typing import Any, Dict

# Retry configuration
RETRY_INCLUDE_403 = (os.getenv("RETRY_INCLUDE_403", "0") == "1")
RETRY_MAX_PER_URL = int(os.getenv("RETRY_MAX_PER_URL", "2"))
RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "6.0"))

# Global retry state tracking
_RETRY_URLS: Dict[str, Dict[str, Any]] = {}

# Metrics tracking
RUN_METRICS = {
    "removed_by_dropper": 0,
    "portal_dropped": 0,
    "impressum_dropped": 0,
    "pdf_dropped": 0,
    "retry_count": 0,
    "status_429": 0,
    "status_403": 0,
    "status_5xx": 0,
}


def _reset_metrics():
    """Reset all run metrics to zero."""
    global RUN_METRICS
    RUN_METRICS = {k: 0 for k in RUN_METRICS}


def _record_drop(reason: str):
    """Record a dropped URL by reason."""
    RUN_METRICS["removed_by_dropper"] += 1
    if reason in ("portal_host", "portal_domain"):
        RUN_METRICS["portal_dropped"] += 1
    if reason == "impressum_no_contact":
        RUN_METRICS["impressum_dropped"] += 1
    if reason == "pdf_without_cv_hint":
        RUN_METRICS["pdf_dropped"] += 1


def _record_retry(status: int):
    """Record a retry attempt by status code."""
    RUN_METRICS["retry_count"] += 1
    if status == 429:
        RUN_METRICS["status_429"] += 1
    elif status == 403:
        RUN_METRICS["status_403"] += 1
    if 500 <= status < 600:
        RUN_METRICS["status_5xx"] += 1


def _should_retry_status(status: int) -> bool:
    """
    Determine if a status code should trigger a retry.
    
    Args:
        status: HTTP status code
        
    Returns:
        True if the status should be retried
    """
    if status in (429, 503, 504):
        return True
    if status == 403 and RETRY_INCLUDE_403:
        return True
    return False


def _schedule_retry(url: str, status: int):
    """
    Schedule a URL for retry.
    
    Args:
        url: URL to retry
        status: HTTP status code that triggered the retry
    """
    _record_retry(status)
    if not url:
        return
    if url in _RETRY_URLS:
        return
    _RETRY_URLS[url] = {"retries": 0, "status": status, "last_ts": time.time()}
