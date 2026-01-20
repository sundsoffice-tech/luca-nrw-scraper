"""
Phone and Email Extraction Module
==================================
Centralized extraction logic for contact information.

This module consolidates phone, WhatsApp, and email extraction logic that was
previously duplicated in luca_scraper/crawlers/generic.py and
luca_scraper/crawlers/kleinanzeigen.py.

Functions:
    extract_phone_numbers: Comprehensive phone number extraction
    extract_email_address: Email extraction from text
    extract_whatsapp_number: WhatsApp number extraction from HTML
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


def extract_phone_numbers(
    html: str,
    text: str,
    normalize_phone_func,
    validate_phone_func,
    is_mobile_number_func,
    MOBILE_RE=None,
    extract_all_phone_patterns_func=None,
    get_best_phone_number_func=None,
    learning_engine=None,
    portal_tag: str = "",
    log_func=None,
) -> Tuple[List[str], Dict[str, str]]:
    """
    Extract phone numbers from HTML and text using multiple methods.
    
    This function consolidates phone extraction logic that was duplicated in
    generic.py and kleinanzeigen.py. It runs multiple extraction methods in
    parallel:
    1. Standard regex extraction (MOBILE_RE)
    2. Advanced pattern extraction (if available)
    3. Best phone number selection
    
    Args:
        html: Raw HTML content
        text: Visible text content
        normalize_phone_func: Function to normalize phone numbers
        validate_phone_func: Function to validate phones (returns tuple: is_valid, phone_type)
        is_mobile_number_func: Function to check if number is mobile
        MOBILE_RE: Compiled regex pattern for mobile numbers
        extract_all_phone_patterns_func: Advanced pattern extraction function
        get_best_phone_number_func: Function to get best phone from results
        learning_engine: Optional learning engine instance for pattern recording
        portal_tag: Source portal tag for logging (e.g., "kleinanzeigen", "markt_de")
        log_func: Logging function
        
    Returns:
        Tuple of (phones: List[str], phone_sources: Dict[str, str])
        - phones: List of normalized phone numbers
        - phone_sources: Dict mapping phone numbers to their extraction source
    """
    phones = []
    phone_sources = {}
    
    # ========================================
    # 1. Standard regex extraction (runs in parallel with advanced)
    # ========================================
    if MOBILE_RE:
        phone_matches = MOBILE_RE.findall(text)
        for phone_match in phone_matches:
            normalized = normalize_phone_func(phone_match)
            if normalized:
                is_valid, phone_type = validate_phone_func(normalized)
                if is_valid and is_mobile_number_func(normalized):
                    if normalized not in phones:
                        phones.append(normalized)
                        phone_sources[normalized] = "regex_standard"
    
    # ========================================
    # 2. Advanced pattern extraction (runs in parallel, not as fallback)
    # ========================================
    if extract_all_phone_patterns_func and get_best_phone_number_func:
        try:
            extraction_results = extract_all_phone_patterns_func(html, text)
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
                                    log_prefix = f"{portal_tag}: " if portal_tag else ""
                                    log_func("info", f"{log_prefix}Advanced extraction ({category}) found phone", 
                                        phone=normalized[:8]+"...")
            
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
                            pattern_type=f"{portal_tag}_enhanced" if portal_tag else "enhanced",
                            example=normalized[:8]+"..."
                        )
        except Exception as e:
            if log_func:
                log_prefix = f"{portal_tag}: " if portal_tag else ""
                log_func("debug", f"{log_prefix}Advanced extraction failed", error=str(e))
    
    return phones, phone_sources


def extract_email_address(
    text: str,
    EMAIL_RE=None,
) -> str:
    """
    Extract email address from text using regex pattern.
    
    This function consolidates email extraction logic that was duplicated in
    generic.py and kleinanzeigen.py.
    
    Args:
        text: Text content to search for email
        EMAIL_RE: Compiled regex pattern for email addresses
        
    Returns:
        First email address found, or empty string if none found
    """
    email = ""
    if EMAIL_RE:
        email_matches = EMAIL_RE.findall(text)
        if email_matches:
            email = email_matches[0]
    return email


def extract_whatsapp_number(
    html: str,
    normalize_phone_func,
    validate_phone_func,
    is_mobile_number_func,
    extract_whatsapp_number_func=None,
    portal_tag: str = "",
    log_func=None,
) -> Tuple[str, Dict[str, str]]:
    """
    Extract WhatsApp number from HTML using multiple methods.
    
    This function consolidates WhatsApp extraction logic that was duplicated in
    generic.py and kleinanzeigen.py. It tries multiple approaches:
    1. Enhanced WhatsApp extraction function (if provided)
    2. Fallback extraction from wa.me and api.whatsapp.com links
    
    Args:
        html: Raw HTML content
        normalize_phone_func: Function to normalize phone numbers
        validate_phone_func: Function to validate phones (returns tuple: is_valid, phone_type)
        is_mobile_number_func: Function to check if number is mobile
        extract_whatsapp_number_func: Optional enhanced WhatsApp extraction function
        portal_tag: Source portal tag for logging
        log_func: Logging function
        
    Returns:
        Tuple of (whatsapp_number: str, phone_sources: Dict[str, str])
        - whatsapp_number: Normalized WhatsApp number or empty string
        - phone_sources: Dict mapping the number to its extraction source
    """
    whatsapp = ""
    phone_sources = {}
    
    # ========================================
    # 1. Enhanced WhatsApp extraction (if available)
    # ========================================
    if extract_whatsapp_number_func:
        try:
            wa_number = extract_whatsapp_number_func(html)
            if wa_number:
                normalized_wa = normalize_phone_func(wa_number)
                if normalized_wa and is_mobile_number_func(normalized_wa):
                    whatsapp = normalized_wa
                    phone_sources[normalized_wa] = "whatsapp_enhanced"
                    if log_func:
                        log_prefix = f"{portal_tag}: " if portal_tag else ""
                        log_func("info", f"{log_prefix}WhatsApp extraction found phone", 
                            phone=normalized_wa[:8]+"...")
        except Exception:
            pass
    
    # ========================================
    # 2. Fallback WhatsApp link extraction
    # ========================================
    if not whatsapp:
        soup = BeautifulSoup(html, "html.parser")
        wa_link = soup.select_one('a[href*="wa.me"], a[href*="api.whatsapp.com"]')
        if wa_link:
            wa_href = wa_link.get("href", "")
            wa_phone = re.sub(r'\D', '', wa_href)
            if wa_phone:
                wa_normalized = "+" + wa_phone
                is_valid, phone_type = validate_phone_func(wa_normalized)
                if is_valid and is_mobile_number_func(wa_normalized):
                    whatsapp = wa_normalized
                    phone_sources[wa_normalized] = "whatsapp_link"
    
    return whatsapp, phone_sources
