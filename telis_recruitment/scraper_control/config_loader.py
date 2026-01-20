"""
Scraper Configuration Loader
Lädt alle Scraper-Einstellungen aus der Django DB.
Wird von luca_scraper/config.py importiert.
"""

from typing import Dict, List, Set, Any
import logging

logger = logging.getLogger(__name__)

def get_scraper_config() -> Dict[str, Any]:
    """
    Lädt komplette Scraper-Konfiguration aus DB.
    
    Returns:
        Dict mit allen Scraper-Parametern
    """
    from .models import ScraperConfig
    
    try:
        config = ScraperConfig.get_config()
        
        return {
            # Basis
            'industry': config.industry,
            'mode': config.mode,
            'qpi': config.qpi,
            'daterestrict': config.daterestrict,
            'smart': config.smart,
            'force': config.force,
            'once': config.once,
            'dry_run': config.dry_run,
            
            # HTTP & Networking
            'http_timeout': config.http_timeout,
            'async_limit': config.async_limit,
            'pool_size': config.pool_size,
            'http2_enabled': config.http2_enabled,
            
            # Rate Limiting
            'sleep_between_queries': config.sleep_between_queries,
            'max_google_pages': config.max_google_pages,
            'circuit_breaker_penalty': config.circuit_breaker_penalty,
            'retry_max_per_url': config.retry_max_per_url,
            
            # Scoring
            'min_score': config.min_score,
            'max_per_domain': config.max_per_domain,
            'default_quality_score': config.default_quality_score,
            'confidence_threshold': config.confidence_threshold,
            
            # Feature Flags
            'enable_kleinanzeigen': config.enable_kleinanzeigen,
            'enable_telefonbuch': config.enable_telefonbuch,
            'enable_perplexity': config.enable_perplexity,
            'enable_bing': config.enable_bing,
            'parallel_portal_crawl': config.parallel_portal_crawl,
            'max_concurrent_portals': config.max_concurrent_portals,
            
            # Content
            'allow_pdf': config.allow_pdf,
            'max_content_length': config.max_content_length,
            
            # Security
            'allow_insecure_ssl': config.allow_insecure_ssl,
            'config_version': config.config_version,
        }
    except Exception as e:
        logger.warning(f"Could not load scraper config from DB: {e}")
        return {}


def get_regions() -> Dict[str, List[str]]:
    """Lädt aktive Regionen aus DB."""
    from .models import SearchRegion
    from django.db import OperationalError
    
    try:
        all_regions = list(SearchRegion.objects.filter(is_active=True).values_list('name', flat=True))
        metropolis = list(SearchRegion.objects.filter(is_active=True, is_metropolis=True).values_list('name', flat=True))
        
        return {
            'all': all_regions,
            'metropolis': metropolis,
        }
    except OperationalError as e:
        logger.warning(f"Database not available for regions: {e}")
        return {'all': [], 'metropolis': []}
    except Exception as e:
        logger.warning(f"Could not load regions from DB: {e}")
        return {'all': [], 'metropolis': []}


def get_dorks(category: str = None) -> List[str]:
    """Lädt aktive Dorks aus DB."""
    from .models import SearchDork
    from django.db import OperationalError
    
    try:
        qs = SearchDork.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        return list(qs.order_by('-priority', '-success_rate').values_list('query', flat=True))
    except OperationalError as e:
        logger.warning(f"Database not available for dorks: {e}")
        return []
    except Exception as e:
        logger.warning(f"Could not load dorks from DB: {e}")
        return []


def get_portals() -> Dict[str, Dict]:
    """Lädt Portal-Konfigurationen aus DB."""
    from .models import PortalSource
    from django.db import OperationalError
    
    try:
        portals = {}
        for p in PortalSource.objects.filter(is_active=True):
            portals[p.name] = {
                'display_name': p.display_name,
                'base_url': p.base_url,
                'urls': p.urls or [],
                'rate_limit': p.rate_limit_seconds,
                'max_results': p.max_results,
                'requires_login': p.requires_login,
            }
        return portals
    except OperationalError as e:
        logger.warning(f"Database not available for portals: {e}")
        return {}
    except Exception as e:
        logger.warning(f"Could not load portals from DB: {e}")
        return {}


def get_blacklists() -> Dict[str, Set[str]]:
    """Lädt Blacklist-Einträge aus DB."""
    from .models import BlacklistEntry
    from django.db import OperationalError
    
    try:
        return {
            'domains': set(BlacklistEntry.objects.filter(is_active=True, entry_type='domain').values_list('value', flat=True)),
            'path_patterns': set(BlacklistEntry.objects.filter(is_active=True, entry_type='path_pattern').values_list('value', flat=True)),
            'mailbox_prefixes': set(BlacklistEntry.objects.filter(is_active=True, entry_type='mailbox_prefix').values_list('value', flat=True)),
        }
    except OperationalError as e:
        logger.warning(f"Database not available for blacklists: {e}")
        return {'domains': set(), 'path_patterns': set(), 'mailbox_prefixes': set()}
    except Exception as e:
        logger.warning(f"Could not load blacklists from DB: {e}")
        return {'domains': set(), 'path_patterns': set(), 'mailbox_prefixes': set()}
