"""
Tests for Facebook scraping queries in scriptname.py

These tests verify that the correct Facebook queries have been added to the INDUSTRY_QUERIES.
"""
import re


def test_facebook_queries_in_file():
    """Test that Facebook-specific queries are present in scriptname.py"""
    with open("scriptname.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for the presence of the required queries
    expected_queries = [
        'site:facebook.com/people "Vertrieb" AND ("suche Job" OR "neue Herausforderung" OR "offen für Angebote") NRW',
        'site:facebook.com "Sales Manager" AND ("looking for new opportunities" OR "open to work") NRW',
        'site:facebook.com/groups "Vertrieb" AND "Jobsuche" NRW',
    ]
    
    for query in expected_queries:
        assert query in content, f"Query not found in scriptname.py: {query}"
    
    print(f"✓ All {len(expected_queries)} Facebook queries found in scriptname.py")


def test_facebook_queries_in_candidates_section():
    """Test that Facebook queries are in the 'candidates' section"""
    with open("scriptname.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the candidates section
    candidates_match = re.search(r'"candidates":\s*\[(.*?)\],', content, re.DOTALL)
    assert candidates_match, "Could not find 'candidates' section in INDUSTRY_QUERIES"
    
    candidates_section = candidates_match.group(1)
    
    # Check that Facebook queries are in this section
    assert "facebook.com/people" in candidates_section, "Facebook people query not in candidates section"
    assert "Sales Manager" in candidates_section, "Sales Manager query not in candidates section"
    assert "facebook.com/groups" in candidates_section and "Jobsuche" in candidates_section, "Facebook groups Jobsuche query not in candidates section"
    
    print("✓ Facebook queries are correctly placed in the 'candidates' section")


def test_facebook_queries_include_nrw():
    """Test that all new Facebook queries include NRW location"""
    with open("scriptname.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find lines with the new Facebook queries
    new_fb_patterns = [
        'site:facebook.com/people "Vertrieb"',
        'site:facebook.com "Sales Manager"',
        'site:facebook.com/groups "Vertrieb" AND "Jobsuche"',
    ]
    
    for pattern in new_fb_patterns:
        # Find the full line containing this pattern
        lines = [line for line in content.split('\n') if pattern in line]
        assert lines, f"Pattern not found: {pattern}"
        
        for line in lines:
            assert "NRW" in line, f"Line missing NRW: {line.strip()}"
    
    print("✓ All Facebook queries include NRW location filter")


def test_facebook_queries_syntax():
    """Test that Facebook queries use proper Google Dork syntax"""
    with open("scriptname.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for proper site: syntax and AND operators
    facebook_lines = [line for line in content.split('\n') if 'site:facebook.com' in line and ('people' in line or 'Sales Manager' in line or 'Jobsuche' in line)]
    
    for line in facebook_lines:
        # Should have site: prefix
        assert 'site:facebook.com' in line, f"Missing site: prefix in: {line.strip()}"
        
        # Should use AND operator (not just spaces)
        if 'people' in line or 'Sales Manager' in line or 'Jobsuche' in line:
            assert ' AND ' in line, f"Missing AND operator in: {line.strip()}"
    
    print("✓ Facebook queries use proper Google Dork syntax")


if __name__ == "__main__":
    test_facebook_queries_in_file()
    test_facebook_queries_in_candidates_section()
    test_facebook_queries_include_nrw()
    test_facebook_queries_syntax()
    print("\n✅ All Facebook query tests passed!")
