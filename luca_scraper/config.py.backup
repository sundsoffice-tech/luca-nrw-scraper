"""
LUCA NRW Scraper - Zentrale Konfiguration
==========================================
Alle Konstanten und Environment Variables aus scriptname.py extrahiert.
Phase 1 der Modularisierung.

Configuration Priority System:
------------------------------
The configuration system uses a three-tier priority system to eliminate inconsistencies:

1. **Django Database (Highest Priority)**: ScraperConfig model in the database
   - Managed through Django Admin UI
   - Persistent across runs
   - Single source of truth for production deployments
   
2. **Environment Variables (Medium Priority)**: .env file or system environment
   - Used as fallback when DB is not available
   - Useful for local development and testing
   
3. **Hardcoded Defaults (Lowest Priority)**: Defined in _CONFIG_DEFAULTS
   - Last resort fallback
   - Ensures the scraper always has valid configuration

Usage:
------
All configuration parameters are automatically loaded using get_scraper_config() at module import.
The global variables (HTTP_TIMEOUT, ASYNC_LIMIT, etc.) are available for backward compatibility
but internally use the centralized configuration system.

To reload configuration dynamically:
    >>> from luca_scraper.config import get_scraper_config
    >>> config = get_scraper_config()  # Get all config
    >>> timeout = get_scraper_config('http_timeout')  # Get specific param

AI Configuration Priority:
--------------------------
AI configuration (separate from scraper config) is loaded in the following priority order:
1. Django DB via ai_config app (when available)
2. Environment variables
3. Hardcoded defaults

Use get_config() to access AI configuration with automatic fallback.
"""

import os
import random
import threading
import time
import urllib.parse
from typing import List, Dict, Set, Tuple, Optional, Any
import logging

# Optional Django ai_config integration
# Falls back gracefully when Django is not available or configured
try:
    from telis_recruitment.ai_config.loader import (
        get_ai_config as _get_ai_config_django,
        get_prompt,
        log_usage,
        check_budget
    )
    AI_CONFIG_AVAILABLE = True
except (ImportError, Exception):
    AI_CONFIG_AVAILABLE = False
    _get_ai_config_django = None

# Optional Django scraper_control integration
try:
    from telis_recruitment.scraper_control.config_loader import (
        get_scraper_config as _get_scraper_config_django,
        get_regions as _get_regions_django,
        get_dorks as _get_dorks_django,
        get_portals as _get_portals_django,
        get_blacklists as _get_blacklists_django,
    )
    SCRAPER_CONFIG_AVAILABLE = True
except (ImportError, Exception):
    SCRAPER_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)

# Default fallback for the insecure SSL flag (0 = secure)
ALLOW_INSECURE_SSL_ENV_DEFAULT = "0"
ALLOW_INSECURE_SSL_DEFAULT = ALLOW_INSECURE_SSL_ENV_DEFAULT == "1"


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

# Log the active backend on module import
logger.info(f"Database backend: {DATABASE_BACKEND}")

# =========================
# CENTRALIZED CONFIGURATION LOADER
# =========================

# Configuration defaults (Priority 3: Hardcoded)
_CONFIG_DEFAULTS = {
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

def get_scraper_config(param: Optional[str] = None) -> Any:
    """
    Get scraper configuration with automatic fallback priority.
    
    Priority order:
    1. Django DB via scraper_control app (when available)
    2. Environment variables
    3. Hardcoded defaults
    
    Args:
        param: Optional specific parameter to retrieve. If None, returns full config dict.
    
    Returns:
        Full config dict or specific parameter value
    
    Examples:
        >>> config = get_scraper_config()  # Get full config
        >>> timeout = get_scraper_config('http_timeout')  # Get specific param
    """
    # Start with defaults (Priority 3)
    config = _CONFIG_DEFAULTS.copy()
    
    # Priority 2: Override with environment variables if set
    env_mappings = {
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
    
    for config_key, (env_var, converter) in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                config[config_key] = converter(env_value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for {env_var}: {env_value}, using default")
    
    # Priority 1: Django DB (when available)
    if SCRAPER_CONFIG_AVAILABLE:
        try:
            django_config = _get_scraper_config_django()
            if django_config:
                # Only update with non-None values from DB
                config.update({k: v for k, v in django_config.items() if v is not None})
                logger.debug("Scraper config loaded from Django DB")
        except Exception as e:
            logger.debug(f"Could not load scraper config from Django DB: {e}")
    
    # Return specific param or full config
    if param:
        return config.get(param)
    return config


try:
    _CONFIG_REFRESH_INTERVAL_SECONDS = max(1, int(os.getenv("CONFIG_REFRESH_INTERVAL_SECONDS", "30")))
except ValueError:
    _CONFIG_REFRESH_INTERVAL_SECONDS = 30

_loaded_config: Dict[str, Any] = {}
_config_watcher_thread: Optional[threading.Thread] = None


def _apply_runtime_config(config_dict: Dict[str, Any]) -> None:
    """Update runtime globals from the provided config dictionary."""
    global _loaded_config, HTTP_TIMEOUT, MAX_FETCH_SIZE, POOL_SIZE, ASYNC_LIMIT, ASYNC_PER_HOST, HTTP2_ENABLED
    global ALLOW_PDF, ALLOW_INSECURE_SSL, ALLOW_PDF_NON_CV, SLEEP_BETWEEN_QUERIES, MAX_GOOGLE_PAGES
    global CB_BASE_PENALTY, CB_API_PENALTY, RETRY_MAX_PER_URL, MIN_SCORE_ENV, MAX_PER_DOMAIN
    global DEFAULT_QUALITY_SCORE, MAX_CONTENT_LENGTH, ENABLE_KLEINANZEIGEN, TELEFONBUCH_ENRICHMENT_ENABLED
    global PARALLEL_PORTAL_CRAWL, MAX_CONCURRENT_PORTALS

    if not config_dict:
        return

    old_config = dict(_loaded_config) if isinstance(_loaded_config, dict) else {}
    _loaded_config = config_dict

    HTTP_TIMEOUT = config_dict.get('http_timeout', old_config.get('http_timeout'))
    computed_max_fetch = config_dict.get('max_fetch_size', old_config.get('max_fetch_size'))
    MAX_FETCH_SIZE = computed_max_fetch
    POOL_SIZE = config_dict.get('pool_size', old_config.get('pool_size'))
    ASYNC_LIMIT = config_dict.get('async_limit', old_config.get('async_limit'))
    ASYNC_PER_HOST = config_dict.get('async_per_host', old_config.get('async_per_host'))
    HTTP2_ENABLED = config_dict.get('http2_enabled', old_config.get('http2_enabled'))
    ALLOW_PDF = config_dict.get('allow_pdf', old_config.get('allow_pdf'))
    ALLOW_INSECURE_SSL = config_dict.get('allow_insecure_ssl', old_config.get('allow_insecure_ssl'))
    ALLOW_PDF_NON_CV = config_dict.get('allow_pdf_non_cv', old_config.get('allow_pdf_non_cv'))
    SLEEP_BETWEEN_QUERIES = config_dict.get('sleep_between_queries', old_config.get('sleep_between_queries'))
    MAX_GOOGLE_PAGES = config_dict.get('max_google_pages', old_config.get('max_google_pages'))
    CB_BASE_PENALTY = config_dict.get('circuit_breaker_penalty', old_config.get('circuit_breaker_penalty'))
    CB_API_PENALTY = config_dict.get(
        'circuit_breaker_api_penalty',
        old_config.get('circuit_breaker_api_penalty', 15)
    )
    RETRY_MAX_PER_URL = config_dict.get('retry_max_per_url', old_config.get('retry_max_per_url'))
    MIN_SCORE_ENV = config_dict.get('min_score', old_config.get('min_score'))
    MAX_PER_DOMAIN = config_dict.get('max_per_domain', old_config.get('max_per_domain'))
    DEFAULT_QUALITY_SCORE = config_dict.get('default_quality_score', old_config.get('default_quality_score'))
    MAX_CONTENT_LENGTH = config_dict.get(
        'max_content_length',
        computed_max_fetch or old_config.get('max_content_length')
    )
    ENABLE_KLEINANZEIGEN = config_dict.get('enable_kleinanzeigen', old_config.get('enable_kleinanzeigen'))
    TELEFONBUCH_ENRICHMENT_ENABLED = config_dict.get('enable_telefonbuch', old_config.get('enable_telefonbuch'))
    PARALLEL_PORTAL_CRAWL = config_dict.get('parallel_portal_crawl', old_config.get('parallel_portal_crawl'))
    MAX_CONCURRENT_PORTALS = config_dict.get('max_concurrent_portals', old_config.get('max_concurrent_portals'))


def _start_config_version_watcher() -> None:
    """Background watcher that reloads runtime config when the DB version changes."""
    global _config_watcher_thread

    if _config_watcher_thread is not None:
        return

    def _watcher_loop() -> None:
        last_version = (
            _loaded_config.get('config_version', 0)
            if isinstance(_loaded_config, dict)
            else 0
        )
        interval = _CONFIG_REFRESH_INTERVAL_SECONDS

        while True:
            time.sleep(interval)
            try:
                new_config = get_scraper_config()
            except Exception as exc:
                logger.warning("Could not refresh scraper config: %s", exc)
                continue

            if not new_config:
                continue

            new_version = new_config.get('config_version', last_version)
            if new_version == last_version:
                continue

            logger.info(
                "Detected scraper config version change %s -> %s, reloading runtime settings",
                last_version,
                new_version,
            )
            _apply_runtime_config(new_config)
            last_version = new_version

    thread = threading.Thread(target=_watcher_loop, name="ScraperConfigWatcher", daemon=True)
    thread.start()
    _config_watcher_thread = thread


_apply_runtime_config(get_scraper_config())

if SCRAPER_CONFIG_AVAILABLE:
    _start_config_version_watcher()


# =========================
# HTTP & NETWORKING
# =========================
# Load configuration dynamically using centralized loader
_loaded_config = get_scraper_config()

HTTP_TIMEOUT = _loaded_config['http_timeout']
MAX_FETCH_SIZE = _loaded_config['max_fetch_size']
POOL_SIZE = _loaded_config['pool_size']

# Async settings
ASYNC_LIMIT = _loaded_config['async_limit']
ASYNC_PER_HOST = _loaded_config['async_per_host']
HTTP2_ENABLED = _loaded_config['http2_enabled']
USE_TOR = False

# SSL & PDF
ALLOW_PDF = _loaded_config['allow_pdf']
ALLOW_INSECURE_SSL = _loaded_config['allow_insecure_ssl']
ALLOW_PDF_NON_CV = _loaded_config['allow_pdf_non_cv']

# User Agent
USER_AGENT = "Mozilla/5.0 (compatible; VertriebFinder/2.3; +https://example.com)"

# Proxy environment variables
PROXY_ENV_VARS = [
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
    "FTP_PROXY", "ftp_proxy", "SOCKS_PROXY", "socks_proxy"
]

# =========================
# RATE LIMITING & DELAYS
# =========================

SLEEP_BETWEEN_QUERIES = _loaded_config['sleep_between_queries']
MAX_GOOGLE_PAGES = _loaded_config['max_google_pages']

# Circuit Breaker
CB_BASE_PENALTY = _loaded_config['circuit_breaker_penalty']
CB_API_PENALTY = _loaded_config.get('circuit_breaker_api_penalty', 15)

# Retry settings
RETRY_INCLUDE_403 = (os.getenv("RETRY_INCLUDE_403", "0") == "1")
RETRY_MAX_PER_URL = _loaded_config['retry_max_per_url']
RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "6.0"))

# Robots cache
_ROBOTS_CACHE_TTL = int(os.getenv("ROBOTS_CACHE_TTL", "21600"))  # 6h

# =========================
# SCORING & FILTERING
# =========================

MIN_SCORE_ENV = _loaded_config['min_score']
MAX_PER_DOMAIN = _loaded_config['max_per_domain']
INTERNAL_DEPTH_PER_DOMAIN = int(os.getenv("INTERNAL_DEPTH_PER_DOMAIN", "10"))
DEFAULT_QUALITY_SCORE = _loaded_config['default_quality_score']

# Content limits
MAX_CONTENT_LENGTH = _loaded_config.get('max_content_length', MAX_FETCH_SIZE)
BINARY_CT_PREFIXES = ("image/", "video/", "audio/")
DENY_CT_EXACT = {
    "application/zip", "application/x-tar", "application/x-gzip"
}
PDF_CT = "application/pdf"

# Seed force
SEED_FORCE = (os.getenv("SEED_FORCE", "0") == "1")

# =========================
# FEATURE FLAGS
# =========================

ENABLE_KLEINANZEIGEN = _loaded_config['enable_kleinanzeigen']
KLEINANZEIGEN_MAX_RESULTS = int(os.getenv("KLEINANZEIGEN_MAX_RESULTS", "20"))

# Telefonbuch Enrichment
TELEFONBUCH_ENRICHMENT_ENABLED = _loaded_config['enable_telefonbuch']
TELEFONBUCH_STRICT_MODE = (os.getenv("TELEFONBUCH_STRICT_MODE", "1") == "1")
TELEFONBUCH_RATE_LIMIT = float(os.getenv("TELEFONBUCH_RATE_LIMIT", "3.0"))
TELEFONBUCH_CACHE_DAYS = int(os.getenv("TELEFONBUCH_CACHE_DAYS", "7"))
TELEFONBUCH_MOBILE_ONLY = (os.getenv("TELEFONBUCH_MOBILE_ONLY", "1") == "1")

# Portal crawling
PARALLEL_PORTAL_CRAWL = _loaded_config['parallel_portal_crawl']
MAX_CONCURRENT_PORTALS = _loaded_config['max_concurrent_portals']
PORTAL_CONCURRENCY_PER_SITE = int(os.getenv("PORTAL_CONCURRENCY_PER_SITE", "2"))

# =========================
# NRW CITIES & REGIONS
# =========================

NRW_CITIES = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg",
    "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Gelsenkirchen", "Aachen", "Mönchengladbach"
]

NRW_CITIES_EXTENDED = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg",
    "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Gelsenkirchen", "Mönchengladbach", "Aachen", "Krefeld", "Oberhausen",
    "Hagen", "Hamm", "Mülheim an der Ruhr", "Leverkusen", "Solingen",
    "Neuss", "Paderborn", "Recklinghausen", "Remscheid", "Moers",
    "Siegen", "Witten", "Iserlohn", "Bergisch Gladbach", "Herne"
]

NRW_BIG_CITIES = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Gelsenkirchen", "Mönchengladbach", "Aachen", "Chemnitz", "Krefeld", "Oberhausen", "Hagen", "Hamm", "Mülheim",
    "Leverkusen", "Solingen", "Herne", "Neuss", "Paderborn", "Bottrop", "Recklinghausen", "Bergisch Gladbach",
    "Remscheid", "Moers", "Siegen", "Gütersloh", "Witten", "Iserlohn", "Düren", "Ratingen", "Lünen", "Marl",
    "Velbert", "Minden", "Viersen"
]

METROPOLIS = ["Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Bonn", "Münster"]

NRW_REGIONS = [
    "nrw", "nordrhein-westfalen", "nordrhein westfalen",
    "düsseldorf", "köln", "dortmund", "essen", "duisburg",
    "bochum", "wuppertal", "bielefeld", "bonn", "münster",
    "gelsenkirchen", "mönchengladbach", "aachen", "krefeld",
    "oberhausen", "hagen", "hamm", "mülheim", "leverkusen",
    "solingen", "herne", "neuss", "paderborn", "bottrop",
    "ruhrgebiet", "rheinland", "sauerland", "münsterland", "owl",
]

# =========================
# JOB TITLES & ROLES
# =========================

SALES_TITLES = [
    "Vertrieb", "Sales Manager", "Account Manager", "Außendienst", "Telesales",
    "Verkäufer", "Handelsvertreter", "Key Account Manager", "Area Sales Manager"
]

# =========================
# SEARCH PATTERNS
# =========================

# Private Mail-Provider (keine Firmen!)
PRIVATE_MAILS = '("@gmail.com" OR "@gmx.de" OR "@web.de" OR "@t-online.de" OR "@yahoo.de" OR "@outlook.com" OR "@icloud.com")'

# Handy-Nummern Muster (Masse!)
MOBILE_PATTERNS = '("017" OR "016" OR "015" OR "+49 17" OR "+49 16" OR "+49 15" OR "+4917" OR "+4916" OR "+4915")'

# Search region and contact patterns
REGION = '(NRW OR "Nordrhein-Westfalen" OR Düsseldorf OR Köln OR Essen OR Dortmund OR Bochum OR Duisburg OR Mönchengladbach)'
CONTACT = '(kontakt OR impressum OR ansprechpartner OR "e-mail" OR email OR telefon OR whatsapp)'
SALES = '(vertrieb OR d2d OR "call center" OR telesales OR outbound OR verkauf OR sales)'

# =========================
# PORTAL URLS
# =========================

# Kleinanzeigen URLs
KLEINANZEIGEN_URLS: List[str] = [
    # Stellengesuche NRW - Vertrieb/Sales
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/vertrieb/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/sales/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/verkauf/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/aussendienst/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/kundenberater/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/handelsvertreter/k0c107l929",
    # Bundesweit (mehr Volumen)
    "https://www.kleinanzeigen.de/s-stellengesuche/vertrieb/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/sales/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/verkauf/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/handelsvertreter/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/akquise/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/telesales/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/call-center/k0c107",
    # Alle großen NRW-Städte
    # Köln
    "https://www.kleinanzeigen.de/s-stellengesuche/koeln/vertrieb/k0c107l945",
    "https://www.kleinanzeigen.de/s-stellengesuche/koeln/sales/k0c107l945",
    "https://www.kleinanzeigen.de/s-stellengesuche/koeln/verkauf/k0c107l945",
    # Dortmund
    "https://www.kleinanzeigen.de/s-stellengesuche/dortmund/vertrieb/k0c107l947",
    "https://www.kleinanzeigen.de/s-stellengesuche/dortmund/sales/k0c107l947",
    # Essen
    "https://www.kleinanzeigen.de/s-stellengesuche/essen/vertrieb/k0c107l939",
    "https://www.kleinanzeigen.de/s-stellengesuche/essen/sales/k0c107l939",
    # Duisburg
    "https://www.kleinanzeigen.de/s-stellengesuche/duisburg/vertrieb/k0c107l940",
    # Bochum
    "https://www.kleinanzeigen.de/s-stellengesuche/bochum/vertrieb/k0c107l941",
    # Wuppertal
    "https://www.kleinanzeigen.de/s-stellengesuche/wuppertal/vertrieb/k0c107l942",
    # Bielefeld
    "https://www.kleinanzeigen.de/s-stellengesuche/bielefeld/vertrieb/k0c107l943",
    # Bonn
    "https://www.kleinanzeigen.de/s-stellengesuche/bonn/vertrieb/k0c107l944",
    # Münster
    "https://www.kleinanzeigen.de/s-stellengesuche/muenster/vertrieb/k0c107l946",
    # Gelsenkirchen
    "https://www.kleinanzeigen.de/s-stellengesuche/gelsenkirchen/vertrieb/k0c107l948",
    # Mönchengladbach
    "https://www.kleinanzeigen.de/s-stellengesuche/moenchengladbach/vertrieb/k0c107l949",
    # Aachen
    "https://www.kleinanzeigen.de/s-stellengesuche/aachen/vertrieb/k0c107l950",
    # Krefeld
    "https://www.kleinanzeigen.de/s-stellengesuche/krefeld/vertrieb/k0c107l951",
    # Oberhausen
    "https://www.kleinanzeigen.de/s-stellengesuche/oberhausen/vertrieb/k0c107l952",
    # Hagen
    "https://www.kleinanzeigen.de/s-stellengesuche/hagen/vertrieb/k0c107l953",
    # Hamm
    "https://www.kleinanzeigen.de/s-stellengesuche/hamm/vertrieb/k0c107l954",
    # Zusätzliche Berufsfelder NRW
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/kundenservice/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/call-center/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/promotion/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/telefonverkauf/k0c107l929",
]

# Markt.de Stellengesuche URLs
MARKT_DE_URLS: List[str] = [
    # NRW
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/vertrieb/",
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/sales/",
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/verkauf/",
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/kundenberater/",
    # Bundesweit
    "https://www.markt.de/stellengesuche/vertrieb/",
    "https://www.markt.de/stellengesuche/sales/",
    "https://www.markt.de/stellengesuche/handelsvertreter/",
]

# Quoka.de Stellengesuche URLs
QUOKA_DE_URLS: List[str] = [
    # NRW Städte (erweitert)
    "https://www.quoka.de/stellengesuche/duesseldorf/",
    "https://www.quoka.de/stellengesuche/koeln/",
    "https://www.quoka.de/stellengesuche/dortmund/",
    "https://www.quoka.de/stellengesuche/essen/",
    "https://www.quoka.de/stellengesuche/duisburg/",
    "https://www.quoka.de/stellengesuche/bochum/",
    "https://www.quoka.de/stellengesuche/wuppertal/",
    "https://www.quoka.de/stellengesuche/bielefeld/",
    "https://www.quoka.de/stellengesuche/bonn/",
    "https://www.quoka.de/stellengesuche/muenster/",
    "https://www.quoka.de/stellengesuche/gelsenkirchen/",
    "https://www.quoka.de/stellengesuche/moenchengladbach/",
    "https://www.quoka.de/stellengesuche/aachen/",
    # Kategorien
    "https://www.quoka.de/stellengesuche/vertrieb-verkauf/",
    "https://www.quoka.de/stellengesuche/kundenservice/",
]

# Kalaydo.de Stellengesuche URLs
KALAYDO_DE_URLS: List[str] = [
    "https://www.kalaydo.de/stellengesuche/nordrhein-westfalen/",
    "https://www.kalaydo.de/stellengesuche/koeln/",
    "https://www.kalaydo.de/stellengesuche/duesseldorf/",
    "https://www.kalaydo.de/stellengesuche/bonn/",
    "https://www.kalaydo.de/stellengesuche/aachen/",
]

# Meinestadt.de Stellengesuche URLs
MEINESTADT_DE_URLS: List[str] = [
    "https://www.meinestadt.de/duesseldorf/stellengesuche",
    "https://www.meinestadt.de/koeln/stellengesuche",
    "https://www.meinestadt.de/dortmund/stellengesuche",
    "https://www.meinestadt.de/essen/stellengesuche",
    "https://www.meinestadt.de/duisburg/stellengesuche",
    "https://www.meinestadt.de/bochum/stellengesuche",
    "https://www.meinestadt.de/wuppertal/stellengesuche",
    "https://www.meinestadt.de/bielefeld/stellengesuche",
    "https://www.meinestadt.de/bonn/stellengesuche",
    "https://www.meinestadt.de/muenster/stellengesuche",
    "https://www.meinestadt.de/gelsenkirchen/stellengesuche",
    "https://www.meinestadt.de/moenchengladbach/stellengesuche",
    "https://www.meinestadt.de/aachen/stellengesuche",
    "https://www.meinestadt.de/krefeld/stellengesuche",
    "https://www.meinestadt.de/oberhausen/stellengesuche",
]

# Freelancer Portal URLs
FREELANCER_PORTAL_URLS: List[str] = [
    "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-vertrieb.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-sales.html",
    "https://www.freelance.de/Freiberufler/NRW/Vertrieb/",
    "https://www.freelance.de/Freiberufler/NRW/Sales/",
    "https://www.gulp.de/gulp2/g/projekte?region=nordrhein-westfalen&skill=vertrieb",
]

# DHD24.com Stellengesuche URLs
DHD24_URLS: List[str] = [
    "https://www.dhd24.com/kleinanzeigen/stellengesuche.html",
    "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-vertrieb.html",
    "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-verkauf.html",
]

# Freelancermap.de URLs
FREELANCERMAP_URLS: List[str] = [
    "https://www.freelancermap.de/freelancer-verzeichnis/sales.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/vertrieb.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/business-development.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/account-management.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/key-account-management.html",
]

# Freelance.de URLs
FREELANCE_DE_URLS: List[str] = [
    "https://www.freelance.de/Freiberufler/Vertrieb/",
    "https://www.freelance.de/Freiberufler/Sales/",
    "https://www.freelance.de/Freiberufler/Key-Account/",
    "https://www.freelance.de/Freiberufler/Business-Development/",
    "https://www.freelance.de/Freiberufler/Account-Manager/",
]

# Direct crawl URLs (alias for backward compatibility)
DIRECT_CRAWL_URLS = KLEINANZEIGEN_URLS

# =========================
# BLACKLISTS & FILTERS
# =========================

# Drop mailbox prefixes (generic emails)
DROP_MAILBOX_PREFIXES: Set[str] = {
    "info", "kontakt", "contact", "support", "service",
    "privacy", "datenschutz", "noreply", "no-reply",
    "donotreply", "do-not-reply", "jobs", "karriere",
}

# Drop portal domains (job boards, etc.)
DROP_PORTAL_DOMAINS: Set[str] = {
    "stepstone.de", "indeed.com", "heyjobs.co", "heyjobs.de",
    "softgarden.io", "jobijoba.de", "jobijoba.com", "jobware.de",
    "monster.de", "kununu.com", "ok.ru", "tiktok.com",
    "patents.google.com", "linkedin.com", "xing.com",
    "arbeitsagentur.de", "meinestadt.de", "kimeta.de",
    "stellenanzeigen.de", "bewerbung.net", "freelancermap.de",
    "reddit.com", "jobboard-deutschland.de", "kleinanzeigen.de",
    "praca.egospodarka.pl", "tabellarischer-lebenslauf.net",
    "lexware.de", "tribeworks.de", "junico.de", "qonto.com",
    "accountable.de", "sevdesk.de", "mlp.de", "netspor-tv.com",
    "trendyol.com",
}

# Blacklist domains (kept for backward compatibility - same as DROP_PORTAL_DOMAINS)
BLACKLIST_DOMAINS: Set[str] = DROP_PORTAL_DOMAINS

# Blacklist path patterns
BLACKLIST_PATH_PATTERNS: Set[str] = {
    "lebenslauf", "vorlage", "muster", "sitemap", "seminar",
    "academy", "weiterbildung", "job", "stellenangebot",
    "news", "blog", "ratgeber", "portal"
}

# Always allow patterns (regex)
ALWAYS_ALLOW_PATTERNS: List[str] = [
    r'industrievertretung',
    r'handelsvertret',
    r'vertriebspartner',
    r'/ansprechpartner/',
    r'/team/',
    r'/ueber-uns/',
    r'/kontakt/',
    r'/impressum',
]

# =========================
# PORTAL CONFIGURATIONS
# =========================

# Portal-specific request delays (seconds)
PORTAL_DELAYS: Dict[str, float] = {
    "kleinanzeigen": 3.0,
    "markt_de": 4.0,
    "quoka": 6.0,
    "kalaydo": 4.0,
    "meinestadt": 3.0,
    "dhd24": 4.0,
    "freelancermap": 3.0,
    "freelance_de": 3.0,
}

# Direct crawl source configuration
DIRECT_CRAWL_SOURCES: Dict[str, bool] = {
    "kleinanzeigen": True,
    "markt_de": True,
    "quoka": True,
    "kalaydo": False,
    "meinestadt": False,
    "freelancer_portals": False,
    "dhd24": True,
    "freelancermap": True,
    "freelance_de": False,
}

# Max profiles per URL
MAX_PROFILES_PER_URL = 10

# =========================
# EXPORT FIELDS
# =========================

DEFAULT_CSV = "vertrieb_kontakte.csv"
DEFAULT_XLSX = "vertrieb_kontakte.xlsx"

ENH_FIELDS: List[str] = [
    "name", "rolle", "email", "telefon", "quelle", "score", "tags", "region",
    "role_guess", "lead_type", "salary_hint", "commission_hint", "opening_line",
    "ssl_insecure", "company_name", "company_size", "hiring_volume",
    "industry", "recency_indicator", "location_specific",
    "confidence_score", "last_updated", "data_quality",
    "phone_type", "whatsapp_link", "private_address", "social_profile_url",
    "ai_category", "ai_summary",
    "experience_years", "skills", "availability", "current_status", "industries", "location", "profile_text",
    "candidate_status", "mobility", "industries_experience", "source_type",
    "profile_url", "cv_url", "contact_preference", "last_activity", "name_validated", "crm_status"
]

LEAD_FIELDS: List[str] = [
    "name", "rolle", "email", "telefon", "quelle", "score", "tags", "region",
    "role_guess", "salary_hint", "commission_hint", "opening_line", "ssl_insecure",
    "company_name", "company_size", "hiring_volume", "industry",
    "recency_indicator", "location_specific", "confidence_score",
    "last_updated", "data_quality", "phone_type", "whatsapp_link",
    "private_address", "social_profile_url", "ai_category", "ai_summary",
    "crm_status",
    "lead_type",
]

# =========================
# HELPER FUNCTIONS
# =========================

def get_portal_urls(portal_name: str) -> List[str]:
    """
    Get URLs for a portal from database, with fallback to hardcoded lists.
    
    This function enables database-managed portal URLs while maintaining
    backward compatibility with hardcoded URL lists.
    
    Args:
        portal_name: Internal portal name (e.g., 'kleinanzeigen', 'markt_de')
    
    Returns:
        List of URLs to crawl for the portal
        
    Priority:
        1. Django DB (PortalSource.urls) - if available and non-empty
        2. Hardcoded URL lists - as fallback
    """
    # Mapping from portal names to hardcoded URL lists
    _HARDCODED_URLS = {
        'kleinanzeigen': KLEINANZEIGEN_URLS,
        'markt_de': MARKT_DE_URLS,
        'quoka': QUOKA_DE_URLS,
        'kalaydo': KALAYDO_DE_URLS,
        'meinestadt': MEINESTADT_DE_URLS,
        'dhd24': DHD24_URLS,
        'freelancermap': FREELANCERMAP_URLS,
        'freelance_de': FREELANCE_DE_URLS,
        'freelancer_portals': FREELANCER_PORTAL_URLS,
    }
    
    # Try to load from database first
    if SCRAPER_CONFIG_AVAILABLE:
        try:
            portals = _get_portals_django()
            if portals and portal_name in portals:
                db_urls = portals[portal_name].get('urls', [])
                if db_urls:
                    logger.debug(f"Loaded {len(db_urls)} URLs for {portal_name} from database")
                    return db_urls
        except Exception as e:
            logger.debug(f"Could not load portal URLs from DB for {portal_name}: {e}")
    
    # Fallback to hardcoded lists
    fallback_urls = _HARDCODED_URLS.get(portal_name, [])
    if fallback_urls:
        logger.debug(f"Using {len(fallback_urls)} hardcoded URLs for {portal_name}")
    return fallback_urls


def get_portal_config(portal_name: str) -> Dict[str, Any]:
    """
    Get complete configuration for a portal from database, with fallback to defaults.
    
    Returns a dict with:
        - urls: List[str] - URLs to crawl
        - rate_limit_seconds: float - Delay between requests
        - max_results: int - Maximum results per crawl
        - is_active: bool - Whether portal is enabled
    
    Args:
        portal_name: Internal portal name (e.g., 'kleinanzeigen', 'markt_de')
    
    Returns:
        Dict with portal configuration
    """
    # Default configuration using hardcoded values
    default_config = {
        'urls': get_portal_urls(portal_name),
        'rate_limit_seconds': PORTAL_DELAYS.get(portal_name, 3.0),
        'max_results': 20,
        'is_active': DIRECT_CRAWL_SOURCES.get(portal_name, False),
    }
    
    # Try to load from database
    if SCRAPER_CONFIG_AVAILABLE:
        try:
            portals = _get_portals_django()
            if portals and portal_name in portals:
                db_config = portals[portal_name]
                # Merge with defaults, preferring DB values
                # Note: config_loader returns 'rate_limit' key from rate_limit_seconds field
                db_rate_limit = db_config.get('rate_limit') or db_config.get('rate_limit_seconds')
                return {
                    'urls': db_config.get('urls') or default_config['urls'],
                    'rate_limit_seconds': db_rate_limit or default_config['rate_limit_seconds'],
                    'max_results': db_config.get('max_results', default_config['max_results']),
                    'is_active': True,  # If in DB and active filter, it's active
                }
        except Exception as e:
            logger.debug(f"Could not load portal config from DB for {portal_name}: {e}")
    
    return default_config


def get_all_portal_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get configurations for all portals from database, with fallback to defaults.
    
    Returns a dict mapping portal names to their configurations.
    New portals can be added via the database without code changes.
    """
    # Start with hardcoded portal names
    all_portals = {
        'kleinanzeigen', 'markt_de', 'quoka', 'kalaydo', 'meinestadt',
        'dhd24', 'freelancermap', 'freelance_de'
    }
    
    # Try to get additional portals from database
    if SCRAPER_CONFIG_AVAILABLE:
        try:
            db_portals = _get_portals_django()
            if db_portals:
                all_portals.update(db_portals.keys())
        except Exception as e:
            logger.debug(f"Could not load portal list from DB: {e}")
    
    # Build config for all portals
    configs = {}
    for portal_name in all_portals:
        configs[portal_name] = get_portal_config(portal_name)
    
    return configs


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


def _jitter(a=0.2, b=0.8):
    """Generate random jitter value."""
    return a + random.random() * (b - a)


def _env_list(val: str, sep: str) -> List[str]:
    """Parse environment variable as list."""
    return [x.strip() for x in val.split(sep) if x.strip()]


# =========================
# GOOGLE CUSTOM SEARCH
# =========================

# Normalize and build GCS configuration
GCS_CX = _normalize_cx(GCS_CX_RAW)
GCS_KEYS = [k.strip() for k in os.getenv("GCS_KEYS", "").split(",") if k.strip()] or ([GCS_API_KEY] if GCS_API_KEY else [])
GCS_CXS = [_normalize_cx(x) for x in os.getenv("GCS_CXS", "").split(",") if _normalize_cx(x)] or ([GCS_CX] if GCS_CX else [])

# Enable/Disable search engines
ENABLE_GOOGLE_CSE = bool(GCS_KEYS and GCS_CXS)
ENABLE_PERPLEXITY = bool(PERPLEXITY_API_KEY)
ENABLE_BING = bool(BING_API_KEY)

# =========================
# BASE DORKS
# =========================
# Empty placeholder for future implementation
# Dorks are currently defined in other modules or dynamically generated

BASE_DORKS: List[str] = []


# =========================
# AI CONFIGURATION
# =========================

def get_config(param: Optional[str] = None) -> Any:
    """
    Get AI configuration with automatic fallback priority.
    
    Priority order:
    1. Django DB via ai_config app (when available)
    2. Environment variables
    3. Hardcoded defaults
    
    Args:
        param: Optional specific parameter to retrieve. If None, returns full config dict.
               Available params: 'temperature', 'max_tokens', 'top_p', 'learning_rate',
                                'daily_budget', 'monthly_budget', 'confidence_threshold',
                                'retry_limit', 'timeout_seconds', 'default_provider',
                                'default_model', 'default_model_display'
    
    Returns:
        Full config dict or specific parameter value
    
    Examples:
        >>> config = get_config()  # Get full config
        >>> temp = get_config('temperature')  # Get specific param
        >>> model = get_config('default_model')
    """
    # Default configuration (Priority 3: Hardcoded defaults)
    defaults = {
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
    
    # Priority 2: Override with environment variables if set
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
    
    # Merge defaults with env overrides
    config = {**defaults, **env_overrides}
    
    # Priority 1: Django DB (when available)
    if AI_CONFIG_AVAILABLE:
        try:
            django_config = _get_ai_config_django()
            if django_config:
                config.update(django_config)
                logger.debug("AI config loaded from Django DB")
        except Exception as e:
            logger.debug(f"Could not load AI config from Django DB: {e}")
    
    # Return specific param or full config
    if param:
        return config.get(param)
    return config
