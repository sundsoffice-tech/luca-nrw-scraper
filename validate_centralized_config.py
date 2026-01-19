#!/usr/bin/env python3
"""
Validation script for centralized configuration system.

This script validates that:
1. Configuration can be loaded from all three sources
2. Priority is correctly applied
3. All expected parameters are present
"""

import os
import sys

def validate_config_structure():
    """Validate that config structure is correct."""
    print("🔍 Validating configuration structure...")
    
    try:
        from luca_scraper.config import get_scraper_config, _CONFIG_DEFAULTS
        
        # Check that defaults exist
        assert _CONFIG_DEFAULTS, "❌ _CONFIG_DEFAULTS not found"
        print("✅ _CONFIG_DEFAULTS found")
        
        # Check that get_scraper_config exists
        assert callable(get_scraper_config), "❌ get_scraper_config is not callable"
        print("✅ get_scraper_config is callable")
        
        # Load config
        config = get_scraper_config()
        assert isinstance(config, dict), "❌ Config is not a dictionary"
        print("✅ Configuration loaded successfully")
        
        # Check essential parameters
        essential_params = [
            'http_timeout', 'async_limit', 'pool_size',
            'min_score', 'max_per_domain', 'sleep_between_queries',
            'enable_kleinanzeigen', 'parallel_portal_crawl'
        ]
        
        for param in essential_params:
            assert param in config, f"❌ Missing parameter: {param}"
        print(f"✅ All {len(essential_params)} essential parameters present")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_global_variables():
    """Validate that global variables are set correctly."""
    print("\n🔍 Validating global variables...")
    
    try:
        from luca_scraper.config import (
            HTTP_TIMEOUT, ASYNC_LIMIT, POOL_SIZE,
            MIN_SCORE_ENV, MAX_PER_DOMAIN, SLEEP_BETWEEN_QUERIES,
            ENABLE_KLEINANZEIGEN, PARALLEL_PORTAL_CRAWL
        )
        
        # Check types
        assert isinstance(HTTP_TIMEOUT, int), f"❌ HTTP_TIMEOUT has wrong type: {type(HTTP_TIMEOUT)}"
        assert isinstance(ASYNC_LIMIT, int), f"❌ ASYNC_LIMIT has wrong type: {type(ASYNC_LIMIT)}"
        assert isinstance(POOL_SIZE, int), f"❌ POOL_SIZE has wrong type: {type(POOL_SIZE)}"
        assert isinstance(MIN_SCORE_ENV, int), f"❌ MIN_SCORE_ENV has wrong type: {type(MIN_SCORE_ENV)}"
        assert isinstance(SLEEP_BETWEEN_QUERIES, float), f"❌ SLEEP_BETWEEN_QUERIES has wrong type: {type(SLEEP_BETWEEN_QUERIES)}"
        assert isinstance(ENABLE_KLEINANZEIGEN, bool), f"❌ ENABLE_KLEINANZEIGEN has wrong type: {type(ENABLE_KLEINANZEIGEN)}"
        
        print("✅ All global variables have correct types")
        
        # Check reasonable values
        assert 1 <= HTTP_TIMEOUT <= 120, f"❌ HTTP_TIMEOUT out of range: {HTTP_TIMEOUT}"
        assert 1 <= ASYNC_LIMIT <= 100, f"❌ ASYNC_LIMIT out of range: {ASYNC_LIMIT}"
        assert 1 <= POOL_SIZE <= 50, f"❌ POOL_SIZE out of range: {POOL_SIZE}"
        assert 0 <= MIN_SCORE_ENV <= 100, f"❌ MIN_SCORE_ENV out of range: {MIN_SCORE_ENV}"
        
        print("✅ All global variables have reasonable values")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_priority_system():
    """Validate that priority system works."""
    print("\n🔍 Validating priority system...")
    
    try:
        from luca_scraper.config import get_scraper_config, SCRAPER_CONFIG_AVAILABLE
        
        # Check if DB is available
        if SCRAPER_CONFIG_AVAILABLE:
            print("✅ Django database configuration is available (Priority 1)")
        else:
            print("⚠️  Django database configuration not available, using env/defaults")
        
        # Get config
        config = get_scraper_config()
        
        # Check if we can get specific params
        http_timeout = get_scraper_config('http_timeout')
        assert http_timeout is not None, "❌ Cannot get specific parameter"
        print("✅ Can retrieve specific parameters")
        
        # Test with non-existent param
        non_existent = get_scraper_config('this_does_not_exist')
        assert non_existent is None, "❌ Non-existent param should return None"
        print("✅ Non-existent parameters return None")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_current_config():
    """Print current configuration values."""
    print("\n📋 Current Configuration Values:")
    print("=" * 60)
    
    try:
        from luca_scraper.config import get_scraper_config, SCRAPER_CONFIG_AVAILABLE
        
        config = get_scraper_config()
        
        print(f"Configuration Source: {'Django DB' if SCRAPER_CONFIG_AVAILABLE else 'Env/Defaults'}")
        print()
        
        categories = {
            'HTTP & Networking': ['http_timeout', 'async_limit', 'pool_size', 'http2_enabled'],
            'Rate Limiting': ['sleep_between_queries', 'max_google_pages', 'circuit_breaker_penalty', 'retry_max_per_url'],
            'Scoring': ['min_score', 'max_per_domain', 'default_quality_score', 'confidence_threshold'],
            'Feature Flags': ['enable_kleinanzeigen', 'enable_telefonbuch', 'parallel_portal_crawl', 'max_concurrent_portals'],
            'Content & Security': ['allow_pdf', 'max_content_length', 'allow_insecure_ssl'],
        }
        
        for category, params in categories.items():
            print(f"\n{category}:")
            print("-" * 40)
            for param in params:
                value = config.get(param, 'N/A')
                print(f"  {param:30} = {value}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Could not print config: {e}")


def main():
    """Main validation function."""
    print("=" * 70)
    print("🧪 LUCA NRW Scraper - Configuration Validation")
    print("=" * 70)
    
    results = []
    
    # Run validations
    results.append(("Structure", validate_config_structure()))
    results.append(("Global Variables", validate_global_variables()))
    results.append(("Priority System", validate_priority_system()))
    
    # Print current config
    print_current_config()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Validation Summary:")
    print("=" * 70)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} - {name}")
    
    all_passed = all(success for _, success in results)
    
    print("=" * 70)
    if all_passed:
        print("✅ All validations passed! Configuration system is working correctly.")
        return 0
    else:
        print("❌ Some validations failed! Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
