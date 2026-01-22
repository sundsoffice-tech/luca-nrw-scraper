# -*- coding: utf-8 -*-
"""
Tests for Lead Rules Module
===========================

Tests for the lead inclusion/exclusion rules and CSV export.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luca_scraper.scoring.lead_rules import (
    evaluate_lead_for_csv,
    build_csv_row,
    filter_leads_for_csv,
    LeadDecision,
    ExclusionReason,
    InclusionReason,
    LeadRulesConfig,
    DEFAULT_RULES_CONFIG,
    CSV_HEADERS,
    JOB_OFFER_PATTERNS,
    CANDIDATE_PATTERNS,
)


class TestEvaluateLeadForCSV:
    """Tests for evaluate_lead_for_csv function."""
    
    def test_include_high_score(self):
        """Test that high score leads are included."""
        result = evaluate_lead_for_csv(
            text="Vertriebsmitarbeiter sucht neue Herausforderung",
            url="https://example.com/profile",
            score=10,
            has_phone=True,
        )
        
        assert result.decision == LeadDecision.INCLUDE
        assert result.include_in_csv is True
        assert result.reason_code == InclusionReason.HIGH_VALUE_SCORE.value
    
    def test_include_whatsapp(self):
        """Test that WhatsApp contacts are included."""
        result = evaluate_lead_for_csv(
            text="Kontaktieren Sie mich",
            url="https://example.com",
            score=5,
            has_phone=True,
            has_whatsapp=True,
        )
        
        assert result.decision == LeadDecision.INCLUDE
        assert result.include_in_csv is True
        assert result.reason_code == InclusionReason.WHATSAPP_CONTACT.value
    
    def test_include_sales_mobile_nrw(self):
        """Test Vertrieb + Handy + NRW pattern."""
        result = evaluate_lead_for_csv(
            text="Vertriebsmitarbeiter im Außendienst",
            url="https://example.com",
            score=5,
            has_phone=True,
            has_mobile=True,
            is_nrw=True,
        )
        
        assert result.decision == LeadDecision.INCLUDE
        assert result.include_in_csv is True
        assert result.reason_code == InclusionReason.SALES_MOBILE_NRW.value
    
    def test_include_phone_with_candidate_signal(self):
        """Test phone + candidate signal."""
        result = evaluate_lead_for_csv(
            text="Ich suche einen Job im Vertrieb",
            url="https://example.com",
            score=5,
            has_phone=True,
        )
        
        assert result.decision == LeadDecision.INCLUDE
        assert result.include_in_csv is True
        assert len(result.candidate_signals_found) > 0
    
    def test_include_quality_portal(self):
        """Test quality portal URL."""
        result = evaluate_lead_for_csv(
            text="Stellengesuch",
            url="https://www.kleinanzeigen.de/s-stellengesuche/123",
            score=5,
            has_phone=True,
        )
        
        assert result.decision == LeadDecision.INCLUDE
        assert result.include_in_csv is True
        assert result.reason_code == InclusionReason.QUALITY_PORTAL.value
    
    def test_exclude_job_offer_only(self):
        """Test that job offers without candidate signals are excluded."""
        result = evaluate_lead_for_csv(
            text="Wir suchen Vertriebsmitarbeiter (m/w/d) für unser Team. Ihre Aufgaben:",
            url="https://example.com/jobs",
            score=5,
            has_phone=True,
        )
        
        assert result.decision == LeadDecision.EXCLUDE
        assert result.include_in_csv is False
        assert len(result.job_offer_signals_found) > 0
    
    def test_exclude_aggregator(self):
        """Test that aggregator domains are excluded."""
        result = evaluate_lead_for_csv(
            text="Stellenangebot",
            url="https://www.stepstone.de/jobs/123",
            score=7,
            has_phone=True,
        )
        
        assert result.decision == LeadDecision.EXCLUDE
        assert result.reason_code == ExclusionReason.AGGREGATOR.value
    
    def test_exclude_privacy_page(self):
        """Test that privacy pages are excluded."""
        result = evaluate_lead_for_csv(
            text="Datenschutz",
            url="https://example.com/datenschutz",
            score=5,
            has_phone=True,
        )
        
        assert result.decision == LeadDecision.EXCLUDE
        assert result.reason_code == ExclusionReason.PRIVACY_PAGE.value
    
    def test_exclude_low_score(self):
        """Test that low score leads are excluded."""
        result = evaluate_lead_for_csv(
            text="Ein normaler Text",
            url="https://example.com",
            score=1,
            has_phone=True,
        )
        
        assert result.decision == LeadDecision.EXCLUDE
        assert result.reason_code == ExclusionReason.LOW_SCORE.value
    
    def test_exclude_no_contact(self):
        """Test that leads without contact are excluded."""
        result = evaluate_lead_for_csv(
            text="Vertriebsmitarbeiter",
            url="https://example.com",
            score=5,
            has_phone=False,
            has_email=False,
        )
        
        assert result.decision == LeadDecision.EXCLUDE
        assert result.reason_code == ExclusionReason.NO_CONTACT_INFO.value
    
    def test_candidate_overrides_job_offer(self):
        """Test that strong candidate signals override job offer signals."""
        result = evaluate_lead_for_csv(
            text="Ich suche einen Job. Wir suchen Mitarbeiter.",
            url="https://example.com",
            score=5,
            has_phone=True,
        )
        
        # Should include because of candidate signal
        assert result.include_in_csv is True
        assert len(result.candidate_signals_found) > 0
    
    def test_review_borderline_case(self):
        """Test that borderline cases are marked for review."""
        result = evaluate_lead_for_csv(
            text="Vertriebsmitarbeiter",
            url="https://example.com",
            score=5,
            has_phone=True,
            has_mobile=False,
        )
        
        # Should be included but might be marked for review
        assert result.include_in_csv is True
    
    def test_custom_config(self):
        """Test using custom configuration."""
        custom_config = LeadRulesConfig(
            high_value_threshold=20,  # Very high threshold
            low_score_threshold=5,
        )
        
        result = evaluate_lead_for_csv(
            text="Vertriebsmitarbeiter",
            url="https://example.com",
            score=8,  # Would be high normally, but not with custom config
            has_phone=True,
            config=custom_config,
        )
        
        # Score 8 is now below high threshold of 20
        assert result.decision != LeadDecision.INCLUDE or result.reason_code != InclusionReason.HIGH_VALUE_SCORE.value


class TestBuildCSVRow:
    """Tests for build_csv_row function."""
    
    def test_build_row_basic(self):
        """Test building a basic CSV row."""
        lead_data = {
            "name": "Max Mustermann",
            "telefon": "+4917612345678",
            "email": "max@example.com",
            "quelle": "https://example.com",
            "rolle": "Vertrieb",
        }
        
        from luca_scraper.scoring.lead_rules import LeadDecisionResult
        decision = LeadDecisionResult(score=10)
        
        row = build_csv_row(lead_data, decision)
        
        assert row["name"] == "Max Mustermann"
        assert row["telefon"] == "+4917612345678"
        assert row["email"] == "max@example.com"
        assert row["quelle"] == "https://example.com"
        assert row["score"] == 10
    
    def test_build_row_with_signals(self):
        """Test row includes signal information."""
        lead_data = {"name": "Test", "telefon": "+4917612345678"}
        
        from luca_scraper.scoring.lead_rules import LeadDecisionResult
        decision = LeadDecisionResult(score=10)
        decision.candidate_signals_found = ["ich suche", "arbeitslos"]
        
        row = build_csv_row(lead_data, decision)
        
        assert "ich suche" in row["sales_keywords"]
    
    def test_build_row_alternative_keys(self):
        """Test that alternative key names are handled."""
        lead_data = {
            "phone": "+4917612345678",  # Alternative to 'telefon'
            "url": "https://example.com",  # Alternative to 'quelle'
            "role": "Sales",  # Alternative to 'rolle'
        }
        
        from luca_scraper.scoring.lead_rules import LeadDecisionResult
        decision = LeadDecisionResult(score=5)
        
        row = build_csv_row(lead_data, decision)
        
        assert row["telefon"] == "+4917612345678"
        assert row["quelle"] == "https://example.com"
        assert row["rolle"] == "Sales"


class TestFilterLeadsForCSV:
    """Tests for filter_leads_for_csv function."""
    
    def test_filter_basic(self):
        """Test basic filtering."""
        leads = [
            {"name": "Good Lead", "telefon": "+4917612345678", "score": 10, "text": "Vertrieb"},
            {"name": "Bad Lead", "score": 1, "text": "Impressum"},
        ]
        
        included, excluded, stats = filter_leads_for_csv(leads)
        
        assert stats["total"] == 2
        assert stats["included"] >= 1
        assert stats["excluded"] >= 0
    
    def test_filter_returns_dict_rows(self):
        """Test that filter returns dictionary rows."""
        leads = [
            {"name": "Test", "telefon": "+4917612345678", "score": 10, "text": "Ich suche Job"}
        ]
        
        included, excluded, stats = filter_leads_for_csv(leads)
        
        assert len(included) == 1
        assert isinstance(included[0], dict)
        assert "name" in included[0]
    
    def test_filter_exclusion_reasons(self):
        """Test that exclusion reasons are tracked."""
        leads = [
            {"name": "Bad", "score": 1, "text": "Random"},
            {"name": "Privacy", "score": 5, "quelle": "https://example.com/datenschutz", "telefon": "123"},
        ]
        
        included, excluded, stats = filter_leads_for_csv(leads)
        
        assert "exclusion_reasons" in stats
        assert len(stats["exclusion_reasons"]) > 0


class TestPatternLists:
    """Tests for pattern list constants."""
    
    def test_job_offer_patterns_not_empty(self):
        """Test that job offer patterns list is not empty."""
        assert len(JOB_OFFER_PATTERNS) > 0
    
    def test_candidate_patterns_not_empty(self):
        """Test that candidate patterns list is not empty."""
        assert len(CANDIDATE_PATTERNS) > 0
    
    def test_patterns_lowercase(self):
        """Test that patterns are lowercase."""
        for pattern in JOB_OFFER_PATTERNS:
            assert pattern == pattern.lower()
        for pattern in CANDIDATE_PATTERNS:
            assert pattern == pattern.lower()
    
    def test_common_job_offer_patterns(self):
        """Test common job offer patterns are present."""
        patterns_str = " ".join(JOB_OFFER_PATTERNS)
        assert "wir suchen" in patterns_str
        assert "(m/w/d)" in patterns_str or "(w/m/d)" in patterns_str
    
    def test_common_candidate_patterns(self):
        """Test common candidate patterns are present."""
        patterns_str = " ".join(CANDIDATE_PATTERNS)
        assert "ich suche" in patterns_str
        assert "stellengesuch" in patterns_str


class TestCSVHeaders:
    """Tests for CSV_HEADERS constant."""
    
    def test_required_headers_present(self):
        """Test that required headers are present."""
        required = ["name", "telefon", "email", "quelle", "score"]
        for header in required:
            assert header in CSV_HEADERS
    
    def test_headers_are_strings(self):
        """Test that all headers are strings."""
        for header in CSV_HEADERS:
            assert isinstance(header, str)
    
    def test_no_duplicate_headers(self):
        """Test that there are no duplicate headers."""
        assert len(CSV_HEADERS) == len(set(CSV_HEADERS))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
