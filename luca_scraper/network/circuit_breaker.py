# -*- coding: utf-8 -*-
"""
Circuit breaker and host penalty logic for the network layer.
Tracks host failures and applies exponential backoff penalties.
"""

import os
import time
import urllib.parse
from typing import Any, Dict

from luca_scraper.utils.logging import log

# Circuit breaker constants
CB_BASE_PENALTY = int(os.getenv("CB_BASE_PENALTY", "30"))
CB_API_PENALTY = int(os.getenv("CB_API_PENALTY", "15"))
CB_MAX_PENALTY = int(os.getenv("CB_MAX_PENALTY", "900"))

# Global host state tracking
_HOST_STATE: Dict[str, Dict[str, Any]] = {}


def _host_from(url: str) -> str:
    """Extract host from URL."""
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""


def _penalize_host(host: str, reason: str = "error"):
    """
    Penalize host with exponential backoff.
    
    Args:
        host: Hostname to penalize
        reason: Reason for penalty (for logging)
    """
    if not host:
        return
    
    # API-Hosts bekommen kürzere Penalty
    # Use proper domain matching to avoid substring attacks
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
    
    # Learning Engine informieren
    try:
        from ai_learning_engine import ActiveLearningEngine
        learning = ActiveLearningEngine()
        learning.record_host_failure(host, reason)
    except Exception:
        pass  # Learning ist optional


def _host_allowed(host: str) -> bool:
    """
    Check if host is allowed (not currently penalized).
    
    Args:
        host: Hostname to check
        
    Returns:
        True if host is allowed, False if penalized
    """
    # Use proper domain matching to avoid substring attacks
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
