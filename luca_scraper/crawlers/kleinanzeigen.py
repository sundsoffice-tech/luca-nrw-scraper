"""
Kleinanzeigen Crawler Module
=============================
Crawler for Kleinanzeigen.de job listings.

This module handles crawling and extraction from Kleinanzeigen (formerly eBay Kleinanzeigen),
a major German classifieds platform.
"""

import asyncio
import re
import urllib.parse
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from luca_scraper.extraction.lead_builder import build_lead_data


async def crawl_kleinanzeigen_listings_async(
    listing_url: str,
    max_pages: int = 5,
    http_get_func=None,
    log_func=None,
    normalize_func=None,
    ENABLE_KLEINANZEIGEN=True,
    HTTP_TIMEOUT=30,
    PORTAL_DELAYS=None,
    jitter_func=None,
) -> List[str]:
    """
    Crawl Kleinanzeigen listing pages directly (not via Google) and extract all ad links.
    Supports pagination (page 1, 2, 3...).
    
    Args:
        listing_url: Base URL for the listing (e.g., https://www.kleinanzeigen.de/s-stellengesuche/...)
        max_pages: Maximum number of pages to crawl (default: 5)
        http_get_func: Function to fetch HTTP content
        log_func: Logging function
        normalize_func: URL normalization function for deduplication
        ENABLE_KLEINANZEIGEN: Feature flag
        HTTP_TIMEOUT: HTTP request timeout
        PORTAL_DELAYS: Portal-specific delays config
        jitter_func: Function to add random jitter to delays
        
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
                delay = PORTAL_DELAYS.get("kleinanzeigen", 3.0) if PORTAL_DELAYS else 3.0
                jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                await asyncio.sleep(delay + jitter)
            
            if log_func:
                log_func("info", "Crawling Kleinanzeigen listing", url=url, page=page_num)
            
            r = await http_get_func(url, timeout=HTTP_TIMEOUT)
            if not r or r.status_code != 200:
                if log_func:
                    log_func("warn", "Failed to fetch listing page", url=url, status=r.status_code if r else "None")
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
                norm_url = normalize_func(full_url) if normalize_func else full_url
                
                if norm_url in seen_urls:
                    continue
                
                seen_urls.add(norm_url)
                ad_links.append(full_url)
                page_links += 1
            
            if log_func:
                log_func("info", "Extracted ad links from page", page=page_num, count=page_links)
            
            # If no links found, we've reached the end
            if page_links == 0:
                if log_func:
                    log_func("info", "No more ads found, stopping pagination", page=page_num)
                break
                
        except Exception as e:
            if log_func:
                log_func("error", "Error crawling listing page", url=url, error=str(e))
            break
    
    if log_func:
        log_func("info", "Completed Kleinanzeigen listing crawl", total_ads=len(ad_links), pages=page_num)
    return ad_links


async def extract_kleinanzeigen_detail_async(
    url: str,
    http_get_func=None,
    log_func=None,
    normalize_phone_func=None,
    validate_phone_func=None,
    is_mobile_number_func=None,
    extract_all_phone_patterns_func=None,
    get_best_phone_number_func=None,
    extract_whatsapp_number_func=None,
    extract_phone_with_browser_func=None,
    extract_name_enhanced_func=None,
    learning_engine=None,
    HTTP_TIMEOUT=30,
    EMAIL_RE=None,
    MOBILE_RE=None,
) -> Optional[Dict[str, Any]]:
    """
    Crawl individual Kleinanzeigen ad detail page and extract contact information.
    
    Args:
        url: URL of the ad detail page
        http_get_func: Function to fetch HTTP content
        log_func: Logging function
        normalize_phone_func: Phone normalization function
        validate_phone_func: Phone validation function
        is_mobile_number_func: Function to check if number is mobile
        extract_all_phone_patterns_func: Advanced phone pattern extraction
        get_best_phone_number_func: Function to get best phone from results
        extract_whatsapp_number_func: WhatsApp number extraction
        extract_phone_with_browser_func: Browser-based extraction fallback
        extract_name_enhanced_func: Enhanced name extraction
        learning_engine: Optional learning engine instance
        HTTP_TIMEOUT: HTTP request timeout
        EMAIL_RE: Email regex pattern
        MOBILE_RE: Mobile phone regex pattern
        
    Returns:
        Dict with lead data or None if extraction failed
    """
    try:
        r = await http_get_func(url, timeout=HTTP_TIMEOUT)
        if not r or r.status_code != 200:
            if log_func:
                log_func("debug", "Failed to fetch detail page", url=url, status=r.status_code if r else "None")
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
        
        # ========================================
        # PARALLEL PHONE EXTRACTION
        # Run both regex and advanced extraction simultaneously, merge results
        # ========================================
        phones = []
        phone_sources = {}  # Track where each phone was found for scoring
        
        # 1. Standard regex extraction (runs in parallel with advanced)
        if MOBILE_RE:
            phone_matches = MOBILE_RE.findall(full_text)
            for phone_match in phone_matches:
                normalized = normalize_phone_func(phone_match)
                if normalized:
                    is_valid, phone_type = validate_phone_func(normalized)
                    if is_valid and is_mobile_number_func(normalized):
                        if normalized not in phones:
                            phones.append(normalized)
                            phone_sources[normalized] = "regex_standard"
        
        # 2. Advanced pattern extraction (runs in parallel, not as fallback)
        if extract_all_phone_patterns_func and get_best_phone_number_func:
            try:
                extraction_results = extract_all_phone_patterns_func(html, full_text)
                # Process all results from advanced extraction, not just best
                for category, numbers in extraction_results.items():
                    if isinstance(numbers, list):
                        for num in numbers:
                            normalized = normalize_phone_func(num) if num else None
                            if normalized and is_mobile_number_func(normalized):
                                if normalized not in phones:
                                    phones.append(normalized)
                                    phone_sources[normalized] = f"advanced_{category}"
                                    if log_func:
                                        log_func("info", f"Kleinanzeigen: Advanced extraction ({category}) found phone", 
                                            url=url, phone=normalized[:8]+"...")
                
                # Also get best phone if not already included
                best_phone = get_best_phone_number_func(extraction_results)
                if best_phone:
                    normalized = normalize_phone_func(best_phone)
                    if normalized and is_mobile_number_func(normalized):
                        if normalized not in phones:
                            phones.append(normalized)
                            phone_sources[normalized] = "advanced_best"
                        if learning_engine:
                            learning_engine.record_phone_pattern(
                                pattern="advanced_extraction",
                                pattern_type="enhanced",
                                example=normalized[:8]+"..."
                            )
                        # Learn phone pattern for AI Learning Engine
                        try:
                            from ai_learning_engine import ActiveLearningEngine
                            learning = ActiveLearningEngine()
                            learning.learn_phone_pattern(best_phone, normalized, "kleinanzeigen")
                        except Exception:
                            pass  # Learning is optional
            except Exception as e:
                if log_func:
                    log_func("debug", "Advanced phone extraction failed", error=str(e))
        
        # Extract email
        email = ""
        if EMAIL_RE:
            email_matches = EMAIL_RE.findall(full_text)
            if email_matches:
                email = email_matches[0]
        
        # 3. WhatsApp extraction (parallel with other methods)
        whatsapp = ""
        if extract_whatsapp_number_func:
            try:
                wa_number = extract_whatsapp_number_func(html)
                if wa_number:
                    normalized_wa = normalize_phone_func(wa_number)
                    if normalized_wa and is_mobile_number_func(normalized_wa):
                        whatsapp = normalized_wa
                        if normalized_wa not in phones:
                            phones.append(normalized_wa)
                            phone_sources[normalized_wa] = "whatsapp_enhanced"
                            if log_func:
                                log_func("info", "WhatsApp link extraction found phone", 
                                    url=url, phone=normalized_wa[:8]+"...")
            except Exception:
                pass
        
        # 4. Fallback WhatsApp link extraction
        if not whatsapp:
            wa_link = soup.select_one('a[href*="wa.me"], a[href*="api.whatsapp.com"]')
            if wa_link:
                wa_href = wa_link.get("href", "")
                wa_phone = re.sub(r'\D', '', wa_href)
                if wa_phone:
                    wa_normalized = "+" + wa_phone
                    is_valid, phone_type = validate_phone_func(wa_normalized)
                    if is_valid and is_mobile_number_func(wa_normalized):
                        whatsapp = wa_normalized
                        if wa_normalized not in phones:
                            phones.append(wa_normalized)
                            phone_sources[wa_normalized] = "whatsapp_link"
        
        # Extract location/region
        location_elem = soup.select_one("#viewad-locality, .boxedarticle--details--locality")
        location = location_elem.get_text(" ", strip=True) if location_elem else ""
        
        # Extract name (from title or text)
        name = ""
        if extract_name_enhanced_func:
            name = extract_name_enhanced_func(full_text)
        
        # 5. Browser extraction as last resort (only if no phones found)
        if not phones:
            if log_func:
                log_func("debug", "No mobile numbers found in ad, trying browser extraction", url=url)
            if extract_phone_with_browser_func:
                try:
                    browser_phone = extract_phone_with_browser_func(url, portal='kleinanzeigen')
                    if browser_phone:
                        phones.append(browser_phone)
                        phone_sources[browser_phone] = "browser_extraction"
                        if log_func:
                            log_func("info", "Browser extraction successful", url=url)
                except Exception as e:
                    if log_func:
                        log_func("debug", "Browser extraction failed", url=url, error=str(e))
            
            # If still no phones found, return None
            if not phones:
                if learning_engine:
                    learning_engine.learn_from_failure(
                        url=url,
                        html_content=html,
                        reason="no_mobile_number_found",
                        visible_phones=[]
                    )
                return None
        
        # Build lead data using centralized function
        lead = build_lead_data(
            name=name,
            phones=phones,
            email=email,
            location=location,
            title=title,
            url=url,
            phone_sources=phone_sources,
            portal="kleinanzeigen",
            has_whatsapp=bool(whatsapp),
            tags="kleinanzeigen,candidate,mobile,direct_crawl",
        )
        
        if log_func:
            log_func("info", "Extracted lead from Kleinanzeigen ad", 
                     url=url, has_phone=bool(lead["telefon"]), has_email=bool(email), 
                     score=lead["score"], confidence=lead["confidence"])
        return lead
        
    except Exception as e:
        if log_func:
            log_func("error", "Error extracting Kleinanzeigen detail", url=url, error=str(e))
        return None


async def crawl_kleinanzeigen_portal_async(
    crawl_urls: List[str],
    http_get_func=None,
    url_seen_func=None,
    mark_url_seen_func=None,
    log_func=None,
    jitter_func=None,
    DIRECT_CRAWL_SOURCES=None,
    ENABLE_KLEINANZEIGEN=True,
    **extract_kwargs
) -> List[Dict]:
    """
    Wrapper function to crawl Kleinanzeigen that matches the pattern of other portals.
    Crawls all configured URLs and returns list of lead dicts.
    
    Args:
        crawl_urls: List of listing URLs to crawl
        http_get_func: Function to fetch HTTP content
        url_seen_func: Function to check if URL was already seen
        mark_url_seen_func: Function to mark URL as seen
        log_func: Logging function
        jitter_func: Function to add random jitter to delays
        DIRECT_CRAWL_SOURCES: Config for which sources to crawl
        ENABLE_KLEINANZEIGEN: Feature flag
        **extract_kwargs: Additional kwargs for extraction functions
        
    Returns:
        List of lead dicts extracted from Kleinanzeigen
    """
    if DIRECT_CRAWL_SOURCES and not DIRECT_CRAWL_SOURCES.get("kleinanzeigen", True):
        return []
    
    if not ENABLE_KLEINANZEIGEN:
        return []
    
    leads = []
    
    for crawl_url in crawl_urls:
        try:
            if log_func:
                log_func("info", "Kleinanzeigen: Crawling listing", url=crawl_url)
            
            # Step 1: Get ad links from listing page
            ad_links = await crawl_kleinanzeigen_listings_async(
                crawl_url,
                max_pages=5,
                http_get_func=http_get_func,
                log_func=log_func,
                **extract_kwargs
            )
            
            if not ad_links:
                if log_func:
                    log_func("info", "Kleinanzeigen: No ads found", url=crawl_url)
                continue
            
            if log_func:
                log_func("info", "Kleinanzeigen: Ads found", url=crawl_url, count=len(ad_links))
            
            # Step 2: Extract details from each ad
            for i, ad_url in enumerate(ad_links):
                if url_seen_func and url_seen_func(ad_url):
                    if log_func:
                        log_func("debug", "Kleinanzeigen: URL already seen (skip)", url=ad_url)
                    continue
                
                # Rate limiting between detail page fetches
                if i > 0:
                    jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
                    await asyncio.sleep(2.5 + jitter)
                
                # Extract lead data from ad detail page
                lead_data = await extract_kleinanzeigen_detail_async(
                    ad_url,
                    http_get_func=http_get_func,
                    log_func=log_func,
                    **extract_kwargs
                )
                
                if lead_data:
                    leads.append(lead_data)
                    # Mark URL as seen
                    if mark_url_seen_func:
                        mark_url_seen_func(ad_url, source="Kleinanzeigen")
                else:
                    if log_func:
                        log_func("debug", "Kleinanzeigen: No valid lead data", url=ad_url)
            
            # Rate limiting between listing pages
            jitter = jitter_func(0.5, 1.0) if jitter_func else 0.5
            await asyncio.sleep(3.0 + jitter)
            
        except Exception as e:
            if log_func:
                log_func("error", "Kleinanzeigen: Error crawling", url=crawl_url, error=str(e))
    
    if log_func:
        log_func("info", "Kleinanzeigen: Crawling completed", total_leads=len(leads))
    return leads
