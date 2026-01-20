"""
LUCA NRW Scraper - Configuration Package
=========================================
Modularized configuration with priority-based loading.
"""

# Import from submodules
from .defaults import *
from .env_loader import *
from .portal_urls import *

# Re-export key functions and constants for backward compatibility
__all__ = [
    # From defaults
    'CONFIG_DEFAULTS',
    'AI_CONFIG_DEFAULTS',
    'CONFIG_REFRESH_INTERVAL_SECONDS',
    'USER_AGENT',
    'PROXY_ENV_VARS',
    'USE_TOR',
    'BINARY_CT_PREFIXES',
    'DENY_CT_EXACT',
    'PDF_CT',
    'RETRY_INCLUDE_403',
    'RETRY_BACKOFF_BASE',
    'ROBOTS_CACHE_TTL',
    'KLEINANZEIGEN_MAX_RESULTS',
    'TELEFONBUCH_STRICT_MODE',
    'TELEFONBUCH_RATE_LIMIT',
    'TELEFONBUCH_CACHE_DAYS',
    'TELEFONBUCH_MOBILE_ONLY',
    'PORTAL_CONCURRENCY_PER_SITE',
    'INTERNAL_DEPTH_PER_DOMAIN',
    'SEED_FORCE',
    'DEFAULT_CSV',
    'DEFAULT_XLSX',
    'ENH_FIELDS',
    'LEAD_FIELDS',
    
    # From env_loader
    'OPENAI_API_KEY',
    'PERPLEXITY_API_KEY',
    'GCS_API_KEY',
    'GCS_CX_RAW',
    'BING_API_KEY',
    'DB_PATH',
    'DATABASE_BACKEND',
    'ENV_MAPPINGS',
    'load_ai_config_from_env',
    'GCS_CX',
    'GCS_KEYS',
    'GCS_CXS',
    'ENABLE_GOOGLE_CSE',
    'ENABLE_PERPLEXITY',
    'ENABLE_BING',
    
    # From portal_urls
    'NRW_CITIES',
    'NRW_CITIES_EXTENDED',
    'NRW_BIG_CITIES',
    'METROPOLIS',
    'NRW_REGIONS',
    'SALES_TITLES',
    'PRIVATE_MAILS',
    'MOBILE_PATTERNS',
    'REGION',
    'CONTACT',
    'SALES',
    'KLEINANZEIGEN_URLS',
    'MARKT_DE_URLS',
    'QUOKA_DE_URLS',
    'KALAYDO_DE_URLS',
    'MEINESTADT_DE_URLS',
    'FREELANCER_PORTAL_URLS',
    'DHD24_URLS',
    'FREELANCERMAP_URLS',
    'FREELANCE_DE_URLS',
    'DIRECT_CRAWL_URLS',
    'DROP_MAILBOX_PREFIXES',
    'DROP_PORTAL_DOMAINS',
    'BLACKLIST_DOMAINS',
    'BLACKLIST_PATH_PATTERNS',
    'ALWAYS_ALLOW_PATTERNS',
    'PORTAL_DELAYS',
    'DIRECT_CRAWL_SOURCES',
    'MAX_PROFILES_PER_URL',
    'BASE_DORKS',
    'get_portal_urls',
    'get_portal_config',
    'get_all_portal_configs',
]
