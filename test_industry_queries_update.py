"""
Test for Industry Queries Update
=================================
Validates the new search queries for handelsvertreter, d2d, callcenter, and recruiter.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from luca_scraper.search import build_queries, INDUSTRY_QUERIES


def test_handelsvertreter_queries():
    """Test handelsvertreter queries."""
    print("\n" + "="*60)
    print("Testing Handelsvertreter Queries")
    print("="*60)
    
    queries = INDUSTRY_QUERIES.get("handelsvertreter", [])
    
    # Should have at least 50 queries (requirement)
    assert len(queries) >= 50, f"Expected at least 50 queries, got {len(queries)}"
    print(f"✓ Has {len(queries)} queries (>= 50 required)")
    
    # Check that problematic queries are removed
    combined = " ".join(queries).lower()
    assert 'filetype:xlsx "händlerverzeichnis"' not in combined, "Should not contain xlsx template query"
    assert 'filetype:pdf "preisliste"' not in combined, "Should not contain pdf template query"
    print("✓ Removed problematic filetype queries")
    
    # Check for essential categories
    assert any("kleinanzeigen.de" in q for q in queries), "Should include kleinanzeigen.de queries"
    assert any("xing.com" in q for q in queries), "Should include xing.com queries"
    assert any("linkedin.com" in q for q in queries), "Should include linkedin.com queries"
    assert any("cdh.de" in q for q in queries), "Should include cdh.de queries"
    assert any("facebook.com" in q for q in queries), "Should include facebook.com queries"
    print("✓ Includes all essential platforms (Kleinanzeigen, Xing, LinkedIn, CDH, Facebook)")
    
    # Check for industry-specific queries
    assert any("SHK" in q or "shk" in q.lower() for q in queries), "Should include SHK queries"
    assert any("Elektro" in q or "elektro" in q.lower() for q in queries), "Should include Elektro queries"
    assert any("Maschinenbau" in q for q in queries), "Should include Maschinenbau queries"
    print("✓ Includes industry-specific queries (SHK, Elektro, Maschinenbau)")
    
    # Check for regional queries
    assert any("Düsseldorf" in q for q in queries), "Should include Düsseldorf queries"
    assert any("Köln" in q for q in queries), "Should include Köln queries"
    assert any("NRW" in q for q in queries), "Should include NRW queries"
    print("✓ Includes regional NRW queries")
    
    print(f"\n✅ Handelsvertreter: All checks passed! ({len(queries)} queries)")


def test_d2d_queries():
    """Test D2D queries."""
    print("\n" + "="*60)
    print("Testing D2D Queries")
    print("="*60)
    
    queries = INDUSTRY_QUERIES.get("d2d", [])
    
    # Should have at least 30 queries (15 original + 15 new)
    assert len(queries) >= 30, f"Expected at least 30 queries, got {len(queries)}"
    print(f"✓ Has {len(queries)} queries (>= 30 required)")
    
    # Check for new solar/photovoltaik queries
    combined = " ".join(queries).lower()
    assert "solar" in combined, "Should include solar queries"
    assert "photovoltaik" in combined, "Should include photovoltaik queries"
    print("✓ Includes Solar/Photovoltaik queries (biggest D2D market)")
    
    # Check for new glasfaser queries
    assert "glasfaser" in combined, "Should include glasfaser queries"
    print("✓ Includes Glasfaser queries (new trend)")
    
    # Check for new energie/strom queries
    assert "energie" in combined or "strom" in combined, "Should include energie/strom queries"
    print("✓ Includes Energie/Strom queries")
    
    print(f"\n✅ D2D: All checks passed! ({len(queries)} queries)")


def test_callcenter_queries():
    """Test Callcenter queries."""
    print("\n" + "="*60)
    print("Testing Callcenter Queries")
    print("="*60)
    
    queries = INDUSTRY_QUERIES.get("callcenter", [])
    
    # Should have at least 30 queries (15 original + 15 new)
    assert len(queries) >= 30, f"Expected at least 30 queries, got {len(queries)}"
    print(f"✓ Has {len(queries)} queries (>= 30 required)")
    
    # Check for remote/homeoffice queries
    combined = " ".join(queries).lower()
    assert "remote" in combined or "homeoffice" in combined, "Should include remote/homeoffice queries"
    print("✓ Includes Remote/Homeoffice queries")
    
    # Check for outbound queries
    assert "outbound" in combined and "b2b" in combined, "Should include outbound B2B queries"
    assert "kaltakquise" in combined or "telefonakquise" in combined, "Should include kaltakquise/telefonakquise queries"
    print("✓ Includes Outbound B2B queries")
    
    # Check for inbound queries
    assert "inbound" in combined and ("first level" in combined or "support" in combined), "Should include inbound support queries"
    print("✓ Includes Inbound support queries")
    
    print(f"\n✅ Callcenter: All checks passed! ({len(queries)} queries)")


def test_recruiter_queries():
    """Test Recruiter queries."""
    print("\n" + "="*60)
    print("Testing Recruiter Queries")
    print("="*60)
    
    queries = INDUSTRY_QUERIES.get("recruiter", [])
    
    # Should have at least 30 queries (was only 10 before)
    assert len(queries) >= 30, f"Expected at least 30 queries, got {len(queries)}"
    print(f"✓ Has {len(queries)} queries (>= 30 required, was only 10 before)")
    
    # Check for LinkedIn recruiter queries
    combined = " ".join(queries).lower()
    assert "linkedin.com" in combined and "recruiter" in combined, "Should include LinkedIn recruiter queries"
    print("✓ Includes LinkedIn recruiter queries")
    
    # Check for Xing recruiter queries
    assert "xing.com" in combined and ("recruiter" in combined or "personalberater" in combined), "Should include Xing recruiter queries"
    print("✓ Includes Xing recruiter queries")
    
    # Check for Personaldienstleister queries
    assert "personalvermittlung" in combined or "personalberatung" in combined or "headhunter" in combined, "Should include Personaldienstleister queries"
    print("✓ Includes Personaldienstleister queries")
    
    # Check for specialized recruiters
    assert any("IT Recruiter" in q or "Pharma Recruiter" in q or "Finance Recruiter" in q for q in queries), "Should include specialized recruiter queries"
    print("✓ Includes specialized recruiter queries")
    
    print(f"\n✅ Recruiter: All checks passed! ({len(queries)} queries)")


def test_build_queries_function():
    """Test build_queries function with updated industries."""
    print("\n" + "="*60)
    print("Testing build_queries() Function")
    print("="*60)
    
    # Test each industry
    for industry in ["handelsvertreter", "d2d", "callcenter", "recruiter"]:
        queries = build_queries(industry, 100)
        assert len(queries) > 0, f"Should return queries for {industry}"
        print(f"✓ build_queries('{industry}') returns {len(queries)} queries")
    
    print(f"\n✅ build_queries() function works correctly!")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("INDUSTRY QUERIES UPDATE - VALIDATION TESTS")
    print("="*70)
    
    try:
        test_handelsvertreter_queries()
        test_d2d_queries()
        test_callcenter_queries()
        test_recruiter_queries()
        test_build_queries_function()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nSummary:")
        print(f"  • Handelsvertreter: {len(INDUSTRY_QUERIES['handelsvertreter'])} queries (was 20, now 50+)")
        print(f"  • D2D: {len(INDUSTRY_QUERIES['d2d'])} queries (was 15, now 30+)")
        print(f"  • Callcenter: {len(INDUSTRY_QUERIES['callcenter'])} queries (was 15, now 30+)")
        print(f"  • Recruiter: {len(INDUSTRY_QUERIES['recruiter'])} queries (was 10, now 30+)")
        print("\n")
        
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
