"""
Tests for pre-fetch URL filtering and blacklist checks.
"""

import pytest
import scriptname


class TestPrefetchFiltering:
    """Test URL filtering before fetch."""
    
    def test_blacklist_host_skip(self):
        """Test that blacklisted hosts are skipped."""
        # Portal domains should be skipped
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://stepstone.de/job/12345",
            "Software Developer",
            ""
        )
        assert skip is True
        assert reason == "blacklist_host"
        
        # Indeed
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://indeed.com/viewjob?jk=12345",
            "Sales Manager",
            ""
        )
        assert skip is True
        assert reason == "blacklist_host"
        
        # New additions: qonto, accountable, sevdesk
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://qonto.com/de/pricing",
            "Pricing",
            ""
        )
        assert skip is True
        assert reason == "blacklist_host"
    
    def test_path_pattern_skip(self):
        """Test that blacklist path patterns are skipped."""
        # Job/stellenangebot in path
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://example.com/stellenangebot/vertrieb",
            "Stellenangebot Vertrieb",
            ""
        )
        assert skip is True
        # Can be blocked as either job_posting or blacklist_pattern
        assert "blacklist_pattern" in reason or reason == "job_posting"
        
        # Blog in path
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://example.com/blog/sales-tips",
            "Blog: Sales Tips",
            ""
        )
        assert skip is True
        assert "blacklist_pattern" in reason
        
        # Lebenslauf vorlage (template)
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://example.com/lebenslauf-muster",
            "Lebenslauf Vorlage",
            ""
        )
        assert skip is True
        assert "blacklist_pattern" in reason
    
    def test_valid_url_not_skipped(self):
        """Test that valid URLs are not skipped."""
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://example-company.de/team/vertrieb",
            "Unser Vertriebsteam",
            ""
        )
        assert skip is False
        assert reason == ""
        
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://kleinanzeigen.de/s-stellengesuch/vertrieb/c1",
            "Stellengesuch Vertrieb",
            ""
        )
        # kleinanzeigen IS in blacklist (DROP_PORTAL_DOMAINS)
        assert skip is True
        assert reason == "blacklist_host"
    
    def test_title_pattern_skip(self):
        """Test that patterns in title trigger skip."""
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://example.com/page",
            "Weiterbildung Sales Academy",  # Academy in title
            ""
        )
        assert skip is True
        assert "blacklist_pattern" in reason
    
    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive."""
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://example.com/BLOG/article",
            "BLOG Article",
            ""
        )
        assert skip is True
        
        skip, reason = scriptname.should_skip_url_prefetch(
            "https://example.com/Job-Portal",
            "Job Portal",
            ""
        )
        assert skip is True
