# -*- coding: utf-8 -*-
"""Kleinanzeigen.de crawler functions"""

import asyncio
import re
import urllib.parse
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

# Import from luca_scraper modules
from luca_scraper.config import (
    ENABLE_KLEINANZEIGEN, PORTAL_DELAYS, HTTP_TIMEOUT,
    DIRECT_CRAWL_SOURCES, DIRECT_CRAWL_URLS
)
from luca_scraper.extraction.phone import normalize_phone, validate_phone
from luca_scraper.database import url_seen

# Try importing from scriptname.py with fallback
try:
    from scriptname import (
        http_get_async, log, _jitter, _normalize_for_dedupe,
        extract_name_enhanced, is_mobile_number,
        extract_all_phone_patterns, get_best_phone_number,
        extract_whatsapp_number, extract_phone_with_browser,
        _LEARNING_ENGINE, MOBILE_RE, EMAIL_RE
    )
except ImportError:
    # Fallback stubs
    async def http_get_async(url, **kwargs):
        raise ImportError("http_get_async not available")
    
    def log(level, msg, **ctx):
        print(f"[{level.upper()}] {msg}", ctx)
    
    def _jitter(a=0.2, b=0.8):
        import random
        return a + random.random() * (b - a)
    
    def _normalize_for_dedupe(u: str) -> str:
        return u
    
    def extract_name_enhanced(text: str) -> str:
        return ""
    
    def is_mobile_number(phone: str) -> bool:
        return phone.startswith(("+491", "+4915", "+4916", "+4917"))
    
    def extract_all_phone_patterns(html: str, text: str) -> list:
        return []
    
    def get_best_phone_number(results: list) -> Optional[str]:
        return None
    
    def extract_whatsapp_number(html: str) -> Optional[str]:
        return None
    
    def extract_phone_with_browser(url: str, portal: str = "") -> Optional[str]:
        return None
    
    _LEARNING_ENGINE = None
    MOBILE_RE = re.compile(r'(?:\+49|0049|0)\s*1[5-7]\d(?:[\s\/\-]?\d){6,10}')
    EMAIL_RE = re.compile(r'\b(?!noreply|no-reply|donotreply)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}\b', re.I)

# Import base utilities
from .base import _mark_url_seen


async def crawl_kleinanzeigen_listings_async(listing_url: str, max_pages: int = 5) -> List[str]:
    """
    Crawl Kleinanzeigen listing pages directly (not via Google) and extract all ad links.
    Supports pagination (page 1, 2, 3...).
    
    Args:
        listing_url: Base URL for the listing (e.g., https://www.kleinanzeigen.de/s-stellengesuche/...)
        max_pages: Maximum number of pages to crawl (default: 5)
        
    Returns:
        List of ad detail URLs
    """
    if not ENABLE_KLEINANZEIGEN:
        return []
    
    ad_links: List[str] = []
    seen_urls = set()
    page_num = 1  # Initialize before loop
    
    for page_num in range(1, max_pages + 1):
        # Build URL with page parameter, properly handling existing query params
        if page_num == 1:
            url = listing_url
        else:
            # Parse URL and add page parameter
            parsed = urllib.parse.urlparse(listing_url)
            params = urllib.parse.parse_qs(parsed.query)
            params['page'] = [str(page_num)]
            new_query = urllib.parse.urlencode(params, doseq=True)
            url = urllib.parse.urlunparse(parsed._replace(query=new_query))
        
        try:
            # Use configured delay for kleinanzeigen portal
            if page_num > 1:
                delay = PORTAL_DELAYS.get("kleinanzeigen", 3.0)
                await asyncio.sleep(delay + _jitter(0.5, 1.0))
            
            log("info", "Crawling Kleinanzeigen listing", url=url, page=page_num)
            
            r = await http_get_async(url, timeout=HTTP_TIMEOUT)
            if not r or r.status_code != 200:
                log("warn", "Failed to fetch listing page", url=url, status=r.status_code if r else "None")
                break
            
            html = r.text or ""
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract ad links from listing
            page_links = 0
            for art in soup.select("li.ad-listitem article.aditem"):
                # Try data-href first
                href = art.get("data-href") or ""
                if not href:
                    # Fallback to anchor tag
                    a_tag = art.find("a", href=True)
                    if a_tag:
                        href = a_tag.get("href", "")
                
                if not href or "/s-anzeige/" not in href:
                    continue
                
                # Build full URL using the base URL from the listing
                parsed_listing = urllib.parse.urlparse(listing_url)
                base_url = f"{parsed_listing.scheme}://{parsed_listing.netloc}"
                full_url = urllib.parse.urljoin(base_url, href)
                norm_url = _normalize_for_dedupe(full_url)
                
                if norm_url in seen_urls:
                    continue
                
                seen_urls.add(norm_url)
                ad_links.append(full_url)
                page_links += 1
            
            log("info", "Extracted ad links from page", page=page_num, count=page_links)
            
            # If no links found, we've reached the end
            if page_links == 0:
                log("info", "No more ads found, stopping pagination", page=page_num)
                break
                
        except Exception as e:
            log("error", "Error crawling listing page", url=url, error=str(e))
            break
    
    log("info", "Completed Kleinanzeigen listing crawl", total_ads=len(ad_links), pages=page_num)
    return ad_links


async def extract_kleinanzeigen_detail_async(url: str) -> Optional[Dict[str, Any]]:
    """
    Crawl individual Kleinanzeigen ad detail page and extract contact information.
    
    Args:
        url: URL of the ad detail page
        
    Returns:
        Dict with lead data or None if extraction failed
    """
    try:
        r = await http_get_async(url, timeout=HTTP_TIMEOUT)
        if not r or r.status_code != 200:
            log("debug", "Failed to fetch detail page", url=url, status=r.status_code if r else "None")
            return None
        
        html = r.text or ""
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title
        title_elem = soup.select_one("h1#viewad-title, h1.boxedarticle--title")
        title = title_elem.get_text(" ", strip=True) if title_elem else ""
        
        # Extract description
        desc_elem = soup.select_one("#viewad-description-text, .boxedarticle--description")
        description = desc_elem.get_text(" ", strip=True) if desc_elem else ""
        
        # Combine text for extraction
        full_text = f"{title} {description}"
        
        # Extract mobile phone numbers using advanced patterns
        phones = []
        
        # Standard extraction with existing regex
        phone_matches = MOBILE_RE.findall(full_text)
        for phone_match in phone_matches:
            normalized = normalize_phone(phone_match)
            if normalized:
                is_valid, phone_type = validate_phone(normalized)
                if is_valid and is_mobile_number(normalized):
                    phones.append(normalized)
        
        # Enhanced extraction using phone_patterns module
        if not phones:
            log("debug", "Standard extraction failed, trying advanced patterns", url=url)
            try:
                extraction_results = extract_all_phone_patterns(html, full_text)
                best_phone = get_best_phone_number(extraction_results)
                if best_phone:
                    normalized = normalize_phone(best_phone)
                    if normalized and is_mobile_number(normalized):
                        phones.append(normalized)
                        log("info", "Advanced pattern extraction found phone", 
                            url=url, phone=normalized[:8]+"...")
                        # Record this pattern success
                        if _LEARNING_ENGINE:
                            _LEARNING_ENGINE.record_phone_pattern(
                                pattern="advanced_extraction",
                                pattern_type="enhanced",
                                example=normalized[:8]+"..."
                            )
                        # NEW: Learn phone pattern for AI Learning Engine
                        try:
                            from ai_learning_engine import ActiveLearningEngine
                            learning = ActiveLearningEngine()
                            learning.learn_phone_pattern(best_phone, normalized, "kleinanzeigen")
                        except Exception:
                            pass  # Learning is optional
            except Exception as e:
                log("debug", "Advanced phone extraction failed", error=str(e))
        
        # Extract email
        email = ""
        email_matches = EMAIL_RE.findall(full_text)
        if email_matches:
            email = email_matches[0]
        
        # Extract WhatsApp link using enhanced extraction
        whatsapp = ""
        try:
            wa_number = extract_whatsapp_number(html)
            if wa_number:
                normalized_wa = normalize_phone(wa_number)
                if normalized_wa and is_mobile_number(normalized_wa):
                    whatsapp = normalized_wa
                    if normalized_wa not in phones:
                        phones.append(normalized_wa)
                        log("info", "WhatsApp link extraction found phone", 
                            url=url, phone=normalized_wa[:8]+"...")
        except Exception:
            pass
        
        # Fallback: Try old WhatsApp link extraction
        if not whatsapp:
            wa_link = soup.select_one('a[href*="wa.me"], a[href*="api.whatsapp.com"]')
            if wa_link:
                wa_href = wa_link.get("href", "")
                # Extract phone from WhatsApp link
                wa_phone = re.sub(r'\D', '', wa_href)
                if wa_phone:
                    wa_normalized = "+" + wa_phone
                    is_valid, phone_type = validate_phone(wa_normalized)
                    if is_valid and is_mobile_number(wa_normalized):
                        whatsapp = wa_normalized
                        if wa_normalized not in phones:
                            phones.append(wa_normalized)
        
        # Extract location/region
        location_elem = soup.select_one("#viewad-locality, .boxedarticle--details--locality")
        location = location_elem.get_text(" ", strip=True) if location_elem else ""
        
        # Extract name (from title or text)
        # Use the enhanced name extractor which handles various patterns
        name = extract_name_enhanced(full_text)
        
        # Only create lead if we found at least one mobile number
        if not phones:
            log("debug", "No mobile numbers found in ad, trying browser extraction", url=url)
            # Fallback: Browser-based extraction for JS-hidden numbers
            try:
                browser_phone = extract_phone_with_browser(url, portal='kleinanzeigen')
                if browser_phone:
                    phones.append(browser_phone)
                    log("info", "Browser extraction successful", url=url)
            except Exception as e:
                log("debug", "Browser extraction failed", url=url, error=str(e))
            
            # If still no phones found, return None
            if not phones:
                # Record failure for learning
                if _LEARNING_ENGINE:
                    _LEARNING_ENGINE.learn_from_failure(
                        url=url,
                        html_content=html,
                        reason="no_mobile_number_found",
                        visible_phones=[]
                    )
                return None
        
        # Use first mobile number found
        main_phone = phones[0]
        
        # Build lead data
        lead = {
            "name": name or "",
            "rolle": "Vertrieb",  # Default role
            "email": email,
            "telefon": main_phone,
            "quelle": url,
            "score": 85,  # High score for direct Kleinanzeigen finds
            "tags": "kleinanzeigen,candidate,mobile,direct_crawl",
            "lead_type": "candidate",
            "phone_type": "mobile",
            "opening_line": title[:200] if title else "",
            "firma": "",
            "firma_groesse": "",
            "branche": "",
            "region": location if location else "",
            "frische": "neu",
            "confidence": 0.85,
            "data_quality": 0.80,
        }
        
        log("info", "Extracted lead from Kleinanzeigen ad", url=url, has_phone=bool(main_phone), has_email=bool(email))
        return lead
        
    except Exception as e:
        log("error", "Error extracting Kleinanzeigen detail", url=url, error=str(e))
        return None


async def crawl_kleinanzeigen_portal_async() -> List[Dict]:
    """
    Wrapper function to crawl Kleinanzeigen that matches the pattern of other portals.
    Crawls all configured DIRECT_CRAWL_URLS and returns list of lead dicts.
    
    Returns:
        List of lead dicts extracted from Kleinanzeigen
    """
    if not DIRECT_CRAWL_SOURCES.get("kleinanzeigen", True):
        return []
    
    if not ENABLE_KLEINANZEIGEN:
        return []
    
    leads = []
    
    for crawl_url in DIRECT_CRAWL_URLS:
        try:
            log("info", "Kleinanzeigen: Crawling listing", url=crawl_url)
            
            # Step 1: Get ad links from listing page
            ad_links = await crawl_kleinanzeigen_listings_async(crawl_url, max_pages=5)
            
            if not ad_links:
                log("info", "Kleinanzeigen: No ads found", url=crawl_url)
                continue
            
            log("info", "Kleinanzeigen: Ads found", url=crawl_url, count=len(ad_links))
            
            # Step 2: Extract details from each ad
            for i, ad_url in enumerate(ad_links):
                if url_seen(ad_url):
                    log("debug", "Kleinanzeigen: URL already seen (skip)", url=ad_url)
                    continue
                
                # Rate limiting between detail page fetches
                if i > 0:
                    await asyncio.sleep(2.5 + _jitter(0.5, 1.0))
                
                # Extract lead data from ad detail page
                lead_data = await extract_kleinanzeigen_detail_async(ad_url)
                
                if lead_data:
                    leads.append(lead_data)
                    # Mark URL as seen
                    _mark_url_seen(ad_url, source="Kleinanzeigen")
                else:
                    log("debug", "Kleinanzeigen: No valid lead data", url=ad_url)
            
            # Rate limiting between listing pages
            await asyncio.sleep(3.0 + _jitter(0.5, 1.0))
            
        except Exception as e:
            log("error", "Kleinanzeigen: Error crawling", url=crawl_url, error=str(e))
            continue
    
    log("info", "Kleinanzeigen: Crawling complete", total_leads=len(leads))
    return leads
