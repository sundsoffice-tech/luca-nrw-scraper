#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the Adaptive Search System.
Demonstrates how to integrate the new adaptive system into an existing scraper.
"""

import os
from typing import List, Dict

# Import the adaptive system
from adaptive_system import create_system_from_env

# Import existing scraper components
from scriptname import (
    validate_phone, 
    normalize_phone,
    should_skip_url_prefetch,
    should_drop_lead,
    DEFAULT_QUERIES,
)


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===\n")
    
    # Create the adaptive system
    system = create_system_from_env(all_dorks=DEFAULT_QUERIES)
    
    # Get current status
    status = system.get_status()
    print(f"Current mode: {status['wasserfall']['current_mode']['name']}")
    print(f"Phone find rate: {status['phone_find_rate']:.2%}")
    print(f"Backed-off hosts: {status['backedoff_hosts']}\n")
    
    # Get rate limits for this run
    limits = system.get_rate_limits()
    print(f"Rate limits:")
    print(f"  DDG: {limits['ddg_bucket_rate']}/min")
    print(f"  Google: {limits['google_bucket_rate']}/min")
    print(f"  Workers: {limits['worker_parallelism']}\n")


def example_scraping_workflow():
    """Example of a complete scraping workflow."""
    print("=== Scraping Workflow Example ===\n")
    
    # Initialize system
    system = create_system_from_env(all_dorks=DEFAULT_QUERIES)
    
    # Select dorks for this run
    selected_dorks = system.select_dorks_for_run()
    print(f"Selected {len(selected_dorks)} dorks for this run:\n")
    
    for dork_info in selected_dorks[:3]:  # Show first 3
        print(f"  Pool: {dork_info['pool']:<8} "
              f"Source: {dork_info['source']:<6} "
              f"Score: {dork_info['score']:.3f}")
        print(f"  Query: {dork_info['dork'][:60]}...\n")
    
    # Simulate scraping workflow
    print("\nSimulating scraping workflow...")
    
    for dork_info in selected_dorks[:2]:  # Process first 2
        dork = dork_info["dork"]
        source = dork_info["source"]
        
        print(f"\nProcessing dork via {source}:")
        print(f"  {dork[:60]}...")
        
        # Check cache first
        cached_results = system.get_cached_query_results(dork, source)
        if cached_results:
            print("  ✓ Using cached results")
            results = cached_results
        else:
            print("  → Performing search...")
            # Simulate search results
            results = [
                {"url": f"https://example{i}.com/page", "title": f"Result {i}"}
                for i in range(5)
            ]
            system.cache_query_results(dork, source, results)
        
        # Record query execution
        system.record_query_execution(dork)
        system.record_serp_results(dork, len(results))
        
        print(f"  Found {len(results)} results")
        
        # Process each result
        for result in results[:3]:  # Process first 3
            url = result["url"]
            
            # Pre-fetch filtering
            should_skip, skip_reason = should_skip_url_prefetch(url, result["title"])
            if should_skip:
                print(f"    ✗ Skipped: {url} (reason: {skip_reason})")
                continue
            
            # Check if URL already seen
            should_fetch, reason = system.should_fetch_url(url)
            if not should_fetch:
                print(f"    ✗ Skipped: {url} (reason: {reason})")
                continue
            
            # Mark as seen
            system.mark_url_seen(url)
            
            print(f"    ✓ Fetching: {url}")
            
            # Simulate fetch and extraction
            system.record_url_fetched(dork, url)
            
            # Simulate lead extraction
            lead = {
                "name": "Max Mustermann",
                "email": "max@example.com",
                "telefon": "+491761234567",  # Valid mobile
                "quelle": url,
            }
            
            system.record_lead_found(dork)
            
            # Validate phone
            is_valid, phone_type = validate_phone(lead["telefon"])
            if not is_valid:
                print(f"      ✗ Invalid phone: {lead['telefon']}")
                system.record_lead_dropped(url, "no_phone")
                continue
            
            print(f"      ✓ Valid {phone_type} phone: {lead['telefon']}")
            
            # Check dropper rules
            should_drop, drop_reason = should_drop_lead(lead, url, "Some text")
            if should_drop:
                print(f"      ✗ Dropped: {drop_reason}")
                system.record_lead_dropped(url, drop_reason)
                continue
            
            system.record_lead_kept(dork)
            
            # Simulate scoring and acceptance
            print(f"      ✓ Lead accepted")
            system.record_accepted_lead(dork)
    
    # Complete the run
    print("\n\nCompleting run...")
    system.complete_run()
    
    # Generate report
    print("\nGenerating report...")
    report = system.generate_report(output_format="json")
    
    print(f"\nReport Summary:")
    print(f"  Total queries: {report['summary']['total_queries']}")
    print(f"  Total fetched: {report['summary']['total_urls_fetched']}")
    print(f"  Total leads found: {report['summary']['total_leads_found']}")
    print(f"  Total accepted: {report['summary']['total_accepted_leads']}")
    print(f"  Phone find rate: {report['summary']['phone_find_rate']}")
    
    if report['top_dorks']:
        print(f"\nTop Dork:")
        top = report['top_dorks'][0]
        print(f"  Query: {top['dork'][:50]}...")
        print(f"  Score: {top['score']:.3f}")
        print(f"  Accepted: {top['accepted']}")


def example_phone_validation():
    """Example of phone validation."""
    print("\n=== Phone Validation Example ===\n")
    
    test_phones = [
        "0176 123 4567",           # Valid DE mobile
        "+49 211 123456",          # Valid DE landline
        "+33 612345678",           # Valid FR mobile
        "123",                     # Invalid (too short)
        "+49 (0) 176 1234567",     # Valid with (0)
    ]
    
    for phone in test_phones:
        normalized = normalize_phone(phone)
        is_valid, phone_type = validate_phone(phone)
        
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"{status:<10} {phone:<25} → {normalized:<20} ({phone_type})")


def example_configuration():
    """Example of system configuration via environment."""
    print("\n=== Configuration Example ===\n")
    
    print("Set environment variables before creating system:")
    print("""
export METRICS_DB=my_metrics.db
export QUERY_CACHE_TTL=86400          # 24 hours
export URL_SEEN_TTL=604800            # 7 days
export WASSERFALL_MODE=moderate       # conservative|moderate|aggressive
export HTTP_TIMEOUT=10                # 10 seconds
export MAX_FETCH_SIZE=2097152         # 2 MB
    """)
    
    print("\nOr set in code:")
    print("""
os.environ["WASSERFALL_MODE"] = "moderate"
system = create_system_from_env(all_dorks=DEFAULT_QUERIES)
    """)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Adaptive Search System - Usage Examples")
    print("="*60 + "\n")
    
    # Run examples
    try:
        example_basic_usage()
        example_phone_validation()
        example_scraping_workflow()
        example_configuration()
        
        print("\n" + "="*60)
        print("Examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Note: Some examples require database initialization.")
        print("See ADAPTIVE_SYSTEM.md for complete documentation.\n")
