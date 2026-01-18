"""
Base Crawler Module
===================
Abstract base class for all portal crawlers.

This module provides the interface that all portal-specific crawlers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseCrawler(ABC):
    """
    Abstract base class for portal crawlers.
    
    All portal-specific crawlers should inherit from this class and implement
    the required methods for crawling listings and extracting details.
    """
    
    def __init__(self, portal_name: str):
        """
        Initialize the base crawler.
        
        Args:
            portal_name: Name of the portal (e.g., "Kleinanzeigen", "Markt.de")
        """
        self.portal_name = portal_name
    
    @abstractmethod
    async def crawl_listings(
        self,
        urls: List[str],
        max_pages: int = 3,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Crawl listing pages and extract lead candidates.
        
        Args:
            urls: List of listing URLs to crawl
            max_pages: Maximum number of pages to crawl per URL
            max_results: Maximum number of results to return
            
        Returns:
            List of lead dictionaries with contact information
        """
        pass
    
    @abstractmethod
    async def extract_detail(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract lead details from a detail page.
        
        Args:
            url: URL of the detail page
            html: HTML content of the page
            
        Returns:
            Dict with lead data or None if extraction failed
        """
        pass
    
    def get_portal_name(self) -> str:
        """
        Return the portal name for logging.
        
        Returns:
            Portal name string
        """
        return self.portal_name
