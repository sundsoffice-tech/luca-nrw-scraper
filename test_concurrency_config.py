#!/usr/bin/env python3
"""
Test script to verify that async_limit and pool_size are loaded from Django DB.
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis_recruitment.telis.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'telis_recruitment'))

try:
    import django
    django.setup()
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"Django not available: {e}")
    DJANGO_AVAILABLE = False

def test_config_loading():
    """Test that configuration is loaded correctly from Django DB."""
    print("=" * 60)
    print("Testing Concurrency Configuration Loading")
    print("=" * 60)
    
    if not DJANGO_AVAILABLE:
        print("❌ Django is not available, cannot test DB configuration")
        return False
    
    try:
        # Test 1: Load configuration from Django DB
        print("\n1. Loading configuration from Django DB...")
        from telis_recruitment.scraper_control.config_loader import get_scraper_config
        from telis_recruitment.scraper_control.models import ScraperConfig
        
        db_config = get_scraper_config()
        print(f"   ✓ Configuration loaded from DB")
        print(f"   - async_limit: {db_config.get('async_limit')}")
        print(f"   - pool_size: {db_config.get('pool_size')}")
        print(f"   - sleep_between_queries: {db_config.get('sleep_between_queries')}")
        
        # Test 2: Verify ScraperConfig model has the fields
        print("\n2. Verifying ScraperConfig model fields...")
        config = ScraperConfig.get_config()
        print(f"   ✓ ScraperConfig singleton loaded")
        print(f"   - async_limit: {config.async_limit}")
        print(f"   - pool_size: {config.pool_size}")
        
        # Test 3: Test get_performance_params() function
        print("\n3. Testing get_performance_params() function...")
        
        # Need to simulate scriptname.py environment
        sys.path.insert(0, os.path.dirname(__file__))
        
        # Mock the luca_scraper availability
        import scriptname
        scriptname._LUCA_SCRAPER_AVAILABLE = True
        
        params = scriptname.get_performance_params()
        print(f"   ✓ get_performance_params() executed")
        print(f"   - async_limit: {params.get('async_limit')}")
        print(f"   - pool_size: {params.get('pool_size')}")
        print(f"   - request_delay: {params.get('request_delay')}")
        
        # Test 4: Modify config and verify it's picked up
        print("\n4. Testing configuration update...")
        original_async_limit = config.async_limit
        original_pool_size = config.pool_size
        
        # Update to different values
        config.async_limit = 50
        config.pool_size = 20
        config.save()
        print(f"   ✓ Updated async_limit to 50, pool_size to 20")
        
        # Reload and verify
        params_updated = scriptname.get_performance_params()
        print(f"   ✓ Reloaded configuration")
        print(f"   - async_limit: {params_updated.get('async_limit')}")
        print(f"   - pool_size: {params_updated.get('pool_size')}")
        
        # Verify values match
        assert params_updated['async_limit'] == 50, f"Expected async_limit=50, got {params_updated['async_limit']}"
        assert params_updated['pool_size'] == 20, f"Expected pool_size=20, got {params_updated['pool_size']}"
        print(f"   ✓ Configuration values correctly loaded from DB")
        
        # Restore original values
        config.async_limit = original_async_limit
        config.pool_size = original_pool_size
        config.save()
        print(f"   ✓ Restored original configuration values")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_fallback():
    """Test that environment variables work as fallback."""
    print("\n" + "=" * 60)
    print("Testing Environment Variable Fallback")
    print("=" * 60)
    
    # Set environment variables
    os.environ['ASYNC_LIMIT'] = '42'
    os.environ['POOL_SIZE'] = '15'
    
    # Import after setting env vars
    import importlib
    import scriptname
    importlib.reload(scriptname)
    
    # Temporarily disable Django config
    original_available = scriptname._LUCA_SCRAPER_AVAILABLE
    scriptname._LUCA_SCRAPER_AVAILABLE = False
    
    try:
        params = scriptname.get_performance_params()
        print(f"   ✓ get_performance_params() with env vars only")
        print(f"   - async_limit: {params.get('async_limit')}")
        print(f"   - pool_size: {params.get('pool_size')}")
        
        assert params['async_limit'] == 42, f"Expected async_limit=42 from env, got {params['async_limit']}"
        assert params['pool_size'] == 15, f"Expected pool_size=15 from env, got {params['pool_size']}"
        
        print("   ✅ Environment variable fallback works correctly")
        return True
    finally:
        scriptname._LUCA_SCRAPER_AVAILABLE = original_available
        # Clean up env vars
        del os.environ['ASYNC_LIMIT']
        del os.environ['POOL_SIZE']


if __name__ == '__main__':
    success = True
    
    if DJANGO_AVAILABLE:
        success = test_config_loading() and success
    else:
        print("Skipping Django DB tests (Django not available)")
    
    success = test_env_fallback() and success
    
    sys.exit(0 if success else 1)
