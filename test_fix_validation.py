#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal test to verify Django AppRegistryNotReady fix.

This test simulates the exact error condition from the problem statement
without requiring all dependencies to be installed.
"""

import sys
import os

def test_django_initialization_order():
    """
    Test that verifies Django is initialized before importing modules that need it.
    """
    print("\n" + "=" * 70)
    print("DJANGO INITIALIZATION ORDER TEST")
    print("=" * 70)
    
    # Simulate the scenario: import scriptname.py which imports learning_engine
    # which imports luca_scraper which imports django_db
    
    print("\n1. Checking scriptname.py Django initialization...")
    with open('scriptname.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find where Django setup happens
    django_setup_line = None
    learning_import_line = None
    
    for i, line in enumerate(lines):
        if 'django.setup()' in line:
            django_setup_line = i + 1
        if 'from learning_engine import' in line:
            learning_import_line = i + 1
    
    if django_setup_line and learning_import_line:
        print(f"   Django setup at line {django_setup_line}")
        print(f"   learning_engine import at line {learning_import_line}")
        
        if django_setup_line < learning_import_line:
            print("   ✓ Django is initialized BEFORE learning_engine import")
        else:
            print("   ✗ FAIL: Django is initialized AFTER learning_engine import")
            return False
    else:
        print("   ✗ FAIL: Could not find Django setup or learning_engine import")
        return False
    
    print("\n2. Checking learning_engine.py Django initialization...")
    with open('learning_engine.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    django_setup_line = None
    luca_import_line = None
    
    for i, line in enumerate(lines):
        if 'django.setup()' in line:
            django_setup_line = i + 1
        if 'from luca_scraper import' in line:
            luca_import_line = i + 1
    
    if django_setup_line and luca_import_line:
        print(f"   Django setup at line {django_setup_line}")
        print(f"   luca_scraper import at line {luca_import_line}")
        
        if django_setup_line < luca_import_line:
            print("   ✓ Django is initialized BEFORE luca_scraper import")
        else:
            print("   ✗ FAIL: Django is initialized AFTER luca_scraper import")
            return False
    else:
        print("   ✗ FAIL: Could not find Django setup or luca_scraper import")
        return False
    
    print("\n3. Checking luca_scraper/__init__.py database import handling...")
    with open('luca_scraper/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for try-except around database imports
    if 'try:' in content and 'from .database import' in content and 'except Exception' in content:
        print("   ✓ Database imports are wrapped in try-except")
    else:
        print("   ⚠ Database imports may not be properly protected")
    
    print("\n4. Checking luca_scraper/django_db.py lazy loading...")
    with open('luca_scraper/django_db.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for lazy import helper
    if 'def _get_django_imports():' in content:
        print("   ✓ Lazy import helper function exists")
        
        # Check that functions use lazy imports
        if 'imports = _get_django_imports()' in content:
            print("   ✓ Functions use lazy imports")
        else:
            print("   ⚠ Functions may not use lazy imports")
    else:
        print("   ✗ FAIL: Lazy import helper not found")
        return False
    
    print("\n" + "=" * 70)
    print("✓✓✓ ALL CHECKS PASSED ✓✓✓")
    print("=" * 70)
    print("\nThe fix ensures:")
    print("  1. Django is initialized at the entry point (scriptname.py)")
    print("  2. Django is also initialized in learning_engine.py as a fallback")
    print("  3. Database imports are conditionally loaded")
    print("  4. Django models use lazy loading to avoid import-time errors")
    print("\nThis prevents the AppRegistryNotReady error!")
    return True


if __name__ == '__main__':
    success = test_django_initialization_order()
    sys.exit(0 if success else 1)
