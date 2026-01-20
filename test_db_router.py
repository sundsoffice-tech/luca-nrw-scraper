#!/usr/bin/env python3
"""
Test script to verify db_router implementation.
Tests both SQLite and Django backends (if Django is available).
"""

import os
import sys
import tempfile

# Add the project directory to the path
sys.path.insert(0, '/home/runner/work/luca-nrw-scraper/luca-nrw-scraper')


def test_sqlite_backend():
    """Test SQLite backend"""
    print("\n=== Testing SQLite Backend ===")
    
    # Set backend to SQLite
    os.environ['SCRAPER_DB_BACKEND'] = 'sqlite'
    
    # Create a temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    os.environ['SCRAPER_DB'] = temp_db.name
    temp_db.close()
    
    try:
        # Force reload of config module to pick up new env vars
        import importlib
        import luca_scraper.config
        importlib.reload(luca_scraper.config)
        
        # Import after setting environment
        from luca_scraper.db_router import (
            start_scraper_run,
            finish_scraper_run,
            is_url_seen,
            mark_url_seen,
            is_query_done,
            mark_query_done,
            upsert_lead,
            get_lead_count,
            DATABASE_BACKEND
        )
        
        print(f"✓ Imports successful")
        print(f"✓ Backend: {DATABASE_BACKEND}")
        
        # Initialize database
        from luca_scraper.database import init_db
        init_db()
        print(f"✓ Database initialized")
        
        # Test scraper run tracking
        run_id = start_scraper_run()
        print(f"✓ Started scraper run: {run_id}")
        
        # Test URL tracking
        test_url = "https://example.com/test"
        assert not is_url_seen(test_url), "URL should not be seen initially"
        mark_url_seen(test_url, run_id)
        assert is_url_seen(test_url), "URL should be seen after marking"
        print(f"✓ URL tracking works")
        
        # Test query tracking
        test_query = "test query"
        assert not is_query_done(test_query), "Query should not be done initially"
        mark_query_done(test_query, run_id)
        assert is_query_done(test_query), "Query should be done after marking"
        print(f"✓ Query tracking works")
        
        # Test lead operations
        initial_count = get_lead_count()
        lead_data = {
            'name': 'Test Lead',
            'email': 'test@example.com',
            'telefon': '+491234567890',
            'quelle': 'test',
            'score': 80
        }
        lead_id, created = upsert_lead(lead_data)
        assert created, "Lead should be created"
        assert get_lead_count() == initial_count + 1, "Lead count should increase"
        print(f"✓ Lead operations work (lead_id={lead_id})")
        
        # Test upsert (update existing)
        lead_id2, created2 = upsert_lead(lead_data)
        assert not created2, "Lead should be updated, not created"
        assert lead_id2 == lead_id, "Lead ID should be the same"
        print(f"✓ Lead upsert works")
        
        # Finish scraper run
        finish_scraper_run(run_id, links_checked=10, leads_new=1, status='completed')
        print(f"✓ Finished scraper run")
        
        print("\n✅ SQLite backend tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ SQLite backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            os.unlink(temp_db.name)
        except:
            pass


def test_django_backend():
    """Test Django backend (if available)"""
    print("\n=== Testing Django Backend ===")
    
    # Set backend to Django
    os.environ['SCRAPER_DB_BACKEND'] = 'django'
    
    try:
        # Force reload of config module to pick up new env vars
        import importlib
        import luca_scraper.config
        importlib.reload(luca_scraper.config)
        
        # Import after setting environment
        from luca_scraper.db_router import (
            start_scraper_run,
            finish_scraper_run,
            is_url_seen,
            mark_url_seen,
            is_query_done,
            mark_query_done,
            upsert_lead,
            get_lead_count,
            DATABASE_BACKEND
        )
        
        print(f"✓ Imports successful")
        print(f"✓ Backend: {DATABASE_BACKEND}")
        
        # Test basic operations (without actually writing to DB in test mode)
        print(f"✓ Django backend imports work")
        print(f"Note: Skipping actual DB operations to avoid modifying production database")
        
        print("\n✅ Django backend import tests passed!")
        return True
        
    except ImportError as e:
        print(f"\n⚠️  Django backend not available: {e}")
        print("This is expected if Django dependencies are not installed")
        return True  # Not a failure, just not available
    except Exception as e:
        print(f"\n❌ Django backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DB Router Test Suite")
    print("=" * 60)
    
    results = {
        'sqlite': test_sqlite_backend(),
        'django': test_django_backend()
    }
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for backend, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{backend.upper()}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
