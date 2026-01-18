# -*- coding: utf-8 -*-
"""Network layer: HTTP clients, circuit breakers, rate limiting"""

from .circuit_breaker import (
    _host_from,
    _penalize_host,
    _host_allowed,
)

from .rate_limiter import (
    _should_retry_status,
    _schedule_retry,
    _record_retry,
    _record_drop,
    _reset_metrics,
    RUN_METRICS,
    _RETRY_URLS,
)

from .client import (
    get_client,
    _make_client,
    _acceptable_by_headers,
)

from .robots import (
    check_robots_txt,
    robots_allowed_async,
)

__all__ = [
    # Circuit breaker
    "_host_from",
    "_penalize_host",
    "_host_allowed",
    # Rate limiter
    "_should_retry_status",
    "_schedule_retry",
    "_record_retry",
    "_record_drop",
    "_reset_metrics",
    "RUN_METRICS",
    "_RETRY_URLS",
    # Client
    "get_client",
    "_make_client",
    "_acceptable_by_headers",
    # Robots
    "check_robots_txt",
    "robots_allowed_async",
]
