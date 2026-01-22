# -*- coding: utf-8 -*-
"""
Tests for Sales Context Detection Module
========================================

Tests for the sales context detection and lead scoring.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luca_scraper.scoring.sales_context import (
    score_lead,
    is_sales_context,
    is_job_seeker,
    is_nrw_region,
    LeadScore,
    ScoringConfig,
    DEFAULT_SCORING_CONFIG,
    SALES_KEYWORDS_PRIMARY,
    JOB_SEEKING_SIGNALS_STRONG,
    NRW_INDICATORS,
)


class TestScoreLead:
    """Tests for score_lead function."""
    
    def test_high_value_lead(self):
        """Test scoring a high-value lead."""
        text = """
        Vertriebsmitarbeiter sucht neue Herausforderung in Köln.
        Erfahrung im Außendienst, Solar-Branche.
        Ab sofort verfügbar!
        """
        result = score_lead(
            text=text,
            has_phone=True,
            has_mobile=True,
            has_email=True,
        )
        
        assert result.classification == "HIGH"
        assert result.total_score >= 8
        assert result.is_high_priority is True
        assert "vertrieb" in result.sales_keywords_found
    
    def test_medium_value_lead(self):
        """Test scoring a medium-value lead."""
        text = "Sales Manager mit Erfahrung im Vertrieb"
        result = score_lead(
            text=text,
            has_phone=True,
            has_mobile=False,
        )
        
        assert result.classification in ["HIGH", "MEDIUM"]
        assert result.total_score >= 4
    
    def test_low_value_lead(self):
        """Test scoring a low-value lead."""
        text = "Ein einfacher Text ohne relevante Signale."
        result = score_lead(
            text=text,
            has_phone=False,
            has_email=False,
        )
        
        assert result.classification == "LOW"
        assert result.total_score < 4
    
    def test_sales_keywords_scoring(self):
        """Test that sales keywords increase score."""
        text_no_sales = "Ein normaler Text."
        text_with_sales = "Vertrieb Außendienst Sales"
        
        result_no = score_lead(text_no_sales)
        result_with = score_lead(text_with_sales)
        
        assert result_with.sales_keywords_score > result_no.sales_keywords_score
        assert result_with.total_score > result_no.total_score
    
    def test_job_seeker_signals_scoring(self):
        """Test that job-seeking signals increase score."""
        text_no_signal = "Ein normaler Text."
        text_with_signal = "Ich suche einen Job, bin arbeitslos und ab sofort verfügbar."
        
        result_no = score_lead(text_no_signal)
        result_with = score_lead(text_with_signal)
        
        assert result_with.job_signals_score > result_no.job_signals_score
        assert len(result_with.job_signals_found) > 0
    
    def test_phone_scoring(self):
        """Test that phone presence increases score."""
        text = "Ein Text"
        
        result_no_phone = score_lead(text, has_phone=False)
        result_with_phone = score_lead(text, has_phone=True)
        result_with_mobile = score_lead(text, has_phone=True, has_mobile=True)
        
        assert result_with_phone.contact_score > result_no_phone.contact_score
        assert result_with_mobile.contact_score > result_with_phone.contact_score
    
    def test_whatsapp_scoring(self):
        """Test that WhatsApp increases score."""
        text = "Ein Text"
        
        result_no_wa = score_lead(text, has_phone=True)
        result_with_wa = score_lead(text, has_phone=True, has_whatsapp=True)
        
        assert result_with_wa.contact_score > result_no_wa.contact_score
    
    def test_nrw_region_scoring(self):
        """Test that NRW region increases score."""
        text_no_nrw = "Vertriebsmitarbeiter in Hamburg"
        text_with_nrw = "Vertriebsmitarbeiter in Köln NRW"
        
        result_no = score_lead(text_no_nrw)
        result_with = score_lead(text_with_nrw)
        
        assert result_with.location_score > result_no.location_score
    
    def test_custom_config(self):
        """Test using custom scoring configuration."""
        custom_config = ScoringConfig(
            sales_keyword_primary=5,  # Higher weight for sales keywords
            high_value_threshold=20,   # Higher threshold
        )
        
        text = "Vertriebsmitarbeiter"
        result = score_lead(text, config=custom_config)
        
        # With higher threshold, should be lower classification
        assert result.classification in ["MEDIUM", "LOW"]
    
    def test_score_breakdown(self):
        """Test that score breakdown is accurate."""
        text = "Vertrieb in Düsseldorf"
        result = score_lead(text, has_phone=True, has_email=True)
        
        # Total should equal sum of components
        expected_total = (
            result.sales_keywords_score +
            result.industry_score +
            result.job_signals_score +
            result.contact_score +
            result.location_score
        )
        assert result.total_score == expected_total


class TestIsSalesContext:
    """Tests for is_sales_context function."""
    
    def test_sales_context_detected(self):
        """Test detection of sales context."""
        is_sales, keywords = is_sales_context("Vertriebsmitarbeiter im Außendienst")
        assert is_sales is True
        assert len(keywords) > 0
        assert "vertrieb" in keywords or "außendienst" in keywords
    
    def test_no_sales_context(self):
        """Test when no sales context."""
        is_sales, keywords = is_sales_context("Ein ganz normaler Text")
        assert is_sales is False
        assert len(keywords) == 0
    
    def test_english_sales_keywords(self):
        """Test English sales keywords."""
        is_sales, keywords = is_sales_context("Sales Manager Account Executive")
        assert is_sales is True
        assert "sales" in keywords


class TestIsJobSeeker:
    """Tests for is_job_seeker function."""
    
    def test_job_seeker_detected(self):
        """Test detection of job seeker."""
        is_seeker, signals = is_job_seeker("Ich suche einen neuen Job und bin auf jobsuche")
        assert is_seeker is True
        assert len(signals) > 0
    
    def test_no_job_seeker(self):
        """Test when not a job seeker."""
        is_seeker, signals = is_job_seeker("Wir suchen Mitarbeiter")
        assert is_seeker is False
    
    def test_strong_signals(self):
        """Test strong job-seeking signals."""
        is_seeker, signals = is_job_seeker("arbeitslos, ab sofort verfügbar")
        assert is_seeker is True
        assert len(signals) >= 2
    
    def test_english_signals(self):
        """Test English job-seeking signals."""
        is_seeker, signals = is_job_seeker("Open to work #opentowork")
        assert is_seeker is True


class TestIsNrwRegion:
    """Tests for is_nrw_region function."""
    
    def test_nrw_detected(self):
        """Test NRW detection."""
        is_nrw, indicators = is_nrw_region("Wohnhaft in NRW")
        assert is_nrw is True
        assert "nrw" in indicators
    
    def test_nrw_cities_detected(self):
        """Test NRW city detection."""
        cities = ["Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg"]
        for city in cities:
            is_nrw, indicators = is_nrw_region(f"Arbeitsort: {city}")
            assert is_nrw is True, f"Failed for city: {city}"
    
    def test_no_nrw(self):
        """Test when not NRW."""
        is_nrw, indicators = is_nrw_region("Wohnhaft in Hamburg")
        assert is_nrw is False
    
    def test_ruhrgebiet_detected(self):
        """Test Ruhrgebiet detection."""
        is_nrw, indicators = is_nrw_region("Im Ruhrgebiet tätig")
        assert is_nrw is True


class TestLeadScoreDataclass:
    """Tests for LeadScore dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        score = LeadScore()
        assert score.total_score == 0
        assert score.classification == "LOW"
        assert score.is_high_priority is False
    
    def test_reasons_list(self):
        """Test that reasons list is populated."""
        text = "Vertrieb in Köln mit Telefonnummer"
        result = score_lead(text, has_phone=True)
        assert len(result.reasons) > 0


class TestKeywordLists:
    """Tests for keyword list constants."""
    
    def test_sales_keywords_not_empty(self):
        """Test that sales keywords list is not empty."""
        assert len(SALES_KEYWORDS_PRIMARY) > 0
    
    def test_job_signals_not_empty(self):
        """Test that job signals list is not empty."""
        assert len(JOB_SEEKING_SIGNALS_STRONG) > 0
    
    def test_nrw_indicators_not_empty(self):
        """Test that NRW indicators list is not empty."""
        assert len(NRW_INDICATORS) > 0
    
    def test_keywords_lowercase(self):
        """Test that all keywords are lowercase (for case-insensitive matching)."""
        for kw in SALES_KEYWORDS_PRIMARY:
            assert kw == kw.lower(), f"Keyword not lowercase: {kw}"
        for sig in JOB_SEEKING_SIGNALS_STRONG:
            assert sig == sig.lower(), f"Signal not lowercase: {sig}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
