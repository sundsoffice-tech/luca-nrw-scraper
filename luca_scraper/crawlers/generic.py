# -*- coding: utf-8 -*-
"""Generic detail extractor for classified ads"""

import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

# Import from luca_scraper modules
from luca_scraper.config import HTTP_TIMEOUT
from luca_scraper.extraction.phone import normalize_phone, validate_phone

# Try importing from scriptname.py with fallback
try:
    from scriptname import (
        http_get_async, log,
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


async def extract_generic_detail_async(url: str, source_tag: str = "direct_crawl") -> Optional[Dict[str, Any]]:
    """
    Generic function to extract contact information from any ad detail page.
    Similar to extract_kleinanzeigen_detail_async but works for multiple sites.
    
    Args:
        url: URL of the ad detail page
        source_tag: Tag to identify the source (e.g., "markt_de", "quoka")
        
    Returns:
        Dict with lead data or None if extraction failed
    """
    try:
        r = await http_get_async(url, timeout=HTTP_TIMEOUT)
        if not r or r.status_code != 200:
            log("debug", f"{source_tag}: Failed to fetch detail", url=url, status=r.status_code if r else "None")
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
        
        # Extract mobile phone numbers using standard and advanced patterns
        phones = []
        
        # Standard extraction
        phone_matches = MOBILE_RE.findall(full_text)
        for phone_match in phone_matches:
            normalized = normalize_phone(phone_match)
            if normalized:
                is_valid, phone_type = validate_phone(normalized)
                if is_valid and is_mobile_number(normalized):
                    phones.append(normalized)
        
        # Enhanced extraction if standard failed
        if not phones:
            try:
                extraction_results = extract_all_phone_patterns(html, full_text)
                best_phone = get_best_phone_number(extraction_results)
                if best_phone:
                    normalized = normalize_phone(best_phone)
                    if normalized and is_mobile_number(normalized):
                        phones.append(normalized)
                        log("info", f"{source_tag}: Advanced extraction found phone", 
                            url=url, phone=normalized[:8]+"...")
                        if _LEARNING_ENGINE:
                            _LEARNING_ENGINE.record_phone_pattern(
                                pattern="advanced_extraction",
                                pattern_type=f"{source_tag}_enhanced",
                                example=normalized[:8]+"..."
                            )
                        # NEW: Learn phone pattern for AI Learning Engine
                        try:
                            from ai_learning_engine import ActiveLearningEngine
                            learning = ActiveLearningEngine()
                            learning.learn_phone_pattern(best_phone, normalized, source_tag)
                        except Exception:
                            pass  # Learning is optional
            except Exception as e:
                log("debug", f"{source_tag}: Advanced extraction failed", error=str(e))
        
        # Extract email
        email = ""
        email_matches = EMAIL_RE.findall(full_text)
        if email_matches:
            email = email_matches[0]
        
        # Extract WhatsApp link using enhanced extraction
        try:
            wa_number = extract_whatsapp_number(html)
            if wa_number:
                normalized_wa = normalize_phone(wa_number)
                if normalized_wa and is_mobile_number(normalized_wa):
                    if normalized_wa not in phones:
                        phones.append(normalized_wa)
                        log("info", f"{source_tag}: WhatsApp extraction found phone", url=url)
        except Exception:
            pass
        
        # Fallback: Try old WhatsApp link extraction
        wa_link = soup.select_one('a[href*="wa.me"], a[href*="api.whatsapp.com"]')
        if wa_link:
            wa_href = wa_link.get("href", "")
            wa_phone = re.sub(r'\D', '', wa_href)
            if wa_phone:
                wa_normalized = "+" + wa_phone
                is_valid, phone_type = validate_phone(wa_normalized)
                if is_valid and is_mobile_number(wa_normalized):
                    if wa_normalized not in phones:
                        phones.append(wa_normalized)
        
        # Extract name
        name = extract_name_enhanced(full_text)
        
        # Only create lead if we found at least one mobile number
        if not phones:
            log("debug", f"{source_tag}: No mobile numbers found, trying browser extraction", url=url)
            # Fallback: Browser-based extraction for JS-hidden numbers
            try:
                # Detect portal from source_tag or URL
                portal_map = {
                    'markt_de': 'markt_de',
                    'quoka': 'quoka',
                    'dhd24': 'dhd24',
                    'kalaydo': 'generic',
                    'meinestadt': 'generic',
                }
                portal = portal_map.get(source_tag, 'generic')
                browser_phone = extract_phone_with_browser(url, portal=portal)
                if browser_phone:
                    phones.append(browser_phone)
                    log("info", f"{source_tag}: Browser extraction successful", url=url)
            except Exception as e:
                log("debug", f"{source_tag}: Browser extraction failed", url=url, error=str(e))
            
            # If still no phones found, return None
            if not phones:
                if _LEARNING_ENGINE:
                    _LEARNING_ENGINE.learn_from_failure(
                        url=url,
                        html_content=html,
                        reason=f"{source_tag}_no_mobile_found",
                        visible_phones=[]
                    )
                return None
        
        # Use first mobile number found
        main_phone = phones[0]
        
        # Build lead data
        lead = {
            "name": name or "",
            "rolle": "Vertrieb",
            "email": email,
            "telefon": main_phone,
            "quelle": url,
            "score": 85,
            "tags": f"{source_tag},candidate,mobile,direct_crawl",
            "lead_type": "candidate",
            "phone_type": "mobile",
            "opening_line": title[:200] if title else "",
            "firma": "",
            "firma_groesse": "",
            "branche": "",
            "region": "",
            "frische": "neu",
            "confidence": 0.85,
            "data_quality": 0.80,
        }
        
        return lead
        
    except Exception as e:
        log("error", f"{source_tag}: Error extracting detail", url=url, error=str(e))
        return None
