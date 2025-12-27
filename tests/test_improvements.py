# -*- coding: utf-8 -*-
"""
Unit tests for the improved phonebook lookup, lead validation, and data consistency.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lead_validation import (
    validate_lead_before_insert,
    is_valid_lead_source,
    ALLOWED_LEAD_SOURCES,
)
from data_consistency import (
    normalize_phone,
    normalize_lead,
    deduplicate_by_phone,
    validate_data_quality,
)


class TestLeadValidation:
    """Tests for updated lead validation."""
    
    def test_new_sources_allowed(self):
        """Test that new sources are in the allowed list."""
        assert 'quoka.de' in ALLOWED_LEAD_SOURCES
        assert 'markt.de' in ALLOWED_LEAD_SOURCES
        assert 'dhd24.com' in ALLOWED_LEAD_SOURCES
        assert 'dhd24.de' in ALLOWED_LEAD_SOURCES
        assert 'arbeitsagentur.de' in ALLOWED_LEAD_SOURCES
        assert 'monster.de' in ALLOWED_LEAD_SOURCES
        assert 'freelancermap.de' in ALLOWED_LEAD_SOURCES
    
    def test_lead_with_phone_no_name_accepted(self):
        """Test that leads with phone but no name are accepted."""
        lead = {
            'telefon': '+491721234567',
            'name': '',
            'quelle': 'https://www.kleinanzeigen.de/test',
        }
        valid, reason = validate_lead_before_insert(lead)
        assert valid is True
        assert 'name' in reason.lower() or reason == "OK"
    
    def test_lead_with_phone_invalid_name_accepted(self):
        """Test that leads with phone but invalid name are accepted."""
        lead = {
            'telefon': '+491721234567',
            'name': '_probe_',
            'quelle': 'https://www.kleinanzeigen.de/test',
        }
        valid, reason = validate_lead_before_insert(lead)
        assert valid is True
        assert lead['name'] == ""  # Name should be cleared
    
    def test_lead_with_valid_phone_unknown_source_accepted(self):
        """Test that leads with valid phone from unknown source are accepted."""
        lead = {
            'telefon': '+491721234567',
            'name': 'Max Mustermann',
            'quelle': 'https://unknown-site.com/test',
        }
        valid, reason = validate_lead_before_insert(lead)
        assert valid is True
        assert 'Telefon gültig' in reason or reason == "OK"
    
    def test_source_validation_accepts_new_portals(self):
        """Test that new portal URLs are accepted."""
        urls = [
            'https://www.quoka.de/stellengesuche/vertrieb',
            'https://www.markt.de/jobs/sales',
            'https://www.dhd24.com/jobs',
            'https://www.arbeitsagentur.de/jobsuche',
            'https://www.monster.de/jobs',
        ]
        for url in urls:
            assert is_valid_lead_source(url), f"URL should be valid: {url}"


class TestDataConsistency:
    """Tests for data consistency functions."""
    
    def test_phone_normalization(self):
        """Test phone number normalization."""
        assert normalize_phone('0172 1234567') == '+491721234567'
        assert normalize_phone('+49 172 1234567') == '+491721234567'
        assert normalize_phone('0049-172-1234567') == '+491721234567'
        assert normalize_phone('+491721234567') == '+491721234567'
    
    def test_lead_normalization(self):
        """Test full lead normalization."""
        lead = {
            'name': 'max mustermann',
            'telefon': '0172 1234567',
            'region': 'nordrhein-westfalen',
        }
        normalized = normalize_lead(lead)
        
        assert normalized['name'] == 'Max Mustermann'
        assert normalized['telefon'] == '+491721234567'
        assert normalized['region'] == 'NRW'
        assert 'created_at' in normalized
        assert 'last_updated' in normalized
    
    def test_invalid_name_removed(self):
        """Test that invalid names are removed during normalization."""
        invalid_names = ['_probe_', 'unknown candidate', 'unknown', '']
        for invalid_name in invalid_names:
            lead = {'name': invalid_name, 'telefon': '+491721234567'}
            normalized = normalize_lead(lead)
            assert normalized['name'] == ""
    
    def test_deduplication_by_phone(self):
        """Test deduplication by phone number."""
        leads = [
            {'telefon': '+491721234567', 'name': 'Max Mustermann'},
            {'telefon': '+491721234567', 'name': 'Max M.'},  # Duplicate
            {'telefon': '+491729999999', 'name': 'Anna Schmidt'},
        ]
        unique = deduplicate_by_phone(leads)
        assert len(unique) == 2
        assert unique[0]['telefon'] == '+491721234567'
        assert unique[1]['telefon'] == '+491729999999'
    
    def test_data_quality_score(self):
        """Test data quality scoring."""
        # Minimal lead (only phone)
        minimal = {'telefon': '+491721234567'}
        assert validate_data_quality(minimal) == 30
        
        # Rich lead
        rich = {
            'telefon': '+491721234567',
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'private_address': 'Berlin',
            'region': 'NRW',
            'company_name': 'Test GmbH',
            'name_validated': 1,
        }
        assert validate_data_quality(rich) == 100


class TestPhonebookLookup:
    """Tests for phonebook lookup functionality."""
    
    def test_sources_configuration(self):
        """Test that all sources are configured."""
        from phonebook_lookup import PhonebookLookup
        
        lookup = PhonebookLookup()
        assert len(lookup.SOURCES) == 5
        
        source_names = [s['name'] for s in lookup.SOURCES]
        assert 'dastelefonbuch' in source_names
        assert 'dasoertliche' in source_names
        assert '11880' in source_names
        assert 'goyellow' in source_names
        assert 'klicktel' in source_names
    
    def test_is_valid_name(self):
        """Test name validation."""
        from phonebook_lookup import PhonebookLookup
        
        lookup = PhonebookLookup()
        
        # Valid names
        assert lookup._is_valid_name("Max Mustermann") is True
        assert lookup._is_valid_name("Anna Schmidt") is True
        
        # Invalid names
        assert lookup._is_valid_name("GmbH") is False
        assert lookup._is_valid_name("Firma Test AG") is False
        assert lookup._is_valid_name("keine angabe") is False
        assert lookup._is_valid_name("Max") is False  # Only one word
        assert lookup._is_valid_name("") is False


class TestPerplexityLearning:
    """Tests for Perplexity learning functionality."""
    
    def test_learning_engine_initialization(self):
        """Test that learning engine initializes correctly."""
        import tempfile
        from perplexity_learning import PerplexityLearning
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            pplx = PerplexityLearning(db_path)
            stats = pplx.get_query_stats()
            assert stats['total'] == 0
            assert stats['with_results'] == 0
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_record_and_retrieve(self):
        """Test recording and retrieving results."""
        import tempfile
        from perplexity_learning import PerplexityLearning
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            pplx = PerplexityLearning(db_path)
            
            # Record a result
            query = "site:kleinanzeigen.de vertrieb"
            citations = ["https://www.kleinanzeigen.de/test1", "https://www.kleinanzeigen.de/test2"]
            leads = [
                {'telefon': '+491721234567', 'name': 'Test', 'quelle': 'https://www.kleinanzeigen.de/test1'},
                {'telefon': '+491729999999', 'name': 'Test2', 'quelle': 'https://www.kleinanzeigen.de/test2'},
            ]
            
            pplx.record_perplexity_result(query, citations, leads)
            
            # Check stats
            stats = pplx.get_query_stats()
            assert stats['total'] == 1
            assert stats['total_leads'] == 2
            
            # Check best sources
            sources = pplx.get_best_sources(min_leads=1)
            assert len(sources) >= 1
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
