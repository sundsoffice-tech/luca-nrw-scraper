#!/usr/bin/env python3
"""
Test script for luca_scraper.ai module
"""

import sys

def test_imports():
    """Test that all AI module functions can be imported"""
    try:
        from luca_scraper.ai import (
            openai_extract_contacts,
            validate_real_name_with_ai,
            analyze_content_async,
            extract_contacts_with_ai,
            search_perplexity_async,
            generate_smart_dorks,
        )
        print("✓ All imports successful!")
        
        # Check that functions are callable
        assert callable(openai_extract_contacts)
        assert callable(validate_real_name_with_ai)
        assert callable(analyze_content_async)
        assert callable(extract_contacts_with_ai)
        assert callable(search_perplexity_async)
        assert callable(generate_smart_dorks)
        print("✓ All functions are callable")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_module_structure():
    """Test that module structure is correct"""
    import os
    
    ai_dir = "luca_scraper/ai"
    required_files = [
        "__init__.py",
        "openai_integration.py",
        "perplexity.py"
    ]
    
    for filename in required_files:
        filepath = os.path.join(ai_dir, filename)
        if not os.path.exists(filepath):
            print(f"✗ Missing file: {filepath}")
            return False
        print(f"✓ Found: {filepath}")
    
    return True

if __name__ == "__main__":
    print("Testing luca_scraper.ai module...")
    print("-" * 50)
    
    print("\n1. Testing module structure:")
    struct_ok = test_module_structure()
    
    print("\n2. Testing imports:")
    import_ok = test_imports()
    
    print("\n" + "=" * 50)
    if struct_ok and import_ok:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
