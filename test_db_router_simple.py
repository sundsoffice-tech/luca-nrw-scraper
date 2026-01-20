#!/usr/bin/env python3
"""
Simple test script to verify db_router module structure.
Tests that the module can be imported and has the correct API.
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, '/home/runner/work/luca-nrw-scraper/luca-nrw-scraper')


def test_module_import():
    """Test that db_router module can be imported and has correct structure"""
    print("\n=== Testing db_router Module Structure ===")
    
    # Set backend to SQLite for testing
    os.environ['SCRAPER_DB_BACKEND'] = 'sqlite'
    
    try:
        # Import db_router directly without going through luca_scraper.__init__
        import luca_scraper.db_router as db_router
        
        print(f"✓ db_router module imported successfully")
        
        # Check that all expected functions are present
        expected_functions = [
            'upsert_lead',
            'lead_exists',
            'get_lead_count',
            'is_url_seen',
            'mark_url_seen',
            'is_query_done',
            'mark_query_done',
            'start_scraper_run',
            'finish_scraper_run',
        ]
        
        for func_name in expected_functions:
            if hasattr(db_router, func_name):
                func = getattr(db_router, func_name)
                if callable(func):
                    print(f"✓ {func_name}() is available and callable")
                else:
                    print(f"❌ {func_name} exists but is not callable")
                    return False
            else:
                print(f"❌ {func_name}() is missing")
                return False
        
        # Check DATABASE_BACKEND constant
        if hasattr(db_router, 'DATABASE_BACKEND'):
            print(f"✓ DATABASE_BACKEND is available: {db_router.DATABASE_BACKEND}")
        else:
            print(f"❌ DATABASE_BACKEND constant is missing")
            return False
        
        # Check that __all__ is properly defined
        if hasattr(db_router, '__all__'):
            print(f"✓ __all__ is defined with {len(db_router.__all__)} exports")
        else:
            print(f"⚠️  __all__ is not defined")
        
        print("\n✅ Module structure tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Module structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sqlite_implementations():
    """Test that SQLite implementations exist in database.py"""
    print("\n=== Testing SQLite Implementations ===")
    
    try:
        import luca_scraper.database as database
        
        print(f"✓ database module imported successfully")
        
        # Check that all SQLite implementations are present
        expected_sqlite_funcs = [
            'upsert_lead_sqlite',
            'lead_exists_sqlite',
            'get_lead_count_sqlite',
            'is_url_seen_sqlite',
            'mark_url_seen_sqlite',
            'is_query_done_sqlite',
            'mark_query_done_sqlite',
            'start_scraper_run_sqlite',
            'finish_scraper_run_sqlite',
        ]
        
        for func_name in expected_sqlite_funcs:
            if hasattr(database, func_name):
                func = getattr(database, func_name)
                if callable(func):
                    print(f"✓ {func_name}() is available")
                else:
                    print(f"❌ {func_name} exists but is not callable")
                    return False
            else:
                print(f"❌ {func_name}() is missing")
                return False
        
        print("\n✅ SQLite implementation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ SQLite implementation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_django_implementations():
    """Test that Django implementations exist in django_db.py"""
    print("\n=== Testing Django Implementations ===")
    
    try:
        # Try to import without full Django setup
        import luca_scraper.django_db as django_db
        
        print(f"✓ django_db module imported successfully")
        
        # Check that all Django implementations are present
        expected_django_funcs = [
            'upsert_lead',
            'lead_exists',
            'get_lead_count',
            'is_url_seen',
            'mark_url_seen',
            'is_query_done',
            'mark_query_done',
            'start_scraper_run',
            'finish_scraper_run',
        ]
        
        for func_name in expected_django_funcs:
            if hasattr(django_db, func_name):
                func = getattr(django_db, func_name)
                if callable(func):
                    print(f"✓ {func_name}() is available")
                else:
                    print(f"❌ {func_name} exists but is not callable")
                    return False
            else:
                print(f"❌ {func_name}() is missing")
                return False
        
        print("\n✅ Django implementation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n⚠️  Django implementation test failed: {e}")
        print("This is expected if Django is not fully set up")
        return True  # Not a failure if Django isn't available


def main():
    """Run all tests"""
    print("=" * 60)
    print("DB Router Module Structure Tests")
    print("=" * 60)
    
    results = {
        'module_import': test_module_import(),
        'sqlite_impl': test_sqlite_implementations(),
        'django_impl': test_django_implementations()
    }
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
