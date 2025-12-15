#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test script to verify targeted improvements (no pytest required).
"""
import sys
sys.path.insert(0, '/home/runner/work/luca-nrw-scraper/luca-nrw-scraper')

from scriptname import (
    normalize_phone,
    validate_phone,
    _matches_hostlist,
    DROP_PORTAL_DOMAINS,
    BLACKLIST_PATH_PATTERNS,
    should_skip_url_prefetch,
    MAX_GOOGLE_PAGES,
    build_queries,
)


def test_phone_validation():
    """Test phone validation is strict."""
    print("Testing phone validation...")
    
    # Valid phones
    assert validate_phone("+491761234567")[0] is True, "Valid mobile should pass"
    assert validate_phone("0176 1234567")[0] is True, "Valid mobile with spaces should pass"
    assert validate_phone("+49211123456")[0] is True, "Valid landline should pass"
    
    # Invalid phones
    assert validate_phone("")[0] is False, "Empty phone should fail"
    assert validate_phone(None)[0] is False, "None phone should fail"
    assert validate_phone("123")[0] is False, "Too short should fail"
    assert validate_phone("12345678901234567890")[0] is False, "Too long should fail"
    
    print("✓ Phone validation tests passed")


def test_phone_types():
    """Test phone type detection."""
    print("Testing phone type detection...")
    
    is_valid, phone_type = validate_phone("+491761234567")
    assert is_valid is True and phone_type == "mobile", "Should detect mobile"
    
    is_valid, phone_type = validate_phone("+49211123456")
    assert is_valid is True and phone_type == "landline", "Should detect landline"
    
    is_valid, phone_type = validate_phone("+33612345678")
    assert is_valid is True and phone_type == "international", "Should detect international"
    
    print("✓ Phone type detection tests passed")


def test_phone_normalization():
    """Test robust phone normalization."""
    print("Testing phone normalization...")
    
    assert normalize_phone("0211 123456") == "+49211123456"
    assert normalize_phone("+49 (0) 211-123456") == "+49211123456"
    assert normalize_phone("0049 (0)176 123 45 67") == "+491761234567"
    
    print("✓ Phone normalization tests passed")


def test_extended_deny_domains():
    """Test that new domains are blocked."""
    print("Testing extended deny domains...")
    
    new_blocked_hosts = [
        "jobboard-deutschland.de",
        "kleinanzeigen.de",
        "netspor-tv.com",
        "trendyol.com",
    ]
    for host in new_blocked_hosts:
        assert host in DROP_PORTAL_DOMAINS, f"{host} should be in DROP_PORTAL_DOMAINS"
    
    print("✓ Extended deny domains tests passed")


def test_existing_deny_domains():
    """Test that existing blocked domains are still present."""
    print("Testing existing deny domains...")
    
    existing_blocked = [
        "stepstone.de",
        "indeed.com",
        "bewerbung.net",
        "freelancermap.de",
        "reddit.com",
    ]
    for host in existing_blocked:
        assert host in DROP_PORTAL_DOMAINS, f"{host} should be in DROP_PORTAL_DOMAINS"
    
    print("✓ Existing deny domains tests passed")


def test_hostlist_matching():
    """Test host matching logic."""
    print("Testing hostlist matching...")
    
    blocked = {"example.com", "test.org"}
    
    assert _matches_hostlist("example.com", blocked) is True, "Exact match should work"
    assert _matches_hostlist("www.example.com", blocked) is True, "www match should work"
    assert _matches_hostlist("sub.example.com", blocked) is True, "Subdomain match should work"
    assert _matches_hostlist("other.com", blocked) is False, "Non-blocked should not match"
    
    print("✓ Hostlist matching tests passed")


def test_blacklist_patterns():
    """Test that path patterns are present."""
    print("Testing blacklist patterns...")
    
    required_patterns = [
        "lebenslauf", "vorlage", "muster", "sitemap", 
        "seminar", "academy", "weiterbildung", "job", 
        "stellenangebot", "news", "blog", "ratgeber", "portal"
    ]
    for pattern in required_patterns:
        assert pattern in BLACKLIST_PATH_PATTERNS, f"{pattern} should be in BLACKLIST_PATH_PATTERNS"
    
    print("✓ Blacklist patterns tests passed")


def test_skip_url_prefetch():
    """Test URL skipping logic."""
    print("Testing skip URL prefetch...")
    
    # Blocked host
    should_skip, reason = should_skip_url_prefetch(
        "https://stepstone.de/job/123",
        title="Software Engineer",
        snippet="Great opportunity"
    )
    assert should_skip is True, "Blocked host should be skipped"
    assert reason == "blacklist_host", "Reason should be blacklist_host"
    
    # Blocked pattern
    should_skip, reason = should_skip_url_prefetch(
        "https://example.com/stellenangebot/123",
        title="Job Opportunity",
        snippet=""
    )
    assert should_skip is True, "Blocked pattern should be skipped"
    assert "blacklist_pattern" in reason, "Reason should mention blacklist_pattern"
    
    print("✓ Skip URL prefetch tests passed")


def test_max_google_pages():
    """Test that MAX_GOOGLE_PAGES is reduced."""
    print("Testing MAX_GOOGLE_PAGES...")
    
    assert MAX_GOOGLE_PAGES <= 2, "MAX_GOOGLE_PAGES should be <= 2"
    assert MAX_GOOGLE_PAGES >= 1, "MAX_GOOGLE_PAGES should be >= 1"
    
    print(f"✓ MAX_GOOGLE_PAGES is {MAX_GOOGLE_PAGES} (within 1-2 range)")


def test_qpi():
    """Test QPI related functionality."""
    print("Testing QPI...")
    
    queries = build_queries(per_industry_limit=6)
    assert len(queries) <= 6, f"Queries should be capped at 6, got {len(queries)}"
    
    print(f"✓ QPI test passed (got {len(queries)} queries)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running targeted improvements tests...")
    print("=" * 60)
    
    tests = [
        test_phone_validation,
        test_phone_types,
        test_phone_normalization,
        test_extended_deny_domains,
        test_existing_deny_domains,
        test_hostlist_matching,
        test_blacklist_patterns,
        test_skip_url_prefetch,
        test_max_google_pages,
        test_qpi,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("=" * 60)
    if failed == 0:
        print(f"✓ All {len(tests)} tests passed!")
        return 0
    else:
        print(f"✗ {failed}/{len(tests)} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
