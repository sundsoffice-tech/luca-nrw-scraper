"""
HTTP/Crawler functionality for luca-nrw-scraper.

This module provides HTTP client functionality, URL utilities, retry logic,
and robots.txt handling for the web crawler.
"""

from .client import (
    get_client,
    http_get_async,
    fetch_response_async,
    fetch_with_login_check,
)
from .url_utils import (
    is_denied,
    path_ok,
    prioritize_urls,
)
from .retry import (
    schedule_retry,
    should_retry_status,
)
from .robots import (
    check_robots_txt,
    robots_allowed_async,
)
from .backoff import (
    retry_with_backoff,
    calculate_backoff_delay,
    RetryExhausted,
)

__all__ = [
    # Client functions
    "get_client",
    "http_get_async",
    "fetch_response_async",
    "fetch_with_login_check",
    # URL utilities
    "is_denied",
    "path_ok",
    "prioritize_urls",
    # Retry logic
    "schedule_retry",
    "should_retry_status",
    # Robots handling
    "check_robots_txt",
    "robots_allowed_async",
    # Backoff logic
    "retry_with_backoff",
    "calculate_backoff_delay",
    "RetryExhausted",
]
