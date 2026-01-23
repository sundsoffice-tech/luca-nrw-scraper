"""
LUCA NRW Scraper - Configuration Defaults
==========================================
Hardcoded default values and constants (timeouts, limits, feature flags).
"""

import os

# Default fallback for the insecure SSL flag (0 = secure)
ALLOW_INSECURE_SSL_ENV_DEFAULT = "0"
ALLOW_INSECURE_SSL_DEFAULT = ALLOW_INSECURE_SSL_ENV_DEFAULT == "1"


# =========================
# CONFIGURATION DEFAULTS
# =========================

# Configuration defaults (Priority 3: Hardcoded)
CONFIG_DEFAULTS = {
    # HTTP & Networking
    'http_timeout': 10,
    'max_fetch_size': 2 * 1024 * 1024,  # 2MB
    'pool_size': 12,
    'async_limit': 35,
    'async_per_host': 3,
    'http2_enabled': True,
    
    # SSL & PDF
    'allow_pdf': False,
    'allow_insecure_ssl': ALLOW_INSECURE_SSL_DEFAULT,
    'allow_pdf_non_cv': False,
    
    # Rate Limiting
    'sleep_between_queries': 2.7,
    'max_google_pages': 2,
    'circuit_breaker_penalty': 30,
    'circuit_breaker_api_penalty': 15,
    'retry_max_per_url': 2,
    
    # Scoring
    'min_score': 40,
    'max_per_domain': 5,
    'default_quality_score': 50,
    'confidence_threshold': 0.35,
    
    # Feature Flags
    'enable_kleinanzeigen': True,
    'enable_telefonbuch': True,
    'parallel_portal_crawl': True,
    'max_concurrent_portals': 5,
    
    # Content
    'max_content_length': 2 * 1024 * 1024,  # 2MB
    'config_version': 0,
}


# =========================
# HTTP & NETWORKING CONSTANTS
# =========================

# User Agent
USER_AGENT = "Mozilla/5.0 (compatible; VertriebFinder/2.3; +https://example.com)"

# Proxy environment variables
PROXY_ENV_VARS = [
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
    "FTP_PROXY", "ftp_proxy", "SOCKS_PROXY", "socks_proxy"
]

# Use TOR
USE_TOR = False


# =========================
# CONTENT TYPE CONSTANTS
# =========================

# Content limits and filters
BINARY_CT_PREFIXES = ("image/", "video/", "audio/")
DENY_CT_EXACT = {
    "application/zip", "application/x-tar", "application/x-gzip"
}
PDF_CT = "application/pdf"


# =========================
# RETRY & CIRCUIT BREAKER
# =========================

# Retry settings
RETRY_INCLUDE_403 = (os.getenv("RETRY_INCLUDE_403", "0") == "1")
RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "6.0"))

# Robots cache
ROBOTS_CACHE_TTL = int(os.getenv("ROBOTS_CACHE_TTL", "21600"))  # 6h


# =========================
# FEATURE FLAGS & LIMITS
# =========================

# Kleinanzeigen
KLEINANZEIGEN_MAX_RESULTS = int(os.getenv("KLEINANZEIGEN_MAX_RESULTS", "20"))

# Telefonbuch Enrichment
TELEFONBUCH_STRICT_MODE = (os.getenv("TELEFONBUCH_STRICT_MODE", "1") == "1")
TELEFONBUCH_RATE_LIMIT = float(os.getenv("TELEFONBUCH_RATE_LIMIT", "3.0"))
TELEFONBUCH_CACHE_DAYS = int(os.getenv("TELEFONBUCH_CACHE_DAYS", "7"))
TELEFONBUCH_MOBILE_ONLY = (os.getenv("TELEFONBUCH_MOBILE_ONLY", "1") == "1")

# Portal crawling
PORTAL_CONCURRENCY_PER_SITE = int(os.getenv("PORTAL_CONCURRENCY_PER_SITE", "2"))

# Internal depth per domain
INTERNAL_DEPTH_PER_DOMAIN = int(os.getenv("INTERNAL_DEPTH_PER_DOMAIN", "10"))

# Seed force
SEED_FORCE = (os.getenv("SEED_FORCE", "0") == "1")

# Cache TTL settings
QUERY_CACHE_TTL_HOURS = int(os.getenv("QUERY_CACHE_TTL_HOURS", "24"))  # How long to remember completed queries (hours)
URL_SEEN_TTL_HOURS = int(os.getenv("URL_SEEN_TTL_HOURS", "168"))  # How long to remember seen URLs (hours, default 7 days)


# =========================
# EXPORT FIELDS
# =========================

DEFAULT_CSV = "vertrieb_kontakte.csv"
DEFAULT_XLSX = "vertrieb_kontakte.xlsx"

ENH_FIELDS = [
    "name", "rolle", "email", "telefon", "quelle", "score", "tags", "region",
    "role_guess", "lead_type", "salary_hint", "commission_hint", "opening_line",
    "ssl_insecure", "company_name", "company_size", "hiring_volume",
    "industry", "recency_indicator", "location_specific",
    "confidence_score", "last_updated", "data_quality",
    "phone_type", "whatsapp_link", "private_address", "social_profile_url",
    "ai_category", "ai_summary",
    "experience_years", "skills", "availability", "current_status", "industries", "location", "profile_text",
    "candidate_status", "mobility", "industries_experience", "source_type",
    "profile_url", "cv_url", "contact_preference", "last_activity", "name_validated", "crm_status",
    # NEU: Erweiterte Quellen-Spalten für dork_set="new_sources"
    "source_category", "source_priority", "dork_used",
]

LEAD_FIELDS = [
    "name", "rolle", "email", "telefon", "quelle", "score", "tags", "region",
    "role_guess", "salary_hint", "commission_hint", "opening_line", "ssl_insecure",
    "company_name", "company_size", "hiring_volume", "industry",
    "recency_indicator", "location_specific", "confidence_score",
    "last_updated", "data_quality", "phone_type", "whatsapp_link",
    "private_address", "social_profile_url", "ai_category", "ai_summary",
    "crm_status",
    "lead_type",
    # NEU: Erweiterte Quellen-Spalten für dork_set="new_sources"
    "source_category", "source_priority", "dork_used",
]


# =========================
# AI CONFIGURATION DEFAULTS
# =========================

AI_CONFIG_DEFAULTS = {
    'temperature': 0.3,
    'top_p': 1.0,
    'max_tokens': 4000,
    'learning_rate': 0.01,
    'daily_budget': 5.0,
    'monthly_budget': 150.0,
    'confidence_threshold': 0.35,
    'retry_limit': 2,
    'timeout_seconds': 30,
    'default_provider': 'OpenAI',
    'default_model': 'gpt-4o-mini',
    'default_model_display': 'GPT-4o Mini',
}


# =========================
# CONFIG REFRESH INTERVAL
# =========================

try:
    CONFIG_REFRESH_INTERVAL_SECONDS = max(1, int(os.getenv("CONFIG_REFRESH_INTERVAL_SECONDS", "30")))
except ValueError:
    CONFIG_REFRESH_INTERVAL_SECONDS = 30


# =========================
# HELPER FUNCTIONS
# =========================

def _jitter(a=0.2, b=0.8):
    """Generate random jitter value."""
    import random
    return a + random.random() * (b - a)
