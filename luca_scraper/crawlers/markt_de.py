# -*- coding: utf-8 -*-
"""Markt.de crawler functions"""

import asyncio
import urllib.parse
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

# Import from luca_scraper modules
from luca_scraper.config import (
    MARKT_DE_URLS, PORTAL_DELAYS, HTTP_TIMEOUT,
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


async def crawl_markt_de_listings_async() -> List[Dict]:
    """
    Crawlt markt.de Stellengesuche-Seiten.
    
    HTML-Struktur (typisch):
    - Listing: <div class="ad-list-item"> oder <article class="result-item">
    - Link: <a href="/anzeige/...">
    - Titel: <h2> oder <h3>
    
    Pagination: ?page=2, ?page=3, etc.
    
    Returns:
        Liste von Lead-Dicts
    """
    if not DIRECT_CRAWL_SOURCES.get("markt_de", True):
        return []
    
    leads = []
    max_pages = 3  # Limit pages per URL to avoid overload
    
    for base_url in MARKT_DE_URLS:
        for page in range(1, max_pages + 1):
            if page == 1:
                url = base_url
            else:
                # Add page parameter
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page}"
            
            try:
                # Use configured delay for markt_de portal
                delay = PORTAL_DELAYS.get("markt_de", 3.0)
                await asyncio.sleep(delay + _jitter(0.5, 1.0))
                
                log("info", "Markt.de: Listing-Seite", url=url, page=page)
                
                r = await http_get_async(url, timeout=HTTP_TIMEOUT)
                if not r or r.status_code != 200:
                    log("warn", "Markt.de: Failed to fetch", url=url, status=r.status_code if r else "None")
                    if _LEARNING_ENGINE:
                        _LEARNING_ENGINE.update_domain_performance(
                            domain="markt.de",
                            success=False,
                            rate_limited=(r.status_code == 429 if r else False)
                        )
                    break
                
                html = r.text or ""
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract ad links - try multiple selectors
                ad_links = []
                
                # Try common selectors for markt.de
                for selector in [
                    'a[href*="/anzeige/"]',
                    'a[href*="/stellengesuche/"]',
                    '.ad-list-item a',
                    'article a[href*="/anzeige/"]'
                ]:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get("href", "")
                        if href and ("/anzeige/" in href or "/stellengesuche/" in href):
                            full_url = urllib.parse.urljoin("https://www.markt.de", href)
                            if full_url not in ad_links:
                                ad_links.append(full_url)
                
                log("info", "Markt.de: Anzeigen gefunden", url=url, count=len(ad_links))
                
                if not ad_links:
                    break  # No more ads, stop pagination
                
                # Extract details from each ad
                for ad_url in ad_links:
                    if url_seen(ad_url):
                        continue
                    
                    # Rate limiting
                    await asyncio.sleep(3.0 + _jitter(0.5, 1.0))
                    
                    lead = await extract_generic_detail_async(ad_url, source_tag="markt_de")
                    if lead and lead.get("telefon"):
                        leads.append(lead)
                        log("info", "Markt.de: Lead extrahiert", url=ad_url, has_phone=True)
                        
                        # Mark as seen
                        _mark_url_seen(ad_url, source="Markt.de")
                    else:
                        log("debug", "Markt.de: Keine Handynummer", url=ad_url)
                
            except Exception as e:
                log("error", "Markt.de: Fehler beim Crawlen", url=url, error=str(e))
                break
    
    log("info", "Markt.de: Crawling abgeschlossen", total_leads=len(leads))
    return leads
