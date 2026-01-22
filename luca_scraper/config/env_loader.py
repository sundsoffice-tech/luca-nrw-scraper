"""
LUCA NRW Scraper - Environment Variable Loader
===============================================
Reading and converting environment variables.

This module loads environment variables from .env files using python-dotenv.
load_dotenv() is called at import time to ensure all environment variables
are available when this module is imported.
"""

import os
import urllib.parse
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file
# This must happen before any os.getenv() calls to ensure .env values are available
load_dotenv(override=True)

# =========================
# ENVIRONMENT VARIABLES
# =========================

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
GCS_API_KEY = os.getenv("GCS_API_KEY", "")
GCS_CX_RAW = os.getenv("GCS_CX", "")
BING_API_KEY = os.getenv("BING_API_KEY", "")

# Database
DB_PATH = os.getenv("SCRAPER_DB", "scraper.db")

# Database Backend Selection
# Valid options: 'sqlite' (default) or 'django'
_DATABASE_BACKEND_RAW = os.getenv('SCRAPER_DB_BACKEND', 'sqlite').lower()
if _DATABASE_BACKEND_RAW not in ('sqlite', 'django'):
    raise ValueError(
        f"Invalid SCRAPER_DB_BACKEND value: '{_DATABASE_BACKEND_RAW}'. "
        f"Must be 'sqlite' or 'django'."
    )
DATABASE_BACKEND = _DATABASE_BACKEND_RAW


# =========================
# ENVIRONMENT TO CONFIG MAPPING
# =========================

# Maps config keys to (env_var_name, converter_function) tuples
ENV_MAPPINGS = {
    'http_timeout': ('HTTP_TIMEOUT', int),
    'max_fetch_size': ('MAX_FETCH_SIZE', int),
    'pool_size': ('POOL_SIZE', int),
    'async_limit': ('ASYNC_LIMIT', int),
    'async_per_host': ('ASYNC_PER_HOST', int),
    'http2_enabled': ('HTTP2', lambda x: x == "1"),
    'allow_pdf': ('ALLOW_PDF', lambda x: x == "1"),
    'allow_insecure_ssl': ('ALLOW_INSECURE_SSL', lambda x: x == "1"),
    'allow_pdf_non_cv': ('ALLOW_PDF_NON_CV', lambda x: x == "1"),
    'sleep_between_queries': ('SLEEP_BETWEEN_QUERIES', float),
    'max_google_pages': ('MAX_GOOGLE_PAGES', int),
    'circuit_breaker_penalty': ('CB_BASE_PENALTY', int),
    'circuit_breaker_api_penalty': ('CB_API_PENALTY', int),
    'retry_max_per_url': ('RETRY_MAX_PER_URL', int),
    'min_score': ('MIN_SCORE', int),
    'max_per_domain': ('MAX_PER_DOMAIN', int),
    'enable_kleinanzeigen': ('ENABLE_KLEINANZEIGEN', lambda x: x == "1"),
    'parallel_portal_crawl': ('PARALLEL_PORTAL_CRAWL', lambda x: x == "1"),
    'max_concurrent_portals': ('MAX_CONCURRENT_PORTALS', int),
}


# =========================
# AI CONFIG ENV MAPPINGS
# =========================

def load_ai_config_from_env():
    """
    Load AI configuration from environment variables.
    
    Returns:
        Dict with AI config overrides from environment variables
    """
    env_overrides = {}
    
    if os.getenv('AI_TEMPERATURE'):
        try:
            env_overrides['temperature'] = float(os.getenv('AI_TEMPERATURE'))
        except ValueError:
            pass
    
    if os.getenv('AI_MAX_TOKENS'):
        try:
            env_overrides['max_tokens'] = int(os.getenv('AI_MAX_TOKENS'))
        except ValueError:
            pass
    
    if os.getenv('AI_MODEL'):
        env_overrides['default_model'] = os.getenv('AI_MODEL')
    
    if os.getenv('AI_PROVIDER'):
        env_overrides['default_provider'] = os.getenv('AI_PROVIDER')
    
    return env_overrides


# =========================
# GOOGLE CUSTOM SEARCH
# =========================

def _normalize_cx(s: str) -> str:
    """Normalize Google Custom Search CX parameter."""
    if not s:
        return ""
    try:
        p = urllib.parse.urlparse(s)
        if p.query:
            q = urllib.parse.parse_qs(p.query)
            val = q.get("cx", [""])[0].strip()
            if val:
                return val
    except Exception:
        pass
    return s.strip()


# Normalize and build GCS configuration
GCS_CX = _normalize_cx(GCS_CX_RAW)
GCS_KEYS = [k.strip() for k in os.getenv("GCS_KEYS", "").split(",") if k.strip()] or ([GCS_API_KEY] if GCS_API_KEY else [])
GCS_CXS = [_normalize_cx(x) for x in os.getenv("GCS_CXS", "").split(",") if _normalize_cx(x)] or ([GCS_CX] if GCS_CX else [])

# Enable/Disable search engines
ENABLE_GOOGLE_CSE = bool(GCS_KEYS and GCS_CXS)
ENABLE_PERPLEXITY = bool(PERPLEXITY_API_KEY)
ENABLE_BING = bool(BING_API_KEY)


# =========================
# HELPER FUNCTIONS
# =========================

def _env_list(val: str, sep: str) -> List[str]:
    """Parse environment variable as list."""
    return [x.strip() for x in val.split(sep) if x.strip()]
