#!/usr/bin/env python3
"""
Validation script for multi-portal direct crawling implementation.
This script verifies that all required components are properly defined.
"""

import sys
import re

def validate_implementation():
    """Validate that all required components exist in scriptname.py"""
    
    print("=" * 60)
    print("Multi-Portal Direct Crawling - Implementation Validation")
    print("=" * 60)
    print()
    
    with open('scriptname.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = []
    
    # Check URL constants
    print("1. Checking URL constants...")
    url_constants = [
        'MARKT_DE_URLS',
        'QUOKA_DE_URLS', 
        'KALAYDO_DE_URLS',
        'MEINESTADT_DE_URLS',
    ]
    
    for const in url_constants:
        pattern = f'^{const} = \\['
        if re.search(pattern, content, re.MULTILINE):
            # Count URLs in each constant
            match = re.search(f'{const} = \\[(.*?)\\]', content, re.DOTALL)
            if match:
                url_count = match.group(1).count('http')
                print(f"   ✓ {const}: {url_count} URLs defined")
                results.append(True)
        else:
            print(f"   ✗ {const}: NOT FOUND")
            results.append(False)
    
    # Check configuration dict
    print("\n2. Checking source configuration...")
    if re.search(r'^DIRECT_CRAWL_SOURCES = \{', content, re.MULTILINE):
        print("   ✓ DIRECT_CRAWL_SOURCES configuration defined")
        
        # Check all required keys
        required_keys = ['kleinanzeigen', 'markt_de', 'quoka', 'kalaydo', 'meinestadt']
        config_match = re.search(r'DIRECT_CRAWL_SOURCES = \{(.*?)\}', content, re.DOTALL)
        if config_match:
            config_text = config_match.group(1)
            for key in required_keys:
                if f'"{key}"' in config_text:
                    print(f"      ✓ '{key}' key present")
                else:
                    print(f"      ✗ '{key}' key missing")
        results.append(True)
    else:
        print("   ✗ DIRECT_CRAWL_SOURCES: NOT FOUND")
        results.append(False)
    
    # Check crawler functions
    print("\n3. Checking crawler functions...")
    crawler_functions = [
        'crawl_markt_de_listings_async',
        'crawl_quoka_listings_async',
        'crawl_kalaydo_listings_async',
        'crawl_meinestadt_listings_async',
        'extract_generic_detail_async',
    ]
    
    for func in crawler_functions:
        pattern = f'^async def {func}\\('
        if re.search(pattern, content, re.MULTILINE):
            print(f"   ✓ {func}() defined")
            results.append(True)
        else:
            print(f"   ✗ {func}(): NOT FOUND")
            results.append(False)
    
    # Check integration
    print("\n4. Checking integration in run_scrape_once_async()...")
    integration_checks = [
        ('Kleinanzeigen check', 'if DIRECT_CRAWL_SOURCES.get\\("kleinanzeigen"'),
        ('Markt.de call', 'markt_leads = await crawl_markt_de_listings_async\\(\\)'),
        ('Quoka call', 'quoka_leads = await crawl_quoka_listings_async\\(\\)'),
        ('Kalaydo call', 'kalaydo_leads = await crawl_kalaydo_listings_async\\(\\)'),
        ('Meinestadt call', 'meinestadt_leads = await crawl_meinestadt_listings_async\\(\\)'),
        ('Multi-portal message', 'Multi-Portal-Crawling'),
    ]
    
    for check_name, pattern in integration_checks:
        if re.search(pattern, content):
            print(f"   ✓ {check_name}")
            results.append(True)
        else:
            print(f"   ✗ {check_name}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("✓ ALL CHECKS PASSED - Implementation is complete!")
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Please review implementation")
        return 1

if __name__ == "__main__":
    sys.exit(validate_implementation())
