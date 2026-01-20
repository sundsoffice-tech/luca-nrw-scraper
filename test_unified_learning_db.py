#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for unified learning database adapter.
Validates that the consolidated learning system works correctly.
"""

import os
import tempfile
from luca_scraper import learning_db

def test_unified_learning_db():
    """Test the unified learning database adapter"""
    print("Testing unified learning database adapter...")
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db = tmp.name
        # Close the file handle before using it
    
    try:
        print(f"\n1. Testing with SQLite backend (db: {test_db})")
        
        # Test dork performance tracking
        print("\n2. Recording dork usage...")
        learning_db.record_dork_usage(
            query="vertrieb NRW site:kleinanzeigen.de",
            leads_found=10,
            phone_leads=5,
            results=20,
            db_path=test_db
        )
        
        # Record the same dork again to increase times_used
        learning_db.record_dork_usage(
            query="vertrieb NRW site:kleinanzeigen.de",
            leads_found=12,
            phone_leads=6,
            results=25,
            db_path=test_db
        )
        
        learning_db.record_dork_usage(
            query="sales manager Köln",
            leads_found=8,
            phone_leads=3,
            results=15,
            db_path=test_db
        )
        
        # Get top dorks (use min_uses=1 to see all results)
        print("\n3. Retrieving top dorks...")
        top_dorks = learning_db.get_top_dorks(limit=10, min_uses=1, db_path=test_db)
        print(f"   Found {len(top_dorks)} dorks")
        for dork in top_dorks:
            print(f"   - {dork['query'][:50]}... (success: {dork['success_rate']:.1%}, phone_leads: {dork['phone_leads']})")
        
        # Test source performance tracking
        print("\n4. Recording source hits...")
        learning_db.record_source_hit(
            domain="kleinanzeigen.de",
            leads_found=5,
            has_phone=True,
            quality=0.8,
            db_path=test_db
        )
        
        learning_db.record_source_hit(
            domain="markt.de",
            leads_found=3,
            has_phone=True,
            quality=0.6,
            db_path=test_db
        )
        
        # Get best sources
        print("\n5. Retrieving best sources...")
        best_sources = learning_db.get_best_sources(limit=10, min_leads=1, db_path=test_db)
        print(f"   Found {len(best_sources)} sources")
        for source in best_sources:
            print(f"   - {source['domain']}: {source['leads_with_phone']}/{source['leads_found']} leads (quality: {source['avg_quality']:.1%})")
        
        # Test pattern success tracking
        print("\n6. Recording pattern success...")
        learning_db.record_pattern_success(
            pattern_type="phone",
            pattern_value="0171-XXXXXXX",
            metadata={"example": "0171-1234567"},
            db_path=test_db
        )
        
        learning_db.record_pattern_success(
            pattern_type="domain",
            pattern_value="kleinanzeigen.de",
            metadata={"success_count": 5},
            db_path=test_db
        )
        
        # Get top patterns
        print("\n7. Retrieving top patterns...")
        top_patterns = learning_db.get_top_patterns(
            pattern_type="phone",
            limit=10,
            min_confidence=0.0,
            db_path=test_db
        )
        print(f"   Found {len(top_patterns)} phone patterns")
        for pattern in top_patterns:
            print(f"   - {pattern['pattern_value']}: {pattern['occurrences']}x (confidence: {pattern['confidence']:.1%})")
        
        # Test phonebook cache
        print("\n8. Testing phonebook cache...")
        cache_data = {
            "name": "Test Person",
            "phone": "0171-1234567",
            "address": "Test Street 123"
        }
        
        learning_db.set_phonebook_cache(
            query="Test Person Köln",
            results=cache_data,
            ttl_hours=24,
            db_path=test_db
        )
        
        cached = learning_db.get_phonebook_cache(
            query="Test Person Köln",
            db_path=test_db
        )
        
        if cached:
            print(f"   ✓ Cache hit: {cached}")
        else:
            print("   ✗ Cache miss (unexpected)")
        
        # Test non-existent cache
        cached_missing = learning_db.get_phonebook_cache(
            query="Non-existent query",
            db_path=test_db
        )
        
        if cached_missing is None:
            print("   ✓ Cache miss for non-existent query (expected)")
        else:
            print("   ✗ Unexpected cache hit")
        
        # Get learning stats
        print("\n9. Getting learning statistics...")
        stats = learning_db.get_learning_stats(db_path=test_db)
        print(f"   Backend: {stats['backend']}")
        print(f"   Dorks tracked: {stats['dorks_tracked']}")
        print(f"   Core dorks: {stats['core_dorks']}")
        print(f"   Sources tracked: {stats['sources_tracked']}")
        print(f"   Patterns learned: {stats['patterns_learned']}")
        print(f"   Cache entries: {stats['cache_entries']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        
        print("\n✓ All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(test_db):
            os.unlink(test_db)
            print(f"\nCleaned up test database: {test_db}")

if __name__ == "__main__":
    success = test_unified_learning_db()
    exit(0 if success else 1)
