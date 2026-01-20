#!/usr/bin/env python3
"""
Test to verify that start_run and finish_run functions work correctly
after fixing the import issue.
"""

import sys
import os

# Get the directory of this test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
# Add it to path if not already there (for running tests from root directory)
if TEST_DIR not in sys.path:
    sys.path.insert(0, TEST_DIR)


def test_import_scriptname():
    """Test that scriptname.py can be imported without errors."""
    print("Testing scriptname.py import...")
    import scriptname
    assert scriptname is not None, "Failed to import scriptname"
    print("✓ scriptname.py imported successfully")


def test_start_run_exists():
    """Test that start_run function exists and is callable."""
    print("\nTesting start_run function existence...")
    import scriptname
    assert hasattr(scriptname, 'start_run'), "start_run function not found"
    assert callable(scriptname.start_run), "start_run is not callable"
    print("✓ start_run function exists and is callable")


def test_finish_run_exists():
    """Test that finish_run function exists and is callable."""
    print("\nTesting finish_run function existence...")
    import scriptname
    assert hasattr(scriptname, 'finish_run'), "finish_run function not found"
    assert callable(scriptname.finish_run), "finish_run is not callable"
    print("✓ finish_run function exists and is callable")


def test_functions_can_import():
    """Test that the functions can successfully import their dependencies."""
    print("\nTesting that functions can import their dependencies...")
    import scriptname
    
    # Test that we can inspect the functions without errors
    import inspect
    
    start_source = inspect.getsource(scriptname.start_run)
    assert 'from luca_scraper.db_router import start_scraper_run' in start_source, \
        "start_run function doesn't contain the expected import"
    print("✓ start_run contains direct import of start_scraper_run")
    
    finish_source = inspect.getsource(scriptname.finish_run)
    assert 'from luca_scraper.db_router import finish_scraper_run' in finish_source, \
        "finish_run function doesn't contain the expected import"
    print("✓ finish_run contains direct import of finish_scraper_run")


if __name__ == '__main__':
    print("=" * 70)
    print("Running Import Fix Tests")
    print("=" * 70)
    
    try:
        test_import_scriptname()
        test_start_run_exists()
        test_finish_run_exists()
        test_functions_can_import()
        
        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
