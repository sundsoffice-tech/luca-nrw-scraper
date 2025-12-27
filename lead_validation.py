# -*- coding: utf-8 -*-
"""
Lead Quality Validation & Filtering System

Implements strict validation to filter out low-quality leads:
- Phone number validation (mobile numbers only, fake number detection)
- Source URL whitelist/blacklist
- Name validation (detect headlines, company names, test entries)
- Lead type validation

Usage:
    from lead_validation import validate_lead_before_insert, normalize_phone_number
    
    is_valid, reason = validate_lead_before_insert(lead)
    if not is_valid:
        log("debug", "Lead rejected", reason=reason)
"""

import re
from typing import Tuple, Optional


# =========================
# Phone Number Validation
# =========================

def validate_phone_number(phone: str) -> bool:
    """
    Validates German mobile phone numbers with strict requirements.
    
    Returns True only if:
    - At least 11 digits (without +49)
    - Starts with German mobile prefixes (015, 016, 017)
    - No obvious fake numbers
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        bool: True if valid mobile number, False otherwise
    """
    if not phone:
        return False
    
    # Normalize: Remove everything except digits
    digits = re.sub(r'[^\d]', '', phone)
    
    # Remove leading 49 or 0049
    if digits.startswith('49'):
        digits = '0' + digits[2:]
    elif digits.startswith('0049'):
        digits = '0' + digits[4:]
    
    # Must start with mobile prefix
    mobile_prefixes = ('015', '016', '017')
    if not digits.startswith(mobile_prefixes):
        return False
    
    # At least 11 digits (e.g., 01512345678)
    if len(digits) < 11:
        return False
    
    # Maximum 15 digits
    if len(digits) > 15:
        return False
    
    # Block obvious fake numbers
    fake_patterns = [
        '1234567890',
        '0000000000',
        '1111111111',
        '0123456789',
        '9876543210',
    ]
    for fake in fake_patterns:
        if fake in digits:
            return False
    
    # Block numbers with too many same digits in a row
    if re.search(r'(\d)\1{5,}', digits):  # 6+ same digits
        return False
    
    return True


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    Normalizes phone number to international format +49...
    
    Args:
        phone: Phone number to normalize
        
    Returns:
        Normalized phone number in +49 format, or None if invalid
    """
    if not phone:
        return None
    
    digits = re.sub(r'[^\d]', '', phone)
    
    # Convert to +49 format
    if digits.startswith('0049'):
        digits = digits[4:]
    elif digits.startswith('49') and len(digits) > 10:
        digits = digits[2:]
    elif digits.startswith('0'):
        digits = digits[1:]
    
    return f'+49{digits}'


# =========================
# Source URL Validation
# =========================

# Only these domains are allowed for leads
ALLOWED_LEAD_SOURCES = [
    'kleinanzeigen.de',
    'quoka.de',
    'markt.de',
    'dhd24.com',
    'dhd24.de',  # Alternative TLD
    'kalaydo.de',
    'meinestadt.de',
    'ebay-kleinanzeigen.de',  # old domain
    'arbeitsagentur.de',
    'monster.de',
    'freelancermap.de',
    'freelance.de',
    'xing.com',
    'linkedin.com',
    'indeed.com',
    'stepstone.de',
]

# These domains are ALWAYS blocked (mostly news/irrelevant sites)
BLOCKED_DOMAINS = [
    # Social Media (not professional profiles)
    'facebook.com',
    'tiktok.com',
    'snapchat.com',
    'instagram.com',
    'twitter.com',
    
    # PDFs and Documents
    '.pdf',
    'googleapis.com',
    'storage.google',
    
    # General Websites
    'wikipedia.org',
    'youtube.com',
    
    # Specifically blocked (from analysis)
    'sporef.idu.edu.tr',
    'patentimages.storage',
    'voris.wolterskluwer',
]


def is_valid_lead_source(url: str) -> bool:
    """
    Checks if URL comes from an allowed source.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is from allowed source, False otherwise
    """
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Check blocked list first
    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            return False
    
    # Then check whitelist
    for allowed in ALLOWED_LEAD_SOURCES:
        if allowed in url_lower:
            return True
    
    return False  # Default: Not allowed


# =========================
# Name Validation
# =========================

def validate_lead_name(name: str) -> bool:
    """
    Checks if the name is a real person name.
    
    Returns False for:
    - Too short (< 3 characters)
    - Only one word (no last name)
    - Headlines ("Deine Aufgaben", "Flexible Arbeitszeiten")
    - Company names ("GmbH", "AG", "Krankenhaus")
    - Technical terms
    
    Args:
        name: Name to validate
        
    Returns:
        bool: True if valid person name, False otherwise
    """
    if not name:
        return False
    
    name = name.strip()
    
    # At least 3 characters
    if len(name) < 3:
        return False
    
    # Block technical/test names (exact match or clear test patterns)
    blocked_names = [
        '_probe_',
        'test',
        'beispiel',
        'unknown',
        'n/a',
        'keine angabe',
    ]
    name_lower = name.lower()
    for blocked in blocked_names:
        if blocked in name_lower:
            return False
    
    # Block "muster" only if it's the whole word or at the start
    if re.search(r'\bmuster\b', name_lower) or name_lower.startswith('muster'):
        return False
    
    # Block headlines (typical job ad phrases)
    headline_patterns = [
        'deine aufgaben',
        'ihre aufgaben',
        'wir suchen',
        'wir bieten',
        'flexible arbeitszeiten',
        'kein verkauf',
        'querdenker',
        'studierende',
        'quereinsteiger',
        'curriculum vitae',
        'lebenslauf',
        'stellenangebote',
        'stellengesuche',
        'karriere',
    ]
    for pattern in headline_patterns:
        if pattern in name_lower:
            return False
    
    # Block company names
    company_indicators = [
        'gmbh', 'ag', 'kg', 'ohg', 'mbh', 'ug',
        'krankenhaus', 'klinik', 'klinikum',
        'immobilien', 'versicherung',
        'gruppe', 'group', 'holding',
        'consulting', 'beratung',
        'verlag', 'medien', 'media',
    ]
    for indicator in company_indicators:
        if indicator in name_lower:
            return False
    
    # Block if name starts with special characters
    if name[0] in '0123456789@#$%^&*()[]{}|\\/<>':
        return False
    
    # Block if too many special characters
    special_chars = sum(1 for c in name if not c.isalnum() and c not in ' -.')
    if special_chars > 3:
        return False
    
    return True


def extract_person_name(raw_name: str) -> Optional[str]:
    """
    Tries to extract a real person name from raw text.
    
    Typical patterns for names in ads:
    - "Kontakt: Max Mustermann" -> "Max Mustermann"
    - "Ansprechpartner: Frau Schmidt" -> "Frau Schmidt"
    
    Args:
        raw_name: Raw name text to extract from
        
    Returns:
        Extracted name or original raw_name if no pattern matches
    """
    if not raw_name:
        return None
    
    # Typical patterns for names in ads
    patterns = [
        r'(?:kontakt|ansprechpartner|name)[:\s]+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)',
        r'(?:herr|frau|hr\.|fr\.)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, raw_name, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return raw_name.strip()


# =========================
# Main Validation Function
# =========================

def validate_lead_before_insert(lead: dict) -> Tuple[bool, str]:
    """
    Validates a lead BEFORE inserting into the database.
    
    IMPORTANT: Telefonnummer ist wichtiger als Name!
    Phone number is mandatory, name is optional and can be enriched later.
    
    Args:
        lead: Lead dictionary to validate
        
    Returns:
        Tuple of (is_valid, reason):
        - is_valid: True if lead passes all validations
        - reason: String describing why lead was rejected (or "OK" if valid)
    """
    # 1. Validate phone (MANDATORY)
    phone = lead.get('telefon')
    if not validate_phone_number(phone):
        return False, f"Ungültige Telefonnummer: {phone}"
    
    # 2. Validate source
    source = lead.get('quelle')
    if not is_valid_lead_source(source):
        # If phone is valid, accept anyway but note the source issue
        if phone and validate_phone_number(phone):
            return True, "OK (Quelle unbekannt aber Telefon gültig)"
        return False, f"Nicht erlaubte Quelle: {source}"
    
    # 3. Validate name (OPTIONAL - can be enriched later)
    name = lead.get('name', '').strip()
    if not name or name in ["_probe_", "Unknown Candidate", "unknown", ""]:
        # Name is missing/invalid - mark for enrichment but accept the lead
        lead['name'] = ""
        lead['name_pending_enrichment'] = True
        return True, "OK (Name fehlt - wird später angereichert)"
    
    if not validate_lead_name(name):
        # Name is present but invalid - try to keep lead anyway
        lead['name'] = ""
        lead['name_pending_enrichment'] = True
        return True, "OK (Name ungültig - wird ersetzt)"
    
    # 4. Validate lead type (only candidates)
    lead_type = lead.get('lead_type', '')
    if lead_type and lead_type not in ('candidate', 'kandidat', ''):
        return False, f"Falscher Lead-Type: {lead_type}"
    
    return True, "OK"


# =========================
# Rejection Statistics
# =========================

# Statistics for rejected leads
rejected_stats = {
    'invalid_phone': 0,
    'blocked_source': 0,
    'invalid_name': 0,
    'wrong_type': 0,
}


def increment_rejection_stat(reason: str):
    """
    Increments rejection statistics counter.
    
    Args:
        reason: Rejection reason string
    """
    if 'telefon' in reason.lower():
        rejected_stats['invalid_phone'] += 1
    elif 'quelle' in reason.lower():
        rejected_stats['blocked_source'] += 1
    elif 'name' in reason.lower():
        rejected_stats['invalid_name'] += 1
    elif 'type' in reason.lower():
        rejected_stats['wrong_type'] += 1


def get_rejection_stats() -> dict:
    """
    Returns current rejection statistics.
    
    Returns:
        Dictionary with rejection counts by category
    """
    return rejected_stats.copy()


def reset_rejection_stats():
    """Resets all rejection statistics to zero."""
    global rejected_stats
    rejected_stats = {
        'invalid_phone': 0,
        'blocked_source': 0,
        'invalid_name': 0,
        'wrong_type': 0,
    }
