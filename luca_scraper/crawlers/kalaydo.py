"""
Kalaydo Crawler Module
======================
Crawler for Kalaydo.de job listings.

This module handles crawling and extraction from Kalaydo.de,
a German classifieds portal particularly strong in Rheinland/NRW.
"""

import asyncio
import urllib.parse
from typing import Any, Dict, List

from bs4 import BeautifulSoup


async def crawl_kalaydo_listings_async(
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
    Crawlt kalaydo.de Stellengesuche-Seiten.
    Kalaydo ist besonders stark im Rheinland/NRW!
    
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
    if DIRECT_CRAWL_SOURCES and not DIRECT_CRAWL_SOURCES.get("kalaydo", True):
        return []
    
    leads = []
    max_pages = 3
    
    for base_url in urls:
        for page in range(1, max_pages + 1):
            seen_urls = []
            seen_local = set()
            if page == 1:
                url = base_url
            else:
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page}"
            
            try:
                jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                await asyncio.sleep(3.0 + jitter)
                
                if log_func:
                    log_func("info", "Kalaydo: Listing-Seite", url=url, page=page)
                
                r = await http_get_func(url, timeout=HTTP_TIMEOUT)
                if not r or r.status_code != 200:
                    if log_func:
                        log_func("warn", "Kalaydo: Failed to fetch", url=url, status=r.status_code if r else "None")
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
                
                if log_func:
                    log_func("info", "Kalaydo: Anzeigen gefunden", url=url, count=len(ad_links))
                
                if not ad_links:
                    break
                
                for ad_url in ad_links:
                    if url_seen_func and (url_seen_func(ad_url) or ad_url in seen_local):
                        continue
                    
                    jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                    await asyncio.sleep(3.0 + jitter)
                    
                    lead = await extract_generic_detail_func(ad_url, source_tag="kalaydo")
                    if lead and lead.get("telefon"):
                        leads.append(lead)
                        if log_func:
                            log_func("info", "Kalaydo: Lead extrahiert", url=ad_url, has_phone=True)

                        if mark_url_seen_func:
                            seen_urls.append(ad_url)
                            seen_local.add(ad_url)
                    else:
                        if log_func:
                            log_func("debug", "Kalaydo: Keine Handynummer", url=ad_url)
                
            except Exception as e:
                if log_func:
                    log_func("error", "Kalaydo: Fehler beim Crawlen", url=url, error=str(e))
                break
            finally:
                if mark_url_seen_func and seen_urls:
                    mark_url_seen_func(seen_urls, source="Kalaydo")
    
    if log_func:
        log_func("info", "Kalaydo: Crawling abgeschlossen", total_leads=len(leads))
    return leads
