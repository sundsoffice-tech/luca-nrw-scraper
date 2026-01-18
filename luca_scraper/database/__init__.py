# -*- coding: utf-8 -*-
"""Database layer for LUCA scraper"""

from luca_scraper.database.connection import (
    db,
    get_learning_engine,
    init_mode,
)
from luca_scraper.database.models import (
    init_db,
    migrate_db_unique_indexes,
)
from luca_scraper.database.queries import (
    is_query_done,
    mark_query_done,
    mark_url_seen,
    url_seen,
    insert_leads,
    start_run,
    finish_run,
)

__all__ = [
    # Connection
    "db",
    "get_learning_engine",
    "init_mode",
    # Models
    "init_db",
    "migrate_db_unique_indexes",
    # Queries
    "is_query_done",
    "mark_query_done",
    "mark_url_seen",
    "url_seen",
    "insert_leads",
    "start_run",
    "finish_run",
]
