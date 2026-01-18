# -*- coding: utf-8 -*-
"""
DuckDuckGo search integration for lead generation.
"""

import asyncio
import os
from typing import Dict, List, Optional

from luca_scraper.config import USE_TOR, PROXY_ENV_VARS

# Try to import DDGS
try:
    from ddgs import DDGS
    HAVE_DDG = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAVE_DDG = True
    except ImportError:
        HAVE_DDG = False
        DDGS = None

# Try to import from scriptname.py, fallback if not available
try:
    from scriptname import log
except ImportError:
    def log(level: str, msg: str, **ctx):
        """Fallback log function when running as standalone module."""
        pass


async def duckduckgo_search_async(query: str, max_results: int = 10, date_restrict: Optional[str] = None) -> List[Dict[str, str]]:
    """
    DuckDuckGo-Suche mit strenger Proxy-Steuerung, um ConnectTimeouts zu vermeiden.
    
    === TASK 3: Hardened proxy control ===
    Explicitly manages environment variables to force direct connection (USE_TOR=False)
    or TOR routing (USE_TOR=True) before DDGS initialization.
    """
    if not HAVE_DDG:
        log("warn", "DuckDuckGo-Modul fehlt.")
        return []

    results: List[Dict[str, str]] = []

    for attempt in range(1, 3):  # Attempts 1 and 2 (1 initial + 1 retry)
        try:
            # === CRITICAL: Set environment variables *inside* the try block ===
            # This ensures clean state on each retry attempt
            if USE_TOR:
                # Force TOR routing via SOCKS5 proxy
                os.environ["HTTP_PROXY"] = "socks5://127.0.0.1:9050"
                os.environ["HTTPS_PROXY"] = "socks5://127.0.0.1:9050"
                os.environ["ALL_PROXY"] = "socks5://127.0.0.1:9050"
                os.environ["http_proxy"] = "socks5://127.0.0.1:9050"
                os.environ["https_proxy"] = "socks5://127.0.0.1:9050"
                # Remove no_proxy to ensure proxy is used
                os.environ.pop("no_proxy", None)
                os.environ.pop("NO_PROXY", None)
                log("debug", "DuckDuckGo: TOR proxy configured", proxy="socks5://127.0.0.1:9050")
            else:
                # === Force direct connection by nuclear cleanup ===
                # Clear ALL proxy variables to prevent ConnectTimeout (WinError 10060)
                for key in PROXY_ENV_VARS:
                    os.environ.pop(key, None)
                
                # Explicitly set no_proxy (both case variants) to bypass any system-level proxy settings
                # This is the "nuclear option" to ensure ddgs/httpx/curl_cffi don't use any proxy
                os.environ["no_proxy"] = "*"
                os.environ["NO_PROXY"] = "*"
                log("debug", "DuckDuckGo: Direct connection configured (no_proxy='*', all proxies cleared)")
            
            # Initialize DDGS (Kurzes Timeout für "Fail Fast")
            with DDGS(timeout=10) as ddgs:
                gen = ddgs.text(
                    query,
                    region="de-de",
                    safesearch="off",
                    timelimit="y",
                    max_results=max_results
                )
                count = 0
                for r in gen:
                    if count >= max_results:
                        break
                    link = r.get("href")
                    title = r.get("title", "")
                    snippet = r.get("body", "")
                    if link:
                        results.append({
                            "link": link,
                            "title": title,
                            "snippet": snippet
                        })
                        count += 1

                if results:
                    log("info", "DuckDuckGo Treffer", q=query, count=len(results))
                else:
                    log("info", "DuckDuckGo: Keine Treffer (Seite leer)", q=query)
                    # Log query as weak after "No results" on first attempt
                    # Metrics system tracks this for adaptive dork selection
                    if attempt == 1:
                        log("debug", "DuckDuckGo: Query weak (no results)", q=query)
                return results

        except Exception as e:
            err_msg = str(e)
            if "ConnectTimeout" in err_msg or "WinError 10060" in err_msg:
                log("warn", "DuckDuckGo: Netzwerkproblem, überspringe", q=query)
                return []
            if attempt < 2:  # Retry on first attempt
                log("warn", f"DuckDuckGo Retry attempt {attempt} wegen Fehler", error=err_msg, q=query)
                await asyncio.sleep(3)
            else:
                log("warn", "DuckDuckGo endgültig gescheitert nach Retry", error=err_msg, q=query)
                # Log query as weak after failure - metrics system tracks this
                log("debug", "DuckDuckGo: Query weak (failed)", q=query)

    return []
