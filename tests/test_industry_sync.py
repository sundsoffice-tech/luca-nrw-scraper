"""
Test industry synchronization across all scraper components.
Validates that new industries (handelsvertreter, d2d, callcenter) are properly integrated.
"""

import sys
import os
import re

# Read files directly to avoid import dependencies
def test_new_industries_in_model():
    """Test that new industries are in ScraperConfig.INDUSTRY_CHOICES."""
    with open('telis_recruitment/scraper_control/models.py', 'r') as f:
        content = f.read()
        
    # Check for handelsvertreter
    assert "('handelsvertreter', 'Handelsvertreter')" in content, "handelsvertreter missing from INDUSTRY_CHOICES"
    assert "('d2d', 'Door-to-Door')" in content, "d2d missing from INDUSTRY_CHOICES"
    assert "('callcenter', 'Call Center')" in content, "callcenter missing from INDUSTRY_CHOICES"
    
    print("✓ All new industries in ScraperConfig.INDUSTRY_CHOICES")


def test_new_industries_in_cli():
    """Test that new industries are in CLI ALL_INDUSTRIES."""
    with open('luca_scraper/cli.py', 'r') as f:
        content = f.read()
        
    # Find ALL_INDUSTRIES definition
    assert '"handelsvertreter"' in content, "handelsvertreter missing from CLI"
    assert '"d2d"' in content, "d2d missing from CLI"
    assert '"callcenter"' in content, "callcenter missing from CLI"
    
    print("✓ All new industries in CLI ALL_INDUSTRIES")


def test_new_industries_in_manager():
    """Test that new industries have queries in manager.py."""
    with open('luca_scraper/search/manager.py', 'r') as f:
        content = f.read()
        
    # Check for industry query definitions
    assert '"handelsvertreter":' in content, "handelsvertreter missing from INDUSTRY_QUERIES"
    assert '"d2d":' in content, "d2d missing from INDUSTRY_QUERIES"
    assert '"callcenter":' in content, "callcenter missing from INDUSTRY_QUERIES"
    
    # Check SUPPORTED_INDUSTRIES
    assert '"handelsvertreter"' in content, "handelsvertreter missing from SUPPORTED_INDUSTRIES"
    assert '"d2d"' in content, "d2d missing from SUPPORTED_INDUSTRIES"
    assert '"callcenter"' in content, "callcenter missing from SUPPORTED_INDUSTRIES"
    
    print("✓ All new industries in INDUSTRY_QUERIES and SUPPORTED_INDUSTRIES")


def test_views_uses_dynamic_validation():
    """Test that views_scraper.py uses dynamic validation."""
    with open('telis_recruitment/leads/views_scraper.py', 'r') as f:
        content = f.read()
        
    # Should import from scraper_control
    assert "from scraper_control.models import ScraperConfig" in content, "views_scraper should import ScraperConfig"
    
    # Should use dynamic validation
    assert "valid_industries = [c[0] for c in" in content, "views_scraper should use dynamic validation"
    
    # Should NOT have hardcoded list
    assert "['recruiter', 'candidates', 'talent_hunt', 'all']" not in content, "views_scraper has hardcoded validation"
    
    print("✓ views_scraper.py uses dynamic validation from ScraperConfig")


def test_no_duplicate_scraperconfig():
    """Test that duplicate ScraperConfig was removed from leads/models.py."""
    with open('telis_recruitment/leads/models.py', 'r') as f:
        content = f.read()
        
    # Count class definitions
    scraper_config_count = content.count('class ScraperConfig(models.Model):')
    
    # Should have 0 (imported instead) or use import statement
    assert scraper_config_count == 0, f"Found {scraper_config_count} ScraperConfig class definitions in leads/models.py"
    
    # Should have import
    assert "from scraper_control.models import ScraperConfig" in content, "leads/models.py should import ScraperConfig"
    
    print("✓ Duplicate ScraperConfig removed from leads/models.py")


def test_handelsvertreter_query_count():
    """Test that handelsvertreter has a good number of queries."""
    with open('luca_scraper/search/manager.py', 'r') as f:
        content = f.read()
        
    # Find handelsvertreter section
    match = re.search(r'"handelsvertreter":\s*\[(.*?)\],\s*#.*?NEU:', content, re.DOTALL)
    if match:
        queries = re.findall(r"'[^']*'", match.group(1))
        assert len(queries) >= 15, f"handelsvertreter should have at least 15 queries, found {len(queries)}"
        print(f"✓ handelsvertreter has {len(queries)} queries")
    else:
        assert False, "Could not find handelsvertreter queries"


def test_d2d_query_count():
    """Test that d2d has a good number of queries."""
    with open('luca_scraper/search/manager.py', 'r') as f:
        content = f.read()
        
    # Find d2d section
    match = re.search(r'"d2d":\s*\[(.*?)\],\s*#.*?NEU:', content, re.DOTALL)
    if match:
        queries = re.findall(r"'[^']*'", match.group(1))
        assert len(queries) >= 10, f"d2d should have at least 10 queries, found {len(queries)}"
        print(f"✓ d2d has {len(queries)} queries")
    else:
        assert False, "Could not find d2d queries"


def test_callcenter_query_count():
    """Test that callcenter has a good number of queries."""
    with open('luca_scraper/search/manager.py', 'r') as f:
        content = f.read()
        
    # Find callcenter section - it's followed by RECRUITER
    match = re.search(r'"callcenter":\s*\[(.*?)\],\s*#.*?RECRUITER', content, re.DOTALL)
    if match:
        queries = re.findall(r"'[^']*'", match.group(1))
        assert len(queries) >= 10, f"callcenter should have at least 10 queries, found {len(queries)}"
        print(f"✓ callcenter has {len(queries)} queries")
    else:
        assert False, "Could not find callcenter queries"


def test_dashboard_has_hints():
    """Test that dashboard template has hints for new industries."""
    with open('telis_recruitment/templates/scraper_control/dashboard.html', 'r') as f:
        content = f.read()
        
    assert "handelsvertreter" in content.lower(), "dashboard should have handelsvertreter hints"
    assert "d2d" in content.lower(), "dashboard should have d2d hints"
    assert "callcenter" in content.lower(), "dashboard should have callcenter hints"
    
    print("✓ Dashboard template has hints for new industries")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Industry Synchronization")
    print("=" * 60)
    print()
    
    os.chdir('/home/runner/work/luca-nrw-scraper/luca-nrw-scraper')
    
    test_new_industries_in_model()
    test_new_industries_in_cli()
    test_new_industries_in_manager()
    test_views_uses_dynamic_validation()
    test_no_duplicate_scraperconfig()
    test_handelsvertreter_query_count()
    test_d2d_query_count()
    test_callcenter_query_count()
    test_dashboard_has_hints()
    
    print()
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
