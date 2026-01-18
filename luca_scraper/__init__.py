"""
LUCA NRW Scraper
================
Lead-Generierungs-Tool für NRW

Phase 1: Konsolidierung
- Extrahierte Konfiguration aus scriptname.py
- Extrahierte Database Layer aus scriptname.py
- Backward Compatibility durch Re-Exports

Version: 2.0.0
"""

__version__ = "2.0.0"

# =========================
# Re-export Config
# =========================

from .config import (
    # API Keys
    OPENAI_API_KEY,
    PERPLEXITY_API_KEY,
    GCS_API_KEY,
    GCS_CX_RAW,
    BING_API_KEY,
    GCS_KEYS,
    GCS_CXS,
    GCS_CX,
    
    # Database
    DB_PATH,
    
    # HTTP & Networking
    HTTP_TIMEOUT,
    MAX_FETCH_SIZE,
    POOL_SIZE,
    ASYNC_LIMIT,
    ASYNC_PER_HOST,
    HTTP2_ENABLED,
    USE_TOR,
    ALLOW_PDF,
    ALLOW_INSECURE_SSL,
    ALLOW_PDF_NON_CV,
    USER_AGENT,
    PROXY_ENV_VARS,
    
    # Rate Limiting
    SLEEP_BETWEEN_QUERIES,
    MAX_GOOGLE_PAGES,
    CB_BASE_PENALTY,
    CB_API_PENALTY,
    RETRY_INCLUDE_403,
    RETRY_MAX_PER_URL,
    RETRY_BACKOFF_BASE,
    
    # Scoring
    MIN_SCORE_ENV,
    MAX_PER_DOMAIN,
    INTERNAL_DEPTH_PER_DOMAIN,
    DEFAULT_QUALITY_SCORE,
    MAX_CONTENT_LENGTH,
    BINARY_CT_PREFIXES,
    DENY_CT_EXACT,
    PDF_CT,
    SEED_FORCE,
    
    # Feature Flags
    ENABLE_KLEINANZEIGEN,
    KLEINANZEIGEN_MAX_RESULTS,
    TELEFONBUCH_ENRICHMENT_ENABLED,
    TELEFONBUCH_STRICT_MODE,
    TELEFONBUCH_RATE_LIMIT,
    TELEFONBUCH_CACHE_DAYS,
    TELEFONBUCH_MOBILE_ONLY,
    PARALLEL_PORTAL_CRAWL,
    MAX_CONCURRENT_PORTALS,
    PORTAL_CONCURRENCY_PER_SITE,
    ENABLE_GOOGLE_CSE,
    ENABLE_PERPLEXITY,
    ENABLE_BING,
    
    # NRW Cities
    NRW_CITIES,
    NRW_CITIES_EXTENDED,
    NRW_BIG_CITIES,
    METROPOLIS,
    NRW_REGIONS,
    
    # Job Titles
    SALES_TITLES,
    
    # Search Patterns
    PRIVATE_MAILS,
    MOBILE_PATTERNS,
    REGION,
    CONTACT,
    SALES,
    
    # Portal URLs
    KLEINANZEIGEN_URLS,
    MARKT_DE_URLS,
    QUOKA_DE_URLS,
    KALAYDO_DE_URLS,
    MEINESTADT_DE_URLS,
    FREELANCER_PORTAL_URLS,
    DHD24_URLS,
    FREELANCERMAP_URLS,
    FREELANCE_DE_URLS,
    DIRECT_CRAWL_URLS,
    
    # Blacklists
    DROP_MAILBOX_PREFIXES,
    DROP_PORTAL_DOMAINS,
    BLACKLIST_DOMAINS,
    BLACKLIST_PATH_PATTERNS,
    ALWAYS_ALLOW_PATTERNS,
    
    # Portal Configs
    PORTAL_DELAYS,
    DIRECT_CRAWL_SOURCES,
    MAX_PROFILES_PER_URL,
    
    # Export
    DEFAULT_CSV,
    DEFAULT_XLSX,
    ENH_FIELDS,
    LEAD_FIELDS,
    
    # Helper Functions
    _normalize_cx,
    _jitter,
    _env_list,
    
    # Base Dorks
    BASE_DORKS,
)

# =========================
# Re-export Database
# =========================

from .database import (
    db,
    init_db,
    transaction,
    migrate_db_unique_indexes,
)

# =========================
# Re-export existing modules (when available)
# =========================

# Try to import existing modules for convenience
try:
    from phone_extractor import extract_phones_advanced, normalize_phone
    _HAVE_PHONE_EXTRACTOR = True
except ImportError:
    _HAVE_PHONE_EXTRACTOR = False

try:
    from lead_validation import validate_lead, is_valid_phone
    _HAVE_LEAD_VALIDATION = True
except ImportError:
    _HAVE_LEAD_VALIDATION = False

try:
    from deduplication import LeadDeduplicator
    _HAVE_DEDUPLICATION = True
except ImportError:
    _HAVE_DEDUPLICATION = False

try:
    from cache import TTLCache, URLSeenSet
    _HAVE_CACHE = True
except ImportError:
    _HAVE_CACHE = False

# =========================
# __all__ Export
# =========================

__all__ = [
    # Version
    "__version__",
    
    # Config - API Keys
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "GCS_API_KEY",
    "GCS_CX_RAW",
    "BING_API_KEY",
    "GCS_KEYS",
    "GCS_CXS",
    "GCS_CX",
    
    # Config - Database
    "DB_PATH",
    
    # Config - HTTP
    "HTTP_TIMEOUT",
    "MAX_FETCH_SIZE",
    "POOL_SIZE",
    "ASYNC_LIMIT",
    "ASYNC_PER_HOST",
    "HTTP2_ENABLED",
    "USE_TOR",
    "ALLOW_PDF",
    "ALLOW_INSECURE_SSL",
    "ALLOW_PDF_NON_CV",
    "USER_AGENT",
    "PROXY_ENV_VARS",
    
    # Config - Rate Limiting
    "SLEEP_BETWEEN_QUERIES",
    "MAX_GOOGLE_PAGES",
    "CB_BASE_PENALTY",
    "CB_API_PENALTY",
    "RETRY_INCLUDE_403",
    "RETRY_MAX_PER_URL",
    "RETRY_BACKOFF_BASE",
    
    # Config - Scoring
    "MIN_SCORE_ENV",
    "MAX_PER_DOMAIN",
    "INTERNAL_DEPTH_PER_DOMAIN",
    "DEFAULT_QUALITY_SCORE",
    "MAX_CONTENT_LENGTH",
    "BINARY_CT_PREFIXES",
    "DENY_CT_EXACT",
    "PDF_CT",
    "SEED_FORCE",
    
    # Config - Features
    "ENABLE_KLEINANZEIGEN",
    "KLEINANZEIGEN_MAX_RESULTS",
    "TELEFONBUCH_ENRICHMENT_ENABLED",
    "TELEFONBUCH_STRICT_MODE",
    "TELEFONBUCH_RATE_LIMIT",
    "TELEFONBUCH_CACHE_DAYS",
    "TELEFONBUCH_MOBILE_ONLY",
    "PARALLEL_PORTAL_CRAWL",
    "MAX_CONCURRENT_PORTALS",
    "PORTAL_CONCURRENCY_PER_SITE",
    "ENABLE_GOOGLE_CSE",
    "ENABLE_PERPLEXITY",
    "ENABLE_BING",
    
    # Config - Cities
    "NRW_CITIES",
    "NRW_CITIES_EXTENDED",
    "NRW_BIG_CITIES",
    "METROPOLIS",
    "NRW_REGIONS",
    "SALES_TITLES",
    
    # Config - Search
    "PRIVATE_MAILS",
    "MOBILE_PATTERNS",
    "REGION",
    "CONTACT",
    "SALES",
    
    # Config - URLs
    "KLEINANZEIGEN_URLS",
    "MARKT_DE_URLS",
    "QUOKA_DE_URLS",
    "KALAYDO_DE_URLS",
    "MEINESTADT_DE_URLS",
    "FREELANCER_PORTAL_URLS",
    "DHD24_URLS",
    "FREELANCERMAP_URLS",
    "FREELANCE_DE_URLS",
    "DIRECT_CRAWL_URLS",
    
    # Config - Blacklists
    "DROP_MAILBOX_PREFIXES",
    "DROP_PORTAL_DOMAINS",
    "BLACKLIST_DOMAINS",
    "BLACKLIST_PATH_PATTERNS",
    "ALWAYS_ALLOW_PATTERNS",
    
    # Config - Portals
    "PORTAL_DELAYS",
    "DIRECT_CRAWL_SOURCES",
    "MAX_PROFILES_PER_URL",
    
    # Config - Export
    "DEFAULT_CSV",
    "DEFAULT_XLSX",
    "ENH_FIELDS",
    "LEAD_FIELDS",
    
    # Config - Helpers
    "_normalize_cx",
    "_jitter",
    "_env_list",
    "BASE_DORKS",
    
    # Database
    "db",
    "init_db",
    "transaction",
    "migrate_db_unique_indexes",
]

# Add optional imports to __all__ if available
if _HAVE_PHONE_EXTRACTOR:
    __all__.extend(["extract_phones_advanced", "normalize_phone"])
if _HAVE_LEAD_VALIDATION:
    __all__.extend(["validate_lead", "is_valid_phone"])
if _HAVE_DEDUPLICATION:
    __all__.append("LeadDeduplicator")
if _HAVE_CACHE:
    __all__.extend(["TTLCache", "URLSeenSet"])
