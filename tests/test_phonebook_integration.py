# -*- coding: utf-8 -*-
"""
Integration test for phonebook reverse lookup in scriptname.py
"""
import pytest
import sys
import os

# Make sure we can import from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_phonebook_import():
    """Test that phonebook_lookup can be imported by scriptname."""
    try:
        from scripts.phonebook_lookup import enrich_lead_with_phonebook, PhonebookLookup
        assert enrich_lead_with_phonebook is not None
        assert PhonebookLookup is not None
    except ImportError as e:
        pytest.fail(f"Failed to import phonebook_lookup: {e}")


def test_scriptname_imports_phonebook():
    """Test that scriptname.py imports phonebook_lookup."""
    # Read scriptname.py and check for the import
    with open('scriptname.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that phonebook_lookup is imported
    assert "from scripts.phonebook_lookup import" in content or "import scripts.phonebook_lookup" in content


def test_insert_leads_with_phonebook_enrichment():
    """Test that insert_leads function includes phonebook enrichment logic."""
    # Read scriptname.py and check for the enrichment code
    with open('scriptname.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that it includes phonebook enrichment
    assert "enrich_lead_with_phonebook" in content
    assert "STEP 2.5" in content or "Reverse phonebook" in content


def test_phonebook_enrichment_with_mock_lead():
    """Test phonebook enrichment with a mock lead."""
    from scripts.phonebook_lookup import enrich_lead_with_phonebook
    
    # Create a mock lead with bad name but valid phone
    lead = {
        "name": "Keine Fixkosten",  # Invalid name (ad title)
        "telefon": "+491721234567",
        "quelle": "https://kleinanzeigen.de/test"
    }
    
    # Mock lookup class
    class MockLookup:
        def lookup(self, phone):
            return {
                "name": "Test Person",
                "address": "Test Address",
                "source": "test",
                "confidence": 0.9
            }
    
    # Enrich the lead
    enriched = enrich_lead_with_phonebook(lead, lookup=MockLookup())
    
    # Verify enrichment worked
    assert enriched["name"] == "Test Person"
    assert enriched.get("private_address") == "Test Address"
    assert enriched.get("name_source") == "test"


def test_phonebook_preserves_valid_names():
    """Test that phonebook doesn't overwrite valid names."""
    from scripts.phonebook_lookup import enrich_lead_with_phonebook
    
    lead = {
        "name": "Max Mustermann",  # Valid name
        "telefon": "+491721234567",
        "quelle": "https://example.com"
    }
    
    # Even with a mock that would return different name
    class MockLookup:
        def lookup(self, phone):
            return {
                "name": "Different Name",
                "address": "Test Address",
                "source": "test"
            }
    
    enriched = enrich_lead_with_phonebook(lead, lookup=MockLookup())
    
    # Original name should be preserved
    assert enriched["name"] == "Max Mustermann"


def test_bad_name_detection():
    """Test that bad names are correctly identified."""
    from scripts.phonebook_lookup import enrich_lead_with_phonebook
    
    bad_names = [
        "_probe_",
        "",
        "Unknown Candidate",
        "Keine Fixkosten",
        "Gastronomie",
        "12",  # Too short
    ]
    
    for bad_name in bad_names:
        lead = {
            "name": bad_name,
            "telefon": "+491721234567"
        }
        
        # Mock that returns a name
        class MockLookup:
            def lookup(self, phone):
                return {
                    "name": "Real Name",
                    "source": "test"
                }
        
        enriched = enrich_lead_with_phonebook(lead, lookup=MockLookup())
        
        # Bad name should be replaced
        assert enriched["name"] == "Real Name", f"Failed for bad name: {bad_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
