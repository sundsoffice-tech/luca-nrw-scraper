"""
LUCA NRW Scraper - Database Router
===================================
Central abstraction layer for database operations.

This module routes database operations to either:
- SQLite backend (database.py) when DATABASE_BACKEND='sqlite'
- Django ORM backend (django_db.py) when DATABASE_BACKEND='django'

Provides a unified API for:
- Lead management (upsert_lead, lead_exists, get_lead_count)
- URL tracking (is_url_seen, mark_url_seen)
- Query tracking (is_query_done, mark_query_done)
- Scraper run tracking (start_scraper_run, finish_scraper_run)

Usage:
    from luca_scraper.db_router import upsert_lead, is_url_seen, start_scraper_run
    
    # These calls will automatically route to the correct backend
    run_id = start_scraper_run()
    lead_id, created = upsert_lead(lead_data)
    if not is_url_seen(url):
        mark_url_seen(url, run_id)
"""

import logging
from typing import Dict, Optional, Tuple

from .config import DATABASE_BACKEND

logger = logging.getLogger(__name__)


# =========================
# BACKEND ROUTING LOGIC
# =========================

if DATABASE_BACKEND == 'django':
    logger.info("db_router: Using Django ORM backend")
    
    # Import Django implementations
    from . import django_db
    
    # Lead management functions
    upsert_lead = django_db.upsert_lead
    lead_exists = django_db.lead_exists
    get_lead_count = django_db.get_lead_count
    get_lead_by_id = django_db.get_lead_by_id
    update_lead = django_db.update_lead
    
    # URL tracking functions
    is_url_seen = django_db.is_url_seen
    mark_url_seen = django_db.mark_url_seen
    
    # Query tracking functions
    is_query_done = django_db.is_query_done
    mark_query_done = django_db.mark_query_done
    
    # Scraper run tracking functions
    start_scraper_run = django_db.start_scraper_run
    finish_scraper_run = django_db.finish_scraper_run

else:
    logger.info("db_router: Using SQLite backend")
    
    # Import SQLite implementations
    from . import database
    
    # Lead management functions
    upsert_lead = database.upsert_lead_sqlite
    lead_exists = database.lead_exists_sqlite
    get_lead_count = database.get_lead_count_sqlite
    
    # URL tracking functions
    is_url_seen = database.is_url_seen_sqlite
    mark_url_seen = database.mark_url_seen_sqlite
    
    # Query tracking functions
    is_query_done = database.is_query_done_sqlite
    mark_query_done = database.mark_query_done_sqlite
    
    # Scraper run tracking functions
    start_scraper_run = database.start_scraper_run_sqlite
    finish_scraper_run = database.finish_scraper_run_sqlite
    
    # SQLite-specific functions (not available in Django backend)
    # These can be imported directly if needed
    get_lead_by_id = None
    update_lead = None


# =========================
# PUBLIC API
# =========================

__all__ = [
    # Lead management
    'upsert_lead',
    'lead_exists',
    'get_lead_count',
    
    # URL tracking
    'is_url_seen',
    'mark_url_seen',
    
    # Query tracking
    'is_query_done',
    'mark_query_done',
    
    # Scraper run tracking
    'start_scraper_run',
    'finish_scraper_run',
    
    # Backend info
    'DATABASE_BACKEND',
]


# Export backend info for debugging
def get_backend_info() -> Dict[str, str]:
    """
    Get information about the active database backend.
    
    Returns:
        Dictionary with backend information
    """
    return {
        'backend': DATABASE_BACKEND,
        'module': 'django_db' if DATABASE_BACKEND == 'django' else 'database',
    }
