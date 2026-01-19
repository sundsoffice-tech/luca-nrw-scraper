"""Tests for database-backed portal URL loading functionality.

These tests verify that:
1. Portal URLs can be loaded from the database (PortalSource model)
2. Hardcoded URL lists are used as fallback when database is unavailable
3. Configuration includes rate_limit_seconds and max_results fields
"""

import pytest
from unittest.mock import patch, MagicMock


def test_get_portal_urls_returns_list():
    """Test that get_portal_urls returns a list of URLs for known portals."""
    from luca_scraper.config import get_portal_urls
    
    # Test known portals
    for portal_name in ['kleinanzeigen', 'markt_de', 'quoka', 'kalaydo', 
                        'meinestadt', 'dhd24', 'freelancermap', 'freelance_de']:
        urls = get_portal_urls(portal_name)
        assert isinstance(urls, list), f"{portal_name} should return a list"
        assert len(urls) > 0, f"{portal_name} should have at least one URL"
        assert all(isinstance(u, str) for u in urls), f"{portal_name} URLs should be strings"
        assert all(u.startswith('http') for u in urls), f"{portal_name} URLs should start with http"


def test_get_portal_urls_unknown_portal():
    """Test that get_portal_urls returns empty list for unknown portals."""
    from luca_scraper.config import get_portal_urls
    
    urls = get_portal_urls('unknown_portal_xyz')
    assert isinstance(urls, list)
    assert len(urls) == 0


def test_get_portal_config_returns_dict():
    """Test that get_portal_config returns proper configuration dict."""
    from luca_scraper.config import get_portal_config
    
    config = get_portal_config('kleinanzeigen')
    
    # Check required keys
    assert 'urls' in config
    assert 'rate_limit_seconds' in config
    assert 'max_results' in config
    assert 'is_active' in config
    
    # Check types
    assert isinstance(config['urls'], list)
    assert isinstance(config['rate_limit_seconds'], (int, float))
    assert isinstance(config['max_results'], int)
    assert isinstance(config['is_active'], bool)
    
    # Check reasonable values
    assert config['rate_limit_seconds'] > 0
    assert config['max_results'] > 0


def test_get_portal_config_rate_limit():
    """Test that different portals have appropriate rate limits."""
    from luca_scraper.config import get_portal_config
    
    # Check that quoka has higher rate limit (it's a difficult portal)
    quoka_config = get_portal_config('quoka')
    kleinanzeigen_config = get_portal_config('kleinanzeigen')
    
    assert quoka_config['rate_limit_seconds'] >= kleinanzeigen_config['rate_limit_seconds']


def test_get_all_portal_configs():
    """Test that get_all_portal_configs returns all known portals."""
    from luca_scraper.config import get_all_portal_configs
    
    configs = get_all_portal_configs()
    
    # Should return a dict
    assert isinstance(configs, dict)
    
    # Should have the main portals
    expected_portals = {'kleinanzeigen', 'markt_de', 'quoka', 'meinestadt'}
    assert expected_portals.issubset(set(configs.keys()))
    
    # Each config should have required keys
    for portal_name, config in configs.items():
        assert 'urls' in config, f"{portal_name} missing urls"
        assert 'rate_limit_seconds' in config, f"{portal_name} missing rate_limit_seconds"
        assert 'max_results' in config, f"{portal_name} missing max_results"


def test_kleinanzeigen_urls_count():
    """Test that Kleinanzeigen has expected number of URLs."""
    from luca_scraper.config import get_portal_urls, KLEINANZEIGEN_URLS
    
    urls = get_portal_urls('kleinanzeigen')
    
    # Should have multiple URLs (NRW + cities + categories)
    assert len(urls) >= 20, f"Expected at least 20 Kleinanzeigen URLs, got {len(urls)}"
    
    # Should match hardcoded list (when DB is unavailable)
    assert len(urls) == len(KLEINANZEIGEN_URLS)


def test_markt_de_urls():
    """Test Markt.de URLs configuration."""
    from luca_scraper.config import get_portal_urls
    
    urls = get_portal_urls('markt_de')
    
    assert len(urls) >= 5
    assert all('markt.de' in url for url in urls)


def test_quoka_urls():
    """Test Quoka URLs configuration."""
    from luca_scraper.config import get_portal_urls
    
    urls = get_portal_urls('quoka')
    
    assert len(urls) >= 10
    assert all('quoka.de' in url for url in urls)


def test_meinestadt_urls():
    """Test Meinestadt URLs configuration."""
    from luca_scraper.config import get_portal_urls
    
    urls = get_portal_urls('meinestadt')
    
    assert len(urls) >= 10
    assert all('meinestadt.de' in url for url in urls)


def test_freelancermap_urls():
    """Test Freelancermap URLs configuration."""
    from luca_scraper.config import get_portal_urls
    
    urls = get_portal_urls('freelancermap')
    
    assert len(urls) >= 3
    assert all('freelancermap.de' in url for url in urls)


def test_portal_config_fallback():
    """Test that portal config falls back to hardcoded values when DB unavailable."""
    from luca_scraper.config import (
        get_portal_config, 
        PORTAL_DELAYS, 
        DIRECT_CRAWL_SOURCES
    )
    
    config = get_portal_config('kleinanzeigen')
    
    # Rate limit should match PORTAL_DELAYS
    assert config['rate_limit_seconds'] == PORTAL_DELAYS.get('kleinanzeigen', 3.0)


def test_database_integration_mock():
    """Test that database URLs are preferred when available."""
    from luca_scraper import config as config_module
    
    # Mock the database loader
    mock_db_urls = ['https://db.example.com/test1', 'https://db.example.com/test2']
    mock_portals = {
        'test_portal': {
            'urls': mock_db_urls,
            'rate_limit': 5.0,
            'max_results': 30,
        }
    }
    
    with patch.object(config_module, 'SCRAPER_CONFIG_AVAILABLE', True):
        with patch.object(config_module, '_get_portals_django', return_value=mock_portals):
            urls = config_module.get_portal_urls('test_portal')
            
            assert urls == mock_db_urls


def test_exports_available():
    """Test that portal URL functions are exported from luca_scraper."""
    from luca_scraper import (
        get_portal_urls,
        get_portal_config,
        get_all_portal_configs,
    )
    
    assert callable(get_portal_urls)
    assert callable(get_portal_config)
    assert callable(get_all_portal_configs)


class TestScriptnameIntegration:
    """Test integration with scriptname.py PORTAL_CONFIGS."""
    
    def test_portal_configs_uses_database_backed_urls(self):
        """Test that PORTAL_CONFIGS in scriptname.py uses database-backed URLs."""
        import scriptname
        
        # PORTAL_CONFIGS should exist
        assert hasattr(scriptname, 'PORTAL_CONFIGS')
        configs = scriptname.PORTAL_CONFIGS
        
        # Should have known portals
        assert 'kleinanzeigen' in configs
        assert 'markt_de' in configs
        assert 'quoka' in configs
        
        # Each config should have base_urls
        for name, config in configs.items():
            assert 'base_urls' in config, f"{name} missing base_urls"
            assert isinstance(config['base_urls'], list)
    
    def test_portal_configs_url_counts(self):
        """Test that PORTAL_CONFIGS has expected URL counts."""
        import scriptname
        
        configs = scriptname.PORTAL_CONFIGS
        
        # Check URL counts match expectations
        assert len(configs['kleinanzeigen']['base_urls']) >= 20
        assert len(configs['markt_de']['base_urls']) >= 5
        assert len(configs['quoka']['base_urls']) >= 10
