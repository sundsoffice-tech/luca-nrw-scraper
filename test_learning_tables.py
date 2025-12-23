#!/usr/bin/env python3
"""
Test script to verify learning tables are created correctly
and can be queried by the dashboard.
"""

import sqlite3
import os
import sys

DB_PATH = "scraper_test.db"

def test_tables_creation():
    """Test that all learning tables are created correctly."""
    print("=" * 60)
    print("Testing Learning Tables Creation")
    print("=" * 60)
    
    # Remove test DB if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Test ai_learning_engine (the one actually used)
    print("\n1. Testing ai_learning_engine.ActiveLearningEngine...")
    from ai_learning_engine import ActiveLearningEngine
    ale = ActiveLearningEngine(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check learning_portal_metrics table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_portal_metrics'")
    assert cursor.fetchone() is not None, "learning_portal_metrics table not created!"
    print("   ✓ learning_portal_metrics table exists")
    
    # Check columns
    cursor.execute("PRAGMA table_info(learning_portal_metrics)")
    columns = {row[1] for row in cursor.fetchall()}
    required_cols = {'id', 'run_id', 'timestamp', 'portal', 'urls_crawled', 
                     'leads_found', 'leads_with_phone', 'success_rate', 'errors'}
    assert required_cols.issubset(columns), f"Missing columns: {required_cols - columns}"
    print(f"   ✓ All required columns present: {sorted(columns)}")
    
    # Check learning_dork_performance table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_dork_performance'")
    assert cursor.fetchone() is not None, "learning_dork_performance table not created!"
    print("   ✓ learning_dork_performance table exists")
    
    # Check columns
    cursor.execute("PRAGMA table_info(learning_dork_performance)")
    columns = {row[1] for row in cursor.fetchall()}
    required_cols = {'id', 'dork', 'times_used', 'total_results', 'leads_found', 
                     'leads_with_phone', 'score', 'pool', 'last_used'}
    assert required_cols.issubset(columns), f"Missing columns: {required_cols - columns}"
    print(f"   ✓ All required columns present: {sorted(columns)}")
    
    conn.close()
    
    # Test learning_engine (backup)
    print("\n2. Testing learning_engine.LearningEngine...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    from learning_engine import LearningEngine
    le = LearningEngine(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_portal_metrics'")
    assert cursor.fetchone() is not None, "learning_portal_metrics table not created!"
    print("   ✓ learning_portal_metrics table exists")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_dork_performance'")
    assert cursor.fetchone() is not None, "learning_dork_performance table not created!"
    print("   ✓ learning_dork_performance table exists")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ All table creation tests passed!")
    print("=" * 60)


def test_data_insertion():
    """Test that we can insert and query data."""
    print("\n" + "=" * 60)
    print("Testing Data Insertion and Queries")
    print("=" * 60)
    
    # Remove test DB if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    from ai_learning_engine import ActiveLearningEngine
    ale = ActiveLearningEngine(DB_PATH)
    
    print("\n1. Testing portal metrics insertion...")
    ale.record_portal_result(
        portal="kleinanzeigen",
        urls_crawled=100,
        leads_found=10,
        leads_with_phone=5,
        errors=2,
        run_id=1
    )
    
    ale.record_portal_result(
        portal="quoka",
        urls_crawled=50,
        leads_found=3,
        leads_with_phone=1,
        errors=0,
        run_id=1
    )
    
    # Query like dashboard does
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT portal, 
               SUM(leads_with_phone) as total_leads,
               ROUND(AVG(success_rate) * 100, 1) as avg_success,
               COUNT(*) as runs,
               SUM(urls_crawled) as total_urls
        FROM learning_portal_metrics 
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY portal 
        ORDER BY avg_success DESC
    """)
    results = cursor.fetchall()
    assert len(results) == 2, f"Expected 2 portals, got {len(results)}"
    print(f"   ✓ Portal metrics query returned {len(results)} portals")
    for row in results:
        print(f"     - {row[0]}: {row[1]} leads, {row[2]}% success, {row[3]} runs, {row[4]} URLs")
    
    print("\n2. Testing dork performance insertion...")
    ale.record_dork_result(
        dork="vertrieb NRW site:kleinanzeigen.de",
        results=20,
        leads_found=5,
        leads_with_phone=3
    )
    
    ale.record_dork_result(
        dork="callcenter NRW site:quoka.de",
        results=15,
        leads_found=2,
        leads_with_phone=1
    )
    
    # Query like dashboard does
    cursor.execute("""
        SELECT dork, leads_with_phone, pool, 
               ROUND(score * 100, 1) as score_pct,
               times_used
        FROM learning_dork_performance 
        WHERE leads_with_phone > 0 
        ORDER BY leads_with_phone DESC, score DESC 
        LIMIT 5
    """)
    results = cursor.fetchall()
    assert len(results) == 2, f"Expected 2 dorks, got {len(results)}"
    print(f"   ✓ Dork performance query returned {len(results)} dorks")
    for i, row in enumerate(results, 1):
        print(f"     {i}. [{row[2]}] {row[1]} Leads ({row[3]}%, {row[4]}x)")
        print(f"        {row[0][:60]}...")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ All data insertion tests passed!")
    print("=" * 60)


def cleanup():
    """Clean up test database."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"\n✓ Cleaned up test database: {DB_PATH}")


if __name__ == "__main__":
    try:
        test_tables_creation()
        test_data_insertion()
        cleanup()
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
