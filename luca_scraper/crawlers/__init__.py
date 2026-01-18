# -*- coding: utf-8 -*-
"""Portal-specific crawlers"""

# Base utilities
from .base import _mark_url_seen

# Kleinanzeigen crawler
from .kleinanzeigen import (
    crawl_kleinanzeigen_listings_async,
    extract_kleinanzeigen_detail_async,
    crawl_kleinanzeigen_portal_async,
)

# Other portal crawlers
from .markt_de import crawl_markt_de_listings_async
from .quoka import crawl_quoka_listings_async
from .kalaydo import crawl_kalaydo_listings_async
from .meinestadt import crawl_meinestadt_listings_async
from .dhd24 import crawl_dhd24_listings_async

# Generic detail extractor
from .generic import extract_generic_detail_async

__all__ = [
    # Base
    '_mark_url_seen',
    # Kleinanzeigen
    'crawl_kleinanzeigen_listings_async',
    'extract_kleinanzeigen_detail_async',
    'crawl_kleinanzeigen_portal_async',
    # Portal crawlers
    'crawl_markt_de_listings_async',
    'crawl_quoka_listings_async',
    'crawl_kalaydo_listings_async',
    'crawl_meinestadt_listings_async',
    'crawl_dhd24_listings_async',
    # Generic
    'extract_generic_detail_async',
]
