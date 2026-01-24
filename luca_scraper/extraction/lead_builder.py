# -*- coding: utf-8 -*-
"""
Lead Builder Module
==================
Functions for building lead data dictionaries with dynamic scoring.

This module separates the scoring and lead data construction logic
from the crawler modules, providing a centralized way to build lead
data with consistent structure and scoring.
"""

from typing import Any, Dict, List, Optional


def build_lead_data(
    name: Optional[str],
    phones: List[str],
    email: Optional[str],
    location: Optional[str],
    title: Optional[str],
    url: str,
    phone_sources: Dict[str, str],
    portal: str = "generic",
    has_whatsapp: bool = False,
    tags: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a complete lead data dictionary with dynamic scoring.

    This function encapsulates the logic for:
    1. Selecting the main phone number from a list of phones
    2. Calculating dynamic score based on data completeness and quality
    3. Building a complete lead dictionary with all required fields

    Args:
        name: Contact person name (can be None, will default to empty string)
        phones: List of phone numbers (mobile numbers)
        email: Email address (can be None, will default to empty string)
        location: Location/region (Ort) (can be None, will default to empty string)
        title: Ad title or job title (can be None, will default to empty string)
        url: Source URL
        phone_sources: Dictionary mapping phone numbers to their extraction source
        portal: Portal/source identifier (e.g., "kleinanzeigen", "markt_de")
        has_whatsapp: Whether lead has WhatsApp number
        tags: Optional custom tags string (if None, will be auto-generated)

    Returns:
        Dictionary containing lead data with score, confidence, and quality metrics
    """
    # Use first mobile number found
    main_phone = phones[0] if phones else ""

    # Get phone source for scoring
    phone_source = phone_sources.get(main_phone, "unknown") if main_phone else "unknown"

    # ========================================
    # DYNAMIC SCORING: Use centralized scoring module
    # ========================================
    try:
        from luca_scraper.scoring.dynamic_scoring import calculate_dynamic_score
        dynamic_score, data_quality_score, confidence_score = calculate_dynamic_score(
            has_phone=bool(main_phone),
            has_email=bool(email),
            has_name=bool(name),
            has_title=bool(title),
            has_location=bool(location),
            phones_count=len(phones),
            has_whatsapp=has_whatsapp,
            phone_source=phone_source,
            portal=portal,
        )
    except ImportError:
        # Fallback to default scores if module not available
        dynamic_score = 85
        data_quality_score = 0.80
        confidence_score = 0.85

    # Auto-generate tags if not provided
    if tags is None:
        tags = f"{portal},candidate,mobile,direct_crawl"

    # Build lead data with dynamic scores
    lead = {
        "name": name or "",
        "rolle": "Vertrieb",
        "email": email or "",
        "telefon": main_phone,
        "quelle": url,
        "score": dynamic_score,
        "tags": tags,
        "lead_type": "candidate",
        "phone_type": "mobile",
        "opening_line": (title or "")[:200],
        "firma": "",
        "firma_groesse": "",
        "branche": "",
        "region": location or "",
        "frische": "neu",
        "confidence": confidence_score,
        "data_quality": data_quality_score,
        "phone_source": phone_source,
        "phones_found": len(phones),
        "has_whatsapp": has_whatsapp,
    }

    return lead


__all__ = ["build_lead_data"]
