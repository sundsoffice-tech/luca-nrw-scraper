# -*- coding: utf-8 -*-
"""Extraction layer for contacts, phones, emails"""

from luca_scraper.extraction.phone import (
    normalize_phone,
    validate_phone,
    _phone_context_ok,
)

from luca_scraper.extraction.email import (
    clean_email,
    normalize_email,
    is_private_email,
    is_valid_email,
    email_quality,
    extract_emails_from_text,
)

__all__ = [
    # Phone
    'normalize_phone',
    'validate_phone',
    '_phone_context_ok',
    # Email
    'clean_email',
    'normalize_email',
    'is_private_email',
    'is_valid_email',
    'email_quality',
    'extract_emails_from_text',
]
