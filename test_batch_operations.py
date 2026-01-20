"""
Test batch operations for transaction management optimization.
"""

import os
import sys
import tempfile
from pathlib import Path

# Set up test environment
test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
test_db.close()

os.environ['SCRAPER_DB_PATH'] = test_db.name
os.environ['SCRAPER_DB_BACKEND'] = 'sqlite'

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import only database module directly, not the full luca_scraper package
import luca_scraper.database as database


def test_batch_url_operations():
    """Test batch URL operations."""
    print("\n=== Testing Batch URL Operations ===")
    
    # Test single URL
    url1 = "https://example.com/test1"
    database.mark_url_seen_sqlite(url1, run_id=1)
    assert database.is_url_seen_sqlite(url1), "Single URL should be marked as seen"
    print("✓ Single URL marking works")
    
    # Test batch URLs
    urls = [
        "https://example.com/batch1",
        "https://example.com/batch2",
        "https://example.com/batch3",
        "https://example.com/batch4",
        "https://example.com/batch5",
    ]
    
    database.mark_urls_seen_batch_sqlite(urls, run_id=1)
    
    for url in urls:
        assert database.is_url_seen_sqlite(url), f"Batch URL {url} should be marked as seen"
    
    print(f"✓ Batch marking of {len(urls)} URLs works")
    
    # Test empty batch (should not crash)
    database.mark_urls_seen_batch_sqlite([], run_id=1)
    print("✓ Empty batch handled correctly")
    
    # Test duplicate URLs (should not crash)
    database.mark_urls_seen_batch_sqlite(urls, run_id=1)
    print("✓ Duplicate URLs handled correctly")


def test_batch_query_operations():
    """Test batch query operations."""
    print("\n=== Testing Batch Query Operations ===")
    
    # Test single query
    query1 = "test query 1"
    database.mark_query_done_sqlite(query1, run_id=1)
    assert database.is_query_done_sqlite(query1), "Single query should be marked as done"
    print("✓ Single query marking works")
    
    # Test batch queries
    queries = [
        "batch query 1",
        "batch query 2",
        "batch query 3",
        "batch query 4",
        "batch query 5",
    ]
    
    database.mark_queries_done_batch_sqlite(queries, run_id=1)
    
    for query in queries:
        assert database.is_query_done_sqlite(query), f"Batch query '{query}' should be marked as done"
    
    print(f"✓ Batch marking of {len(queries)} queries works")
    
    # Test empty batch (should not crash)
    database.mark_queries_done_batch_sqlite([], run_id=1)
    print("✓ Empty batch handled correctly")
    
    # Test duplicate queries (should not crash)
    database.mark_queries_done_batch_sqlite(queries, run_id=1)
    print("✓ Duplicate queries handled correctly")


def test_performance_comparison():
    """Compare performance of batch vs individual operations."""
    import time
    
    print("\n=== Performance Comparison ===")
    
    # Test individual URL marking
    individual_urls = [f"https://example.com/perf/individual/{i}" for i in range(100)]
    
    start_time = time.time()
    for url in individual_urls:
        database.mark_url_seen_sqlite(url, run_id=1)
    individual_time = time.time() - start_time
    
    print(f"Individual marking: {len(individual_urls)} URLs in {individual_time:.4f}s")
    
    # Test batch URL marking
    batch_urls = [f"https://example.com/perf/batch/{i}" for i in range(100)]
    
    start_time = time.time()
    database.mark_urls_seen_batch_sqlite(batch_urls, run_id=1)
    batch_time = time.time() - start_time
    
    print(f"Batch marking: {len(batch_urls)} URLs in {batch_time:.4f}s")
    
    if batch_time < individual_time:
        speedup = individual_time / batch_time
        print(f"✓ Batch operation is {speedup:.2f}x faster!")
    else:
        print(f"! Batch operation is slower (unexpected)")
    
    # Verify all URLs were marked
    for url in batch_urls:
        assert database.is_url_seen_sqlite(url), f"Batch URL {url} should be marked"
    print("✓ All batch URLs verified")


def cleanup():
    """Clean up test database."""
    try:
        os.unlink(test_db.name)
        print("\n✓ Test database cleaned up")
    except:
        pass


if __name__ == '__main__':
    try:
        print("Testing Batch Transaction Operations")
        print("=" * 50)
        
        test_batch_url_operations()
        test_batch_query_operations()
        test_performance_comparison()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        
    finally:
        cleanup()
