# -*- coding: utf-8 -*-
"""
German Phone Number Patterns & Normalization Module
===================================================

This module provides comprehensive German phone number detection and normalization:

1. Aufgabe 1 - Deutsche Telefonnummern & E-Mails:
   - Typical German phone formats (Festnetz + Mobilfunk)
   - Robust regex patterns for various formats
   - Label recognition (Tel:, Telefon:, Mobil:, Handy:)
   - Normalization to +49 standard format

German Phone Number Formats:
============================
Mobilfunk (Mobile):
  - +49 1XX XXXX XXXX (international)
  - 0049 1XX XXXX XXXX (alternative international)
  - 01XX XXXX XXXX (national with leading 0)
  - 01XX/XXXX-XXXX (with separators)
  
  Mobile prefixes: 015X, 016X, 017X
  Examples:
    - +49 176 1234 5678
    - 0176 12345678
    - 0176-1234-5678
    - 0176/1234/5678
    - 0 1 7 6 1 2 3 4 5 6 7 8 (spaced, anti-bot)

Festnetz (Landline):
  - +49 XXX XXXXXXX (international)
  - 0XXX XXXXXXX (national)
  - (0XXX) XXXXXXX (with area code in brackets)
  
  Examples:
    - +49 211 123456
    - 0211 123456
    - (0211) 123456
    - 0211/123456

Labels to recognize:
  - Tel:, Tel.:, Telefon:, Telefonnummer:
  - Mobil:, Mobiltelefon:, Handy:
  - Fon:, Phone:, Rückruf:
  - WhatsApp:, WA:
"""

import re
from typing import Dict, List, Optional, Tuple


# ========================================
# GERMAN PHONE NUMBER REGEX PATTERNS
# ========================================

# Pattern 1: International format (+49 or 0049)
# Matches: +49 176 12345678, +49 211 123456, 0049 176 12345678
PATTERN_INTERNATIONAL = (
    r'(?:\+49|0049)'                    # +49 or 0049 prefix
    r'[\s.\-/]?'                        # Optional separator
    r'\(?(\d{2,5})\)?'                  # Area/mobile code (2-5 digits, optional brackets)
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{3,4})'                        # First digit group (3-4 digits)
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{3,6})'                        # Second digit group (3-6 digits)
)

# Pattern 2: National format (leading 0)
# Matches: 0176 12345678, 0211 123456, 0176-1234-5678
PATTERN_NATIONAL = (
    r'(?<!\d)0'                         # Leading 0 (not preceded by digit)
    r'[\s.\-/]?'                        # Optional separator
    r'\(?(\d{2,5})\)?'                  # Area/mobile code (2-5 digits, optional brackets)
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{3,4})'                        # First digit group
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{3,6})'                        # Second digit group
)

# Pattern 3: Mobile numbers with specific prefixes (015x, 016x, 017x)
# Matches: 0176 12345678, 01512 1234567
PATTERN_MOBILE = (
    r'(?:\+49[\s.\-/]?|0049[\s.\-/]?|0[\s.\-/]?)'  # Country code or leading 0
    r'(1[567]\d)'                       # Mobile prefix: 15x, 16x, 17x
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{3,4})'                        # First digit group
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{4,5})'                        # Second digit group
)

# Pattern 4: Compact format (no separators)
# Matches: +4917612345678, 017612345678
PATTERN_COMPACT = (
    r'(?:\+49|0049|0)'                  # Prefix
    r'(1[567]\d)'                       # Mobile prefix
    r'(\d{7,8})'                        # Rest of number (7-8 digits)
)

# Pattern 5: With Labels (Tel:, Mobil:, Handy:, etc.)
# Matches: Tel: 0176 12345678, Handy: +49 176 12345678
PATTERN_WITH_LABEL = (
    r'(?:Tel(?:efon)?|Fon|Phone|Mobil(?:telefon)?|Handy|Rückruf|WhatsApp|WA)'
    r'[:\s.\-/]*'                       # Label separator
    r'(?:\+49|0049|0)'                  # Country code
    r'[\s.\-/]?'                        # Optional separator  
    r'\(?(\d{2,5})\)?'                  # Area/mobile code
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{3,4})'                        # First digit group
    r'[\s.\-/]?'                        # Optional separator
    r'(\d{3,6})'                        # Second digit group
)

# Pattern 6: Spaced numbers (anti-bot protection)
# Matches: 0 1 7 6 1 2 3 4 5 6 7 8
PATTERN_SPACED = (
    r'0\s+1\s+[567]\s+'                 # 0 1 5/6/7
    r'(?:\d\s+){7,9}'                   # 7-9 spaced digits
    r'\d'                               # Final digit (no trailing space)
)

# ========================================
# COMPILED REGEX PATTERNS
# ========================================

PHONE_PATTERNS_COMPILED: Dict[str, re.Pattern] = {
    "international": re.compile(PATTERN_INTERNATIONAL, re.IGNORECASE),
    "national": re.compile(PATTERN_NATIONAL, re.IGNORECASE),
    "mobile": re.compile(PATTERN_MOBILE, re.IGNORECASE),
    "compact": re.compile(PATTERN_COMPACT, re.IGNORECASE),
    "with_label": re.compile(PATTERN_WITH_LABEL, re.IGNORECASE),
    "spaced": re.compile(PATTERN_SPACED, re.IGNORECASE),
}

# ========================================
# LABEL PATTERNS
# ========================================

# German phone labels that indicate a phone number follows
PHONE_LABELS = [
    "Tel:",
    "Tel.:",
    "Telefon:",
    "Telefonnummer:",
    "Fon:",
    "Phone:",
    "Mobil:",
    "Mobiltelefon:",
    "Mobilnummer:",
    "Handy:",
    "Handynummer:",
    "Rückruf:",
    "Rückrufnummer:",
    "WhatsApp:",
    "WA:",
    "Erreichbar unter:",
    "Kontakt:",
    "Festnetz:",
]

# Compiled label pattern
LABEL_PATTERN = re.compile(
    r'(?:' + '|'.join(re.escape(label) for label in PHONE_LABELS) + r')',
    re.IGNORECASE
)

# ========================================
# MOBILE PREFIX VALIDATION
# ========================================

# Valid German mobile prefixes (without country code) - deduplicated
GERMAN_MOBILE_PREFIXES = [
    # Deutsche Telekom (D1)
    "151", "159", "160", "161", "164", "165", "166", "167", "168", "169", "170", "171", "175",
    # Vodafone (D2)
    "152", "162", "172", "173", "174",
    # O2/E-Plus (merged)
    "155", "156", "157", "163", "176", "177", "178", "179",
]

# Valid German area code ranges (first digits)
GERMAN_AREA_CODE_STARTS = ["2", "3", "4", "5", "6", "7", "8", "9"]


# ========================================
# NORMALIZATION FUNCTIONS
# ========================================

def normalize_german_phone(raw: str) -> str:
    """
    Normalize any German phone number to standard +49 format.
    
    Normalization Rules:
    1. Remove all non-digit characters except leading +
    2. Handle different prefix formats:
       - +49XXXXXXXXXX -> +49XXXXXXXXXX (already normalized)
       - 0049XXXXXXXXXX -> +49XXXXXXXXXX
       - 0XXXXXXXXXX -> +49XXXXXXXXXX (remove leading 0)
       - 49XXXXXXXXXX -> +49XXXXXXXXXX (add +)
    3. Validate length (10-11 digits after +49)
    4. Return empty string if invalid
    
    Args:
        raw: Raw phone number string
        
    Returns:
        Normalized phone number in +49 format, or empty string if invalid
        
    Examples:
        >>> normalize_german_phone("+49 176 1234 5678")
        '+4917612345678'
        >>> normalize_german_phone("0176 1234 5678")
        '+4917612345678'
        >>> normalize_german_phone("0049 176 1234 5678")
        '+4917612345678'
        >>> normalize_german_phone("176/1234-5678")  # No prefix, ambiguous
        ''
    """
    if not raw:
        return ""
    
    # Step 1: Clean the string - keep only digits and leading +
    cleaned = raw.strip()
    
    # Extract digits, preserving position of + at start
    has_plus = cleaned.startswith('+')
    digits = re.sub(r'[^\d]', '', cleaned)
    
    if not digits:
        return ""
    
    # Step 2: Handle different prefix formats
    normalized_digits = ""
    
    if has_plus:
        # Already has +, check if it starts with 49
        if digits.startswith('49'):
            normalized_digits = digits[2:]  # Remove 49
        else:
            # Invalid: + but not +49
            return ""
    elif digits.startswith('0049'):
        # 0049 prefix
        normalized_digits = digits[4:]
    elif digits.startswith('49') and len(digits) >= 11:
        # 49 without + or 00 (could be valid)
        normalized_digits = digits[2:]
    elif digits.startswith('0') and len(digits) >= 10:
        # National format with leading 0
        normalized_digits = digits[1:]
    else:
        # Unknown format
        return ""
    
    # Step 3: Validate length
    # German mobile numbers: 10-11 digits after country code
    # German landline numbers: 8-11 digits after country code
    if len(normalized_digits) < 8 or len(normalized_digits) > 12:
        return ""
    
    # Step 4: Return normalized format
    return f"+49{normalized_digits}"


def validate_german_mobile(phone: str) -> bool:
    """
    Validate if a normalized phone number is a valid German mobile number.
    
    Args:
        phone: Normalized phone number starting with +49
        
    Returns:
        True if valid German mobile number, False otherwise
    """
    if not phone or not phone.startswith('+49'):
        return False
    
    # Extract digits after +49
    digits = phone[3:]
    
    # Check if it starts with mobile prefix (1XX)
    if not digits.startswith('1'):
        return False
    
    # Check specific mobile prefixes
    prefix = digits[:3]
    if prefix not in GERMAN_MOBILE_PREFIXES:
        # Still allow if it's a valid 15x, 16x, 17x pattern
        if not (prefix.startswith('15') or prefix.startswith('16') or prefix.startswith('17')):
            return False
    
    # Check length (10-11 digits for mobile after +49)
    if len(digits) < 10 or len(digits) > 11:
        return False
    
    return True


def validate_german_landline(phone: str) -> bool:
    """
    Validate if a normalized phone number is a valid German landline number.
    
    Args:
        phone: Normalized phone number starting with +49
        
    Returns:
        True if valid German landline number, False otherwise
    """
    if not phone or not phone.startswith('+49'):
        return False
    
    # Extract digits after +49
    digits = phone[3:]
    
    # Landline numbers should NOT start with 1 (reserved for mobile)
    if digits.startswith('1'):
        return False
    
    # First digit should be valid area code start
    if not digits or digits[0] not in GERMAN_AREA_CODE_STARTS:
        return False
    
    # Check length (8-11 digits for landline after +49)
    if len(digits) < 7 or len(digits) > 11:
        return False
    
    return True


# ========================================
# EXTRACTION FUNCTIONS
# ========================================

def extract_german_phones(
    text: str,
    html: str = "",
    mobile_only: bool = False,
) -> List[Tuple[str, str, str, float]]:
    """
    Extract all German phone numbers from text using multiple patterns.
    
    Args:
        text: Text content to search
        html: Optional HTML content for additional context
        mobile_only: If True, only return mobile numbers
        
    Returns:
        List of tuples: (normalized_phone, raw_match, extraction_method, confidence)
        
    Example:
        >>> extract_german_phones("Rufen Sie an: Tel: 0176 1234 5678 oder Festnetz 0211-123456")
        [
            ('+4917612345678', 'Tel: 0176 1234 5678', 'with_label', 0.9),
            ('+492111234567', '0211-123456', 'national', 0.7)
        ]
    """
    results: List[Tuple[str, str, str, float]] = []
    combined_text = (text or "") + " " + (html or "")
    
    if not combined_text.strip():
        return results
    
    # Track found numbers to avoid duplicates
    found_normalized: set = set()
    
    # Try each pattern
    for pattern_name, pattern in PHONE_PATTERNS_COMPILED.items():
        try:
            for match in pattern.finditer(combined_text):
                raw_match = match.group(0)
                
                # Handle spaced numbers specially
                if pattern_name == "spaced":
                    # Remove all spaces
                    raw_match = re.sub(r'\s+', '', raw_match)
                
                normalized = normalize_german_phone(raw_match)
                
                if not normalized:
                    continue
                
                # Skip if already found
                if normalized in found_normalized:
                    continue
                
                # Validate type if mobile_only
                is_mobile = validate_german_mobile(normalized)
                if mobile_only and not is_mobile:
                    continue
                
                # Calculate confidence based on pattern type
                confidence = _calculate_extraction_confidence(
                    pattern_name, raw_match, combined_text
                )
                
                found_normalized.add(normalized)
                results.append((normalized, raw_match, pattern_name, confidence))
                
        except re.error:
            continue
    
    # Sort by confidence (highest first)
    results.sort(key=lambda x: x[3], reverse=True)
    
    return results


def extract_phone_with_label(text: str) -> List[Tuple[str, str, str]]:
    """
    Extract phone numbers that have an explicit label (Tel:, Mobil:, etc.)
    
    These are higher confidence extractions because they're explicitly marked.
    
    Args:
        text: Text content to search
        
    Returns:
        List of tuples: (normalized_phone, label, raw_match)
    """
    results = []
    
    # Find all labels and their following phone numbers
    pattern = re.compile(
        r'(' + '|'.join(re.escape(label) for label in PHONE_LABELS) + r')'
        r'\s*'
        r'((?:\+49|0049|0)[\s.\-/]*\d[\s.\-/\d]{8,18})',
        re.IGNORECASE
    )
    
    for match in pattern.finditer(text):
        label = match.group(1)
        raw_phone = match.group(2)
        normalized = normalize_german_phone(raw_phone)
        
        if normalized:
            results.append((normalized, label, raw_phone))
    
    return results


def _calculate_extraction_confidence(
    pattern_name: str,
    raw_match: str,
    context: str,
) -> float:
    """
    Calculate confidence score for extracted phone number.
    
    Confidence factors:
    - Pattern type (labeled > mobile > national > spaced)
    - Number format quality
    - Context keywords (Tel:, Mobil:, etc.)
    
    Args:
        pattern_name: Name of the extraction pattern used
        raw_match: Raw matched string
        context: Full text context
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Base confidence by pattern type
    base_confidence = {
        "with_label": 0.90,    # Highest: explicitly labeled
        "mobile": 0.85,        # High: clearly a mobile number
        "international": 0.80, # High: explicit country code
        "compact": 0.75,       # Medium-high: no separators but valid
        "national": 0.70,      # Medium: common format
        "spaced": 0.60,        # Lower: possibly anti-bot obfuscation
    }
    
    confidence = base_confidence.get(pattern_name, 0.50)
    
    # Bonus for context keywords (near the number)
    match_pos = context.lower().find(raw_match.lower())
    if match_pos > 0:
        nearby_context = context[max(0, match_pos - 50):match_pos + len(raw_match) + 50].lower()
        
        # Positive context keywords
        positive_keywords = [
            "tel", "telefon", "phone", "mobil", "handy", "erreichen",
            "kontakt", "anrufen", "rückruf", "whatsapp", "erreichbar"
        ]
        for kw in positive_keywords:
            if kw in nearby_context:
                confidence = min(1.0, confidence + 0.05)
                break
        
        # Negative context keywords
        negative_keywords = [
            "fax", "steuernummer", "ust-id", "iban", "blz", "impressum",
            "agb", "datenschutz"
        ]
        for kw in negative_keywords:
            if kw in nearby_context:
                confidence = max(0.1, confidence - 0.15)
                break
    
    # Bonus for well-formatted numbers
    if re.search(r'[\s\-./]', raw_match):
        confidence = min(1.0, confidence + 0.05)
    
    return round(confidence, 2)


# ========================================
# BLACKLIST FOR FAKE/INVALID NUMBERS
# ========================================

PHONE_BLACKLIST = [
    # Test/example numbers
    "0123456789", "1234567890",
    # All same digit
    "0000000000", "1111111111", "2222222222", "3333333333",
    "4444444444", "5555555555", "6666666666", "7777777777",
    "8888888888", "9999999999",
    # Service numbers (should not be extracted as contact numbers)
    "0800",  # Free service
    "0900",  # Premium service
    "0180",  # Service/hotline
    "0137",  # Mass traffic
    "0700",  # Personal numbers
]


def is_blacklisted_phone(phone: str) -> bool:
    """Check if a phone number is blacklisted (fake/service number)."""
    if not phone:
        return True
    
    # Extract digits only
    digits = re.sub(r'[^\d]', '', phone)
    
    # Check against blacklist
    for blacklisted in PHONE_BLACKLIST:
        if digits.startswith(blacklisted) or blacklisted in digits:
            return True
    
    # Check for repeated digits (e.g., 1111111)
    for digit in '0123456789':
        if digit * 6 in digits:
            return True
    
    return False


# ========================================
# EXPORTS
# ========================================

__all__ = [
    # Constants
    "PHONE_PATTERNS_COMPILED",
    "PHONE_LABELS",
    "LABEL_PATTERN",
    "GERMAN_MOBILE_PREFIXES",
    "PHONE_BLACKLIST",
    # Normalization functions
    "normalize_german_phone",
    "validate_german_mobile",
    "validate_german_landline",
    # Extraction functions  
    "extract_german_phones",
    "extract_phone_with_label",
    # Validation functions
    "is_blacklisted_phone",
]
