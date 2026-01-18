# -*- coding: utf-8 -*-
"""
Phone number validation and normalization for German phone numbers.

This module provides utilities for normalizing and validating phone numbers,
with special support for German (DE) phone numbers in E.164 format.
"""

import re
from typing import Tuple

# Try to import is_mobile_number from learning_engine, fallback if not available
try:
    from learning_engine import is_mobile_number
except ImportError:
    # Fallback implementation if learning_engine is not available
    def is_mobile_number(phone: str) -> bool:
        """Fallback: Check if phone is a German mobile number."""
        if not phone:
            return False
        # Simple check for German mobile prefixes
        return any(phone.startswith(f'+4915{i}') or phone.startswith(f'+4916{i}') or phone.startswith(f'+4917{i}') 
                   for i in range(10))


# German mobile prefixes (015x, 016x, 017x)
MOBILE_PREFIXES_DE = {'150', '151', '152', '155', '156', '157', '159',
                      '160', '162', '163', '170', '171', '172', '173',
                      '174', '175', '176', '177', '178', '179'}

# Context keywords that indicate candidate-related phone numbers
CANDIDATE_PHONE_CONTEXT = (
    "lebenslauf", "cv", "profil", "erfahrung", "qualifikation", "vita",
    "bewerbung", "stellengesuch", "ich suche", "ich bin", "open to work", "freelancer", "freiberuf",
)


def normalize_phone(p: str) -> str:
    """
    Normalize German phone numbers to E.164-like format, handling edge cases like '(0)'.
    
    This function handles various phone number formats commonly found in Germany:
    - National format with leading 0: '0211 123456' -> '+49211123456'
    - International format with (0): '+49 (0) 211 123456' -> '+49211123456'
    - 00-prefix format: '0049 (0) 211-123456' -> '+49211123456'
    - Mobile numbers: '+49-(0)-176 123 45 67' -> '+491761234567'
    
    Args:
        p: Phone number string in various formats
        
    Returns:
        Normalized phone number in E.164-like format (with + prefix),
        or empty string if input is empty or invalid
        
    Examples:
        >>> normalize_phone('0211 123456')
        '+49211123456'
        >>> normalize_phone('+49 (0) 211 123456')
        '+49211123456'
        >>> normalize_phone('0049 (0) 211-123456')
        '+49211123456'
        >>> normalize_phone('+49-(0)-176 123 45 67')
        '+491761234567'
    """
    if not p:
        return ""

    s = str(p).strip()
    if not s:
        return ""

    # Handle (0) edge cases before main cleanup
    # Captures (), [], {} with optional whitespace: '(0)', '( 0 )', '[0]', etc.
    s = re.sub(r'[\(\[\{]\s*0\s*[\)\]\}]', '0', s)

    # Remove common extension/additional info at the end (ext, Durchwahl, DW, Tel.)
    s = re.sub(r'(?:durchwahl|dw|ext\.?|extension)\s*[:\-]?\s*\d+\s*$', '', s, flags=re.I)

    # Remove all characters except digits and plus
    s = re.sub(r'[^\d+]', '', s)

    # Normalize international prefixes
    s = re.sub(r'^00', '+', s)        # 0049 -> +49, 0033 -> +33, etc.
    s = re.sub(r'^\+049', '+49', s)   # Handle typo variant
    s = re.sub(r'^0049', '+49', s)    # Redundant but explicit

    # Remove optional (0) after +49 (already converted to '0' above)
    # Examples: '+490211...' -> '+49211...'
    s = re.sub(r'^\+490', '+49', s)

    # Convert national leading 0 → +49
    if s.startswith('0') and not s.startswith('+'):
        s = '+49' + s[1:]

    # Handle multiple '+' signs
    if s.count('+') > 1:
        s = '+' + re.sub(r'\D', '', s)

    # If no '+' present yet, add it (E.164-like format)
    if not s.startswith('+'):
        s = '+' + re.sub(r'\D', '', s)

    # Plausibility check (total digit count)
    digits = re.sub(r'\D', '', s)
    if len(digits) < 8 or len(digits) > 16:
        return s  # Return unmodified if outside valid range

    return s


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate phone numbers with strict requirements.
    
    This function performs robust validation of phone numbers, checking:
    - Format: Must be E.164 format or DE format
    - Length: 10-15 digits after normalization
    - Country support: German (+49/0049/0...) and international formats
    - Type detection: Mobile (015/016/017) vs landline
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        Tuple of (is_valid, phone_type) where:
        - is_valid: Boolean indicating if phone number is valid
        - phone_type: String indicating type - 'mobile', 'landline', 'international', or 'invalid'
        
    Requirements:
        - Must be in E.164 format or DE format
        - Length: 10-15 digits after normalization
        - Support DE/intl formats: +49/0049/0...
        - Detect mobile prefixes: 015/016/017
        
    Examples:
        >>> validate_phone('+49176123456789')
        (True, 'mobile')
        >>> validate_phone('0211 123456')
        (True, 'landline')
        >>> validate_phone('+1234567890')
        (True, 'international')
        >>> validate_phone('invalid')
        (False, 'invalid')
    """
    if not phone or not isinstance(phone, str):
        return False, "invalid"
    
    normalized = normalize_phone(phone)
    if not normalized:
        return False, "invalid"
    
    # Extract digits only
    digits = re.sub(r'\D', '', normalized)
    
    # Length check: 10-15 digits
    if len(digits) < 10 or len(digits) > 15:
        return False, "invalid"
    
    # Check if it's a valid German number
    if normalized.startswith('+49'):
        # Extract area/mobile code (first 3 digits after country code)
        if len(digits) >= 5:
            prefix = digits[2:5]  # Skip '49' country code
            if prefix in MOBILE_PREFIXES_DE:
                return True, "mobile"
            # Landline numbers typically start with area codes
            elif prefix[0] in '23456789':  # Valid landline area code starts
                return True, "landline"
    
    # International numbers (non-DE)
    elif normalized.startswith('+') and len(digits) >= 10:
        return True, "international"
    
    return False, "invalid"


def _phone_context_ok(text: str, start: int, end: int) -> bool:
    """
    Check if phone number appears in a candidate-relevant context.
    
    This helper function examines the text surrounding a phone number to determine
    if it appears in a context that suggests it belongs to a candidate (e.g., in a CV,
    profile, or job application).
    
    Args:
        text: Full text containing the phone number
        start: Start position of the phone number in text
        end: End position of the phone number in text
        
    Returns:
        True if phone appears in candidate-relevant context, False otherwise
        
    Note:
        Examines a window of 120 characters before and after the phone number
        position for candidate-related keywords.
    """
    window = text[max(0, start - 120): min(len(text), end + 120)].lower()
    return any(k in window for k in CANDIDATE_PHONE_CONTEXT)
