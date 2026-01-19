"""
script.py - Backward Compatibility Shim
========================================

This file provides backward compatibility for code that imports from 'script'.
It re-exports all functionality from scriptname.py.

DEPRECATION NOTICE:
  This file is maintained for backward compatibility only.
  New code should import directly from:
  - luca_scraper package (modular components)
  - scriptname module (main scraper logic)
  
Usage:
  from script import *  # Legacy - works but discouraged
  
Recommended:
  from luca_scraper import validate_config, parse_args
  from scriptname import run_scrape_once_async
"""

from scriptname import *
from scriptname import _bounded_process
