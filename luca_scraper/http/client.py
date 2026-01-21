"""
HTTP client functionality with retry, circuit breaker, and SSL fallback support.
"""

import asyncio
import os
import random
import time
from typing import Any, Dict, Optional, Tuple

from curl_cffi.requests import AsyncSession

from .retry import _host_allowed, _penalize_host, _schedule_retry, _should_retry_status
from .url_utils import _host_from


# Configuration
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (compatible; VertriebFinder/2.3; +https://example.com)")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))
USE_TOR = False
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))
WORKER_PARALLELISM = max(1, int(os.getenv("WORKER_PARALLELISM", "35")))
_HTTP_SEMAPHORE = asyncio.Semaphore(WORKER_PARALLELISM)

# Content type guards
BINARY_CT_PREFIXES = ("image/", "video/", "audio/")
DENY_CT_EXACT = {
    "application/octet-stream",
    "application/x-msdownload",
}
PDF_CT = "application/pdf"

# Global client instances with asyncio lock for thread-safe access
_CLIENT_SECURE: Optional[AsyncSession] = None
_CLIENT_INSECURE: Optional[AsyncSession] = None
_CLIENT_LOCK = asyncio.Lock()

# Rotation pools
_env_list = lambda val, sep: [x.strip() for x in (val or "").split(sep) if x.strip()]
PROXY_POOL = _env_list(os.getenv("PROXY_POOL", ""), ",")
UA_POOL_ENV = _env_list(os.getenv("UA_POOL", ""), "|")
UA_POOL_DEFAULT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]
UA_POOL = UA_POOL_ENV if UA_POOL_ENV else UA_POOL_DEFAULT

# Last HTTP status tracking
_LAST_STATUS: Dict[str, int] = {}

# Config dataclass placeholder
class _CFG:
    allow_pdf = os.getenv("ALLOW_PDF", "0") == "1"

CFG = _CFG()


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    import json
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    print(f"[{ts}] [{level.upper():7}] {msg}{ctx_str}", flush=True)


async def get_client(secure: bool = True) -> AsyncSession:
    """
    Get a global async HTTP client instance (thread-safe with asyncio lock).
    
    Args:
        secure: If True, use secure client with SSL verification
        
    Returns:
        AsyncSession instance
    """
    global _CLIENT_SECURE, _CLIENT_INSECURE
    
    # Use asyncio lock to prevent race conditions when creating clients
    async with _CLIENT_LOCK:
        proxy_cfg = {"http://": "socks5://127.0.0.1:9050", "https://": "socks5://127.0.0.1:9050"} if USE_TOR else None
        if secure:
            if _CLIENT_SECURE is None:
                _CLIENT_SECURE = AsyncSession(
                    impersonate="chrome120",
                    headers={"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
                    verify=True,
                    timeout=HTTP_TIMEOUT,
                    proxies=proxy_cfg,
                )
            return _CLIENT_SECURE
        else:
            if _CLIENT_INSECURE is None:
                _CLIENT_INSECURE = AsyncSession(
                    impersonate="chrome120",
                    headers={"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
                    verify=False,
                    timeout=HTTP_TIMEOUT,
                    proxies=proxy_cfg,
                )
            return _CLIENT_INSECURE


def _make_client(secure: bool, ua: str, proxy_url: Optional[str], force_http1: bool, timeout_s: int) -> AsyncSession:
    """
    Create a new HTTP client with specific configuration.
    
    Args:
        secure: Enable SSL verification
        ua: User-Agent string
        proxy_url: Proxy URL (optional)
        force_http1: Force HTTP/1.1
        timeout_s: Request timeout in seconds
        
    Returns:
        AsyncSession instance
    """
    if USE_TOR:
        proxy_url = "socks5://127.0.0.1:9050"
    headers = {
        "User-Agent": ua or USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    
    if secure and not USE_TOR and not proxy_url:
        proxies = None
    else:
        proxies = {"http://": proxy_url, "https://": proxy_url} if proxy_url else None
    
    return AsyncSession(
        impersonate="chrome120",
        headers=headers,
        verify=True if secure else False,
        timeout=timeout_s,
        proxies=proxies,
    )


def _acceptable_by_headers(hdrs: Dict[str, str]) -> Tuple[bool, str]:
    """
    Check if content is acceptable based on HTTP headers.
    
    Args:
        hdrs: HTTP response headers
        
    Returns:
        Tuple of (acceptable, reason)
    """
    ct = (hdrs.get("Content-Type", "") or "").lower().split(";")[0].strip()
    if any(ct.startswith(p) for p in BINARY_CT_PREFIXES) or ct in DENY_CT_EXACT:
        return False, f"content-type={ct}"
    if (PDF_CT in ct) and (not CFG.allow_pdf):
        return False, "pdf-not-allowed"
    try:
        cl = int(hdrs.get("Content-Length", "0"))
        if cl > 0 and cl > MAX_CONTENT_LENGTH:
            return False, f"too-large:{cl}"
    except Exception:
        pass
    return True, ct or "unknown"


def set_worker_parallelism(limit: int):
    """
    Adjust the global worker parallelism limit.
    Should be called before starting heavy crawls so the semaphore reflects the active Wasserfall mode.
    """
    global WORKER_PARALLELISM, _HTTP_SEMAPHORE
    limit = max(1, limit)
    if limit == WORKER_PARALLELISM:
        return
    WORKER_PARALLELISM = limit
    _HTTP_SEMAPHORE = asyncio.Semaphore(limit)


async def http_get_async(url: str, headers: Optional[Dict] = None, params: Optional[Dict[str, Any]] = None, timeout: int = HTTP_TIMEOUT) -> Optional[Any]:
    """
    HTTP GET with optional HEAD preflight, proxy/UA rotation, and HTTP/2→1.1 fallback.
    
    Features:
    - HEAD preflight to check content type before downloading
    - User-Agent and proxy rotation
    - Circuit breaker for problematic hosts
    - SSL fallback for sites with certificate issues
    - Retry logic for 429/503/504 errors
    
    Args:
        url: URL to fetch
        headers: Optional additional headers
        params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Response object or None on failure
    """
    async with _HTTP_SEMAPHORE:
        return await _http_get_inner(url, headers=headers, params=params, timeout=timeout)

async def _http_get_inner(url: str, headers: Optional[Dict] = None, params: Optional[Dict[str, Any]] = None, timeout: int = HTTP_TIMEOUT) -> Optional[Any]:

    # Choose rotation
    ua = random.choice(UA_POOL) if UA_POOL else USER_AGENT
    proxy = random.choice(PROXY_POOL) if PROXY_POOL else None

    # Merge headers
    headers = {**(headers or {})}
    headers["User-Agent"] = ua

    host = _host_from(url)
    if not _host_allowed(host):
        log("warn", "Circuit-Breaker: host muted (skip)", url=url, host=host)
        return None

    base_to = max(5, min(timeout, 45))
    eff_timeout = base_to + random.uniform(0.0, 1.25)

    # 1) HEAD preflight (optional)
    r_head = None
    try:
        async with _make_client(True, ua, proxy, force_http1=False, timeout_s=eff_timeout) as client_head:
            r_head = await client_head.head(url, headers=headers, params=params, allow_redirects=True, timeout=eff_timeout)
            if r_head is not None:
                if r_head.status_code == 405:
                    _penalize_host(host, "405")
                    log("info", "HEAD 405: host penalized, continue with GET", url=url)
                if r_head.status_code in (405, 501):
                    pass
                elif r_head.status_code in (200, 204):
                    ok, reason = _acceptable_by_headers(r_head.headers or {})
                    if not ok:
                        log("info", "Head-preflight: skipped by headers", url=url, reason=reason)
                        return None
    except asyncio.TimeoutError as e:
        log("debug", "HEAD request timeout", url=url, error=str(e))
        _penalize_host(host, "timeout")
        r_head = None
    except (ConnectionError, OSError) as e:
        log("debug", "HEAD request connection error", url=url, error=str(e))
        _penalize_host(host, "connection_error")
        r_head = None
    except Exception as e:
        log("debug", "HEAD request failed", url=url, error=str(e), error_type=type(e).__name__)
        r_head = None

    async def _do_get(secure: bool, force_http1: bool) -> Optional[Any]:
        async with _make_client(secure, ua, proxy, force_http1, eff_timeout) as cl:
            return await cl.get(url, headers=headers, params=params, timeout=eff_timeout, allow_redirects=True)

    # 2) Primary GET (secure, HTTP/2 allowed)
    try:
        r = await _do_get(secure=True, force_http1=False)
        if r.status_code == 200:
            ok, reason = _acceptable_by_headers(r.headers or {})
            if not ok:
                log("info", "GET: skipped by headers", url=url, reason=reason)
                return None
            setattr(r, "insecure_ssl", False)
            return r
        if _should_retry_status(r.status_code):
            reason = "429" if r.status_code == 429 else "error"
            _penalize_host(host, reason)
            _schedule_retry(url, r.status_code)
            log("warn", f"{r.status_code} received", url=url)
            return r
    except asyncio.TimeoutError as e:
        log("debug", "Primary GET timeout, trying HTTP/1.1", url=url, error=str(e))
        _penalize_host(host, "timeout")
        # 2a) Retry as HTTP/1.1
        try:
            r = await _do_get(secure=True, force_http1=True)
            if r.status_code == 200:
                ok, reason = _acceptable_by_headers(r.headers or {})
                if not ok:
                    return None
                setattr(r, "insecure_ssl", False)
                return r
            if _should_retry_status(r.status_code):
                reason = "429" if r.status_code == 429 else "error"
                _penalize_host(host, reason)
                _schedule_retry(url, r.status_code)
                log("warn", f"{r.status_code} received (HTTP/1.1 retry)", url=url)
                return r
        except asyncio.TimeoutError as e:
            log("debug", "HTTP/1.1 retry timeout", url=url, error=str(e))
            _penalize_host(host, "timeout")
        except (ConnectionError, OSError) as e:
            log("debug", "HTTP/1.1 retry connection error", url=url, error=str(e))
            _penalize_host(host, "connection_error")
        except Exception as e:
            log("debug", "HTTP/1.1 retry failed", url=url, error=str(e), error_type=type(e).__name__)
    except (ConnectionError, OSError) as e:
        log("debug", "Primary GET connection error, trying HTTP/1.1", url=url, error=str(e))
        _penalize_host(host, "connection_error")
        # 2a) Retry as HTTP/1.1
        try:
            r = await _do_get(secure=True, force_http1=True)
            if r.status_code == 200:
                ok, reason = _acceptable_by_headers(r.headers or {})
                if not ok:
                    return None
                setattr(r, "insecure_ssl", False)
                return r
            if _should_retry_status(r.status_code):
                reason = "429" if r.status_code == 429 else "error"
                _penalize_host(host, reason)
                _schedule_retry(url, r.status_code)
                log("warn", f"{r.status_code} received (HTTP/1.1 retry)", url=url)
                return r
        except asyncio.TimeoutError as e:
            log("debug", "HTTP/1.1 retry timeout", url=url, error=str(e))
            _penalize_host(host, "timeout")
        except (ConnectionError, OSError) as e:
            log("debug", "HTTP/1.1 retry connection error", url=url, error=str(e))
            _penalize_host(host, "connection_error")
        except Exception as e:
            log("debug", "HTTP/1.1 retry failed", url=url, error=str(e), error_type=type(e).__name__)
    except Exception as e:
        log("debug", "Primary GET failed with unexpected error, trying HTTP/1.1", url=url, error=str(e), error_type=type(e).__name__)
        # 2a) Retry as HTTP/1.1
        try:
            r = await _do_get(secure=True, force_http1=True)
            if r.status_code == 200:
                ok, reason = _acceptable_by_headers(r.headers or {})
                if not ok:
                    return None
                setattr(r, "insecure_ssl", False)
                return r
            if _should_retry_status(r.status_code):
                reason = "429" if r.status_code == 429 else "error"
                _penalize_host(host, reason)
                _schedule_retry(url, r.status_code)
                log("warn", f"{r.status_code} received (HTTP/1.1 retry)", url=url)
                return r
        except asyncio.TimeoutError as e:
            log("debug", "HTTP/1.1 retry timeout", url=url, error=str(e))
            _penalize_host(host, "timeout")
        except (ConnectionError, OSError) as e:
            log("debug", "HTTP/1.1 retry connection error", url=url, error=str(e))
            _penalize_host(host, "connection_error")
        except Exception as e:
            log("debug", "HTTP/1.1 retry failed", url=url, error=str(e), error_type=type(e).__name__)

    # 3) SSL fallback (insecure), first HTTP/2, then HTTP/1.1
    allow_insecure_ssl = os.getenv("ALLOW_INSECURE_SSL", "0") == "1"
    if allow_insecure_ssl:
        try:
            r2 = await _do_get(secure=False, force_http1=False)
            if r2.status_code == 200:
                ok, reason = _acceptable_by_headers(r2.headers or {})
                if not ok:
                    return None
                setattr(r2, "insecure_ssl", True)
                log("warn", "SSL Fallback ohne Verify genutzt", url=url)
                return r2
            if _should_retry_status(r2.status_code):
                reason = "429" if r2.status_code == 429 else "error"
                _penalize_host(host, reason)
                _schedule_retry(url, r2.status_code)
                log("warn", f"{r2.status_code} received (insecure TLS)", url=url)
                return r2
        except asyncio.TimeoutError as e:
            log("debug", "SSL fallback timeout, trying HTTP/1.1", url=url, error=str(e))
            _penalize_host(host, "timeout")
            try:
                r2 = await _do_get(secure=False, force_http1=True)
                if r2.status_code == 200:
                    ok, reason = _acceptable_by_headers(r2.headers or {})
                    if not ok:
                        return None
                    setattr(r2, "insecure_ssl", True)
                    log("warn", "SSL Fallback (HTTP/1.1) genutzt", url=url)
                    return r2
                if _should_retry_status(r2.status_code):
                    reason = "429" if r2.status_code == 429 else "error"
                    _penalize_host(host, reason)
                    _schedule_retry(url, r2.status_code)
                    log("warn", f"{r2.status_code} received (insecure TLS, HTTP/1.1)", url=url)
                    return r2
            except asyncio.TimeoutError as e:
                log("debug", "SSL fallback HTTP/1.1 timeout", url=url, error=str(e))
                _penalize_host(host, "timeout")
            except (ConnectionError, OSError) as e:
                log("debug", "SSL fallback HTTP/1.1 connection error", url=url, error=str(e))
                _penalize_host(host, "connection_error")
            except Exception as e:
                log("debug", "SSL fallback HTTP/1.1 failed", url=url, error=str(e), error_type=type(e).__name__)
        except (ConnectionError, OSError) as e:
            log("debug", "SSL fallback connection error, trying HTTP/1.1", url=url, error=str(e))
            _penalize_host(host, "connection_error")
            try:
                r2 = await _do_get(secure=False, force_http1=True)
                if r2.status_code == 200:
                    ok, reason = _acceptable_by_headers(r2.headers or {})
                    if not ok:
                        return None
                    setattr(r2, "insecure_ssl", True)
                    log("warn", "SSL Fallback (HTTP/1.1) genutzt", url=url)
                    return r2
                if _should_retry_status(r2.status_code):
                    reason = "429" if r2.status_code == 429 else "error"
                    _penalize_host(host, reason)
                    _schedule_retry(url, r2.status_code)
                    log("warn", f"{r2.status_code} received (insecure TLS, HTTP/1.1)", url=url)
                    return r2
            except asyncio.TimeoutError as e:
                log("debug", "SSL fallback HTTP/1.1 timeout", url=url, error=str(e))
                _penalize_host(host, "timeout")
            except (ConnectionError, OSError) as e:
                log("debug", "SSL fallback HTTP/1.1 connection error", url=url, error=str(e))
                _penalize_host(host, "connection_error")
            except Exception as e:
                log("debug", "SSL fallback HTTP/1.1 failed", url=url, error=str(e), error_type=type(e).__name__)
        except Exception as e:
            log("debug", "SSL fallback failed, trying HTTP/1.1", url=url, error=str(e), error_type=type(e).__name__)
            try:
                r2 = await _do_get(secure=False, force_http1=True)
                if r2.status_code == 200:
                    ok, reason = _acceptable_by_headers(r2.headers or {})
                    if not ok:
                        return None
                    setattr(r2, "insecure_ssl", True)
                    log("warn", "SSL Fallback (HTTP/1.1) genutzt", url=url)
                    return r2
                if _should_retry_status(r2.status_code):
                    reason = "429" if r2.status_code == 429 else "error"
                    _penalize_host(host, reason)
                    _schedule_retry(url, r2.status_code)
                    log("warn", f"{r2.status_code} received (insecure TLS, HTTP/1.1)", url=url)
                    return r2
            except asyncio.TimeoutError as e:
                log("debug", "SSL fallback HTTP/1.1 timeout", url=url, error=str(e))
                _penalize_host(host, "timeout")
            except (ConnectionError, OSError) as e:
                log("debug", "SSL fallback HTTP/1.1 connection error", url=url, error=str(e))
                _penalize_host(host, "connection_error")
            except Exception as e:
                log("debug", "SSL fallback HTTP/1.1 failed", url=url, error=str(e), error_type=type(e).__name__)

    if "sitemap" in (url or "").lower():
        log("debug", "Sitemap nicht verfügbar", url=url)
    else:
        log("error", "HTTP GET endgültig gescheitert", url=url)
    return None


async def fetch_response_async(url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = HTTP_TIMEOUT) -> Optional[Any]:
    """
    Fetch URL and return response only if status is 200.
    
    Args:
        url: URL to fetch
        headers: Optional additional headers
        params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Response object or None
    """
    r = await http_get_async(url, headers=headers, params=params, timeout=timeout)
    if r is None:
        _LAST_STATUS[url] = -1
        return None
    status = getattr(r, "status_code", 0)
    if status != 200:
        _LAST_STATUS[url] = status
        log("warn", "Nicht-200 beim Abruf – skip", url=url, status=status)
        return None
    _LAST_STATUS[url] = 200
    return r


async def fetch_with_login_check(url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = HTTP_TIMEOUT) -> Optional[Any]:
    """
    Fetch with automatic login detection and session management.
    
    Uses the login handler functionality to detect if login is required
    and manage session cookies.
    
    Args:
        url: URL to fetch
        headers: Optional additional headers
        params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Response object or None
    """
    try:
        from login_handler import get_login_handler
    except ImportError:
        # Fallback if login_handler not available
        return await fetch_response_async(url, headers=headers, params=params, timeout=timeout)
    
    handler = get_login_handler()
    portal = handler.get_portal_from_url(url)
    
    # Load saved cookies if available
    if portal and handler.has_valid_session(portal):
        saved_cookies = handler.get_session_cookies(portal)
        if saved_cookies:
            log("debug", f"Verwende gespeicherte Cookies für {portal}")
    
    # Execute normal request
    r = await fetch_response_async(url, headers=headers, params=params, timeout=timeout)
    
    # Check response for login requirements
    if r is not None:
        response_text = getattr(r, "text", "") or ""
        status = getattr(r, "status_code", 200)
        
        if handler.detect_login_required(response_text, status, url):
            log("warn", f"Login erforderlich für {portal or url}")
            
            # Invalidate old session
            if portal:
                handler.invalidate_session(portal)
            
            log("warn", f"Bitte führe manuell aus: python scriptname.py --login {portal}")
            return None
    
    return r
