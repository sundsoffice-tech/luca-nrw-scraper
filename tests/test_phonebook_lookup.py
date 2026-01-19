# -*- coding: utf-8 -*-
"""
Tests for phonebook_lookup module (reverse phone lookup).
"""
import pytest
import sqlite3
import os
import tempfile
from phonebook_lookup import (
    PhonebookLookup,
    enrich_lead_with_phonebook,
    enrich_existing_leads,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def lookup(temp_db):
    """Create a PhonebookLookup instance with temp database."""
    return PhonebookLookup(db_path=temp_db)


def test_phonebook_lookup_init(temp_db):
    """Test that PhonebookLookup initializes correctly and creates cache table."""
    lookup = PhonebookLookup(db_path=temp_db)
    
    # Check that cache table was created
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='phone_lookup_cache'
    """)
    result = cur.fetchone()
    conn.close()
    
    assert result is not None
    assert result[0] == "phone_lookup_cache"


def test_format_phone_for_german_sites(lookup):
    """Test phone number formatting for German sites."""
    # Test +49 conversion to 0
    assert lookup._format_phone_for_german_sites("+491721234567") == "01721234567"
    assert lookup._format_phone_for_german_sites("+49 172 1234567") == "01721234567"
    assert lookup._format_phone_for_german_sites("+49-172-1234567") == "01721234567"
    
    # Test already formatted numbers
    assert lookup._format_phone_for_german_sites("01721234567") == "01721234567"
    assert lookup._format_phone_for_german_sites("0172 123 4567") == "01721234567"


def test_cache_functionality(lookup, temp_db):
    """Test caching of lookup results."""
    test_phone = "+491721234567"
    test_result = {
        "name": "Max Mustermann",
        "address": "Musterstr. 1, 12345 Musterstadt",
        "source": "dastelefonbuch",
        "confidence": 0.9
    }
    
    # Should not be in cache initially
    cached = lookup._check_cache(test_phone)
    assert cached is None
    
    # Save to cache
    lookup._save_cache(test_phone, test_result)
    
    # Should now be in cache
    cached = lookup._check_cache(test_phone)
    assert cached is not None
    assert cached["name"] == "Max Mustermann"
    assert cached["address"] == "Musterstr. 1, 12345 Musterstadt"
    assert cached["source"] == "dastelefonbuch"
    assert cached["confidence"] == 0.9


def test_cache_negative_results(lookup, temp_db):
    """Test that negative results (not found) are also cached."""
    test_phone = "+491721234567"
    
    # Cache a negative result
    lookup._save_cache(test_phone, {"name": None, "source": "not_found", "confidence": 0})
    
    # Check cache
    cached = lookup._check_cache(test_phone)
    assert cached is not None
    assert cached["name"] is None
    assert cached["source"] == "not_found"


def test_enrich_lead_with_phonebook_no_phone():
    """Test that leads without phone are not enriched."""
    lead = {
        "name": "",
        "telefon": "",
        "quelle": "https://example.com"
    }
    
    result = enrich_lead_with_phonebook(lead)
    
    # Lead should remain unchanged (no phone to lookup)
    assert result["name"] == ""


def test_enrich_lead_with_phonebook_has_valid_name():
    """Test that leads with valid names are not enriched."""
    lead = {
        "name": "Max Mustermann",
        "telefon": "+491721234567",
        "quelle": "https://example.com"
    }
    
    result = enrich_lead_with_phonebook(lead)
    
    # Name should remain unchanged (already valid)
    assert result["name"] == "Max Mustermann"


def test_enrich_lead_with_phonebook_invalid_name():
    """Test that leads with invalid names should be enriched."""
    # This test checks the logic, but won't actually find a name
    # since we're using a test phone number
    lead = {
        "name": "_probe_",
        "telefon": "+491721234567",
        "quelle": "https://example.com"
    }
    
    result = enrich_lead_with_phonebook(lead)
    
    # The function should attempt enrichment (we can't test actual lookup
    # without making real HTTP requests, but we can test the logic)
    assert "telefon" in result


def test_enrich_lead_with_phonebook_bad_names():
    """Test that various bad names trigger enrichment."""
    bad_names = [
        "_probe_",
        "",
        None,
        "Unknown Candidate",
        "Keine Fixkosten",
        "Gastronomie",
        "12",  # Too short
        "123",  # No letters
    ]
    
    for bad_name in bad_names:
        lead = {
            "name": bad_name,
            "telefon": "+491721234567",
            "quelle": "https://example.com"
        }
        
        # Create a mock lookup that returns a result
        class MockLookup:
            def lookup(self, phone):
                return {
                    "name": "Real Name",
                    "address": "Test Address",
                    "source": "test",
                    "confidence": 0.9
                }
        
        result = enrich_lead_with_phonebook(lead, lookup=MockLookup())
        
        # Should be enriched with the mock result
        assert result["name"] == "Real Name"
        assert result["private_address"] == "Test Address"
        assert result["name_source"] == "test"


def test_enrich_existing_leads_empty_db(temp_db):
    """Test batch enrichment on empty database."""
    # Create empty leads table
    conn = sqlite3.connect(temp_db)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY,
            name TEXT,
            telefon TEXT,
            private_address TEXT
        )
    """)
    conn.commit()
    conn.close()
    
    # Should handle empty database gracefully
    enrich_existing_leads(db_path=temp_db)
    
    # No errors should occur


def test_enrich_existing_leads_with_data(temp_db):
    """Test batch enrichment with test data."""
    # Create leads table and insert test data
    conn = sqlite3.connect(temp_db)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY,
            name TEXT,
            telefon TEXT,
            private_address TEXT
        )
    """)
    
    # Insert test leads with invalid names
    conn.execute(
        "INSERT INTO leads (name, telefon) VALUES (?, ?)",
        ("_probe_", "+491721234567")
    )
    conn.execute(
        "INSERT INTO leads (name, telefon) VALUES (?, ?)",
        ("", "+491729876543")
    )
    conn.execute(
        "INSERT INTO leads (name, telefon) VALUES (?, ?)",
        ("Valid Name", "+491728888888")
    )
    conn.commit()
    conn.close()
    
    # Run enrichment (won't find real names for test numbers, but should run without errors)
    enrich_existing_leads(db_path=temp_db)
    
    # Verify database is still intact
    conn = sqlite3.connect(temp_db)
    cur = conn.execute("SELECT COUNT(*) FROM leads")
    count = cur.fetchone()[0]
    conn.close()
    
    assert count == 3  # All leads should still be there


def test_rate_limiting(lookup):
    """Test that rate limiting works."""
    import time
    
    # Record time before first rate limit
    start = time.time()
    
    # Call rate limit twice
    lookup._rate_limit()
    first_time = time.time()
    
    lookup._rate_limit()
    second_time = time.time()
    
    # Second call should have been delayed
    delay = second_time - first_time
    
    # min_delay is 2.0 seconds, but allow 0.5s tolerance for test execution time
    assert delay >= 1.5  # At least 1.5 seconds (tolerance for 2.0s min_delay)


def test_lookup_with_cache(lookup, temp_db):
    """Test that lookup uses cache and doesn't make duplicate queries."""
    test_phone = "+491721234567"
    
    # Pre-populate cache with a result
    cached_result = {
        "name": "Cached Name",
        "address": "Cached Address",
        "source": "cache",
        "confidence": 0.9
    }
    lookup._save_cache(test_phone, cached_result)
    
    # Call lookup - should return cached result without making HTTP request
    result = lookup.lookup(test_phone)
    
    assert result is not None
    assert result["name"] == "Cached Name"
    assert result["source"] == "cache"


def test_lookup_respects_negative_cache(lookup, temp_db):
    """Test that negative results are cached and not re-queried."""
    test_phone = "+491721234567"
    
    # Cache a "not found" result
    lookup._save_cache(test_phone, {"name": None, "source": "not_found", "confidence": 0})
    
    # Call lookup - should return None without making HTTP request
    result = lookup.lookup(test_phone)
    
    assert result is None


def test_cli_interface():
    """Test that CLI interface exists and doesn't crash."""
    import phonebook_lookup
    import sys
    
    # Test --help (just make sure it doesn't crash)
    original_argv = sys.argv
    try:
        sys.argv = ["phonebook_lookup.py"]
        # Running without args should show usage info
        # We're not actually running it, just checking it's importable
        assert hasattr(phonebook_lookup, 'enrich_existing_leads')
        assert hasattr(phonebook_lookup, 'PhonebookLookup')
    finally:
        sys.argv = original_argv


def test_integration_with_lead_dict_structure():
    """Test that enrichment works with realistic lead dict structure."""
    lead = {
        "name": "Keine Fixkosten",  # Ad title, not a real name
        "telefon": "+491721234567",
        "email": "",
        "quelle": "https://kleinanzeigen.de/example",
        "score": 75,
        "tags": "kleinanzeigen",
        "region": "Düsseldorf",
        "company_name": "",
        "lead_type": "candidate"
    }
    
    # Create mock lookup
    class MockLookup:
        def lookup(self, phone):
            return {
                "name": "Max Mustermann",
                "address": "Musterstr. 1, 51145 Köln",
                "source": "dastelefonbuch",
                "confidence": 0.9
            }
    
    result = enrich_lead_with_phonebook(lead, lookup=MockLookup())
    
    # Name should be replaced
    assert result["name"] == "Max Mustermann"
    assert result["private_address"] == "Musterstr. 1, 51145 Köln"
    assert result["name_source"] == "dastelefonbuch"
    
    # Other fields should remain intact
    assert result["telefon"] == "+491721234567"
    assert result["quelle"] == "https://kleinanzeigen.de/example"
    assert result["score"] == 75
    assert result["lead_type"] == "candidate"


def test_company_enrichment():
    """Test that company/organization information is enriched."""
    lead = {
        "name": "Unknown Candidate",
        "telefon": "+491721234567",
        "email": "",
        "quelle": "https://kleinanzeigen.de/example",
        "score": 75,
        "tags": "",
        "region": "Düsseldorf",
    }
    
    # Create mock lookup that returns company info
    class MockLookupWithCompany:
        def lookup(self, phone):
            return {
                "name": "Max Mustermann",
                "address": "Musterstr. 1, 51145 Köln",
                "company": "Muster GmbH",
                "source": "dastelefonbuch",
                "confidence": 0.9
            }
    
    result = enrich_lead_with_phonebook(lead, lookup=MockLookupWithCompany())
    
    # Name should be replaced
    assert result["name"] == "Max Mustermann"
    assert result["private_address"] == "Musterstr. 1, 51145 Köln"
    assert result["company_name"] == "Muster GmbH"
    assert result["name_source"] == "dastelefonbuch"


def test_company_enrichment_empty():
    """Test that empty company info doesn't add company_name field."""
    lead = {
        "name": "_probe_",
        "telefon": "+491721234567",
        "email": "",
        "quelle": "https://kleinanzeigen.de/example",
        "score": 75,
        "tags": "",
        "region": "Köln",
    }
    
    # Create mock lookup without company info
    class MockLookupNoCompany:
        def lookup(self, phone):
            return {
                "name": "Anna Schmidt",
                "address": "Hauptstr. 5, 50667 Köln",
                "company": "",  # Empty company
                "source": "dasoertliche",
                "confidence": 0.85
            }
    
    result = enrich_lead_with_phonebook(lead, lookup=MockLookupNoCompany())
    
    # Name should be replaced
    assert result["name"] == "Anna Schmidt"
    assert result["private_address"] == "Hauptstr. 5, 50667 Köln"
    # company_name should not be set when company is empty
    assert result.get("company_name", "") == ""


def test_source_selectors_include_company():
    """Test that all source configurations include company selectors."""
    from phonebook_lookup import PhonebookLookup
    
    lookup = PhonebookLookup()
    
    for source in lookup.SOURCES:
        assert "company" in source["selectors"], f"Source {source['name']} missing company selectors"
        assert len(source["selectors"]["company"]) > 0, f"Source {source['name']} has empty company selectors"


def test_cache_includes_company():
    """Test that the cache stores and retrieves company information."""
    import tempfile
    import os
    from phonebook_lookup import PhonebookLookup
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name
    
    try:
        lookup = PhonebookLookup(temp_db)
        
        # Manually save to cache with company info
        test_result = {
            "name": "Test Person",
            "address": "Test Address",
            "company": "Test Company",
            "source": "test_source",
            "confidence": 0.9
        }
        lookup._save_cache("+491721234567", test_result)
        
        # Check that it's cached correctly
        cached = lookup._check_cache("+491721234567")
        
        assert cached is not None
        assert cached["name"] == "Test Person"
        assert cached["address"] == "Test Address"
        assert cached["company"] == "Test Company"
        assert cached["source"] == "test_source"
        assert cached["confidence"] == 0.9
    finally:
        os.unlink(temp_db)
