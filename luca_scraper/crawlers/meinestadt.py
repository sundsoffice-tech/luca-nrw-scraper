# -*- coding: utf-8 -*-
"""Meinestadt.de crawler functions"""

import asyncio
import urllib.parse
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

# Import from luca_scraper modules
from luca_scraper.config import (
    MEINESTADT_DE_URLS, HTTP_TIMEOUT,
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


async def crawl_meinestadt_listings_async() -> List[Dict]:
    """
    Crawlt meinestadt.de Stellengesuche-Seiten.
    Städte-basiert, gut für lokale Kandidaten.
    
    Returns:
        Liste von Lead-Dicts
    """
    if not DIRECT_CRAWL_SOURCES.get("meinestadt", True):
        return []
    
    leads = []
    max_pages = 3
    
    for base_url in MEINESTADT_DE_URLS:
        for page in range(1, max_pages + 1):
            if page == 1:
                url = base_url
            else:
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page}"
            
            try:
                await asyncio.sleep(3.0 + _jitter(0.5, 1.0))
                
                log("info", "Meinestadt: Listing-Seite", url=url, page=page)
                
                r = await http_get_async(url, timeout=HTTP_TIMEOUT)
                if not r or r.status_code != 200:
                    log("warn", "Meinestadt: Failed to fetch", url=url, status=r.status_code if r else "None")
                    break
                
                html = r.text or ""
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract ad links
                ad_links = []
                
                for selector in [
                    'a[href*="/stellengesuche/anzeige/"]',
                    'a[href*="/anzeige/"]',
                    '.job-listing a',
                    'article a'
                ]:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get("href", "")
                        if href and ("/stellengesuche/" in href or "/anzeige/" in href):
                            full_url = urllib.parse.urljoin("https://www.meinestadt.de", href)
                            if full_url not in ad_links:
                                ad_links.append(full_url)
                
                log("info", "Meinestadt: Anzeigen gefunden", url=url, count=len(ad_links))
                
                if not ad_links:
                    break
                
                for ad_url in ad_links:
                    if url_seen(ad_url):
                        continue
                    
                    await asyncio.sleep(3.0 + _jitter(0.5, 1.0))
                    
                    lead = await extract_generic_detail_async(ad_url, source_tag="meinestadt")
                    if lead and lead.get("telefon"):
                        leads.append(lead)
                        log("info", "Meinestadt: Lead extrahiert", url=ad_url, has_phone=True)
                        
                        _mark_url_seen(ad_url, source="Meinestadt")
                    else:
                        log("debug", "Meinestadt: Keine Handynummer", url=ad_url)
                
            except Exception as e:
                log("error", "Meinestadt: Fehler beim Crawlen", url=url, error=str(e))
                break
    
    log("info", "Meinestadt: Crawling abgeschlossen", total_leads=len(leads))
    return leads
