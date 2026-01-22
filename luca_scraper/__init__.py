"""
LUCA NRW Scraper
================
Lead-Generierungs-Tool für NRW

Phase 1: Konsolidierung
- Extrahierte Konfiguration aus scriptname.py
- Extrahierte Database Layer aus scriptname.py
- Backward Compatibility durch Re-Exports

Phase 3: Search, Scoring, Validation & CLI
- Extrahierte Search Query Management
- Extrahierte Scoring und Validation
- Extrahierte CLI Interface

Phase 4: Portal Crawlers Extraction
- Extrahierte Portal-Crawler in dedizierte Module
- BaseCrawler Abstract Class
- Kleinanzeigen, Markt.de, Quoka, Kalaydo, MeineStadt Crawler
- Generic Detail Extractor

Version: 4.0.0
"""

__version__ = "4.0.0"

# =========================
# Re-export Config
# =========================

from .config import (
    # Configuration loaders
    get_scraper_config,
    get_config,
    
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
    
    # Portal URL Loading (database-backed)
    get_portal_urls,
    get_portal_config,
    get_all_portal_configs,
    
    # Base Dorks
    BASE_DORKS,
)

# =========================
# Re-export Database
# =========================

try:
    from .database import (
        db,
        init_db,
        transaction,
        migrate_db_unique_indexes,
        sync_status_to_scraper,
    )
except Exception as e:
    import logging
    from contextlib import contextmanager
    
    logging.warning(f"Database module not available: {e}")
    
    # Define placeholder functions to prevent import errors
    # These will raise errors if actually called, but allow the module to import
    def db():
        raise RuntimeError("Database module is not available - cannot get database connection")
    
    def init_db():
        raise RuntimeError("Database module is not available - cannot initialize database")
    
    @contextmanager
    def transaction():
        """Placeholder transaction context manager that raises error if used."""
        raise RuntimeError("Database module is not available - cannot create transaction")
        yield  # Never reached, but makes this a valid generator
    
    def migrate_db_unique_indexes():
        raise RuntimeError("Database module is not available - cannot migrate database")
    
    def sync_status_to_scraper():
        raise RuntimeError("Database module is not available - cannot sync status")

# =========================
# Re-export Search Module (Phase 3)
# =========================

from .search import (
    DEFAULT_QUERIES,
    INDUSTRY_QUERIES,
    build_queries,
)

# =========================
# Re-export Scoring Module (Phase 3)
# =========================

from .scoring import (
    # Patterns
    EMAIL_RE,
    PHONE_RE,
    MOBILE_RE,
    SALES_RE,
    PROVISION_HINT,
    D2D_HINT,
    CALLCENTER_HINT,
    B2C_HINT,
    JOBSEEKER_RE,
    CANDIDATE_TEXT_RE,
    EMPLOYER_TEXT_RE,
    RECRUITER_RE,
    WHATSAPP_RE,
    WA_LINK_RE,
    WHATS_RE,
    WHATSAPP_PHRASE_RE,
    TELEGRAM_LINK_RE,
    CITY_RE,
    NAME_RE,
    SALES_WINDOW,
    JOBSEEKER_WINDOW,
    
    # Signals
    CANDIDATE_POSITIVE_SIGNALS,
    JOB_OFFER_SIGNALS,
    STRICT_JOB_AD_MARKERS,
    MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE,
    CANDIDATE_KEYWORDS,
    IGNORE_KEYWORDS,
    JOB_AD_MARKERS,
    HIRING_INDICATORS,
    SOLO_BIZ_INDICATORS,
    AGENT_FINGERPRINTS,
    RETAIL_ROLES,
    
    # Functions
    is_candidate_seeking_job,
    is_job_advertisement,
    classify_lead,
    is_garbage_context,
    should_drop_lead,
    should_skip_url_prefetch,
)

# =========================
# Re-export CLI Module (Phase 3)
# =========================

from .cli import (
    parse_args,
    validate_config,
    print_banner,
    print_help,
)

# =========================
# Re-export Crawlers Module (Phase 4)
# =========================

from .crawlers import (
    # Base
    BaseCrawler,
    
    # Kleinanzeigen
    crawl_kleinanzeigen_listings_async,
    extract_kleinanzeigen_detail_async,
    crawl_kleinanzeigen_portal_async,
    
    # Other Portals
    crawl_markt_de_listings_async,
    crawl_quoka_listings_async,
    crawl_kalaydo_listings_async,
    crawl_meinestadt_listings_async,
    
    # Generic
    extract_detail_generic,
    extract_generic_detail_async,  # Backward compatibility alias
    _mark_url_seen,
)

# =========================
# Re-export existing modules (when available)
# =========================

# Try to import existing modules for convenience
try:
    from phone_extractor import extract_phones_advanced, normalize_phone
    _HAVE_PHONE_EXTRACTOR = True
except ImportError:
    try:
        import sys
        import os
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from phone_extractor import extract_phones_advanced, normalize_phone
        _HAVE_PHONE_EXTRACTOR = True
    except ImportError:
        _HAVE_PHONE_EXTRACTOR = False

try:
    from lead_validation import validate_lead, is_valid_phone
    _HAVE_LEAD_VALIDATION = True
except ImportError:
    try:
        import sys
        import os
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from lead_validation import validate_lead, is_valid_phone
        _HAVE_LEAD_VALIDATION = True
    except ImportError:
        _HAVE_LEAD_VALIDATION = False

try:
    from deduplication import LeadDeduplicator
    _HAVE_DEDUPLICATION = True
except ImportError:
    try:
        import sys
        import os
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from deduplication import LeadDeduplicator
        _HAVE_DEDUPLICATION = True
    except ImportError:
        _HAVE_DEDUPLICATION = False

try:
    from cache import TTLCache, URLSeenSet
    _HAVE_CACHE = True
except ImportError:
    try:
        import sys
        import os
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root not in sys.path:
            sys.path.insert(0, _root)
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
    
    # Portal URL Loading (database-backed)
    "get_portal_urls",
    "get_portal_config",
    "get_all_portal_configs",
    
    # Database
    "db",
    "init_db",
    "transaction",
    "migrate_db_unique_indexes",
    "sync_status_to_scraper",
    
    # Search Module (Phase 3)
    "DEFAULT_QUERIES",
    "INDUSTRY_QUERIES",
    "build_queries",
    
    # Scoring Module - Patterns (Phase 3)
    "EMAIL_RE",
    "PHONE_RE",
    "MOBILE_RE",
    "SALES_RE",
    "PROVISION_HINT",
    "D2D_HINT",
    "CALLCENTER_HINT",
    "B2C_HINT",
    "JOBSEEKER_RE",
    "CANDIDATE_TEXT_RE",
    "EMPLOYER_TEXT_RE",
    "RECRUITER_RE",
    "WHATSAPP_RE",
    "WA_LINK_RE",
    "WHATS_RE",
    "WHATSAPP_PHRASE_RE",
    "TELEGRAM_LINK_RE",
    "CITY_RE",
    "NAME_RE",
    "SALES_WINDOW",
    "JOBSEEKER_WINDOW",
    
    # Scoring Module - Signals (Phase 3)
    "CANDIDATE_POSITIVE_SIGNALS",
    "JOB_OFFER_SIGNALS",
    "STRICT_JOB_AD_MARKERS",
    "MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE",
    "CANDIDATE_KEYWORDS",
    "IGNORE_KEYWORDS",
    "JOB_AD_MARKERS",
    "HIRING_INDICATORS",
    "SOLO_BIZ_INDICATORS",
    "AGENT_FINGERPRINTS",
    "RETAIL_ROLES",
    
    # Scoring Module - Functions (Phase 3)
    "is_candidate_seeking_job",
    "is_job_advertisement",
    "classify_lead",
    "is_garbage_context",
    "should_drop_lead",
    "should_skip_url_prefetch",
    
    # CLI Module (Phase 3)
    "parse_args",
    "validate_config",
    "print_banner",
    "print_help",
    
    # Crawlers Module (Phase 4)
    "BaseCrawler",
    "crawl_kleinanzeigen_listings_async",
    "extract_kleinanzeigen_detail_async",
    "crawl_kleinanzeigen_portal_async",
    "crawl_markt_de_listings_async",
    "crawl_quoka_listings_async",
    "crawl_kalaydo_listings_async",
    "crawl_meinestadt_listings_async",
    "extract_detail_generic",
    "extract_generic_detail_async",  # Backward compatibility alias
    "_mark_url_seen",
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
