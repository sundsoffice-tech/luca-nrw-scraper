# -*- coding: utf-8 -*-
"""
Kleinanzeigen.de search integration for job seeker lead generation.
"""

import re
import urllib.parse
from typing import Dict, List

from bs4 import BeautifulSoup

from luca_scraper.config import ENABLE_KLEINANZEIGEN, KLEINANZEIGEN_MAX_RESULTS, HTTP_TIMEOUT

# Import manager utilities
from .manager import _normalize_for_dedupe, _extract_url

# Try to import from scriptname.py, fallback if not available
try:
    from scriptname import http_get_async, is_denied, log
except ImportError:
    async def http_get_async(url, headers=None, params=None, timeout=None):
        """Fallback http_get_async when running as standalone module."""
        return None
    
    def is_denied(url: str) -> bool:
        """Fallback is_denied when running as standalone module."""
        return False
    
    def log(level: str, msg: str, **ctx):
        """Fallback log function when running as standalone module."""
        pass


def _ka_keywords_from_query(q: str) -> str:
    if not q:
        return ""
    cleaned = re.sub(r"site:[^\s]+", " ", q, flags=re.I)
    cleaned = re.sub(r"[()\"']", " ", cleaned)
    cleaned = re.sub(r"\b(OR|AND)\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:120]


async def kleinanzeigen_search_async(q: str, max_results: int = KLEINANZEIGEN_MAX_RESULTS) -> List[Dict[str, str]]:
    if (not ENABLE_KLEINANZEIGEN) or max_results <= 0:
        return []

    keywords = _ka_keywords_from_query(q)
    if not keywords:
        return []

    url = "https://www.kleinanzeigen.de/s-stellengesuche/k0"
    try:
        r = await http_get_async(
            url,
            params={
                "keywords": keywords,
                "locationStr": "NRW",
            },
            timeout=HTTP_TIMEOUT
        )
    except Exception as e:
        log("warn", "Kleinanzeigen-Suche fehlgeschlagen", q=keywords, err=str(e))
        return []
    if not r:
        return []
    if r.status_code != 200:
        log("warn", "Kleinanzeigen Status != 200", status=r.status_code, q=keywords)
        return []

    html = r.text or ""
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, str]] = []
    for art in soup.select("li.ad-listitem article.aditem"):
        href = art.get("data-href") or ""
        if not href:
            a_tag = art.find("a", href=True)
            if a_tag:
                href = a_tag.get("href", "")
        if not href:
            continue
        full = urllib.parse.urljoin("https://www.kleinanzeigen.de", href)
        title_el = art.select_one("h2 a")
        desc_el = art.select_one(".aditem-main--middle--description")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        snippet = desc_el.get_text(" ", strip=True) if desc_el else ""
        items.append({"url": full, "title": title, "snippet": snippet})
        if len(items) >= max_results:
            break

    uniq: List[Dict[str, str]] = []
    seen = set()
    for entry in items:
        u = _extract_url(entry)
        if not u:
            continue
        nu = _normalize_for_dedupe(u)
        if nu in seen:
            continue
        seen.add(nu)
        if is_denied(nu):
            continue
        uniq.append({**entry, "url": nu})

    if uniq:
        log("info", "Kleinanzeigen Treffer", q=keywords, count=len(uniq))
    return uniq
