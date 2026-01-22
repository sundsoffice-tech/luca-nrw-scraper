# -*- coding: utf-8 -*-
"""
Tests for NEW_SOURCES_CONFIG integration.

Tests the new dork_set="new_sources" feature including:
- NEW_SOURCES_CONFIG loading
- always_crawl domain detection
- Priority-based dork sorting
- Filter bypass for always_crawl domains
- CLI parameter support
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestNewSourcesConfig:
    """Tests for new_sources_config module."""
    
    def test_config_structure(self):
        """Test that NEW_SOURCES_CONFIG has correct structure."""
        from luca_scraper.config.new_sources_config import NEW_SOURCES_CONFIG
        
        assert len(NEW_SOURCES_CONFIG) == 5
        
        required_categories = [
            "handelsvertreter_portale",
            "b2b_verzeichnisse",
            "firmenlisten",
            "lokale_nrw",
            "verbaende"
        ]
        
        for category in required_categories:
            assert category in NEW_SOURCES_CONFIG
            assert "domains" in NEW_SOURCES_CONFIG[category]
            assert "dorks" in NEW_SOURCES_CONFIG[category]
            assert "priority" in NEW_SOURCES_CONFIG[category]
    
    def test_get_new_sources_dorks(self):
        """Test that get_new_sources_dorks returns all dorks."""
        from luca_scraper.config.new_sources_config import get_new_sources_dorks
        
        dorks = get_new_sources_dorks()
        assert len(dorks) == 14  # Total dorks across all categories
        assert all(isinstance(d, str) for d in dorks)
    
    def test_get_new_sources_dorks_by_priority(self):
        """Test that dorks are sorted by priority (descending)."""
        from luca_scraper.config.new_sources_config import get_new_sources_dorks_by_priority
        
        dorks = get_new_sources_dorks_by_priority()
        assert len(dorks) > 0
        
        # Check that dorks are sorted by priority (highest first)
        priorities = [d["priority"] for d in dorks]
        assert priorities == sorted(priorities, reverse=True)
        
        # Check that each dork has required metadata
        for dork_info in dorks:
            assert "dork" in dork_info
            assert "category" in dork_info
            assert "priority" in dork_info
            assert "always_crawl" in dork_info
            assert "domains" in dork_info
    
    def test_get_always_crawl_domains(self):
        """Test that always_crawl domains are correctly identified."""
        from luca_scraper.config.new_sources_config import get_always_crawl_domains
        
        domains = get_always_crawl_domains()
        
        # These should be always_crawl (priority 5 and 4 with always_crawl: True)
        expected_domains = {
            "handelsvertreter.de",
            "cdh.de",
            "handelsvertreter-netzwerk.de",
            "gelbeseiten.de",
            "dasoertliche.de",
            "11880.com",
        }
        
        assert domains == expected_domains
    
    def test_is_always_crawl_url(self):
        """Test URL detection for always_crawl domains."""
        from luca_scraper.config.new_sources_config import is_always_crawl_url
        
        # Should be True
        assert is_always_crawl_url("https://handelsvertreter.de/profile/123")
        assert is_always_crawl_url("https://www.cdh.de/members")
        assert is_always_crawl_url("https://gelbeseiten.de/search?q=test")
        
        # Should be False
        assert not is_always_crawl_url("https://example.com/test")
        assert not is_always_crawl_url("https://listflix.de/test")  # firmenlisten has always_crawl: False
    
    def test_get_source_category_for_url(self):
        """Test source category detection from URL."""
        from luca_scraper.config.new_sources_config import get_source_category_for_url
        
        assert get_source_category_for_url("https://handelsvertreter.de/x") == "handelsvertreter_portale"
        assert get_source_category_for_url("https://gelbeseiten.de/x") == "b2b_verzeichnisse"
        assert get_source_category_for_url("https://listflix.de/x") == "firmenlisten"
        assert get_source_category_for_url("https://koeln.business/x") == "lokale_nrw"
        assert get_source_category_for_url("https://direktvertrieb.de/x") == "verbaende"
        assert get_source_category_for_url("https://unknown.com/x") == "unknown"
    
    def test_get_source_priority_for_url(self):
        """Test source priority detection from URL."""
        from luca_scraper.config.new_sources_config import get_source_priority_for_url
        
        assert get_source_priority_for_url("https://handelsvertreter.de/x") == 5
        assert get_source_priority_for_url("https://gelbeseiten.de/x") == 4
        assert get_source_priority_for_url("https://listflix.de/x") == 4
        assert get_source_priority_for_url("https://koeln.business/x") == 3
        assert get_source_priority_for_url("https://unknown.com/x") == 0
    
    def test_get_dork_metadata(self):
        """Test dork metadata retrieval."""
        from luca_scraper.config.new_sources_config import get_dork_metadata, NEW_SOURCES_CONFIG
        
        # Get a known dork
        known_dork = NEW_SOURCES_CONFIG["handelsvertreter_portale"]["dorks"][0]
        
        meta = get_dork_metadata(known_dork)
        assert meta["category"] == "handelsvertreter_portale"
        assert meta["priority"] == 5
        assert meta["always_crawl"] is True
        
        # Unknown dork should return empty dict
        meta_unknown = get_dork_metadata("unknown dork query")
        assert meta_unknown == {}


class TestSearchManagerDorkSets:
    """Tests for search manager dork_set support."""
    
    def test_get_dork_set_default(self):
        """Test that default dork set returns standard dorks."""
        from luca_scraper.search.manager import get_dork_set
        
        default_dorks = get_dork_set("default")
        assert len(default_dorks) > 0
        assert all(isinstance(d, str) for d in default_dorks)
    
    def test_get_dork_set_new_sources(self):
        """Test that new_sources dork set returns new sources dorks."""
        from luca_scraper.search.manager import get_dork_set
        
        new_sources_dorks = get_dork_set("new_sources")
        assert len(new_sources_dorks) == 14  # Total new sources dorks
    
    def test_build_queries_with_dork_set_new_sources(self):
        """Test building queries with new_sources dork set."""
        from luca_scraper.search.manager import build_queries_with_dork_set
        
        dorks = build_queries_with_dork_set("new_sources", per_industry_limit=10)
        
        assert len(dorks) <= 10
        
        # Check structure
        for d in dorks:
            assert "dork" in d
            assert "category" in d
            assert "priority" in d
            assert "always_crawl" in d
            assert "domains" in d
    
    def test_build_queries_with_dork_set_default(self):
        """Test building queries with default dork set."""
        from luca_scraper.search.manager import build_queries_with_dork_set
        
        dorks = build_queries_with_dork_set("default", per_industry_limit=10)
        
        assert len(dorks) <= 10
        
        # Default dorks should have default metadata
        for d in dorks:
            assert d["category"] == "default"
            assert d["priority"] == 1
            assert d["always_crawl"] is False


class TestValidationAlwaysCrawl:
    """Tests for validation module always_crawl bypass."""
    
    def test_is_garbage_context_bypass_for_always_crawl(self):
        """Test that is_garbage_context bypasses for always_crawl URLs."""
        from luca_scraper.scoring.validation import is_garbage_context
        
        always_crawl_url = "https://handelsvertreter.de/profile"
        garbage_content = "warenkorb bestellen preis inkl mwst"  # Shop content
        
        # With bypass enabled (default), should NOT be garbage
        is_garbage, reason = is_garbage_context(
            garbage_content,
            url=always_crawl_url,
            title="Shop",
            bypass_for_always_crawl=True
        )
        assert not is_garbage
        
        # With bypass disabled, should be garbage
        is_garbage2, reason2 = is_garbage_context(
            garbage_content,
            url=always_crawl_url,
            title="Shop",
            bypass_for_always_crawl=False
        )
        assert is_garbage2
        assert reason2 == "shop_product"
    
    def test_is_garbage_context_normal_url(self):
        """Test that is_garbage_context still works for normal URLs."""
        from luca_scraper.scoring.validation import is_garbage_context
        
        normal_url = "https://example.com/page"
        garbage_content = "warenkorb bestellen preis inkl mwst"
        
        # Should be garbage for normal URL
        is_garbage, reason = is_garbage_context(
            garbage_content,
            url=normal_url,
            title="Shop",
            bypass_for_always_crawl=True
        )
        assert is_garbage
        assert reason == "shop_product"
    
    def test_should_skip_url_prefetch_bypass(self):
        """Test that should_skip_url_prefetch respects always_crawl."""
        from luca_scraper.scoring.validation import should_skip_url_prefetch
        
        always_crawl_url = "https://cdh.de/members"
        
        # With bypass enabled, should not skip
        should_skip, reason = should_skip_url_prefetch(
            always_crawl_url,
            bypass_for_always_crawl=True
        )
        assert not should_skip


class TestCLIDorkSetParameter:
    """Tests for CLI --dork-set parameter."""
    
    def test_dork_set_parameter_default(self):
        """Test that --dork-set defaults to 'default'."""
        import sys
        original_argv = sys.argv
        
        try:
            sys.argv = ["test", "--once"]
            from luca_scraper.cli import parse_args
            args = parse_args()
            assert args.dork_set == "default"
        finally:
            sys.argv = original_argv
    
    def test_dork_set_parameter_new_sources(self):
        """Test that --dork-set new_sources is accepted."""
        import sys
        original_argv = sys.argv
        
        try:
            sys.argv = ["test", "--once", "--dork-set", "new_sources"]
            from luca_scraper.cli import parse_args
            args = parse_args()
            assert args.dork_set == "new_sources"
        finally:
            sys.argv = original_argv


class TestCSVExportFields:
    """Tests for new CSV export fields."""
    
    def test_enh_fields_has_new_columns(self):
        """Test that ENH_FIELDS has new source columns."""
        from luca_scraper.config.defaults import ENH_FIELDS
        
        assert "source_category" in ENH_FIELDS
        assert "source_priority" in ENH_FIELDS
        assert "dork_used" in ENH_FIELDS
    
    def test_lead_fields_has_new_columns(self):
        """Test that LEAD_FIELDS has new source columns."""
        from luca_scraper.config.defaults import LEAD_FIELDS
        
        assert "source_category" in LEAD_FIELDS
        assert "source_priority" in LEAD_FIELDS
        assert "dork_used" in LEAD_FIELDS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
