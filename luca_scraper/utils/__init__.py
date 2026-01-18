# -*- coding: utf-8 -*-
"""Utility functions and helpers"""

from luca_scraper.utils.logging import log
from luca_scraper.utils.helpers import (
    etld1,
    is_likely_human_name,
    looks_like_company,
    has_nrw_signal,
    extract_company_name,
    detect_company_size,
    detect_recency,
    normalize_whitespace,
    clean_url,
)

__all__ = [
    'log',
    'etld1',
    'is_likely_human_name',
    'looks_like_company',
    'has_nrw_signal',
    'extract_company_name',
    'detect_company_size',
    'detect_recency',
    'normalize_whitespace',
    'clean_url',
]
