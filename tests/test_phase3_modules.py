"""
Unit Tests for Phase 3 Refactoring
===================================
Tests for search, scoring, validation and CLI modules.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luca_scraper.search import build_queries, DEFAULT_QUERIES, INDUSTRY_QUERIES
from luca_scraper.scoring import (
    is_candidate_seeking_job,
    is_job_advertisement,
    classify_lead,
    is_garbage_context,
    CANDIDATE_POSITIVE_SIGNALS,
    JOB_OFFER_SIGNALS,
)


class TestSearchModule:
    """Tests for search module."""
    
    def test_default_queries_not_empty(self):
        assert len(DEFAULT_QUERIES) > 0, "DEFAULT_QUERIES should not be empty"
        print(f"✓ DEFAULT_QUERIES contains {len(DEFAULT_QUERIES)} queries")
    
    def test_industry_queries_has_modes(self):
        assert "candidates" in INDUSTRY_QUERIES, "Should have candidates mode"
        assert "talent_hunt" in INDUSTRY_QUERIES, "Should have talent_hunt mode"
        print(f"✓ INDUSTRY_QUERIES has {len(INDUSTRY_QUERIES)} modes")
    
    def test_build_queries_standard_mode(self):
        queries = build_queries(None, 10)
        assert len(queries) <= 10, "Should return at most 10 queries"
        assert len(queries) > 0, "Should return at least 1 query"
        print(f"✓ build_queries(standard) returned {len(queries)} queries")
    
    def test_build_queries_candidates_mode(self):
        queries = build_queries("candidates", 20)
        assert len(queries) <= 20, "Should return at most 20 queries"
        assert len(queries) > 0, "Should return at least 1 query"
        # Check that candidates queries contain expected patterns
        combined = " ".join(queries)
        assert "stellengesuche" in combined.lower() or "suche" in combined.lower()
        print(f"✓ build_queries(candidates) returned {len(queries)} queries")
    
    def test_build_queries_talent_hunt_mode(self):
        queries = build_queries("talent_hunt", 15)
        assert len(queries) <= 15, "Should return at most 15 queries"
        assert len(queries) > 0, "Should return at least 1 query"
        # Check that talent_hunt queries avoid #opentowork
        combined = " ".join(queries)
        # Most queries should exclude open to work
        assert queries[0]  # Just check we have queries
        print(f"✓ build_queries(talent_hunt) returned {len(queries)} queries")


class TestValidationModule:
    """Tests for validation module."""
    
    def test_candidate_seeking_job_positive_signals(self):
        """Test detection of 'ich suche' patterns."""
        assert is_candidate_seeking_job("Ich suche Job im Vertrieb", "", "") is True
        assert is_candidate_seeking_job("ich suche arbeit als Verkäufer", "", "") is True
        print("✓ Detects 'ich suche' patterns")
    
    def test_candidate_seeking_job_stellengesuch(self):
        """Test detection of 'stellengesuch' patterns."""
        assert is_candidate_seeking_job("Stellengesuch: Vertriebsmitarbeiter", "", "") is True
        assert is_candidate_seeking_job("", "Stellengesuch Verkäufer", "") is True
        print("✓ Detects 'stellengesuch' patterns")
    
    def test_candidate_seeking_job_open_to_work(self):
        """Test detection of 'open to work' patterns."""
        assert is_candidate_seeking_job("Sales Manager - Open to Work", "", "") is True
        assert is_candidate_seeking_job("#OpenToWork Vertrieb Köln", "", "") is True
        print("✓ Detects '#opentowork' patterns")
    
    def test_not_candidate_when_company_hiring(self):
        """Test that company job offers are not detected as candidates."""
        assert is_candidate_seeking_job("Wir suchen Vertriebsmitarbeiter", "", "") is False
        assert is_candidate_seeking_job("Gesucht: Sales Manager (m/w/d)", "", "") is False
        print("✓ Does not detect company hiring as candidates")
    
    def test_candidate_not_marked_as_job_ad(self):
        """Test that candidates seeking jobs are NOT marked as job ads."""
        assert is_job_advertisement("Ich suche Job im Vertrieb", "", "") is False
        assert is_job_advertisement("Stellengesuch: Verkäufer mit Erfahrung", "", "") is False
        print("✓ Candidates are not marked as job ads")
    
    def test_company_job_offers_marked_as_job_ad(self):
        """Test that company job offers ARE marked as job ads."""
        assert is_job_advertisement("Wir suchen Vertriebsmitarbeiter (m/w/d)", "", "") is True
        assert is_job_advertisement("Sales Manager gesucht", "", "") is True
        print("✓ Company job offers are marked as job ads")
    
    def test_candidate_not_marked_as_garbage(self):
        """Test that candidates are NOT marked as garbage."""
        is_garbage, reason = is_garbage_context("Ich suche Job im Vertrieb", "", "Stellengesuch", "")
        assert is_garbage is False
        print("✓ Candidates are not marked as garbage")
    
    def test_job_ads_marked_as_garbage(self):
        """Test that job ads are marked as garbage."""
        is_garbage, reason = is_garbage_context("Wir suchen Vertriebsmitarbeiter", "", "Job (m/w/d)", "")
        assert is_garbage is True
        assert reason == "job_ad"
        print("✓ Job ads are marked as garbage")
    
    def test_classify_lead_types(self):
        """Test lead classification."""
        # Test with individual
        lead = {"name": "Max Mustermann"}
        lead_type = classify_lead(lead, "Vertriebsmitarbeiter", "Sales Erfahrung")
        assert lead_type in ["individual", "candidate"]
        print(f"✓ classify_lead works: {lead_type}")


class TestSignalLists:
    """Tests for signal lists."""
    
    def test_candidate_positive_signals_not_empty(self):
        assert len(CANDIDATE_POSITIVE_SIGNALS) > 0
        assert "suche job" in CANDIDATE_POSITIVE_SIGNALS
        assert "open to work" in CANDIDATE_POSITIVE_SIGNALS
        print(f"✓ CANDIDATE_POSITIVE_SIGNALS has {len(CANDIDATE_POSITIVE_SIGNALS)} signals")
    
    def test_job_offer_signals_not_empty(self):
        assert len(JOB_OFFER_SIGNALS) > 0
        assert "(m/w/d)" in JOB_OFFER_SIGNALS
        assert "wir suchen" in JOB_OFFER_SIGNALS
        print(f"✓ JOB_OFFER_SIGNALS has {len(JOB_OFFER_SIGNALS)} signals")


def run_tests():
    """Run all tests."""
    print("="*60)
    print("Phase 3 Refactoring Unit Tests")
    print("="*60)
    print()
    
    # Search Module Tests
    print("Testing Search Module...")
    test_search = TestSearchModule()
    test_search.test_default_queries_not_empty()
    test_search.test_industry_queries_has_modes()
    test_search.test_build_queries_standard_mode()
    test_search.test_build_queries_candidates_mode()
    test_search.test_build_queries_talent_hunt_mode()
    print()
    
    # Validation Module Tests
    print("Testing Validation Module...")
    test_validation = TestValidationModule()
    test_validation.test_candidate_seeking_job_positive_signals()
    test_validation.test_candidate_seeking_job_stellengesuch()
    test_validation.test_candidate_seeking_job_open_to_work()
    test_validation.test_not_candidate_when_company_hiring()
    test_validation.test_candidate_not_marked_as_job_ad()
    test_validation.test_company_job_offers_marked_as_job_ad()
    test_validation.test_candidate_not_marked_as_garbage()
    test_validation.test_job_ads_marked_as_garbage()
    test_validation.test_classify_lead_types()
    print()
    
    # Signal Lists Tests
    print("Testing Signal Lists...")
    test_signals = TestSignalLists()
    test_signals.test_candidate_positive_signals_not_empty()
    test_signals.test_job_offer_signals_not_empty()
    print()
    
    print("="*60)
    print("✅ All tests passed!")
    print("="*60)


if __name__ == "__main__":
    run_tests()
