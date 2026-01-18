"""
MeineStadt Crawler Module
=========================
Crawler for MeineStadt.de job listings.

This module handles crawling and extraction from MeineStadt.de,
a German city-based classifieds portal, good for local candidates.
"""

import asyncio
import urllib.parse
from typing import Any, Dict, List

from bs4 import BeautifulSoup


async def crawl_meinestadt_listings_async(
    urls: List[str],
    http_get_func=None,
    url_seen_func=None,
    mark_url_seen_func=None,
    extract_generic_detail_func=None,
    log_func=None,
    jitter_func=None,
    DIRECT_CRAWL_SOURCES=None,
    HTTP_TIMEOUT=30,
) -> List[Dict]:
    """
    Crawlt meinestadt.de Stellengesuche-Seiten.
    Städte-basiert, gut für lokale Kandidaten.
    
    Args:
        urls: List of base URLs to crawl
        http_get_func: Function to fetch HTTP content
        url_seen_func: Function to check if URL was already seen
        mark_url_seen_func: Function to mark URL as seen
        extract_generic_detail_func: Generic detail extraction function
        log_func: Logging function
        jitter_func: Function to add random jitter to delays
        DIRECT_CRAWL_SOURCES: Config for which sources to crawl
        HTTP_TIMEOUT: HTTP request timeout
        
    Returns:
        Liste von Lead-Dicts
    """
    if DIRECT_CRAWL_SOURCES and not DIRECT_CRAWL_SOURCES.get("meinestadt", True):
        return []
    
    leads = []
    max_pages = 3
    
    for base_url in urls:
        for page in range(1, max_pages + 1):
            if page == 1:
                url = base_url
            else:
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page}"
            
            try:
                jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                await asyncio.sleep(3.0 + jitter)
                
                if log_func:
                    log_func("info", "Meinestadt: Listing-Seite", url=url, page=page)
                
                r = await http_get_func(url, timeout=HTTP_TIMEOUT)
                if not r or r.status_code != 200:
                    if log_func:
                        log_func("warn", "Meinestadt: Failed to fetch", url=url, status=r.status_code if r else "None")
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
                
                if log_func:
                    log_func("info", "Meinestadt: Anzeigen gefunden", url=url, count=len(ad_links))
                
                if not ad_links:
                    break
                
                for ad_url in ad_links:
                    if url_seen_func and url_seen_func(ad_url):
                        continue
                    
                    jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                    await asyncio.sleep(3.0 + jitter)
                    
                    lead = await extract_generic_detail_func(ad_url, source_tag="meinestadt")
                    if lead and lead.get("telefon"):
                        leads.append(lead)
                        if log_func:
                            log_func("info", "Meinestadt: Lead extrahiert", url=ad_url, has_phone=True)
                        
                        if mark_url_seen_func:
                            mark_url_seen_func(ad_url, source="Meinestadt")
                    else:
                        if log_func:
                            log_func("debug", "Meinestadt: Keine Handynummer", url=ad_url)
                
            except Exception as e:
                if log_func:
                    log_func("error", "Meinestadt: Fehler beim Crawlen", url=url, error=str(e))
                break
    
    if log_func:
        log_func("info", "Meinestadt: Crawling abgeschlossen", total_leads=len(leads))
    return leads
