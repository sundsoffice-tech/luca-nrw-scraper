"""
LUCA NRW Scraper - Zentrale Konfiguration
==========================================
Priority logic and configuration loading.

This module has been modularized into:
- luca_scraper/config/defaults.py - Hardcoded default values and constants
- luca_scraper/config/env_loader.py - Environment variable loading
- luca_scraper/config/portal_urls.py - Portal URLs, cities, blacklists, and functions

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
   
3. **Hardcoded Defaults (Lowest Priority)**: Defined in CONFIG_DEFAULTS
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

import threading
import time
import os
from typing import Dict, Optional, Any
import logging

# Import from modularized config subpackages
from .config.defaults import (
    CONFIG_DEFAULTS as _CONFIG_DEFAULTS,
    AI_CONFIG_DEFAULTS,
    CONFIG_REFRESH_INTERVAL_SECONDS as _CONFIG_REFRESH_INTERVAL_SECONDS,
)
from .config.env_loader import (
    ENV_MAPPINGS,
    load_ai_config_from_env,
)
from .config import portal_urls as portal_urls_module

# Re-export all public APIs from submodules for backward compatibility
from .config import *  # noqa: F401, F403

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
    _get_portals_django = None

logger = logging.getLogger(__name__)

# Set Django loaders in portal_urls module to avoid circular imports
portal_urls_module._set_django_loaders(_get_portals_django if SCRAPER_CONFIG_AVAILABLE else None, SCRAPER_CONFIG_AVAILABLE)

# Log the active backend on module import
from .config.env_loader import DATABASE_BACKEND
logger.info(f"Database backend: {DATABASE_BACKEND}")

# =========================
# CENTRALIZED CONFIGURATION LOADER
# =========================

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
    for config_key, (env_var, converter) in ENV_MAPPINGS.items():
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


# =========================
# RUNTIME CONFIGURATION INITIALIZATION
# =========================

# Apply runtime configuration and start watcher
_apply_runtime_config(get_scraper_config())

if SCRAPER_CONFIG_AVAILABLE:
    _start_config_version_watcher()


# =========================
# BACKWARD COMPATIBILITY: RUNTIME GLOBALS
# =========================
# These globals are loaded from the centralized config for backward compatibility
_loaded_config = get_scraper_config()

HTTP_TIMEOUT = _loaded_config['http_timeout']
MAX_FETCH_SIZE = _loaded_config['max_fetch_size']
POOL_SIZE = _loaded_config['pool_size']
ASYNC_LIMIT = _loaded_config['async_limit']
ASYNC_PER_HOST = _loaded_config['async_per_host']
HTTP2_ENABLED = _loaded_config['http2_enabled']
ALLOW_PDF = _loaded_config['allow_pdf']
ALLOW_INSECURE_SSL = _loaded_config['allow_insecure_ssl']
ALLOW_PDF_NON_CV = _loaded_config['allow_pdf_non_cv']
SLEEP_BETWEEN_QUERIES = _loaded_config['sleep_between_queries']
MAX_GOOGLE_PAGES = _loaded_config['max_google_pages']
CB_BASE_PENALTY = _loaded_config['circuit_breaker_penalty']
CB_API_PENALTY = _loaded_config.get('circuit_breaker_api_penalty', 15)
RETRY_MAX_PER_URL = _loaded_config['retry_max_per_url']
MIN_SCORE_ENV = _loaded_config['min_score']
MAX_PER_DOMAIN = _loaded_config['max_per_domain']
DEFAULT_QUALITY_SCORE = _loaded_config['default_quality_score']
MAX_CONTENT_LENGTH = _loaded_config.get('max_content_length', MAX_FETCH_SIZE)
ENABLE_KLEINANZEIGEN = _loaded_config['enable_kleinanzeigen']
TELEFONBUCH_ENRICHMENT_ENABLED = _loaded_config['enable_telefonbuch']
PARALLEL_PORTAL_CRAWL = _loaded_config['parallel_portal_crawl']
MAX_CONCURRENT_PORTALS = _loaded_config['max_concurrent_portals']


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
    # Start with defaults (Priority 3: Hardcoded defaults)
    config = AI_CONFIG_DEFAULTS.copy()
    
    # Priority 2: Override with environment variables if set
    env_overrides = load_ai_config_from_env()
    config.update(env_overrides)
    
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
