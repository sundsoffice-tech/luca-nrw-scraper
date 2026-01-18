"""
LUCA NRW Scraper - Search Query Management
==========================================
Search query building and search strategy management.
Phase 3 der Modularisierung.
"""

from .manager import (
    DEFAULT_QUERIES,
    INDUSTRY_QUERIES,
    RECRUITER_QUERIES,
    build_queries,
)

__all__ = [
    "DEFAULT_QUERIES",
    "INDUSTRY_QUERIES",
    "RECRUITER_QUERIES",
    "build_queries",
]
