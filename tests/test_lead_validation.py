# -*- coding: utf-8 -*-
"""Integration tests for lead validation with mobile numbers and job posting detection."""

import pytest
import os
import sqlite3
import tempfile
from scriptname import (
    should_drop_lead,
    insert_leads,
    DB_PATH,
    init_db,
)
from learning_engine import is_mobile_number, is_job_posting


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    original_db = DB_PATH
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Temporarily override DB_PATH
    import scriptname
    scriptname.DB_PATH = path
    scriptname._DB_READY = False
    scriptname._LEARNING_ENGINE = None
    
    yield path
    
    # Restore original
    scriptname.DB_PATH = original_db
    scriptname._DB_READY = False
    scriptname._LEARNING_ENGINE = None
    
    if os.path.exists(path):
        os.unlink(path)


class TestMobileOnlyValidation:
    """Tests for mobile-only lead validation."""
    
    def test_mobile_number_required(self):
        """Test that leads without mobile numbers are dropped."""
        # Lead with landline number only
        lead_landline = {
            "name": "Max Mustermann",
            "rolle": "Vertrieb",
            "email": "max@example.com",
            "telefon": "+49211123456",  # Landline
            "quelle": "https://example.com"
        }
        
        should_drop, reason = should_drop_lead(lead_landline, "https://example.com")
        assert should_drop is True
        assert reason == "not_mobile_number"
    
    def test_mobile_number_accepted(self):
        """Test that leads with mobile numbers pass validation."""
        # Lead with mobile number
        lead_mobile = {
            "name": "Max Mustermann",
            "rolle": "Vertrieb",
            "email": "max@example.com",
            "telefon": "+491761234567",  # Mobile
            "quelle": "https://example.com"
        }
        
        should_drop, reason = should_drop_lead(lead_mobile, "https://example.com")
        # May still be dropped for other reasons, but not for phone type
        if should_drop:
            assert reason != "not_mobile_number"
    
    def test_german_mobile_prefixes(self):
        """Test that all German mobile prefixes are accepted."""
        mobile_numbers = ["01512345678", "01612345678", "01712345678"]
        
        for phone in mobile_numbers:
            lead = {
                "name": "Test User",
                "rolle": "Vertrieb",
                "email": "test@example.com",
                "telefon": phone,
                "quelle": "https://example.com/team"
            }
            # Should not be dropped for phone type
            should_drop, reason = should_drop_lead(lead, "https://example.com/team", 
                                                   text="Ich bin Vertriebsleiter", 
                                                   title="Test User - Vertrieb")
            if should_drop:
                assert reason != "not_mobile_number", f"Failed for phone {phone}, reason: {reason}"


class TestJobPostingFilter:
    """Tests for job posting detection and filtering."""
    
    def test_job_posting_url_rejected(self):
        """Test that job posting URLs are rejected."""
        lead = {
            "name": "Sales Manager",
            "telefon": "+491761234567",
            "quelle": "https://example.com/jobs/sales-manager"
        }
        
        should_drop, reason = should_drop_lead(lead, "https://example.com/jobs/sales-manager")
        assert should_drop is True
        assert reason == "job_posting"
    
    def test_job_posting_title_rejected(self):
        """Test that job posting titles are rejected."""
        lead = {
            "name": "Vertriebsmitarbeiter gesucht",
            "telefon": "+491761234567",
            "quelle": "https://example.com/team"
        }
        
        # Even with mobile number, should be rejected
        should_drop, reason = should_drop_lead(
            lead, 
            "https://example.com/team",
            title="Wir suchen Vertriebsmitarbeiter (m/w/d)"
        )
        assert should_drop is True
        assert reason == "job_posting"
    
    def test_job_posting_content_rejected(self):
        """Test that job posting content is rejected."""
        lead = {
            "name": "Max Mustermann",
            "telefon": "+491761234567",
            "quelle": "https://example.com/karriere"
        }
        
        content = """
        Wir suchen einen Vertriebsmitarbeiter (m/w/d) in Vollzeit.
        Ihre Aufgaben: Kaltakquise, Kundenbetreuung
        Wir bieten: Firmenwagen, unbefristete Anstellung
        Bewerben Sie sich jetzt!
        """
        
        should_drop, reason = should_drop_lead(lead, "https://example.com/karriere", text=content)
        assert should_drop is True
        assert reason == "job_posting"
    
    def test_personal_profile_accepted(self):
        """Test that personal profiles are not flagged as job postings."""
        lead = {
            "name": "Max Mustermann",
            "telefon": "+491761234567",
            "quelle": "https://example.com/profile"
        }
        
        content = "Ich bin Vertriebsleiter mit 10 Jahren Erfahrung im Außendienst."
        
        should_drop, reason = should_drop_lead(lead, "https://example.com/profile", text=content)
        # Should not be dropped as job posting
        if should_drop:
            assert reason != "job_posting"


class TestLeadInsertion:
    """Tests for lead insertion with validation."""
    
    def test_insert_with_mobile_number(self, temp_db):
        """Test that leads with mobile numbers are inserted."""
        init_db()
        
        leads = [{
            "name": "Max Mustermann",
            "rolle": "Vertriebsleiter",
            "email": "max@example.com",
            "telefon": "+491761234567",
            "quelle": "https://example.com/team",
            "score": 95,
            "tags": "vertrieb,mobile",
            "region": "NRW",
            "role_guess": "Vertriebsleiter",
            "lead_type": "candidate",
            "salary_hint": "",
            "commission_hint": "",
            "opening_line": "Test",
            "ssl_insecure": "no",
            "company_name": "Example GmbH",
            "company_size": "50-100",
            "hiring_volume": "niedrig",
            "industry": "IT",
            "recency_indicator": "aktuell",
            "location_specific": "Köln",
            "confidence_score": 90,
            "last_updated": "2024-01-01T00:00:00",
            "data_quality": 80,
            "phone_type": "mobile",
            "whatsapp_link": "no",
            "private_address": "",
            "social_profile_url": "",
            "ai_category": "",
            "ai_summary": ""
        }]
        
        inserted = insert_leads(leads)
        assert len(inserted) == 1
        assert inserted[0]["telefon"] == "+491761234567"
    
    def test_insert_without_mobile_rejected(self, temp_db):
        """Test that leads without mobile numbers are rejected."""
        init_db()
        
        leads = [{
            "name": "Max Mustermann",
            "rolle": "Vertriebsleiter",
            "email": "max@example.com",
            "telefon": "+49211123456",  # Landline
            "quelle": "https://example.com/team",
            "score": 95,
            "tags": "vertrieb",
            "region": "NRW",
            "role_guess": "Vertriebsleiter",
            "lead_type": "candidate",
            "salary_hint": "",
            "commission_hint": "",
            "opening_line": "Test",
            "ssl_insecure": "no",
            "company_name": "Example GmbH",
            "company_size": "50-100",
            "hiring_volume": "niedrig",
            "industry": "IT",
            "recency_indicator": "aktuell",
            "location_specific": "Köln",
            "confidence_score": 90,
            "last_updated": "2024-01-01T00:00:00",
            "data_quality": 80,
            "phone_type": "landline",
            "whatsapp_link": "no",
            "private_address": "",
            "social_profile_url": "",
            "ai_category": "",
            "ai_summary": ""
        }]
        
        inserted = insert_leads(leads)
        assert len(inserted) == 0  # Should be rejected
    
    def test_insert_job_posting_rejected(self, temp_db):
        """Test that job postings are rejected even with mobile numbers."""
        init_db()
        
        leads = [{
            "name": "Vertriebsmitarbeiter gesucht",
            "rolle": "Sales",
            "email": "jobs@example.com",
            "telefon": "+491761234567",  # Mobile number
            "quelle": "https://example.com/jobs/vertrieb",
            "score": 95,
            "tags": "vertrieb",
            "region": "NRW",
            "role_guess": "Vertrieb",
            "lead_type": "candidate",
            "salary_hint": "",
            "commission_hint": "",
            "opening_line": "Wir suchen",
            "ssl_insecure": "no",
            "company_name": "Example GmbH",
            "company_size": "50-100",
            "hiring_volume": "niedrig",
            "industry": "IT",
            "recency_indicator": "aktuell",
            "location_specific": "Köln",
            "confidence_score": 90,
            "last_updated": "2024-01-01T00:00:00",
            "data_quality": 80,
            "phone_type": "mobile",
            "whatsapp_link": "no",
            "private_address": "",
            "social_profile_url": "",
            "ai_category": "",
            "ai_summary": ""
        }]
        
        inserted = insert_leads(leads)
        assert len(inserted) == 0  # Should be rejected as job posting


class TestLearningIntegration:
    """Tests for learning engine integration."""
    
    def test_learning_triggered_on_insert(self, temp_db):
        """Test that learning is triggered when a lead is successfully inserted."""
        init_db()
        
        leads = [{
            "name": "Max Mustermann",
            "rolle": "Vertriebsleiter",
            "email": "max@gooddomain.com",
            "telefon": "+491761234567",
            "quelle": "https://gooddomain.com/team",
            "score": 95,
            "tags": "vertrieb,mobile,premium",
            "region": "NRW",
            "role_guess": "Vertriebsleiter",
            "lead_type": "candidate",
            "salary_hint": "",
            "commission_hint": "",
            "opening_line": "Test",
            "ssl_insecure": "no",
            "company_name": "Good Company",
            "company_size": "50-100",
            "hiring_volume": "niedrig",
            "industry": "IT",
            "recency_indicator": "aktuell",
            "location_specific": "Köln",
            "confidence_score": 90,
            "last_updated": "2024-01-01T00:00:00",
            "data_quality": 80,
            "phone_type": "mobile",
            "whatsapp_link": "no",
            "private_address": "",
            "social_profile_url": "",
            "ai_category": "",
            "ai_summary": "",
            "_query_context": "vertrieb kontakt handynummer NRW"
        }]
        
        inserted = insert_leads(leads)
        assert len(inserted) == 1
        
        # Check that learning patterns were created
        from scriptname import get_learning_engine
        learning_engine = get_learning_engine()
        
        # Get learned patterns
        top_domains = learning_engine.get_top_patterns("domain", min_confidence=0.0, min_successes=1)
        assert len(top_domains) > 0
        assert any("gooddomain.com" in d[0] for d in top_domains)
