"""
Generic Detail Extractor Module
================================
Generic functions for extracting contact information from ad detail pages.

This module provides generic extraction logic that can be used across multiple
portal crawlers.
"""

import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from luca_scraper.extraction.phone_email_extraction import (
    extract_phone_numbers,
    extract_email_address,
    extract_whatsapp_number,
)


async def extract_generic_detail_async(
    url: str,
    source_tag: str = "direct_crawl",
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
    Generic function to extract contact information from any ad detail page.
    Similar to extract_kleinanzeigen_detail_async but works for multiple sites.
    
    Args:
        url: URL of the ad detail page
        source_tag: Tag to identify the source (e.g., "markt_de", "quoka")
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
                log_func("debug", f"{source_tag}: Failed to fetch detail", url=url, status=r.status_code if r else "None")
            return None
        
        html = r.text or ""
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title - try multiple selectors
        title = ""
        for selector in ["h1", "h1.title", ".ad-title", ".listing-title"]:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(" ", strip=True)
                break
        
        # Extract description - get all text from body
        description = soup.get_text(" ", strip=True)
        
        # Combine text for extraction
        full_text = f"{title} {description}"
        
        # ========================================
        # PHONE EXTRACTION - Using centralized extraction module
        # ========================================
        phones, phone_sources = extract_phone_numbers(
            html=html,
            text=full_text,
            normalize_phone_func=normalize_phone_func,
            validate_phone_func=validate_phone_func,
            is_mobile_number_func=is_mobile_number_func,
            MOBILE_RE=MOBILE_RE,
            extract_all_phone_patterns_func=extract_all_phone_patterns_func,
            get_best_phone_number_func=get_best_phone_number_func,
            learning_engine=learning_engine,
            portal_tag=source_tag,
            log_func=log_func,
        )
        
        # EMAIL EXTRACTION - Using centralized extraction module
        email = extract_email_address(
            text=full_text,
            EMAIL_RE=EMAIL_RE,
        )
        
        # WHATSAPP EXTRACTION - Using centralized extraction module
        whatsapp, wa_sources = extract_whatsapp_number(
            html=html,
            normalize_phone_func=normalize_phone_func,
            validate_phone_func=validate_phone_func,
            is_mobile_number_func=is_mobile_number_func,
            extract_whatsapp_number_func=extract_whatsapp_number_func,
            portal_tag=source_tag,
            log_func=log_func,
        )
        
        # Merge WhatsApp results into phones list
        if whatsapp and whatsapp not in phones:
            phones.append(whatsapp)
            phone_sources.update(wa_sources)
        
        # Extract name
        name = ""
        if extract_name_enhanced_func:
            name = extract_name_enhanced_func(full_text)
        
        # 5. Browser extraction as last resort (only if no phones found)
        if not phones:
            if log_func:
                log_func("debug", f"{source_tag}: No mobile numbers found, trying browser extraction", url=url)
            if extract_phone_with_browser_func:
                try:
                    portal_map = {
                        'markt_de': 'markt_de',
                        'quoka': 'quoka',
                        'dhd24': 'dhd24',
                        'kalaydo': 'generic',
                        'meinestadt': 'generic',
                    }
                    portal = portal_map.get(source_tag, 'generic')
                    browser_phone = extract_phone_with_browser_func(url, portal=portal)
                    if browser_phone:
                        phones.append(browser_phone)
                        phone_sources[browser_phone] = "browser_extraction"
                        if log_func:
                            log_func("info", f"{source_tag}: Browser extraction successful", url=url)
                except Exception as e:
                    if log_func:
                        log_func("debug", f"{source_tag}: Browser extraction failed", url=url, error=str(e))
            
            # If still no phones found, return None
            if not phones:
                if learning_engine:
                    learning_engine.learn_from_failure(
                        url=url,
                        html_content=html,
                        reason=f"{source_tag}_no_mobile_found",
                        visible_phones=[]
                    )
                return None
        
        # Use first mobile number found
        main_phone = phones[0]
        
        # ========================================
        # DYNAMIC SCORING: Use centralized scoring module
        # ========================================
        phone_source = phone_sources.get(main_phone, "unknown")
        
        try:
            from luca_scraper.scoring.dynamic_scoring import calculate_dynamic_score
            dynamic_score, data_quality_score, confidence_score = calculate_dynamic_score(
                has_phone=bool(main_phone),
                has_email=bool(email),
                has_name=bool(name),
                has_title=bool(title),
                has_location=False,  # Generic crawler doesn't extract location
                phones_count=len(phones),
                has_whatsapp=False,  # Will be checked separately
                phone_source=phone_source,
                portal=source_tag,
            )
        except ImportError:
            # Fallback to default scores if module not available
            dynamic_score = 85
            data_quality_score = 0.80
            confidence_score = 0.85
        
        # Build lead data with dynamic scores
        lead = {
            "name": name or "",
            "rolle": "Vertrieb",
            "email": email,
            "telefon": main_phone,
            "quelle": url,
            "score": dynamic_score,
            "tags": f"{source_tag},candidate,mobile,direct_crawl",
            "lead_type": "candidate",
            "phone_type": "mobile",
            "opening_line": title[:200] if title else "",
            "firma": "",
            "firma_groesse": "",
            "branche": "",
            "region": "",
            "frische": "neu",
            "confidence": confidence_score,
            "data_quality": data_quality_score,
            "phone_source": phone_source,
            "phones_found": len(phones),
        }
        
        return lead
        
    except Exception as e:
        if log_func:
            log_func("error", f"{source_tag}: Error extracting detail", url=url, error=str(e))
        return None


def _mark_url_seen(url: str, source: str = "", db_func=None, log_func=None, seen_cache=None, normalize_func=None):
    """
    Helper function to mark a URL as seen in the database.
    
    Args:
        url: The URL to mark as seen
        source: Optional source name for logging (e.g., "Markt.de", "Quoka")
        db_func: Database connection function
        log_func: Logging function
        seen_cache: Cache set for seen URLs
        normalize_func: URL normalization function
    """
    try:
        con = db_func()
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO urls_seen (url) VALUES (?)", (url,))
        con.commit()
        con.close()
        if seen_cache is not None and normalize_func:
            seen_cache.add(normalize_func(url))
    except Exception as e:
        if log_func:
            log_prefix = f"{source}: " if source else ""
            log_func("warn", f"{log_prefix}Konnte URL nicht als gesehen markieren", url=url, error=str(e))
