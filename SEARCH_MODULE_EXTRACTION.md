# Search Module Extraction - Phase 2 Complete

## Overview
Successfully extracted all search-related functions from `scriptname.py` into the modular `luca_scraper/search/` package.

## Extracted Files

### 1. `luca_scraper/search/perplexity.py`
**Source:** scriptname.py lines 1605-1638  
**Functions:**
- `search_perplexity_async(query: str) -> List[Dict[str, str]]`

**Description:** Perplexity AI (sonar) search integration returning citation URLs.

---

### 2. `luca_scraper/search/google_cse.py`
**Source:** scriptname.py lines 1640-1734  
**Functions:**
- `google_cse_search_async(q: str, max_results: int = 60, date_restrict: Optional[str] = None) -> Tuple[List[Dict[str, str]], bool]`

**Description:** Google Custom Search Engine with API key rotation, pagination, deduplication, and URL prioritization.

**Features:**
- Multi-key/CX rotation for rate limiting
- Automatic retry with exponential backoff
- 429 rate limit detection
- URL normalization and deduplication
- Path filtering with `is_denied()` and `path_ok()`

---

### 3. `luca_scraper/search/duckduckgo.py`
**Source:** scriptname.py lines 1737-1825  
**Functions:**
- `duckduckgo_search_async(query: str, max_results: int = 10, date_restrict: Optional[str] = None) -> List[Dict[str, str]]`

**Description:** DuckDuckGo search with hardened proxy control.

**Features:**
- TOR/SOCKS5 proxy support
- "Nuclear" proxy cleanup for direct connections
- Automatic retry (1 retry allowed)
- ConnectTimeout detection and handling

---

### 4. `luca_scraper/search/kleinanzeigen.py`
**Source:** scriptname.py lines 1827-1900  
**Functions:**
- `_ka_keywords_from_query(q: str) -> str`
- `kleinanzeigen_search_async(q: str, max_results: int = KLEINANZEIGEN_MAX_RESULTS) -> List[Dict[str, str]]`

**Description:** Kleinanzeigen.de Stellengesuche (job seeker) scraper.

**Features:**
- Query normalization (removes site:, operators, special chars)
- BeautifulSoup HTML parsing
- URL extraction and deduplication
- Configurable via `ENABLE_KLEINANZEIGEN` environment variable

---

### 5. `luca_scraper/search/manager.py`
**Source:** scriptname.py lines 894-906, 1483-1602  
**Functions:**
- `_normalize_cx(s: str) -> str` (line 894)
- `_jitter(a=0.2, b=0.8)` (line 906)
- `_normalize_for_dedupe(u: str) -> str` (line 1483)
- `_extract_url(item: UrlLike) -> str` (line 1512)
- `prioritize_urls(urls: List[str]) -> List[str]` (line 1523)

**Description:** URL normalization, deduplication, and prioritization utilities.

**Features:**
- **prioritize_urls:** Scores URLs based on patterns (/kontakt, /impressum, /karriere, etc.)
- **_normalize_for_dedupe:** Removes tracking params (utm_*, gclid, fbclid, page)
- **_normalize_cx:** Extracts CX from Google CSE URLs
- **_extract_url:** Flexible URL extraction from string or dict
- **_jitter:** Random delay for rate limiting

---

## Import Structure

### Configuration Imports
```python
from luca_scraper.config import (
    HTTP_TIMEOUT,
    ENABLE_KLEINANZEIGEN,
    KLEINANZEIGEN_MAX_RESULTS,
    USE_TOR,
    PROXY_ENV_VARS,
)
```

### Fallback Imports from scriptname.py
All modules include fallback imports for functions still in scriptname.py:
```python
try:
    from scriptname import http_get_async, is_denied, path_ok, log
except ImportError:
    # Fallback implementations
    pass
```

---

## Exported Functions

### Public API (`luca_scraper/search/__init__.py`)
```python
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
```

---

## Testing & Verification

### Import Test
```python
from luca_scraper.search import *
# All 9 functions imported successfully
```

### Utility Function Tests
- ✅ `_normalize_cx`: Extracts CX from URLs
- ✅ `_jitter`: Generates random delays (0.2-0.8)
- ✅ `_normalize_for_dedupe`: Removes tracking params
- ✅ `_extract_url`: Handles string and dict inputs
- ✅ `prioritize_urls`: Ranks URLs by contact page patterns

### Function Signatures
All functions maintain exact signatures from original code:
- Type hints preserved
- Default parameters unchanged
- Return types documented

---

## Code Quality

### Code Review Addressed
- ✅ Fixed capitalization in Perplexity system message
- ✅ Clarified MAX_GOOGLE_PAGES comment
- ✅ Improved retry loop comments in DuckDuckGo
- ✅ Fixed retry logging message consistency

### Best Practices
- Proper docstrings for all public functions
- Type hints on all parameters and return values
- Graceful fallbacks for missing dependencies
- Consistent error handling

---

## Next Steps

The following functions remain in `scriptname.py` and will be extracted in future phases:
- Network layer (`http_get_async`, `http_post_async`)
- Content filtering (`is_denied`, `path_ok`)
- Logging system (`log`)
- Database operations
- Extraction and scoring functions

---

## Statistics

**Total Files Created:** 6  
**Total Lines Extracted:** ~400 lines  
**Total Functions Extracted:** 9  
**Source Range:** scriptname.py lines 894-1900

---

**Status:** ✅ Complete  
**Date:** 2025-01-18  
**Branch:** copilot/refactor-search-module-and-crawlers
