"""
Retry logic and circuit breaker for HTTP requests.
"""

import os
import time
from typing import Any, Dict


# Configuration
CB_BASE_PENALTY = int(os.getenv("CB_BASE_PENALTY", "30"))
CB_API_PENALTY = int(os.getenv("CB_API_PENALTY", "15"))
CB_MAX_PENALTY = int(os.getenv("CB_MAX_PENALTY", "900"))
RETRY_INCLUDE_403 = (os.getenv("RETRY_INCLUDE_403", "0") == "1")

# Global state
_HOST_STATE: Dict[str, Dict[str, Any]] = {}
_RETRY_URLS: Dict[str, Dict[str, Any]] = {}
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


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    import json
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    print(f"[{ts}] [{level.upper():7}] {msg}{ctx_str}", flush=True)


def _reset_metrics():
    """Reset run metrics to zero."""
    global RUN_METRICS
    RUN_METRICS = {k: 0 for k in RUN_METRICS}


def _record_drop(reason: str):
    """
    Record a dropped URL.
    
    Args:
        reason: Reason for dropping the URL
    """
    RUN_METRICS["removed_by_dropper"] += 1
    if reason in ("portal_host", "portal_domain"):
        RUN_METRICS["portal_dropped"] += 1
    if reason == "impressum_no_contact":
        RUN_METRICS["impressum_dropped"] += 1
    if reason == "pdf_without_cv_hint":
        RUN_METRICS["pdf_dropped"] += 1


def _record_retry(status: int):
    """
    Record a retry attempt.
    
    Args:
        status: HTTP status code that triggered the retry
    """
    RUN_METRICS["retry_count"] += 1
    if status == 429:
        RUN_METRICS["status_429"] += 1
    elif status == 403:
        RUN_METRICS["status_403"] += 1
    if 500 <= status < 600:
        RUN_METRICS["status_5xx"] += 1


def _penalize_host(host: str, reason: str = "error"):
    """
    Penalize host with learning integration.
    
    Implements circuit breaker pattern with exponential backoff.
    API hosts get shorter penalties.
    
    Args:
        host: Hostname to penalize
        reason: Reason for penalty
    """
    if not host:
        return
    
    # API hosts get shorter penalty
    is_google_api = host in {"googleapis.com", "www.googleapis.com"} or host.endswith(".googleapis.com")
    is_api_host = host.startswith("api.")
    
    if is_google_api or is_api_host:
        penalty = CB_API_PENALTY
    else:
        penalty = CB_BASE_PENALTY
    
    if is_google_api:
        # Google API: never hard-penalize; at most a short cool-down
        st = _HOST_STATE.setdefault(host, {"penalty_until": 0.0, "failures": 0})
        st["penalty_until"] = time.time() + penalty
        st["failures"] = 0
        log("info", "Google API backoff (soft)", host=host, penalty_s=penalty)
    else:
        st = _HOST_STATE.setdefault(host, {"penalty_until": 0.0, "failures": 0})
        st["failures"] = min(st["failures"] + 1, 10)
        penalty = min(penalty * (2 ** (st["failures"] - 1)), CB_MAX_PENALTY)
        st["penalty_until"] = time.time() + penalty
        log("warn", "Circuit-Breaker: Host penalized", host=host, failures=st["failures"], penalty_s=penalty)
    
    # Inform learning engine
    try:
        from ai_learning_engine import ActiveLearningEngine
        learning = ActiveLearningEngine()
        learning.record_host_failure(host, reason)
    except Exception:
        pass


def _host_allowed(host: str) -> bool:
    """
    Check if host is allowed (not penalized).
    
    Args:
        host: Hostname to check
        
    Returns:
        True if host is allowed
    """
    if host in {"googleapis.com", "www.googleapis.com"} or host.endswith(".googleapis.com"):
        return True
    st = _HOST_STATE.get(host)
    if not st:
        return True
    if time.time() >= st.get("penalty_until", 0.0):
        st["failures"] = 0
        st["penalty_until"] = 0.0
        return True
    return False


def _should_retry_status(status: int) -> bool:
    """
    Check if HTTP status should trigger a retry.
    
    Args:
        status: HTTP status code
        
    Returns:
        True if should retry
    """
    if status in (429, 503, 504):
        return True
    if status == 403 and RETRY_INCLUDE_403:
        return True
    return False


def _schedule_retry(url: str, status: int):
    """
    Schedule URL for retry.
    
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


# Public API aliases
def schedule_retry(url: str, status: int):
    """Public API for scheduling retries."""
    _schedule_retry(url, status)


def should_retry_status(status: int) -> bool:
    """Public API for checking if status should retry."""
    return _should_retry_status(status)
