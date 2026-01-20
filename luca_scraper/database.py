"""
LUCA NRW Scraper - Database Layer
==================================
SQLite Connection und Schema Management
Phase 1 der Modularisierung.

Database Backend Selection:
---------------------------
This module supports two backends:
- 'sqlite' (default): Direct SQLite connection
- 'django': Django ORM adapter

Set via SCRAPER_DB_BACKEND environment variable.

REFACTORING NOTE:
-----------------
This module has been refactored into three separate modules:
- connection.py: SQLite connections, context managers, thread-safety
- schema.py: Schema definitions and migrations
- repository.py: CRUD operations and queries

This file now serves as a backward compatibility layer, re-exporting
functions from the new modules.
"""

import logging

# Import DB_PATH and DATABASE_BACKEND from config
from .config import DATABASE_BACKEND

logger = logging.getLogger(__name__)


# =========================
# RE-EXPORT FROM NEW MODULES
# =========================

# Re-export from connection module
from .connection import (
    DB_PATH,
    db,
    init_db,
    transaction,
)

# Re-export from schema module
from .schema import (
    migrate_db_unique_indexes,
)

# Re-export from repository module
from .repository import (
    # Django backend functions (if available)
    upsert_lead,
    get_lead_count,
    lead_exists,
    get_lead_by_id,
    update_lead,
    
    # SQLite-specific functions
    upsert_lead_sqlite,
    lead_exists_sqlite,
    is_url_seen_sqlite,
    mark_url_seen_sqlite,
    is_query_done_sqlite,
    mark_query_done_sqlite,
    start_scraper_run_sqlite,
    finish_scraper_run_sqlite,
    get_lead_count_sqlite,
    
    # Sync function
    sync_status_to_scraper,
)


# =========================
# EXPORTS
# =========================

# Export the global ready flag for external access
# Base exports available for all backends
_BASE_EXPORTS = [
    'db', 'init_db', 'transaction', 'DB_PATH', 
    'migrate_db_unique_indexes', 'sync_status_to_scraper',
    'DATABASE_BACKEND',
    # SQLite-specific functions
    'upsert_lead_sqlite',
    'lead_exists_sqlite',
    'is_url_seen_sqlite',
    'mark_url_seen_sqlite',
    'is_query_done_sqlite',
    'mark_query_done_sqlite',
    'start_scraper_run_sqlite',
    'finish_scraper_run_sqlite',
    'get_lead_count_sqlite',
]

# When using Django backend, also export Django adapter functions
if DATABASE_BACKEND == 'django':
    __all__ = _BASE_EXPORTS + [
        # Django backend functions
        'upsert_lead', 'get_lead_count', 'lead_exists', 
        'get_lead_by_id', 'update_lead'
    ]
else:
    __all__ = _BASE_EXPORTS
