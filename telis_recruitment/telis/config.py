"""
Configuration constants for the Telis Recruitment application.

This module centralizes all configuration values that were previously hardcoded,
making them easier to maintain and override via environment variables.
"""

import os
from pathlib import Path
from django.conf import settings


# Database paths
def get_scraper_db_path():
    """
    Get the path to the scraper database.
    
    Returns:
        Path: Path to scraper.db file
    """
    return getattr(
        settings, 
        'SCRAPER_DB_PATH', 
        os.path.join(settings.BASE_DIR.parent, 'scraper.db')
    )


# Rate limits
API_RATE_LIMIT_OPT_IN = getattr(settings, 'API_RATE_LIMIT_OPT_IN', '10/m')
"""Rate limit for opt-in API endpoint (default: 10 requests per minute)"""

API_RATE_LIMIT_IMPORT = getattr(settings, 'API_RATE_LIMIT_IMPORT', '5/m')
"""Rate limit for CSV import API endpoint (default: 5 requests per minute)"""


# Upload limits
MAX_CSV_UPLOAD_SIZE = getattr(settings, 'MAX_CSV_UPLOAD_SIZE', 10 * 1024 * 1024)
"""Maximum CSV file upload size in bytes (default: 10MB)"""


# CSV Import settings
CSV_IMPORT_DEFAULT_PATHS = [
    'vertrieb_kontakte.csv',
    'leads.csv',
    'export.csv',
    'vertrieb_kontakte.xlsx',
]
"""Default CSV file names to search for during import"""


# Lead scoring defaults
DEFAULT_QUALITY_SCORE = getattr(settings, 'DEFAULT_QUALITY_SCORE', 50)
"""Default quality score for leads without explicit score (default: 50)"""

LANDING_PAGE_QUALITY_SCORE = getattr(settings, 'LANDING_PAGE_QUALITY_SCORE', 70)
"""Quality score for leads from landing page opt-in (default: 70)"""


# Email tracking defaults
DEFAULT_INTEREST_LEVEL = getattr(settings, 'DEFAULT_INTEREST_LEVEL', 3)
"""Default interest level for new leads (default: 3 out of 5)"""


# Validation settings
MIN_PHONE_LENGTH = getattr(settings, 'MIN_PHONE_LENGTH', 11)
"""Minimum length for valid phone numbers (default: 11)"""

MAX_PHONE_LENGTH = getattr(settings, 'MAX_PHONE_LENGTH', 15)
"""Maximum length for valid phone numbers (default: 15)"""
