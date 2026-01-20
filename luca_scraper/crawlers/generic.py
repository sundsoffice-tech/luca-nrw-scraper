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

from luca_scraper.extraction.lead_builder import build_lead_data


async def extract_detail_generic(
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
                                        log_func("info", f"{source_tag}: Advanced extraction ({category}) found phone", 
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
                                pattern_type=f"{source_tag}_enhanced",
                                example=normalized[:8]+"..."
                            )
                        # Learn phone pattern for AI Learning Engine
                        try:
                            from ai_learning_engine import ActiveLearningEngine
                            learning = ActiveLearningEngine()
                            learning.learn_phone_pattern(best_phone, normalized, source_tag)
                        except Exception:
                            pass  # Learning is optional
            except Exception as e:
                if log_func:
                    log_func("debug", f"{source_tag}: Advanced extraction failed", error=str(e))

        # Extract email
        email = ""
        if EMAIL_RE:
            email_matches = EMAIL_RE.findall(full_text)
            if email_matches:
                email = email_matches[0]

        # 3. WhatsApp extraction (parallel with other methods)
        if extract_whatsapp_number_func:
            try:
                wa_number = extract_whatsapp_number_func(html)
                if wa_number:
                    normalized_wa = normalize_phone_func(wa_number)
                    if normalized_wa and is_mobile_number_func(normalized_wa):
                        if normalized_wa not in phones:
                            phones.append(normalized_wa)
                            phone_sources[normalized_wa] = "whatsapp_enhanced"
                            if log_func:
                                log_func("info", f"{source_tag}: WhatsApp extraction found phone", url=url)
            except Exception:
                pass

        # 4. Fallback WhatsApp link extraction
        wa_link = soup.select_one('a[href*="wa.me"], a[href*="api.whatsapp.com"]')
        if wa_link:
            wa_href = wa_link.get("href", "")
            wa_phone = re.sub(r'\D', '', wa_href)
            if wa_phone:
                wa_normalized = "+" + wa_phone
                is_valid, phone_type = validate_phone_func(wa_normalized)
                if is_valid and is_mobile_number_func(wa_normalized):
                    if wa_normalized not in phones:
                        phones.append(wa_normalized)
                        phone_sources[wa_normalized] = "whatsapp_link"

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

        # Build lead data using centralized function
        lead = build_lead_data(
            name=name,
            phones=phones,
            email=email,
            location="",  # Generic crawler doesn't extract location
            title=title,
            url=url,
            phone_sources=phone_sources,
            portal=source_tag,
            has_whatsapp=False,  # Will be checked separately
            tags=f"{source_tag},candidate,mobile,direct_crawl",
        )

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


# Backward compatibility alias
extract_generic_detail_async = extract_detail_generic

