# -*- coding: utf-8 -*-
"""
LUCA NRW Scraper - Lead Generation Tool
Refactored modular package structure
"""

__version__ = "2.3.0"
__author__ = "LUCA Team"

# Phase 2: Re-export new modules for convenience
# Import from submodules with graceful fallback
try:
    from luca_scraper import search, scoring, crawlers
    __all__ = ['search', 'scoring', 'crawlers', 'config', 'database', 'extraction', 'network', 'utils']
except ImportError:
    # Fallback if modules not yet available
    __all__ = ['config', 'database', 'extraction', 'network', 'utils']
