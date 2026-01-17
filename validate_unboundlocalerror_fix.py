#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for UnboundLocalError fix in ActiveLearningEngine usage.

This script validates that the global declaration of ActiveLearningEngine
prevents UnboundLocalError when the variable is accessed before any 
local assignment in the run_scrape_once_async function.
"""

import sys
import os
import inspect

# Add the parent directory to the path to import scriptname
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_activelearningengine_import():
    """Test that ActiveLearningEngine can be imported from scriptname module."""
    print("Test 1: Checking ActiveLearningEngine import...")
    try:
        from scriptname import ActiveLearningEngine
        
        # ActiveLearningEngine should either be a class or None (if import failed)
        assert ActiveLearningEngine is None or callable(ActiveLearningEngine)
        print("✓ PASS: ActiveLearningEngine import successful")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def test_activelearningengine_global_declaration():
    """Test that ActiveLearningEngine is properly declared as global in run_scrape_once_async."""
    print("\nTest 2: Checking global declaration...")
    try:
        from scriptname import run_scrape_once_async
        
        # Get the source code of the function
        source = inspect.getsource(run_scrape_once_async)
        
        # Check that the function contains a global declaration for ActiveLearningEngine
        has_global = 'global' in source and 'ActiveLearningEngine' in source
        assert has_global, "ActiveLearningEngine should be declared as global in run_scrape_once_async"
        
        # Verify the global declaration appears early in the function (before usage)
        lines = source.split('\n')
        global_line = None
        usage_line = None
        
        for i, line in enumerate(lines):
            if 'global' in line and 'ActiveLearningEngine' in line:
                global_line = i
            if global_line is None and 'ActiveLearningEngine is not None' in line:
                usage_line = i
        
        assert global_line is not None, "Global declaration for ActiveLearningEngine not found"
        if usage_line is not None:
            assert global_line < usage_line, \
                "Global declaration should appear before first usage of ActiveLearningEngine"
        
        print(f"✓ PASS: Global declaration found at line {global_line}")
        if usage_line:
            print(f"  First usage at line {usage_line} (after global declaration)")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_problematic_local_import():
    """Test that there's no problematic local import of ActiveLearningEngine."""
    print("\nTest 3: Checking for problematic local imports...")
    try:
        from scriptname import run_scrape_once_async
        
        # Get the source code of the function
        source = inspect.getsource(run_scrape_once_async)
        lines = source.split('\n')
        
        # Check for problematic patterns
        global_declared = False
        local_imports = []
        
        for i, line in enumerate(lines):
            # Check if global is declared
            if 'global' in line and 'ActiveLearningEngine' in line:
                global_declared = True
            
            # Check for local import
            if 'from ai_learning_engine import ActiveLearningEngine' in line:
                local_imports.append((i, line.strip()))
        
        # If there were local imports found, they should be after global declaration
        if local_imports:
            print(f"  Found {len(local_imports)} local import(s):")
            for line_num, line in local_imports:
                print(f"    Line {line_num}: {line}")
            assert global_declared, "Local import found but no global declaration"
            print("  ⚠ WARNING: Local imports found, but global declaration exists")
        
        if global_declared and not local_imports:
            print("✓ PASS: Global declaration exists and no problematic local imports")
        elif global_declared and local_imports:
            print("✓ PASS: Global declaration protects against local imports")
        else:
            print("✓ PASS: No local imports found")
        
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_activelearningengine_none_check():
    """Test that ActiveLearningEngine usage is protected with None checks."""
    print("\nTest 4: Checking for None checks before usage...")
    try:
        from scriptname import run_scrape_once_async
        
        # Get the source code of the function
        source = inspect.getsource(run_scrape_once_async)
        
        # When ActiveLearningEngine is used, it should be checked for None
        if 'ActiveLearningEngine(' in source:
            # Should have a None check before instantiation
            has_none_check = 'ActiveLearningEngine is not None' in source
            assert has_none_check, "ActiveLearningEngine should be checked for None before use"
            print("✓ PASS: None checks found before ActiveLearningEngine usage")
        else:
            print("✓ PASS: ActiveLearningEngine not instantiated in function")
        
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("Validation: UnboundLocalError Fix for ActiveLearningEngine")
    print("=" * 70)
    
    results = []
    results.append(test_activelearningengine_import())
    results.append(test_activelearningengine_global_declaration())
    results.append(test_no_problematic_local_import())
    results.append(test_activelearningengine_none_check())
    
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ ALL TESTS PASSED - Fix is validated!")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Please review the output above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
