"""
Test for ScraperConfig admin field visibility based on DEBUG mode.
"""
import os
import sys
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'telis_recruitment'))

def test_admin_field_visibility_in_debug_mode():
    """Test that allow_insecure_ssl field is visible in DEBUG mode."""
    # Mock settings.DEBUG = True
    with mock.patch('django.conf.settings') as mock_settings:
        mock_settings.DEBUG = True
        
        # Import after mocking
        from scraper_control.admin import ScraperConfigAdmin
        
        # Create admin instance
        admin = ScraperConfigAdmin(model=None, admin_site=None)
        
        # Get fieldsets
        fieldsets = admin.get_fieldsets(request=None, obj=None)
        
        # Find Content fieldset
        content_fieldset = None
        for name, config in fieldsets:
            if name == 'Content':
                content_fieldset = config
                break
        
        assert content_fieldset is not None, "Content fieldset not found"
        assert 'allow_insecure_ssl' in content_fieldset['fields'], \
            "allow_insecure_ssl should be visible in DEBUG mode"
        
        print("✅ Test passed: allow_insecure_ssl is visible in DEBUG mode")


def test_admin_field_visibility_in_production_mode():
    """Test that allow_insecure_ssl field is hidden in production mode."""
    # Mock settings.DEBUG = False
    with mock.patch('django.conf.settings') as mock_settings:
        mock_settings.DEBUG = False
        
        # Import after mocking
        from scraper_control.admin import ScraperConfigAdmin
        
        # Create admin instance
        admin = ScraperConfigAdmin(model=None, admin_site=None)
        
        # Get fieldsets
        fieldsets = admin.get_fieldsets(request=None, obj=None)
        
        # Find Content fieldset
        content_fieldset = None
        for name, config in fieldsets:
            if name == 'Content':
                content_fieldset = config
                break
        
        assert content_fieldset is not None, "Content fieldset not found"
        assert 'allow_insecure_ssl' not in content_fieldset['fields'], \
            "allow_insecure_ssl should be hidden in production mode"
        
        print("✅ Test passed: allow_insecure_ssl is hidden in production mode")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Testing ScraperConfig Admin Field Visibility")
    print("=" * 70 + "\n")
    
    try:
        test_admin_field_visibility_in_debug_mode()
        test_admin_field_visibility_in_production_mode()
        print("\n" + "=" * 70)
        print("✅ All admin field visibility tests passed!")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
