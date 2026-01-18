"""
Centralized Configuration Module

This module provides centralized configuration for the Telis Recruitment system,
reducing hardcoded values throughout the codebase.
"""
import os
from django.conf import settings
from pathlib import Path


# ===========================
# Database Paths
# ===========================

def get_scraper_db_path():
    """
    Get the path to the scraper database.
    
    Returns:
        str: Absolute path to scraper.db
    """
    return getattr(
        settings,
        'SCRAPER_DB_PATH',
        os.path.join(settings.BASE_DIR.parent, 'scraper.db')
    )


# ===========================
# Rate Limiting
# ===========================

# Rate limit for opt-in API endpoint (requests per minute per IP)
API_RATE_LIMIT_OPT_IN = getattr(
    settings,
    'API_RATE_LIMIT_OPT_IN',
    '10/m'  # 10 requests per minute
)

# Rate limit for CSV import API endpoint (requests per minute per user)
API_RATE_LIMIT_IMPORT = getattr(
    settings,
    'API_RATE_LIMIT_IMPORT',
    '5/m'  # 5 requests per minute
)

# Rate limit for general API endpoints
API_RATE_LIMIT_DEFAULT = getattr(
    settings,
    'API_RATE_LIMIT_DEFAULT',
    '60/m'  # 60 requests per minute
)


# ===========================
# Upload Limits
# ===========================

# Maximum CSV upload size in bytes (default: 10MB)
MAX_CSV_UPLOAD_SIZE = getattr(
    settings,
    'MAX_CSV_UPLOAD_SIZE',
    10 * 1024 * 1024  # 10 MB
)

# Maximum number of rows to process in a single CSV import
MAX_CSV_ROWS = getattr(
    settings,
    'MAX_CSV_ROWS',
    10000
)


# ===========================
# Lead Quality Defaults
# ===========================

# Default quality score for new leads
DEFAULT_LEAD_QUALITY_SCORE = getattr(
    settings,
    'DEFAULT_LEAD_QUALITY_SCORE',
    50
)

# Minimum quality score for hot leads
HOT_LEAD_MIN_SCORE = getattr(
    settings,
    'HOT_LEAD_MIN_SCORE',
    80
)

# Minimum interest level for hot leads
HOT_LEAD_MIN_INTEREST = getattr(
    settings,
    'HOT_LEAD_MIN_INTEREST',
    3
)


# ===========================
# Email Integration (Brevo)
# ===========================

# Brevo API configuration
BREVO_API_KEY = getattr(settings, 'BREVO_API_KEY', None)
BREVO_SENDER_EMAIL = getattr(settings, 'BREVO_SENDER_EMAIL', 'info@telis.de')
BREVO_SENDER_NAME = getattr(settings, 'BREVO_SENDER_NAME', 'TELIS Recruitment')


# ===========================
# CSV Import Settings
# ===========================

# Supported CSV delimiters
CSV_DELIMITERS = [',', ';', '\t']

# CSV encodings to try in order
CSV_ENCODINGS = ['utf-8', 'latin-1', 'iso-8859-1']


# ===========================
# Paths and Directories
# ===========================

def get_data_dir():
    """
    Get the data directory path.
    
    Returns:
        Path: Path to data directory
    """
    data_dir = getattr(
        settings,
        'DATA_DIR',
        settings.BASE_DIR.parent / 'data'
    )
    return Path(data_dir)


def get_backup_dir():
    """
    Get the backup directory path.
    
    Returns:
        Path: Path to backup directory
    """
    backup_dir = getattr(
        settings,
        'BACKUP_DIR',
        get_data_dir() / 'backups'
    )
    path = Path(backup_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_temp_dir():
    """
    Get the temporary files directory path.
    
    Returns:
        Path: Path to temp directory
    """
    temp_dir = getattr(
        settings,
        'TEMP_DIR',
        settings.BASE_DIR / 'tmp'
    )
    path = Path(temp_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path
