#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manual demonstration of phonebook reverse lookup functionality.

This script demonstrates how the phonebook_lookup module works with realistic examples.
"""

from phonebook_lookup import PhonebookLookup, enrich_lead_with_phonebook
import sqlite3
import os

def demo_reverse_lookup():
    """Demonstrate reverse phone number lookup."""
    print("=" * 70)
    print("Phonebook Reverse Lookup Demo")
    print("=" * 70)
    print()
    
    # Create a temporary database
    db_path = "demo_phonebook.db"
    
    # Initialize lookup service
    lookup = PhonebookLookup(db_path=db_path)
    
    # Test with some example numbers
    # Note: These are example numbers and won't find real results
    # In production, real German phone numbers would be looked up
    test_numbers = [
        "+491721234567",
        "+491769876543",
        "+491751112233",
    ]
    
    print("1. Testing individual phone number lookups:")
    print("-" * 70)
    for phone in test_numbers:
        print(f"\nLooking up: {phone}")
        result = lookup.lookup(phone)
        if result:
            print(f"  ✓ Found: {result['name']}")
            if result.get('address'):
                print(f"    Address: {result['address']}")
            print(f"    Source: {result['source']}")
        else:
            print(f"  ✗ No result found (expected for test numbers)")
    
    print("\n" + "=" * 70)
    print("2. Testing lead enrichment:")
    print("-" * 70)
    
    # Create test leads with invalid names
    test_leads = [
        {
            "id": 1,
            "name": "Keine Fixkosten",  # Ad title, not a name
            "telefon": "+491721234567",
            "quelle": "https://kleinanzeigen.de/ad1"
        },
        {
            "id": 2,
            "name": "Gastronomie Thekenverkäufer",  # Job title, not a name
            "telefon": "+491769876543",
            "quelle": "https://kleinanzeigen.de/ad2"
        },
        {
            "id": 3,
            "name": "_probe_",  # Placeholder
            "telefon": "+491751112233",
            "quelle": "https://example.com/ad3"
        },
        {
            "id": 4,
            "name": "Max Mustermann",  # Valid name - should NOT be changed
            "telefon": "+491754445566",
            "quelle": "https://example.com/ad4"
        }
    ]
    
    for lead in test_leads:
        print(f"\nLead {lead['id']}:")
        print(f"  Before: name='{lead['name']}', phone={lead['telefon']}")
        
        enriched = enrich_lead_with_phonebook(lead, lookup=lookup)
        
        print(f"  After:  name='{enriched['name']}', phone={enriched['telefon']}")
        if enriched.get('private_address'):
            print(f"          address='{enriched['private_address']}'")
        if enriched.get('name_source'):
            print(f"          source='{enriched['name_source']}'")
    
    print("\n" + "=" * 70)
    print("3. Testing cache functionality:")
    print("-" * 70)
    
    # Check cache entries
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT phone, name, source FROM phone_lookup_cache")
    entries = cur.fetchall()
    conn.close()
    
    print(f"\nCache entries: {len(entries)}")
    for phone, name, source in entries:
        status = "✓ Found" if name else "✗ Not found"
        print(f"  {phone}: {status} (source: {source})")
    
    print("\n" + "=" * 70)
    print("4. Production usage:")
    print("-" * 70)
    print("""
In production, the phonebook lookup is automatically integrated into the
lead insertion process in scriptname.py:

1. When a lead is being inserted with a phone number but no/invalid name
2. The system automatically looks up the phone number in German phonebooks
3. If a name is found, it replaces the invalid name
4. Results are cached to avoid repeated lookups
5. Rate limiting ensures we don't overwhelm the phonebook services

CLI Commands:
  # Batch enrich all existing leads without names:
  python phonebook_lookup.py --enrich
  
  # Look up a single phone number:
  python phonebook_lookup.py --lookup +491721234567
  
  # Normal scraper operation (automatic enrichment):
  python scriptname.py --once --industry candidates --qpi 30
    """)
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    demo_reverse_lookup()
