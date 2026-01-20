# -*- coding: utf-8 -*-
"""
Advanced phone number pattern detection and extraction.

This module provides enhanced phone number detection including:
- Obfuscated numbers (with spaces, asterisks, words)
- WhatsApp links (wa.me, api.whatsapp.com)
- Non-standard formats
"""

import re
from typing import List, Optional, Dict, Any


# Enhanced phone patterns for German mobile numbers
LEARNED_PHONE_PATTERNS = [
    # Standard formats
    r'\+49\s*1[567]\d[\s\-]*\d{7,8}',  # +49 15x... with optional separators
    r'0\s*1\s*[567]\s*\d[\s\-]*\d{7,8}',  # 0 1 5x... with spaces
    
    # Obfuscated with asterisks or 'x'
    r'01[567][0-9*x]{1,2}[-/\s]*[0-9*x]{3,4}[-/\s]*[0-9]{3,4}',
    
    # Heavy spacing (anti-bot)
    r'0\s+1\s+[567]\s+\d\s+\d{7,8}',
    
    # WhatsApp links
    r'wa\.me/49[0-9]{10,11}',
    r'api\.whatsapp\.com/send\?phone=49[0-9]{10,11}',
    r'chat\.whatsapp\.com.*?phone=49[0-9]{10,11}',
    
    # Text obfuscation hints (will need manual review)
    r'null\s*eins\s*[567]',  # "null eins sieben" etc.
]


WORD_TO_DIGIT = {
    'null': '0', 'eins': '1', 'zwei': '2', 'drei': '3', 'vier': '4',
    'fünf': '5', 'fuenf': '5', 'sechs': '6', 'sieben': '7', 
    'acht': '8', 'neun': '9'
}


def normalize_phone_from_words(text: str) -> Optional[str]:
    """
    Convert phone numbers written as words to digits.
    
    Example: "null eins sieben sechs" -> "0176"
    
    Args:
        text: Text potentially containing phone as words
    
    Returns:
        Normalized phone number or None
    """
    text_lower = text.lower()
    digits = []
    
    # Find sequences of number words
    words = text_lower.split()
    for word in words:
        if word in WORD_TO_DIGIT:
            digits.append(WORD_TO_DIGIT[word])
        elif digits:  # If we've started collecting digits but hit a non-number, stop
            break
    
    if len(digits) >= 10:  # Minimum length for a phone number
        return ''.join(digits)
    
    return None


def extract_whatsapp_number(html: str) -> Optional[str]:
    """
    Extract phone number from WhatsApp links.
    
    Args:
        html: HTML content
    
    Returns:
        Normalized phone number or None
    """
    # WhatsApp link patterns
    whatsapp_patterns = [
        r'wa\.me/(\d{10,15})',
        r'api\.whatsapp\.com/send\?phone=(\d{10,15})',
        r'chat\.whatsapp\.com.*?phone=(\d{10,15})',
        r'whatsapp://send\?phone=(\d{10,15})',
    ]
    
    for pattern in whatsapp_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            number = match.group(1)
            # WhatsApp numbers are usually without leading 0 or +
            # German number: +49 (2) + mobile prefix (3) + rest (8) = 13 total
            if number.startswith('49') and len(number) == 13:
                return '+' + number
            elif len(number) == 11:  # Might be German without country code (01761234567)
                if number.startswith('0'):
                    return '+49' + number[1:]  # Remove leading 0
                else:
                    return '+49' + number  # Keep all digits if not starting with 0
            elif len(number) == 10:  # Might be missing leading 0 (1761234567)
                return '+49' + number
    
    return None


def extract_obfuscated_number(text: str) -> Optional[str]:
    """
    Extract phone numbers that are obfuscated with asterisks or x.
    
    Example: "0176***4567" or "0176xxx4567"
    
    Args:
        text: Text with potentially obfuscated number
    
    Returns:
        Partial phone number or None
    """
    # Pattern for obfuscated mobile numbers
    pattern = r'0\s*1\s*[567]\s*\d[*x\s\-]{3,6}\d{3,4}'
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        # Return the match - caller can decide if partial number is useful
        number = match.group(0)
        # Clean up the number
        cleaned = re.sub(r'[*x\s\-]', '', number)
        if len(cleaned) >= 6:  # At least prefix + some digits
            return cleaned
    
    return None


def extract_phone_with_spacing(text: str) -> List[str]:
    """
    Extract phone numbers with heavy spacing (anti-bot measure).
    
    Example: "0 1 7 6 1 2 3 4 5 6 7"
    
    Args:
        text: Text with spaced phone number
    
    Returns:
        List of potential phone numbers
    """
    results = []
    
    # Look for patterns of single digits with spaces
    # This is a heuristic - might need refinement
    pattern = r'0\s+1\s+[567]\s+(?:\d\s+){7,9}\d'
    
    matches = re.finditer(pattern, text)
    for match in matches:
        # Remove all spaces
        number = re.sub(r'\s+', '', match.group(0))
        if len(number) >= 10:
            results.append(number)
    
    return results


def extract_all_phone_patterns(html: str, text_content: str) -> Dict[str, Any]:
    """
    Apply all phone extraction patterns to find hidden numbers.
    
    Args:
        html: Raw HTML content
        text_content: Visible text content
    
    Returns:
        Dictionary with found patterns and numbers
    """
    results = {
        "standard": [],
        "whatsapp": [],
        "obfuscated": [],
        "spaced": [],
        "words": [],
    }
    
    # Try WhatsApp extraction
    wa_number = extract_whatsapp_number(html)
    if wa_number:
        results["whatsapp"].append(wa_number)
    
    # Try obfuscated extraction
    obf_number = extract_obfuscated_number(text_content)
    if obf_number:
        results["obfuscated"].append(obf_number)
    
    # Try spaced extraction
    spaced_numbers = extract_phone_with_spacing(text_content)
    results["spaced"].extend(spaced_numbers)
    
    # Try word-based extraction
    word_number = normalize_phone_from_words(text_content)
    if word_number:
        results["words"].append(word_number)
    
    # Try all learned patterns
    for pattern in LEARNED_PHONE_PATTERNS:
        try:
            matches = re.finditer(pattern, html + " " + text_content, re.IGNORECASE)
            for match in matches:
                number = match.group(0)
                # Clean and normalize
                cleaned = re.sub(r'[^\d+]', '', number)
                if len(cleaned) >= 10:
                    results["standard"].append(cleaned)
        except re.error:
            # Skip invalid patterns
            continue
    
    return results


def get_best_phone_number(extraction_results: Dict[str, Any]) -> Optional[str]:
    """
    From multiple extraction results, return the most likely valid number.
    
    Priority:
    1. WhatsApp numbers (most likely to be valid)
    2. Standard patterns
    3. Spaced numbers
    4. Word-based numbers
    5. Obfuscated (least reliable)
    
    Args:
        extraction_results: Results from extract_all_phone_patterns
    
    Returns:
        Best phone number or None
    """
    # Priority 1: WhatsApp
    if extraction_results.get("whatsapp"):
        return extraction_results["whatsapp"][0]
    
    # Priority 2: Standard patterns
    if extraction_results.get("standard"):
        # Return the first one that looks most complete
        for num in extraction_results["standard"]:
            if len(num) >= 11:  # Full number with country code or 0
                return num
        return extraction_results["standard"][0]
    
    # Priority 3: Spaced
    if extraction_results.get("spaced"):
        return extraction_results["spaced"][0]
    
    # Priority 4: Words
    if extraction_results.get("words"):
        return extraction_results["words"][0]
    
    # Priority 5: Obfuscated (might be incomplete)
    if extraction_results.get("obfuscated"):
        return extraction_results["obfuscated"][0]
    
    return None


def extract_phone_with_ai(html: str, openai_api_key: str = None) -> Optional[str]:
    """
    Use OpenAI to find hidden/unusual phone numbers.
    
    This is a placeholder for AI-powered extraction. Implementation would:
    1. Send HTML snippet to OpenAI with specialized prompt
    2. Ask to find phone numbers even if obfuscated
    3. Return normalized number
    
    Args:
        html: HTML content snippet
        openai_api_key: OpenAI API key
    
    Returns:
        Extracted phone number or None
    
    Note:
        This is a premium feature that uses AI tokens.
        Should only be called when standard extraction fails.
    """
    # This is a placeholder - actual implementation would call OpenAI API
    # For now, just return None to avoid unnecessary API calls
    
    # TODO: Implement OpenAI-based extraction with prompt:
    # """
    # Analysiere diesen HTML-Ausschnitt einer deutschen Stellengesuch-Anzeige.
    # Finde alle Telefonnummern, auch wenn sie:
    # - Durch Leerzeichen getrennt sind (0 1 7 6 1 2 3 4 5 6 7)
    # - Mit Worten geschrieben sind (null eins sieben sechs...)
    # - Mit Sternchen verschleiert sind (0176***4567)
    # - In Bildern versteckt sind (suche nach img alt text oder data attributes)
    # 
    # Gib NUR die normalisierte Nummer zurück im Format +49... oder 0...
    # Wenn keine Nummer gefunden: Gib 'NONE' zurück.
    # """
    
    return None
