"""
Crawlers Package
================
Portal-specific crawlers for extracting leads from various German job/classifieds portals.

This package contains individual crawler modules for each supported portal,
along with a generic detail extractor that can be used across multiple portals.

Modules:
    - base: Abstract base class for all crawlers
    - kleinanzeigen: Crawler for Kleinanzeigen.de (formerly eBay Kleinanzeigen)
    - markt_de: Crawler for Markt.de
    - quoka: Crawler for Quoka.de
    - kalaydo: Crawler for Kalaydo.de (strong in Rheinland/NRW)
    - meinestadt: Crawler for MeineStadt.de (city-based)
    - generic: Generic detail extraction functions for multiple portals

Usage:
    from luca_scraper.crawlers import (
        crawl_kleinanzeigen_listings_async,
        crawl_markt_de_listings_async,
        extract_generic_detail_async,
    )
"""

__version__ = "1.0.0"

# Import base crawler
from .base import BaseCrawler

# Import Kleinanzeigen crawler functions
from .kleinanzeigen import (
    crawl_kleinanzeigen_listings_async,
    extract_kleinanzeigen_detail_async,
    crawl_kleinanzeigen_portal_async,
)

# Import other portal crawler functions
from .markt_de import crawl_markt_de_listings_async
from .quoka import crawl_quoka_listings_async
from .kalaydo import crawl_kalaydo_listings_async
from .meinestadt import crawl_meinestadt_listings_async

# Import generic functions
from .generic import (
    extract_generic_detail_async,
    _mark_url_seen,
)

__all__ = [
    # Version
    "__version__",
    
    # Base
    "BaseCrawler",
    
    # Kleinanzeigen
    "crawl_kleinanzeigen_listings_async",
    "extract_kleinanzeigen_detail_async",
    "crawl_kleinanzeigen_portal_async",
    
    # Other Portals
    "crawl_markt_de_listings_async",
    "crawl_quoka_listings_async",
    "crawl_kalaydo_listings_async",
    "crawl_meinestadt_listings_async",
    
    # Generic
    "extract_generic_detail_async",
    "_mark_url_seen",
]
