"""
Markt.de Crawler Module
=======================
Crawler for Markt.de job listings.

This module handles crawling and extraction from Markt.de,
a German classifieds portal for local classified ads.
"""

import asyncio
import urllib.parse
from typing import Any, Dict, List

from bs4 import BeautifulSoup


async def crawl_markt_de_listings_async(
    urls: List[str],
    http_get_func=None,
    url_seen_func=None,
    mark_url_seen_func=None,
    extract_generic_detail_func=None,
    log_func=None,
    jitter_func=None,
    learning_engine=None,
    DIRECT_CRAWL_SOURCES=None,
    HTTP_TIMEOUT=30,
    PORTAL_DELAYS=None,
) -> List[Dict]:
    """
    Crawlt markt.de Stellengesuche-Seiten.
    
    HTML-Struktur (typisch):
    - Listing: <div class="ad-list-item"> oder <article class="result-item">
    - Link: <a href="/anzeige/...">
    - Titel: <h2> oder <h3>
    
    Pagination: ?page=2, ?page=3, etc.
    
    Args:
        urls: List of base URLs to crawl
        http_get_func: Function to fetch HTTP content
        url_seen_func: Function to check if URL was already seen
        mark_url_seen_func: Function to mark URL as seen
        extract_generic_detail_func: Generic detail extraction function
        log_func: Logging function
        jitter_func: Function to add random jitter to delays
        learning_engine: Optional learning engine instance
        DIRECT_CRAWL_SOURCES: Config for which sources to crawl
        HTTP_TIMEOUT: HTTP request timeout
        PORTAL_DELAYS: Portal-specific delays config
        
    Returns:
        Liste von Lead-Dicts
    """
    if DIRECT_CRAWL_SOURCES and not DIRECT_CRAWL_SOURCES.get("markt_de", True):
        return []
    
    leads = []
    max_pages = 3  # Limit pages per URL to avoid overload
    
    for base_url in urls:
        for page in range(1, max_pages + 1):
            if page == 1:
                url = base_url
            else:
                # Add page parameter
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page}"
            
            try:
                # Use configured delay for markt_de portal
                delay = PORTAL_DELAYS.get("markt_de", 3.0) if PORTAL_DELAYS else 3.0
                jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                await asyncio.sleep(delay + jitter)
                
                if log_func:
                    log_func("info", "Markt.de: Listing-Seite", url=url, page=page)
                
                r = await http_get_func(url, timeout=HTTP_TIMEOUT)
                if not r or r.status_code != 200:
                    if log_func:
                        log_func("warn", "Markt.de: Failed to fetch", url=url, status=r.status_code if r else "None")
                    if learning_engine:
                        learning_engine.update_domain_performance(
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
                
                if log_func:
                    log_func("info", "Markt.de: Anzeigen gefunden", url=url, count=len(ad_links))
                
                if not ad_links:
                    break  # No more ads, stop pagination
                
                # Extract details from each ad
                for ad_url in ad_links:
                    if url_seen_func and url_seen_func(ad_url):
                        continue
                    
                    # Rate limiting
                    jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                    await asyncio.sleep(3.0 + jitter)
                    
                    lead = await extract_generic_detail_func(ad_url, source_tag="markt_de")
                    if lead and lead.get("telefon"):
                        leads.append(lead)
                        if log_func:
                            log_func("info", "Markt.de: Lead extrahiert", url=ad_url, has_phone=True)
                        
                        # Mark as seen
                        if mark_url_seen_func:
                            mark_url_seen_func(ad_url, source="Markt.de")
                    else:
                        if log_func:
                            log_func("debug", "Markt.de: Keine Handynummer", url=ad_url)
                
            except Exception as e:
                if log_func:
                    log_func("error", "Markt.de: Fehler beim Crawlen", url=url, error=str(e))
                break
    
    if log_func:
        log_func("info", "Markt.de: Crawling abgeschlossen", total_leads=len(leads))
    return leads
