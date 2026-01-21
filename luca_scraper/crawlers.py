"""
Crawler-Funktionen für verschiedene Portale
"""
import asyncio
import re
from typing import List, Dict, Callable, Optional, Any
from bs4 import BeautifulSoup

# ============================================
# KLEINANZEIGEN CRAWLER
# ============================================

async def crawl_kleinanzeigen_listings_async(
    listing_url: str,
    max_pages: int = 5,
    http_get_func: Callable = None,
    log_func:  Callable = None,
    normalize_func: Callable = None,
    ENABLE_KLEINANZEIGEN: bool = True,
    HTTP_TIMEOUT: int = 25,
    PORTAL_DELAYS: Dict = None,
    jitter_func: Callable = None,
) -> List[str]:
    """
    Crawlt Kleinanzeigen Listing-Seiten und extrahiert Detail-URLs. 
    """
    if not ENABLE_KLEINANZEIGEN:
        return []
    
    if log_func:
        log_func("debug", f"Crawling Kleinanzeigen: {listing_url}")
    
    detail_urls = []
    
    for page in range(1, max_pages + 1):
        # Pagination
        if page == 1:
            url = listing_url
        else:
            if "seite:" in listing_url:
                url = re.sub(r'seite:\d+', f'seite:{page}', listing_url)
            else:
                url = f"{listing_url}/seite:{page}"
        
        try:
            # Jitter delay
            if jitter_func and PORTAL_DELAYS:
                delay = PORTAL_DELAYS.get("kleinanzeigen", 2.0)
                await asyncio.sleep(jitter_func(delay))
            
            # HTTP Request
            if http_get_func:
                html = await http_get_func(url, timeout=HTTP_TIMEOUT)
                if not html:
                    break
                
                # Parse HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # Finde Anzeigen-Links
                found_on_page = 0
                for link in soup. select('a[href*="/s-anzeige/"]'):
                    href = link.get('href', '')
                    if href and '/s-anzeige/' in href:
                        full_url = f"https://www.kleinanzeigen.de{href}" if href.startswith('/') else href
                        
                        # Normalize und dedupe
                        if normalize_func:
                            full_url = normalize_func(full_url)
                        
                        if full_url not in detail_urls:
                            detail_urls.append(full_url)
                            found_on_page += 1
                
                if log_func:
                    log_func("debug", f"Kleinanzeigen Seite {page}: {found_on_page} URLs gefunden")
                
                # Keine Ergebnisse = Ende
                if found_on_page == 0:
                    break
                    
        except Exception as e:
            if log_func:
                log_func("warn", f"Kleinanzeigen crawl error: {e}")
            break
    
    if log_func:
        log_func("info", f"Kleinanzeigen:  {len(detail_urls)} Detail-URLs gesammelt", url=listing_url)
    
    return detail_urls


async def extract_kleinanzeigen_detail_async(
    detail_url: str,
    http_get_func: Callable = None,
    log_func:  Callable = None,
    HTTP_TIMEOUT: int = 25,
) -> Optional[Dict]:
    """
    Extrahiert Lead-Daten von einer Kleinanzeigen Detail-Seite.
    """
    try:
        if http_get_func:
            html = await http_get_func(detail_url, timeout=HTTP_TIMEOUT)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html. parser')
            
            # Extrahiere Daten
            data = {
                'url': detail_url,
                'source': 'kleinanzeigen',
            }
            
            # Titel
            title_el = soup.select_one('h1#viewad-title')
            if title_el: 
                data['title'] = title_el.get_text(strip=True)
            
            # Beschreibung
            desc_el = soup.select_one('#viewad-description-text')
            if desc_el:
                data['description'] = desc_el.get_text(strip=True)
            
            # Name
            name_el = soup. select_one('. userprofile-vip a, .iconlist--text')
            if name_el: 
                data['name'] = name_el.get_text(strip=True)
            
            # Ort
            loc_el = soup.select_one('#viewad-locality')
            if loc_el: 
                data['location'] = loc_el.get_text(strip=True)
            
            return data
            
    except Exception as e:
        if log_func:
            log_func("debug", f"Kleinanzeigen detail error: {e}")
    
    return None


async def crawl_kleinanzeigen_portal_async(
    urls: List[str],
    http_get_func: Callable = None,
    log_func:  Callable = None,
    **kwargs
) -> List[Dict]:
    """
    Crawlt mehrere Kleinanzeigen URLs. 
    """
    results = []
    for url in urls:
        detail_urls = await crawl_kleinanzeigen_listings_async(
            listing_url=url,
            http_get_func=http_get_func,
            log_func=log_func,
            **kwargs
        )
        for detail_url in detail_urls: 
            data = await extract_kleinanzeigen_detail_async(
                detail_url=detail_url,
                http_get_func=http_get_func,
                log_func=log_func,
            )
            if data:
                results.append(data)
    return results


# ============================================
# ANDERE PORTAL CRAWLER (Stubs)
# ============================================

async def crawl_markt_de_listings_async(*args, **kwargs) -> List[str]:
    """Markt.de crawler - Stub"""
    return []

async def crawl_quoka_listings_async(*args, **kwargs) -> List[str]:
    """Quoka crawler - Stub"""
    return []

async def crawl_kalaydo_listings_async(*args, **kwargs) -> List[str]:
    """Kalaydo crawler - Stub"""
    return []

async def crawl_meinestadt_listings_async(*args, **kwargs) -> List[str]:
    """MeineStadt crawler - Stub"""
    return []

async def extract_generic_detail_async(*args, **kwargs) -> Optional[Dict]:
    """Generic detail extractor - Stub"""
    return None

def _mark_url_seen(url: str, db_path: str = None) -> bool:
    """Mark URL as seen - Stub"""
    return True


# Export all
__all__ = [
    'crawl_kleinanzeigen_listings_async',
    'extract_kleinanzeigen_detail_async', 
    'crawl_kleinanzeigen_portal_async',
    'crawl_markt_de_listings_async',
    'crawl_quoka_listings_async',
    'crawl_kalaydo_listings_async',
    'crawl_meinestadt_listings_async',
    'extract_generic_detail_async',
    '_mark_url_seen',
]
