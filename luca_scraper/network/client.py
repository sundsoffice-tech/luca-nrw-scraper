# -*- coding: utf-8 -*-
"""
HTTP client configuration and setup for async network requests.
Provides client factory functions with proxy and security settings.
"""

import os
from typing import Dict, Optional, Tuple

from curl_cffi.requests import AsyncSession

from luca_scraper.config import (
    USER_AGENT,
    HTTP_TIMEOUT,
    USE_TOR,
)

# Content-Type filtering
BINARY_CT_PREFIXES = [
    "image/", "video/", "audio/", "application/zip", "application/x-rar",
    "application/x-7z", "application/x-tar", "application/x-gzip",
    "application/octet-stream",
]
DENY_CT_EXACT = {"application/json", "application/ld+json", "application/xml", "text/xml"}
PDF_CT = "application/pdf"
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))

# Global client instances
_CLIENT_SECURE: Optional[AsyncSession] = None
_CLIENT_INSECURE: Optional[AsyncSession] = None


async def get_client(secure: bool = True) -> AsyncSession:
    """
    Get or create an async HTTP client with browser impersonation.
    
    Args:
        secure: If True, verify SSL certificates
        
    Returns:
        AsyncSession configured for the specified security level
    """
    global _CLIENT_SECURE, _CLIENT_INSECURE
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


def _make_client(secure: bool, ua: str, proxy_url: Optional[str], force_http1: bool, timeout_s: int):
    """
    Create a new async HTTP client with custom settings.
    
    Args:
        secure: If True, verify SSL certificates
        ua: User-Agent string
        proxy_url: Proxy URL (optional)
        force_http1: If True, force HTTP/1.1
        timeout_s: Request timeout in seconds
        
    Returns:
        New AsyncSession instance
    """
    # === TASK 2: Harden proxy handling for normal HTTP requests ===
    if USE_TOR:
        proxy_url = "socks5://127.0.0.1:9050"
    headers = {
        "User-Agent": ua or USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    
    # When secure=True and NOT using Tor, explicitly disable proxies
    # to prevent environment variable lookup that causes ConnectTimeout
    if secure and not USE_TOR and not proxy_url:
        proxies = None  # Explicitly None to bypass all proxy lookups
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
    Check if response headers indicate acceptable content.
    
    Args:
        hdrs: Response headers dictionary
        
    Returns:
        Tuple of (is_acceptable, content_type_or_reason)
    """
    ct = (hdrs.get("Content-Type", "") or "").lower().split(";")[0].strip()
    if any(ct.startswith(p) for p in BINARY_CT_PREFIXES) or ct in DENY_CT_EXACT:
        return False, f"content-type={ct}"
    
    from luca_scraper.config import ALLOW_PDF
    if (PDF_CT in ct) and (not ALLOW_PDF):
        return False, "pdf-not-allowed"
    try:
        cl = int(hdrs.get("Content-Length", "0"))
        if cl > 0 and cl > MAX_CONTENT_LENGTH:
            return False, f"too-large:{cl}"
    except Exception:
        pass
    return True, ct or "unknown"
