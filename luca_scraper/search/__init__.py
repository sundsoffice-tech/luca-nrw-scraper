# -*- coding: utf-8 -*-
"""Search engines and query building"""

from .perplexity import search_perplexity_async
from .google_cse import google_cse_search_async
from .duckduckgo import duckduckgo_search_async
from .kleinanzeigen import kleinanzeigen_search_async
from .manager import (
    prioritize_urls,
    _normalize_for_dedupe,
    _normalize_cx,
    _extract_url,
    _jitter,
)

__all__ = [
    # Search functions
    "search_perplexity_async",
    "google_cse_search_async",
    "duckduckgo_search_async",
    "kleinanzeigen_search_async",
    # Utility functions
    "prioritize_urls",
    "_normalize_for_dedupe",
    "_normalize_cx",
    "_extract_url",
    "_jitter",
]
