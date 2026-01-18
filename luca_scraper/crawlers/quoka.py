# -*- coding: utf-8 -*-
"""Quoka.de crawler functions"""

import asyncio
import urllib.parse
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

# Import from luca_scraper modules
from luca_scraper.config import (
    QUOKA_DE_URLS, PORTAL_DELAYS, HTTP_TIMEOUT,
    DIRECT_CRAWL_SOURCES
)
from luca_scraper.database import url_seen

# Try importing from scriptname.py with fallback
try:
    from scriptname import (
        http_get_async, log, _jitter,
        _LEARNING_ENGINE
    )
except ImportError:
    async def http_get_async(url, **kwargs):
        raise ImportError("http_get_async not available")
    
    def log(level, msg, **ctx):
        print(f"[{level.upper()}] {msg}", ctx)
    
    def _jitter(a=0.2, b=0.8):
        import random
        return a + random.random() * (b - a)
    
    _LEARNING_ENGINE = None

# Import base utilities
from .base import _mark_url_seen

# Import generic extractor
from .generic import extract_generic_detail_async


async def crawl_quoka_listings_async() -> List[Dict]:
    """
    Crawlt quoka.de Stellengesuche-Seiten.
    
    HTML-Struktur:
    - Listing: <li class="q-ad"> oder <div class="result-list-item">
    - Link: <a href="/stellengesuche/...">
    
    Returns:
        Liste von Lead-Dicts
    """
    if not DIRECT_CRAWL_SOURCES.get("quoka", True):
        return []
    
    leads = []
    max_pages = 3
    
    for base_url in QUOKA_DE_URLS:
        for page in range(1, max_pages + 1):
            if page == 1:
                url = base_url
            else:
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page}"
            
            try:
                # Use configured delay for quoka portal
                delay = PORTAL_DELAYS.get("quoka", 3.0)
                await asyncio.sleep(delay + _jitter(0.5, 1.0))
                
                log("info", "Quoka: Listing-Seite", url=url, page=page)
                
                r = await http_get_async(url, timeout=HTTP_TIMEOUT)
                if not r or r.status_code != 200:
                    log("warn", "Quoka: Failed to fetch", url=url, status=r.status_code if r else "None")
                    # Record failure for learning
                    if _LEARNING_ENGINE:
                        _LEARNING_ENGINE.update_domain_performance(
                            domain="quoka.de",
                            success=False,
                            rate_limited=(r.status_code == 429 if r else False)
                        )
                    break
                
                html = r.text or ""
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract ad links
                ad_links = []
                
                for selector in [
                    'a.q-ad-link',
                    'li.q-ad a',
                    'a[href*="/stellengesuche/"]',
                    '.result-list-item a'
                ]:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get("href", "")
                        if href and "/stellengesuche/" in href:
                            full_url = urllib.parse.urljoin("https://www.quoka.de", href)
                            if full_url not in ad_links:
                                ad_links.append(full_url)
                
                log("info", "Quoka: Anzeigen gefunden", url=url, count=len(ad_links))
                
                if not ad_links:
                    break
                
                for ad_url in ad_links:
                    if url_seen(ad_url):
                        continue
                    
                    await asyncio.sleep(3.0 + _jitter(0.5, 1.0))
                    
                    lead = await extract_generic_detail_async(ad_url, source_tag="quoka")
                    if lead and lead.get("telefon"):
                        leads.append(lead)
                        log("info", "Quoka: Lead extrahiert", url=ad_url, has_phone=True)
                        
                        _mark_url_seen(ad_url, source="Quoka")
                    else:
                        log("debug", "Quoka: Keine Handynummer", url=ad_url)
                
            except Exception as e:
                log("error", "Quoka: Fehler beim Crawlen", url=url, error=str(e))
                break
    
    log("info", "Quoka: Crawling abgeschlossen", total_leads=len(leads))
    return leads
