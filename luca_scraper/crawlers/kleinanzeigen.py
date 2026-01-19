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
        
        # Use first mobile number found
        main_phone = phones[0]
        
        # ========================================
        # DYNAMIC SCORING: Calculate score based on data quality, completeness, and source
        # ========================================
        
        # Base score starts at 50 (Kleinanzeigen has higher base due to portal reputation)
        dynamic_score = 55
        data_quality_score = 0.0
        
        # Data completeness bonuses
        if main_phone:
            dynamic_score += 20
            data_quality_score += 0.30
        if email:
            dynamic_score += 15
            data_quality_score += 0.20
        if name:
            dynamic_score += 10
            data_quality_score += 0.15
        if title:
            dynamic_score += 5
            data_quality_score += 0.10
        if location:
            dynamic_score += 3
            data_quality_score += 0.05
        
        # Multiple phone numbers found = higher confidence
        if len(phones) > 1:
            dynamic_score += 5
            data_quality_score += 0.05
        
        # WhatsApp presence is a strong signal for candidates
        if whatsapp:
            dynamic_score += 8
            data_quality_score += 0.10
        
        # Phone source quality bonus
        phone_source = phone_sources.get(main_phone, "unknown")
        source_quality_map = {
            "regex_standard": 0.10,        # Standard regex is reliable
            "whatsapp_enhanced": 0.15,     # WhatsApp links are very reliable
            "whatsapp_link": 0.15,         # WhatsApp links are very reliable
            "advanced_whatsapp": 0.15,     # WhatsApp links are very reliable
            "advanced_standard": 0.08,     # Advanced patterns are good
            "advanced_spaced": 0.05,       # Spaced numbers are medium confidence
            "advanced_obfuscated": 0.03,   # Obfuscated are lower confidence
            "advanced_words": 0.02,        # Word-based are lowest
            "advanced_best": 0.08,
            "browser_extraction": 0.06,    # Browser extraction is reliable
        }
        source_bonus = source_quality_map.get(phone_source, 0.05)
        data_quality_score += source_bonus
        dynamic_score += int(source_bonus * 50)  # Scale to score points
        
        # Kleinanzeigen has high portal reputation for job seekers
        portal_reputation_bonus = 10
        dynamic_score += portal_reputation_bonus
        data_quality_score += 0.10
        
        # Cap scores to valid ranges
        dynamic_score = max(0, min(100, dynamic_score))
        data_quality_score = max(0.0, min(1.0, data_quality_score))
        
        # Calculate confidence based on extraction method and data completeness
        confidence_score = 0.55  # Higher base confidence for Kleinanzeigen
        if main_phone:
            confidence_score += 0.20
        if email:
            confidence_score += 0.10
        if name:
            confidence_score += 0.08
        if whatsapp:
            confidence_score += 0.07
        if phone_source.startswith("whatsapp"):
            confidence_score += 0.05
        elif phone_source == "regex_standard":
            confidence_score += 0.05
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Build lead data with dynamic scores
        lead = {
            "name": name or "",
            "rolle": "Vertrieb",
            "email": email,
            "telefon": main_phone,
            "quelle": url,
            "score": dynamic_score,
            "tags": "kleinanzeigen,candidate,mobile,direct_crawl",
            "lead_type": "candidate",
            "phone_type": "mobile",
            "opening_line": title[:200] if title else "",
            "firma": "",
            "firma_groesse": "",
            "branche": "",
            "region": location if location else "",
            "frische": "neu",
            "confidence": confidence_score,
            "data_quality": data_quality_score,
            "phone_source": phone_source,
            "phones_found": len(phones),
            "has_whatsapp": bool(whatsapp),
        }
        
        if log_func:
            log_func("info", "Extracted lead from Kleinanzeigen ad", 
                     url=url, has_phone=bool(main_phone), has_email=bool(email), 
                     score=dynamic_score, confidence=confidence_score)
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
