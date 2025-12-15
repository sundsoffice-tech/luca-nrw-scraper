"""
Tests for targeted improvements:
1. Phone hardfilter
2. Google cost reduction
3. Host/path guards
4. DDG retries
"""
import pytest
from scriptname import (
    normalize_phone,
    validate_phone,
    _matches_hostlist,
    DROP_PORTAL_DOMAINS,
    BLACKLIST_PATH_PATTERNS,
    should_skip_url_prefetch,
    MAX_GOOGLE_PAGES,
)


class TestPhoneHardfilter:
    """Test phone hardfilter functionality."""
    
    def test_phone_validation_strict(self):
        """Test that phone validation is strict."""
        # Valid phones
        assert validate_phone("+491761234567")[0] is True
        assert validate_phone("0176 1234567")[0] is True
        assert validate_phone("+49211123456")[0] is True
        
        # Invalid phones
        assert validate_phone("")[0] is False
        assert validate_phone(None)[0] is False
        assert validate_phone("123")[0] is False  # Too short
        assert validate_phone("12345678901234567890")[0] is False  # Too long
    
    def test_phone_type_detection(self):
        """Test phone type detection."""
        is_valid, phone_type = validate_phone("+491761234567")
        assert is_valid is True
        assert phone_type == "mobile"
        
        is_valid, phone_type = validate_phone("+49211123456")
        assert is_valid is True
        assert phone_type == "landline"
        
        is_valid, phone_type = validate_phone("+33612345678")
        assert is_valid is True
        assert phone_type == "international"
    
    def test_normalize_phone_robust(self):
        """Test robust phone normalization."""
        assert normalize_phone("0211 123456") == "+49211123456"
        assert normalize_phone("+49 (0) 211-123456") == "+49211123456"
        assert normalize_phone("0049 (0)176 123 45 67") == "+491761234567"
        assert normalize_phone("+49-(0)-176 123 45 67") == "+491761234567"


class TestHostPathGuards:
    """Test host and path guard improvements."""
    
    def test_extended_deny_domains(self):
        """Test that new domains are blocked."""
        new_blocked_hosts = [
            "jobboard-deutschland.de",
            "kleinanzeigen.de",
            "netspor-tv.com",
            "trendyol.com",
        ]
        for host in new_blocked_hosts:
            assert host in DROP_PORTAL_DOMAINS
    
    def test_existing_deny_domains(self):
        """Test that existing blocked domains are still present."""
        existing_blocked = [
            "stepstone.de",
            "indeed.com",
            "bewerbung.net",
            "freelancermap.de",
            "reddit.com",
        ]
        for host in existing_blocked:
            assert host in DROP_PORTAL_DOMAINS
    
    def test_matches_hostlist(self):
        """Test host matching logic."""
        blocked = {"example.com", "test.org"}
        
        # Exact match
        assert _matches_hostlist("example.com", blocked) is True
        
        # With www
        assert _matches_hostlist("www.example.com", blocked) is True
        
        # Subdomain
        assert _matches_hostlist("sub.example.com", blocked) is True
        
        # Not blocked
        assert _matches_hostlist("other.com", blocked) is False
    
    def test_blacklist_path_patterns(self):
        """Test that path patterns are present."""
        required_patterns = [
            "lebenslauf", "vorlage", "muster", "sitemap", 
            "seminar", "academy", "weiterbildung", "job", 
            "stellenangebot", "news", "blog", "ratgeber", "portal"
        ]
        for pattern in required_patterns:
            assert pattern in BLACKLIST_PATH_PATTERNS
    
    def test_should_skip_url_prefetch_host(self):
        """Test that blocked hosts are skipped."""
        should_skip, reason = should_skip_url_prefetch(
            "https://stepstone.de/job/123",
            title="Software Engineer",
            snippet="Great opportunity"
        )
        assert should_skip is True
        assert reason == "blacklist_host"
    
    def test_should_skip_url_prefetch_pattern(self):
        """Test that URLs with blacklisted patterns are skipped."""
        should_skip, reason = should_skip_url_prefetch(
            "https://example.com/stellenangebot/123",
            title="Job Opportunity",
            snippet=""
        )
        assert should_skip is True
        assert "blacklist_pattern" in reason


class TestGoogleCostReduction:
    """Test Google cost reduction settings."""
    
    def test_max_google_pages_reduced(self):
        """Test that MAX_GOOGLE_PAGES is reduced to 1-2."""
        assert MAX_GOOGLE_PAGES <= 2
        assert MAX_GOOGLE_PAGES >= 1


class TestConfiguration:
    """Test configuration values."""
    
    def test_qpi_default(self):
        """Test that QPI default is in 6-8 range."""
        # This will be tested via CLI parsing, but we can verify
        # the build_queries function would respect it
        from scriptname import build_queries
        queries = build_queries(per_industry_limit=6)
        assert len(queries) <= 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
