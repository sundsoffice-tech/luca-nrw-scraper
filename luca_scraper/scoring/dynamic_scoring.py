# -*- coding: utf-8 -*-
"""
Dynamic Lead Scoring Configuration Module
=========================================
Centralized configuration for dynamic lead scoring calculations.

This module provides shared scoring constants and utility functions
used by both generic.py and kleinanzeigen.py crawlers.
"""

from typing import Dict, Tuple

# ========================================
# PHONE SOURCE QUALITY SCORES
# ========================================
# Higher values indicate more reliable extraction methods

PHONE_SOURCE_QUALITY: Dict[str, float] = {
    "regex_standard": 0.10,        # Standard regex is reliable
    "whatsapp_enhanced": 0.15,     # WhatsApp links are very reliable
    "whatsapp_link": 0.15,         # WhatsApp links are very reliable
    "advanced_whatsapp": 0.15,     # WhatsApp links are very reliable
    "advanced_standard": 0.08,     # Advanced patterns are good
    "advanced_spaced": 0.05,       # Spaced numbers are medium confidence
    "advanced_obfuscated": 0.03,   # Obfuscated are lower confidence
    "advanced_words": 0.02,        # Word-based are lowest
    "advanced_best": 0.08,         # Best from advanced extraction
    "browser_extraction": 0.06,    # Browser extraction is reliable
    "unknown": 0.05,               # Default for unknown sources
}

# ========================================
# PORTAL REPUTATION SCORES
# ========================================
# Higher values indicate more reputable portals for job seekers

PORTAL_REPUTATION: Dict[str, int] = {
    "kleinanzeigen": 10,    # High reputation for job seekers
    "markt_de": 8,          # Medium-high reputation
    "meinestadt": 7,        # Medium reputation
    "quoka": 6,             # Medium reputation
    "kalaydo": 6,           # Medium reputation
    "direct_crawl": 5,      # Generic crawl
    "dhd24": 4,             # Lower reputation
    "generic": 5,           # Default for generic sources
}

# ========================================
# DATA COMPLETENESS BONUSES
# ========================================
# Points added to score based on presence of data fields

DATA_COMPLETENESS_SCORE_BONUSES: Dict[str, int] = {
    "phone": 20,
    "email": 15,
    "name": 10,
    "title": 5,
    "location": 3,
    "multiple_phones": 5,
    "whatsapp": 8,
}

DATA_COMPLETENESS_QUALITY_BONUSES: Dict[str, float] = {
    "phone": 0.30,
    "email": 0.20,
    "name": 0.15,
    "title": 0.10,
    "location": 0.05,
    "multiple_phones": 0.05,
    "whatsapp": 0.10,
}

# ========================================
# BASE SCORES BY PORTAL
# ========================================
# Starting score varies by portal

PORTAL_BASE_SCORES: Dict[str, int] = {
    "kleinanzeigen": 55,
    "markt_de": 52,
    "meinestadt": 52,
    "quoka": 50,
    "kalaydo": 50,
    "direct_crawl": 50,
    "dhd24": 48,
    "generic": 50,
}

# ========================================
# UTILITY FUNCTIONS
# ========================================

def get_phone_source_quality(source: str) -> float:
    """
    Get the quality score for a phone extraction source.
    
    Args:
        source: The phone extraction source identifier
        
    Returns:
        Quality score between 0.0 and 1.0
    """
    return PHONE_SOURCE_QUALITY.get(source, PHONE_SOURCE_QUALITY["unknown"])


def get_portal_reputation(portal: str) -> int:
    """
    Get the reputation bonus for a portal.
    
    Args:
        portal: The portal identifier
        
    Returns:
        Reputation bonus points
    """
    return PORTAL_REPUTATION.get(portal, PORTAL_REPUTATION["generic"])


def get_base_score(portal: str) -> int:
    """
    Get the base score for a portal.
    
    Args:
        portal: The portal identifier
        
    Returns:
        Base score points
    """
    return PORTAL_BASE_SCORES.get(portal, PORTAL_BASE_SCORES["generic"])


def cap_score(score: int) -> int:
    """
    Cap a score to the valid range [0, 100].
    
    Args:
        score: The raw score value
        
    Returns:
        Score capped to valid range
    """
    return max(0, min(100, score))


def cap_confidence(confidence: float) -> float:
    """
    Cap a confidence value to the valid range [0.0, 1.0].
    
    Args:
        confidence: The raw confidence value
        
    Returns:
        Confidence capped to valid range
    """
    return max(0.0, min(1.0, confidence))


def calculate_dynamic_score(
    has_phone: bool = False,
    has_email: bool = False,
    has_name: bool = False,
    has_title: bool = False,
    has_location: bool = False,
    phones_count: int = 0,
    has_whatsapp: bool = False,
    phone_source: str = "unknown",
    portal: str = "generic",
) -> Tuple[int, float, float]:
    """
    Calculate dynamic score, data quality, and confidence for a lead.
    
    Args:
        has_phone: Whether lead has a phone number
        has_email: Whether lead has an email
        has_name: Whether lead has a name
        has_title: Whether lead has a title
        has_location: Whether lead has a location
        phones_count: Number of phones found
        has_whatsapp: Whether lead has a WhatsApp number
        phone_source: The source of the primary phone number
        portal: The source portal
        
    Returns:
        Tuple of (score, data_quality, confidence)
    """
    # Start with base score for portal
    score = get_base_score(portal)
    data_quality = 0.0
    
    # Data completeness bonuses
    if has_phone:
        score += DATA_COMPLETENESS_SCORE_BONUSES["phone"]
        data_quality += DATA_COMPLETENESS_QUALITY_BONUSES["phone"]
    if has_email:
        score += DATA_COMPLETENESS_SCORE_BONUSES["email"]
        data_quality += DATA_COMPLETENESS_QUALITY_BONUSES["email"]
    if has_name:
        score += DATA_COMPLETENESS_SCORE_BONUSES["name"]
        data_quality += DATA_COMPLETENESS_QUALITY_BONUSES["name"]
    if has_title:
        score += DATA_COMPLETENESS_SCORE_BONUSES["title"]
        data_quality += DATA_COMPLETENESS_QUALITY_BONUSES["title"]
    if has_location:
        score += DATA_COMPLETENESS_SCORE_BONUSES["location"]
        data_quality += DATA_COMPLETENESS_QUALITY_BONUSES["location"]
    
    # Multiple phones bonus
    if phones_count > 1:
        score += DATA_COMPLETENESS_SCORE_BONUSES["multiple_phones"]
        data_quality += DATA_COMPLETENESS_QUALITY_BONUSES["multiple_phones"]
    
    # WhatsApp bonus
    if has_whatsapp:
        score += DATA_COMPLETENESS_SCORE_BONUSES["whatsapp"]
        data_quality += DATA_COMPLETENESS_QUALITY_BONUSES["whatsapp"]
    
    # Phone source quality bonus
    source_bonus = get_phone_source_quality(phone_source)
    data_quality += source_bonus
    score += int(source_bonus * 50)  # Scale to score points
    
    # Portal reputation bonus
    portal_bonus = get_portal_reputation(portal)
    score += portal_bonus
    data_quality += portal_bonus / 100.0
    
    # Cap scores
    score = cap_score(score)
    data_quality = cap_confidence(data_quality)
    
    # Calculate confidence
    confidence = 0.50  # Base confidence
    if portal == "kleinanzeigen":
        confidence = 0.55  # Higher base for kleinanzeigen
    
    if has_phone:
        confidence += 0.20
    if has_email:
        confidence += 0.10
    if has_name:
        confidence += 0.08
    if has_whatsapp:
        confidence += 0.07
    if phone_source.startswith("whatsapp"):
        confidence += 0.05
    elif phone_source == "regex_standard":
        confidence += 0.05
    
    confidence = cap_confidence(confidence)
    
    return score, data_quality, confidence


__all__ = [
    "PHONE_SOURCE_QUALITY",
    "PORTAL_REPUTATION",
    "DATA_COMPLETENESS_SCORE_BONUSES",
    "DATA_COMPLETENESS_QUALITY_BONUSES",
    "PORTAL_BASE_SCORES",
    "get_phone_source_quality",
    "get_portal_reputation",
    "get_base_score",
    "cap_score",
    "cap_confidence",
    "calculate_dynamic_score",
]
