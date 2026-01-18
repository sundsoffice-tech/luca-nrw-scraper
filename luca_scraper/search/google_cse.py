# -*- coding: utf-8 -*-
"""
Google Custom Search Engine (CSE) integration for lead generation.
"""

import asyncio
import os
import re
from typing import Dict, List, Optional, Tuple

from luca_scraper.config import HTTP_TIMEOUT

# Import manager utilities
from .manager import _jitter, _normalize_for_dedupe, _normalize_cx, prioritize_urls

# Try to import from scriptname.py, fallback if not available
try:
    from scriptname import http_get_async, is_denied, path_ok, log
except ImportError:
    async def http_get_async(url, headers=None, params=None, timeout=None):
        """Fallback http_get_async when running as standalone module."""
        return None
    
    def is_denied(url: str) -> bool:
        """Fallback is_denied when running as standalone module."""
        return False
    
    def path_ok(url: str) -> bool:
        """Fallback path_ok when running as standalone module."""
        return True
    
    def log(level: str, msg: str, **ctx):
        """Fallback log function when running as standalone module."""
        pass

# Try to import connection error classes
try:
    from aiohttp.client_exceptions import ClientConnectorError, ServerDisconnectedError
except Exception:
    class _NetErr(Exception): ...
    ClientConnectorError = ServerDisconnectedError = _NetErr

try:
    from httpx import ReadError
except Exception:
    class _DDGTimeout(Exception): ...
    ReadError = _DDGTimeout

# Google CSE API configuration
GCS_API_KEY = os.getenv("GCS_API_KEY", "")
GCS_CX_RAW = os.getenv("GCS_CX", "")
GCS_CX = _normalize_cx(GCS_CX_RAW)

# Multi-Key/CX Rotation
GCS_KEYS = [k.strip() for k in os.getenv("GCS_KEYS","").split(",") if k.strip()] or ([GCS_API_KEY] if GCS_API_KEY else [])
GCS_CXS  = [_normalize_cx(x) for x in os.getenv("GCS_CXS","").split(",") if _normalize_cx(x)] or ([GCS_CX] if GCS_CX else [])


async def google_cse_search_async(q: str, max_results: int = 60, date_restrict: Optional[str] = None) -> Tuple[List[Dict[str, str]], bool]:
    if os.getenv("DISABLE_GOOGLE") == "1" or not (GCS_KEYS and GCS_CXS):
        log("info","Google CSE disabled; skipping"); return [], False

    def _preview(txt: Optional[str]) -> str:
        if not txt: return ""
        # HTML-Tags & übermäßige Whitespaces entfernen, dann hart bei 200 cutten
        txt = re.sub(r"<[^>]+>", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt[:200]

    url = "https://www.googleapis.com/customsearch/v1"
    results: List[Dict[str, str]] = []
    page_no, key_i, cx_i = 0, 0, 0
    had_429 = False
    page_cap = int(os.getenv("MAX_GOOGLE_PAGES","2"))  # Default: 2 pages (20 results) for cost control
    while len(results) < max_results and page_no < page_cap:
        params = {
            "key": GCS_KEYS[key_i], "cx": GCS_CXS[cx_i], "q": q,
            "num": min(10, max_results - len(results)),
            "start": 1 + page_no*10, "lr":"lang_de", "safe":"off",
        }
        if date_restrict:
            params["dateRestrict"] = date_restrict

        try:
            r = await http_get_async(url, headers=None, params=params, timeout=HTTP_TIMEOUT)
        except (ReadError, ClientConnectorError, ServerDisconnectedError) as e:
            log("warn", "Google CSE Netzfehler, retry", error=str(e))
            await asyncio.sleep(3)
            continue
        except Exception as e:
            log("warn", "Google CSE Fehler", error=str(e))
            await asyncio.sleep(3)
            continue
        if not r:
            key_i = (key_i + 1) % max(1,len(GCS_KEYS))
            cx_i  = (cx_i  + 1) % max(1,len(GCS_CXS))
            sleep_s = 4 + int(4*_jitter())
            await asyncio.sleep(sleep_s)
            continue

        if r.status_code == 429:
            had_429 = True
            log("warn","Google 429 – skip this query without retry")
            return [], had_429

        if r.status_code != 200:
            log("error","Google CSE Status != 200", status=r.status_code, body=_preview(r.text))
            break

        try:
            data = r.json()
        except Exception:
            log("error","Google CSE JSON-Parsing fehlgeschlagen", text=_preview(r.text))
            break

        items = data.get("items", []) or []
        batch = [
            {
                "url": it.get("link"),
                "title": it.get("title", "") or "",
                "snippet": it.get("snippet", "") or "",
            }
            for it in items
            if it.get("link")
        ]
        results.extend(batch)
        log("info","Google CSE Batch", q=q, batch=len(batch), total=len(results), page_no=page_no)

        if not batch: break
        page_no += 1
        await asyncio.sleep(0.5 + _jitter(0,0.6))

    uniq_items: List[Dict[str, str]] = []
    seen = set()
    for entry in results:
        raw_url = entry.get("url", "")
        if not raw_url:
            continue
        nu = _normalize_for_dedupe(raw_url)
        if nu in seen: continue
        seen.add(nu)
        if is_denied(nu): continue
        if not path_ok(nu): continue
        uniq_items.append({
            "url": nu,
            "title": entry.get("title", "") or "",
            "snippet": entry.get("snippet", "") or "",
        })
    if uniq_items:
        ordered = prioritize_urls([item["url"] for item in uniq_items])
        order_map = {u: i for i, u in enumerate(ordered)}
        uniq_items.sort(key=lambda item: order_map.get(item["url"], len(order_map)))
    return uniq_items, had_429
