#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script to showcase the Active Learning System functionality.

This script demonstrates:
1. Portal performance tracking
2. Dork/query optimization
3. Phone pattern learning
4. Automatic portal skipping based on poor performance
"""

from learning_engine import ActiveLearningEngine, LearningEngine
import tempfile
import os

def demo_active_learning():
    """Demonstrate the Active Learning System."""
    
    print("=" * 70)
    print("Active Self-Learning AI System Demo")
    print("=" * 70)
    print()
    
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Initialize engines
        base_engine = LearningEngine(db_path)
        learning = ActiveLearningEngine(db_path)
        
        print("✓ Learning engines initialized\n")
        
        # Simulate multiple scraping runs with different portal performances
        print("Simulating Portal Performance Over 5 Runs...")
        print("-" * 70)
        
        portals_data = {
            "kleinanzeigen": [(100, 50, 10), (120, 60, 12), (110, 55, 11), (105, 52, 10), (115, 58, 12)],
            "markt_de": [(80, 30, 5), (85, 32, 6), (90, 35, 7), (88, 33, 6), (92, 36, 7)],
            "quoka": [(50, 10, 2), (55, 12, 2), (52, 11, 2), (54, 10, 1), (51, 9, 1)],
            "meinestadt": [(100, 0, 0), (120, 0, 0), (110, 0, 0), (115, 0, 0), (105, 0, 0)],
            "dhd24": [(60, 8, 1), (65, 9, 1), (70, 10, 2), (68, 9, 1), (72, 11, 2)],
        }
        
        for run_id in range(1, 6):
            print(f"\nRun #{run_id}:")
            for portal, data_list in portals_data.items():
                urls_crawled, leads_found, leads_with_phone = data_list[run_id - 1]
                learning.record_portal_result(
                    portal=portal,
                    urls_crawled=urls_crawled,
                    leads_found=leads_found,
                    leads_with_phone=leads_with_phone,
                    run_id=run_id
                )
                success_rate = (leads_with_phone / urls_crawled) * 100
                print(f"  {portal:15s}: {leads_with_phone:2d}/{leads_found:2d} leads with phone ({success_rate:5.1f}% success)")
        
        print("\n" + "=" * 70)
        print("Portal Performance Analysis")
        print("=" * 70)
        
        # Get portal statistics
        stats = learning.get_portal_stats()
        for portal, portal_stats in sorted(stats.items(), key=lambda x: x[1]['avg_success_rate'], reverse=True):
            print(f"\n{portal}:")
            print(f"  Total runs: {portal_stats['runs']}")
            print(f"  Total URLs: {portal_stats['total_urls']}")
            print(f"  Total leads: {portal_stats['total_leads']}")
            print(f"  Leads with phone: {portal_stats['total_with_phone']}")
            print(f"  Average success rate: {portal_stats['avg_success_rate']*100:.2f}%")
            
            # Check if portal should be skipped
            if learning.should_skip_portal(portal):
                print(f"  ⚠️  RECOMMENDATION: SKIP this portal (< 1% success rate)")
        
        print("\n" + "=" * 70)
        print("Dork/Query Performance Tracking")
        print("=" * 70)
        
        # Simulate dork performance
        dorks_data = [
            ("site:kleinanzeigen.de vertrieb NRW", 50, 12),
            ("site:markt.de sales manager", 30, 8),
            ("vertrieb handy kontakt NRW", 20, 5),
            ("callcenter mitarbeiter gesucht", 15, 0),
            ("aussendienst mobil", 25, 6),
        ]
        
        print("\nRecording dork performance:")
        for dork, leads, with_phone in dorks_data:
            # Record multiple times to simulate usage
            for _ in range(3):
                learning.record_dork_result(dork, leads, with_phone)
            score = (with_phone / leads * 100) if leads > 0 else 0
            print(f"  '{dork[:45]}...' → {with_phone}/{leads} ({score:.0f}%)")
        
        # Get best dorks
        best_dorks = learning.get_best_dorks(n=3)
        print(f"\n✓ Top 3 performing dorks:")
        for i, dork in enumerate(best_dorks, 1):
            print(f"  {i}. {dork}")
        
        print("\n" + "=" * 70)
        print("Phone Pattern Learning")
        print("=" * 70)
        
        # Simulate phone pattern learning
        phone_patterns = [
            ("0171 123 456", "+491711234567", "kleinanzeigen"),
            ("0176-123-456", "+491761234567", "markt_de"),
            ("0162 12 34 56", "+491621234567", "kleinanzeigen"),
            ("0171 987 654", "+491719876547", "quoka"),
            ("0171 555 444", "+491715554447", "kleinanzeigen"),
        ]
        
        print("\nLearning phone patterns:")
        for raw, normalized, portal in phone_patterns:
            learning.learn_phone_pattern(raw, normalized, portal)
            print(f"  {raw:15s} → {normalized:15s} (from {portal})")
        
        learned_patterns = learning.get_learned_phone_patterns()
        print(f"\n✓ Learned {len(learned_patterns)} unique patterns (with >2 occurrences)")
        for pattern in learned_patterns:
            print(f"  - {pattern}")
        
        print("\n" + "=" * 70)
        print("Learning Summary")
        print("=" * 70)
        
        summary = learning.get_learning_summary()
        print(f"\nTotal metrics tracked:")
        print(f"  Portal runs: {summary['total_portal_runs']}")
        print(f"  Dorks tracked: {summary['total_dorks_tracked']}")
        print(f"  Core dorks: {summary['core_dorks']}")
        print(f"  Phone patterns: {summary['phone_patterns_learned']}")
        print(f"  Hosts in backoff: {summary['hosts_in_backoff']}")
        
        print("\n" + "=" * 70)
        print("Recommendations")
        print("=" * 70)
        print("\nBased on the learning data:")
        print("1. ✓ Kleinanzeigen: KEEP (best performer, ~10% success rate)")
        print("2. ✓ Markt.de: KEEP (good performer, ~7-8% success rate)")
        print("3. ⚠️  Quoka: MONITOR (low performer, ~2-3% success rate)")
        print("4. ❌ Meinestadt: DISABLE (0% success rate consistently)")
        print("5. ⚠️  DHD24: MONITOR (low performer, ~1-2% success rate)")
        
        print("\n✅ Demo completed successfully!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    demo_active_learning()
