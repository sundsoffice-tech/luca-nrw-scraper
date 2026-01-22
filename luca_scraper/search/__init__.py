"""
LUCA NRW Scraper - Search Query Management
==========================================
Search query building and search strategy management.
Phase 3 der Modularisierung.
"""

from .manager import (
    DEFAULT_QUERIES,
    INDUSTRY_QUERIES,
    build_queries,
    # NEU: Dork-Set Support
    DORK_SETS,
    get_dork_set,
    build_queries_with_dork_set,
)

__all__ = [
    "DEFAULT_QUERIES",
    "INDUSTRY_QUERIES",
    "build_queries",
    # NEU: Dork-Set Support
    "DORK_SETS",
    "get_dork_set",
    "build_queries_with_dork_set",
]
