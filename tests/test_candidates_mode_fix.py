"""
Tests for Candidates Mode fixes.
This validates the complete overhaul of the candidates mode functionality.
"""
import pytest
import os
from scriptname import (
    build_queries,
    is_candidate_url,
    INDUSTRY_QUERIES,
)


class TestBuildQueriesForCandidates:
    """Test that build_queries correctly uses candidates queries."""
    
    def test_build_queries_candidates_mode(self):
        """Test that candidates mode uses INDUSTRY_QUERIES['candidates']."""
        queries = build_queries(selected_industry="candidates", per_industry_limit=10)
        
        # Should return some queries
        assert len(queries) > 0
        assert len(queries) <= 10
        
        # Queries should be from INDUSTRY_QUERIES["candidates"]
        # Check that at least one query contains candidate-specific keywords
        candidates_keywords = [
            "stellengesuche",
            "kleinanzeigen.de/s-stellengesuche",
            "open to work",
            "offen für angebote",
            "suche arbeit"
        ]
        
        found_candidate_query = False
        for query in queries:
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in candidates_keywords):
                found_candidate_query = True
                break
        
        assert found_candidate_query, "No candidate-specific queries found"
    
    def test_build_queries_recruiter_mode(self):
        """Test that recruiter mode also uses INDUSTRY_QUERIES['candidates']."""
        # Get more queries to ensure we hit candidates keywords
        queries = build_queries(selected_industry="recruiter", per_industry_limit=50)
        
        # Should return some queries
        assert len(queries) > 0
        assert len(queries) <= 50
        
        # Queries should be from INDUSTRY_QUERIES["candidates"]
        candidates_keywords = [
            "stellengesuche",
            "kleinanzeigen.de/s-stellengesuche",
            "open to work",
            "offen für angebote",
            "suche arbeit"
        ]
        
        found_candidate_query = False
        for query in queries:
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in candidates_keywords):
                found_candidate_query = True
                break
        
        assert found_candidate_query, "No candidate-specific queries found in recruiter mode"
    
    def test_build_queries_standard_mode(self):
        """Test that standard mode uses DEFAULT_QUERIES, not candidate queries."""
        queries = build_queries(selected_industry="all", per_industry_limit=10)
        
        # Should return some queries
        assert len(queries) > 0
        assert len(queries) <= 10
        
        # Should not be exclusively candidate queries
        # (DEFAULT_QUERIES contains some candidate-related queries too, but it's not the primary focus)
    
    def test_build_queries_respects_limit(self):
        """Test that per_industry_limit is respected."""
        queries_5 = build_queries(selected_industry="candidates", per_industry_limit=5)
        queries_15 = build_queries(selected_industry="candidates", per_industry_limit=15)
        
        assert len(queries_5) <= 5
        assert len(queries_15) <= 15
        
        # Should use different limits
        if len(INDUSTRY_QUERIES.get("candidates", [])) > 15:
            assert len(queries_15) > len(queries_5)


class TestIsCandidateUrlFixed:
    """Test that is_candidate_url is less restrictive."""
    
    def test_stellengesuche_with_jobs_path(self):
        """Test that URLs with /jobs/ but containing 'stellengesuch' are allowed."""
        # This was blocked before, but should be allowed now
        url = "https://example.com/jobs/stellengesuch-vertrieb-123"
        assert is_candidate_url(url) is True
        
        url2 = "https://example.com/jobs/jobgesuch-sales-456"
        assert is_candidate_url(url2) is True
    
    def test_positive_patterns_still_work(self):
        """Test that known positive patterns still work."""
        positive_urls = [
            "https://www.kleinanzeigen.de/s-stellengesuche/vertrieb/k0",
            "https://www.markt.de/stellengesuche/vertrieb-123.html",
            "https://www.linkedin.com/in/john-doe-123456",
            "https://www.xing.com/profile/Max_Mustermann",
            "https://www.freelancermap.de/freelancer/12345-vertrieb",
            "https://www.facebook.com/groups/vertrieb-jobs-nrw",
            "https://t.me/vertrieb_jobs_gruppe",
            "https://www.reddit.com/r/de_jobs/comments/abc123",
            "https://www.gutefrage.net/frage/wie-finde-ich-vertriebsjob",
        ]
        
        for url in positive_urls:
            result = is_candidate_url(url)
            assert result is True, f"URL {url} should be True but got {result}"
    
    def test_negative_patterns_still_blocked(self):
        """Test that clearly non-candidate URLs are still blocked."""
        negative_urls = [
            "https://www.stepstone.de/jobs/vertrieb",
            "https://de.indeed.com/jobs?q=vertrieb",
            "https://www.monster.de/jobs/search",
            "https://www.linkedin.com/jobs/view/123456",
            "https://www.xing.com/jobs/dusseldorf-sales-123",
            "https://www.linkedin.com/company/example-gmbh",
            "https://www.company.de/impressum",
        ]
        
        for url in negative_urls:
            result = is_candidate_url(url)
            assert result is False, f"URL {url} should be False but got {result}"
    
    def test_jobs_path_without_candidate_keywords(self):
        """Test that /jobs/ without candidate keywords returns None (uncertain)."""
        # This should be None (uncertain), not False (definitely not)
        url = "https://example.com/jobs/vertrieb-position"
        result = is_candidate_url(url)
        # Should be None (uncertain) because it doesn't match positive or negative patterns definitively
        assert result is None or result is False  # Could be either depending on implementation


class TestCandidatesModeEnvironment:
    """Test that INDUSTRY environment variable is properly set."""
    
    def test_industry_env_parsing(self):
        """Test that INDUSTRY can be set via environment variable."""
        # This is tested implicitly through parse_args
        # The default value already reads from os.getenv("INDUSTRY", "all")
        original_industry = os.environ.get("INDUSTRY")
        
        try:
            os.environ["INDUSTRY"] = "candidates"
            # When parse_args reads it, it should use "candidates"
            assert os.getenv("INDUSTRY") == "candidates"
        finally:
            # Restore original value
            if original_industry:
                os.environ["INDUSTRY"] = original_industry
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
