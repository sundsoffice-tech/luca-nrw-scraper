#!/usr/bin/env python3
"""
Test the modularized config package without importing luca_scraper package.
"""

import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Direct import of config module components
from luca_scraper.config.defaults import CONFIG_DEFAULTS, USER_AGENT
from luca_scraper.config.env_loader import OPENAI_API_KEY, GCS_KEYS
from luca_scraper.config.portal_urls import KLEINANZEIGEN_URLS, NRW_CITIES, get_portal_urls

# Import from the main config package
from luca_scraper.config import (
    get_scraper_config,
    get_config,
    HTTP_TIMEOUT,
    ENABLE_KLEINANZEIGEN,
)

def test_defaults():
    """Test defaults module."""
    print("Testing defaults module...")
    assert isinstance(CONFIG_DEFAULTS, dict)
    assert 'http_timeout' in CONFIG_DEFAULTS
    assert isinstance(USER_AGENT, str)
    print("✓ defaults module works")

def test_env_loader():
    """Test env_loader module."""
    print("Testing env_loader module...")
    assert isinstance(OPENAI_API_KEY, str)
    assert isinstance(GCS_KEYS, list)
    print("✓ env_loader module works")

def test_portal_urls():
    """Test portal_urls module."""
    print("Testing portal_urls module...")
    assert isinstance(KLEINANZEIGEN_URLS, list)
    assert len(KLEINANZEIGEN_URLS) > 0
    assert isinstance(NRW_CITIES, list)
    assert len(NRW_CITIES) > 0
    assert callable(get_portal_urls)
    urls = get_portal_urls('kleinanzeigen')
    assert isinstance(urls, list)
    assert len(urls) > 0
    print(f"✓ portal_urls module works (found {len(urls)} URLs for kleinanzeigen)")

def test_main_config():
    """Test main config package."""
    print("Testing main config package...")
    assert callable(get_scraper_config)
    assert callable(get_config)
    config = get_scraper_config()
    assert isinstance(config, dict)
    assert 'http_timeout' in config
    assert isinstance(HTTP_TIMEOUT, int)
    assert isinstance(ENABLE_KLEINANZEIGEN, bool)
    print(f"✓ main config package works (HTTP_TIMEOUT={HTTP_TIMEOUT})")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Modularized Config Package")
    print("=" * 60)
    
    test_defaults()
    test_env_loader()
    test_portal_urls()
    test_main_config()
    
    print("=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)

if __name__ == '__main__':
    main()
