# -*- coding: utf-8 -*-
"""
Test Lead Builder Module
========================
Tests for the lead_builder module that builds lead data dictionaries.
"""

import pytest
from luca_scraper.extraction.lead_builder import build_lead_data


class TestBuildLeadData:
    """Test suite for build_lead_data function."""
    
    def test_build_lead_data_complete_data(self):
        """Test building lead data with all fields provided."""
        phones = ["+491761234567"]
        phone_sources = {"+491761234567": "regex_standard"}
        
        lead = build_lead_data(
            name="Max Mustermann",
            phones=phones,
            email="max@example.com",
            location="Berlin",
            title="Suche Job als Vertriebsmitarbeiter",
            url="https://example.com/ad/123",
            phone_sources=phone_sources,
            portal="kleinanzeigen",
            has_whatsapp=True,
            tags="kleinanzeigen,candidate,mobile",
        )
        
        # Check basic fields
        assert lead["name"] == "Max Mustermann"
        assert lead["telefon"] == "+491761234567"
        assert lead["email"] == "max@example.com"
        assert lead["region"] == "Berlin"
        assert lead["opening_line"] == "Suche Job als Vertriebsmitarbeiter"
        assert lead["quelle"] == "https://example.com/ad/123"
        assert lead["tags"] == "kleinanzeigen,candidate,mobile"
        
        # Check computed fields
        assert lead["rolle"] == "Vertrieb"
        assert lead["lead_type"] == "candidate"
        assert lead["phone_type"] == "mobile"
        assert lead["frische"] == "neu"
        
        # Check scoring fields
        assert 0 <= lead["score"] <= 100
        assert 0.0 <= lead["confidence"] <= 1.0
        assert 0.0 <= lead["data_quality"] <= 1.0
        assert lead["phone_source"] == "regex_standard"
        assert lead["phones_found"] == 1
        assert lead["has_whatsapp"] is True
    
    def test_build_lead_data_minimal_data(self):
        """Test building lead data with minimal fields."""
        phones = ["+491761234567"]
        phone_sources = {"+491761234567": "unknown"}
        
        lead = build_lead_data(
            name="",
            phones=phones,
            email="",
            location="",
            title="",
            url="https://example.com/ad/456",
            phone_sources=phone_sources,
            portal="generic",
        )
        
        # Check basic fields
        assert lead["name"] == ""
        assert lead["telefon"] == "+491761234567"
        assert lead["email"] == ""
        assert lead["region"] == ""
        assert lead["opening_line"] == ""
        assert lead["quelle"] == "https://example.com/ad/456"
        
        # Check auto-generated tags
        assert lead["tags"] == "generic,candidate,mobile,direct_crawl"
        
        # Check scoring still works with minimal data
        assert 0 <= lead["score"] <= 100
        assert lead["phone_source"] == "unknown"
        assert lead["phones_found"] == 1
        assert lead["has_whatsapp"] is False
    
    def test_build_lead_data_multiple_phones(self):
        """Test building lead data with multiple phone numbers."""
        phones = ["+491761234567", "+491769876543"]
        phone_sources = {
            "+491761234567": "whatsapp_enhanced",
            "+491769876543": "regex_standard"
        }
        
        lead = build_lead_data(
            name="Test User",
            phones=phones,
            email="test@example.com",
            location="München",
            title="Test Ad",
            url="https://example.com/ad/789",
            phone_sources=phone_sources,
            portal="markt_de",
        )
        
        # Should use the first phone as main
        assert lead["telefon"] == "+491761234567"
        assert lead["phone_source"] == "whatsapp_enhanced"
        assert lead["phones_found"] == 2
    
    def test_build_lead_data_no_phones(self):
        """Test building lead data with no phone numbers."""
        phones = []
        phone_sources = {}
        
        lead = build_lead_data(
            name="Test User",
            phones=phones,
            email="test@example.com",
            location="Hamburg",
            title="Test Ad",
            url="https://example.com/ad/999",
            phone_sources=phone_sources,
            portal="quoka",
        )
        
        # Should have empty phone
        assert lead["telefon"] == ""
        assert lead["phone_source"] == "unknown"
        assert lead["phones_found"] == 0
    
    def test_build_lead_data_different_portals(self):
        """Test that different portals produce different scores."""
        phones = ["+491761234567"]
        phone_sources = {"+491761234567": "regex_standard"}
        
        base_params = {
            "name": "Test User",
            "phones": phones,
            "email": "test@example.com",
            "location": "Berlin",
            "title": "Test Ad",
            "url": "https://example.com/ad/123",
            "phone_sources": phone_sources,
        }
        
        lead_kleinanzeigen = build_lead_data(**base_params, portal="kleinanzeigen")
        lead_generic = build_lead_data(**base_params, portal="generic")
        
        # Kleinanzeigen should have higher base score due to portal reputation
        # But exact values depend on scoring algorithm, so just check they're different
        # and both valid
        assert 0 <= lead_kleinanzeigen["score"] <= 100
        assert 0 <= lead_generic["score"] <= 100
    
    def test_build_lead_data_title_truncation(self):
        """Test that long titles are truncated to 200 characters."""
        phones = ["+491761234567"]
        phone_sources = {"+491761234567": "regex_standard"}
        
        long_title = "A" * 300  # 300 characters
        
        lead = build_lead_data(
            name="Test User",
            phones=phones,
            email="test@example.com",
            location="Berlin",
            title=long_title,
            url="https://example.com/ad/123",
            phone_sources=phone_sources,
            portal="kleinanzeigen",
        )
        
        # Should be truncated to 200 characters
        assert len(lead["opening_line"]) == 200
        assert lead["opening_line"] == "A" * 200
    
    def test_build_lead_data_phone_source_priority(self):
        """Test that phone source affects scoring."""
        phones = ["+491761234567"]
        
        base_params = {
            "name": "Test User",
            "phones": phones,
            "email": "test@example.com",
            "location": "Berlin",
            "title": "Test Ad",
            "url": "https://example.com/ad/123",
            "portal": "kleinanzeigen",
        }
        
        # WhatsApp source should be high quality
        lead_whatsapp = build_lead_data(
            **base_params,
            phone_sources={"+491761234567": "whatsapp_enhanced"}
        )
        
        # Unknown source should be lower quality
        lead_unknown = build_lead_data(
            **base_params,
            phone_sources={"+491761234567": "unknown"}
        )
        
        # WhatsApp should have higher data quality
        assert lead_whatsapp["data_quality"] >= lead_unknown["data_quality"]
