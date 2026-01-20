"""
Extraction Module
=================
Contact information extraction utilities.

This module provides centralized extraction logic for:
- Phone numbers (standard regex, advanced patterns, obfuscated)
- WhatsApp numbers (from HTML links and attributes)
- Email addresses

Extracted from luca_scraper/crawlers/generic.py and luca_scraper/crawlers/kleinanzeigen.py
to eliminate code duplication and provide reusable extraction functions.
"""

from .phone_email_extraction import (
    extract_phone_numbers,
    extract_email_address,
    extract_whatsapp_number,
)

__all__ = [
    "extract_phone_numbers",
    "extract_email_address", 
    "extract_whatsapp_number",
]
