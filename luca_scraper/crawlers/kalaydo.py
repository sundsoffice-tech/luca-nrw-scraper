# -*- coding: utf-8 -*-
"""Kalaydo.de crawler functions"""

import asyncio
import urllib.parse
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

# Import from luca_scraper modules
from luca_scraper.config import (
    KALAYDO_DE_URLS, HTTP_TIMEOUT,
    DIRECT_CRAWL_SOURCES
)
from luca_scraper.database import url_seen

# Try importing from scriptname.py with fallback
try:
    from scriptname import (
        http_get_async, log, _jitter
    )
except ImportError:
    async def http_get_async(url, **kwargs):
        raise ImportError("http_get_async not available")
    
    def log(level, msg, **ctx):
        print(f"[{level.upper()}] {msg}", ctx)
    
    def _jitter(a=0.2, b=0.8):
        import random
        return a + random.random() * (b - a)

# Import base utilities
from .base import _mark_url_seen

# Import generic extractor
from .generic import extract_generic_detail_async


async def crawl_kalaydo_listings_async() -> List[Dict]:
    """
    Crawlt kalaydo.de Stellengesuche-Seiten.
    Kalaydo ist besonders stark im Rheinland/NRW!
    
    Returns:
        Liste von Lead-Dicts
    """
    if not DIRECT_CRAWL_SOURCES.get("kalaydo", True):
        return []
    
    leads = []
    max_pages = 3
    
    for base_url in KALAYDO_DE_URLS:
        for page in range(1, max_pages + 1):
            if page == 1:
                url = base_url
            else:
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page}"
            
            try:
                await asyncio.sleep(3.0 + _jitter(0.5, 1.0))
                
                log("info", "Kalaydo: Listing-Seite", url=url, page=page)
                
                r = await http_get_async(url, timeout=HTTP_TIMEOUT)
                if not r or r.status_code != 200:
                    log("warn", "Kalaydo: Failed to fetch", url=url, status=r.status_code if r else "None")
                    break
                
                html = r.text or ""
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract ad links
                ad_links = []
                
                for selector in [
                    'article.classified-ad a',
                    'a[href*="/anzeige/"]',
                    'a[href*="/stellengesuche/"]',
                    '.ad-item a'
                ]:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get("href", "")
                        if href and ("/anzeige/" in href or "/stellengesuche/" in href):
                            full_url = urllib.parse.urljoin("https://www.kalaydo.de", href)
                            if full_url not in ad_links:
                                ad_links.append(full_url)
                
                log("info", "Kalaydo: Anzeigen gefunden", url=url, count=len(ad_links))
                
                if not ad_links:
                    break
                
                for ad_url in ad_links:
                    if url_seen(ad_url):
                        continue
                    
                    await asyncio.sleep(3.0 + _jitter(0.5, 1.0))
                    
                    lead = await extract_generic_detail_async(ad_url, source_tag="kalaydo")
                    if lead and lead.get("telefon"):
                        leads.append(lead)
                        log("info", "Kalaydo: Lead extrahiert", url=ad_url, has_phone=True)
                        
                        _mark_url_seen(ad_url, source="Kalaydo")
                    else:
                        log("debug", "Kalaydo: Keine Handynummer", url=ad_url)
                
            except Exception as e:
                log("error", "Kalaydo: Fehler beim Crawlen", url=url, error=str(e))
                break
    
    log("info", "Kalaydo: Crawling abgeschlossen", total_leads=len(leads))
    return leads
