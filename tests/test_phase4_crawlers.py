"""
Unit Tests for Phase 4 Refactoring
===================================
Tests for crawler modules.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCrawlersPackage:
    """Tests for crawlers package structure."""
    
    def test_crawlers_package_imports(self):
        """Test that crawlers package can be imported."""
        from luca_scraper.crawlers import (
            BaseCrawler,
            crawl_kleinanzeigen_listings_async,
            extract_kleinanzeigen_detail_async,
            crawl_kleinanzeigen_portal_async,
            crawl_markt_de_listings_async,
            crawl_quoka_listings_async,
            crawl_kalaydo_listings_async,
            crawl_meinestadt_listings_async,
            extract_generic_detail_async,
            _mark_url_seen,
        )
        print("✓ All crawler functions can be imported from luca_scraper.crawlers")
    
    def test_base_crawler_exists(self):
        """Test that BaseCrawler class exists."""
        from luca_scraper.crawlers import BaseCrawler
        assert BaseCrawler is not None
        print("✓ BaseCrawler class exists")
    
    def test_kleinanzeigen_functions_exist(self):
        """Test that Kleinanzeigen functions exist."""
        from luca_scraper.crawlers import (
            crawl_kleinanzeigen_listings_async,
            extract_kleinanzeigen_detail_async,
        )
        assert callable(crawl_kleinanzeigen_listings_async)
        assert callable(extract_kleinanzeigen_detail_async)
        print("✓ Kleinanzeigen crawler functions exist")
    
    def test_portal_crawlers_exist(self):
        """Test that all portal crawler functions exist."""
        from luca_scraper.crawlers import (
            crawl_markt_de_listings_async,
            crawl_quoka_listings_async,
            crawl_kalaydo_listings_async,
            crawl_meinestadt_listings_async,
        )
        assert callable(crawl_markt_de_listings_async)
        assert callable(crawl_quoka_listings_async)
        assert callable(crawl_kalaydo_listings_async)
        assert callable(crawl_meinestadt_listings_async)
        print("✓ All portal crawler functions exist")
    
    def test_generic_extractor_exists(self):
        """Test that generic extractor exists."""
        from luca_scraper.crawlers import extract_generic_detail_async
        assert callable(extract_generic_detail_async)
        print("✓ Generic detail extractor exists")
    
    def test_helper_functions_exist(self):
        """Test that helper functions exist."""
        from luca_scraper.crawlers import _mark_url_seen
        assert callable(_mark_url_seen)
        print("✓ Helper functions exist")


class TestBackwardCompatibility:
    """Tests for backward compatibility in scriptname.py."""
    
    def test_scriptname_imports(self):
        """Test that crawler functions can still be imported from scriptname.py."""
        import scriptname
        
        # Check that functions exist
        assert hasattr(scriptname, 'crawl_kleinanzeigen_listings_async')
        assert hasattr(scriptname, 'extract_kleinanzeigen_detail_async')
        assert hasattr(scriptname, 'crawl_markt_de_listings_async')
        assert hasattr(scriptname, 'crawl_quoka_listings_async')
        assert hasattr(scriptname, 'crawl_kalaydo_listings_async')
        assert hasattr(scriptname, 'crawl_meinestadt_listings_async')
        assert hasattr(scriptname, 'extract_generic_detail_async')
        assert hasattr(scriptname, '_mark_url_seen')
        
        print("✓ All crawler functions still accessible from scriptname.py")
    
    def test_functions_are_callable(self):
        """Test that functions are callable."""
        import scriptname
        
        assert callable(scriptname.crawl_kleinanzeigen_listings_async)
        assert callable(scriptname.extract_kleinanzeigen_detail_async)
        assert callable(scriptname.crawl_markt_de_listings_async)
        assert callable(scriptname.crawl_quoka_listings_async)
        assert callable(scriptname.crawl_kalaydo_listings_async)
        assert callable(scriptname.crawl_meinestadt_listings_async)
        assert callable(scriptname.extract_generic_detail_async)
        assert callable(scriptname._mark_url_seen)
        
        print("✓ All functions are callable")


def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Phase 4 Crawler Module Tests")
    print("="*60 + "\n")
    
    # Test crawlers package
    print("Testing Crawlers Package:")
    print("-" * 60)
    test_pkg = TestCrawlersPackage()
    test_pkg.test_crawlers_package_imports()
    test_pkg.test_base_crawler_exists()
    test_pkg.test_kleinanzeigen_functions_exist()
    test_pkg.test_portal_crawlers_exist()
    test_pkg.test_generic_extractor_exists()
    test_pkg.test_helper_functions_exist()
    
    # Test backward compatibility
    print("\nTesting Backward Compatibility:")
    print("-" * 60)
    test_compat = TestBackwardCompatibility()
    test_compat.test_scriptname_imports()
    test_compat.test_functions_are_callable()
    
    print("\n" + "="*60)
    print("All Tests Passed! ✓")
    print("="*60)


if __name__ == "__main__":
    run_tests()
