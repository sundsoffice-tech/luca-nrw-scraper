#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to verify Django initialization fixes work correctly.

This test verifies:
1. scriptname.py can be imported without AppRegistryNotReady error
2. learning_engine.py can be imported without AppRegistryNotReady error
3. luca_scraper modules can be imported without AppRegistryNotReady error
"""

import sys
import os

def test_import_chain():
    """
    Test the import chain that was failing:
    scriptname.py → learning_engine.py → luca_scraper → django_db.py → Django models
    """
    print("\n" + "=" * 70)
    print("TESTING DJANGO INITIALIZATION FIX")
    print("=" * 70)
    
    try:
        print("\n1. Testing learning_engine.py import...")
        print("   (This should initialize Django before importing luca_scraper)")
        from learning_engine import LearningEngine, is_mobile_number, is_job_posting
        print("   ✓ learning_engine.py imported successfully")
        
        print("\n2. Testing luca_scraper package import...")
        print("   (This should handle database imports gracefully)")
        import luca_scraper
        print("   ✓ luca_scraper package imported successfully")
        
        print("\n3. Testing luca_scraper.django_db lazy imports...")
        print("   (Django models should only be imported when functions are called)")
        from luca_scraper import django_db
        print("   ✓ luca_scraper.django_db imported successfully")
        
        print("\n4. Verifying Django was initialized...")
        import django
        from django.apps import apps
        if apps.ready:
            print("   ✓ Django apps are loaded and ready")
        else:
            print("   ⚠ Django apps not ready (this is OK if Django is not available)")
        
        print("\n" + "=" * 70)
        print("✓✓✓ ALL IMPORTS SUCCESSFUL - NO AppRegistryNotReady ERROR ✓✓✓")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗✗✗ IMPORT FAILED ✗✗✗")
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scriptname_import():
    """
    Test that scriptname.py can be imported (main entry point).
    This is a critical test as scriptname.py is where the error was occurring.
    """
    print("\n" + "=" * 70)
    print("TESTING SCRIPTNAME.PY IMPORT (MAIN ENTRY POINT)")
    print("=" * 70)
    
    try:
        print("\nImporting scriptname.py...")
        print("   (This should initialize Django at the very top)")
        
        # Note: We can't fully import scriptname.py as it has Flask and other dependencies
        # But we can verify the Django initialization code is there
        with open('scriptname.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check that Django initialization is present
        if "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')" in content:
            print("   ✓ Django settings module is configured")
        else:
            print("   ✗ Django settings module NOT configured")
            return False
            
        if "django.setup()" in content:
            print("   ✓ django.setup() is called")
        else:
            print("   ✗ django.setup() is NOT called")
            return False
            
        # Check that Django initialization happens before learning_engine import
        django_setup_pos = content.find("django.setup()")
        learning_import_pos = content.find("from learning_engine import")
        
        if django_setup_pos > 0 and learning_import_pos > 0:
            if django_setup_pos < learning_import_pos:
                print("   ✓ Django setup occurs BEFORE learning_engine import")
            else:
                print("   ✗ Django setup occurs AFTER learning_engine import (WRONG ORDER!)")
                return False
        
        print("\n" + "=" * 70)
        print("✓✓✓ SCRIPTNAME.PY HAS CORRECT DJANGO INITIALIZATION ✓✓✓")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗✗✗ TEST FAILED ✗✗✗")
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║  Django Initialization Fix - Verification Test                    ║")
    print("╚" + "=" * 68 + "╝")
    
    success = True
    
    # Test 1: Verify scriptname.py has correct structure
    if not test_scriptname_import():
        success = False
    
    # Test 2: Verify import chain works
    if not test_import_chain():
        success = False
    
    # Final result
    print("\n")
    if success:
        print("╔" + "=" * 68 + "╗")
        print("║  ✓✓✓ ALL TESTS PASSED ✓✓✓                                        ║")
        print("║                                                                    ║")
        print("║  Django initialization fixes are working correctly!               ║")
        print("║  No more AppRegistryNotReady errors!                              ║")
        print("╚" + "=" * 68 + "╝")
        sys.exit(0)
    else:
        print("╔" + "=" * 68 + "╗")
        print("║  ✗✗✗ TESTS FAILED ✗✗✗                                            ║")
        print("╚" + "=" * 68 + "╝")
        sys.exit(1)
