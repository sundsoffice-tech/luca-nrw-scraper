"""
Test for DuckDuckGo proxy configuration fixes.

This test verifies that:
1. Environment variables are set correctly for direct connections (USE_TOR=False)
2. Environment variables are set correctly for TOR routing (USE_TOR=True)
3. The function doesn't pass a 'proxies' argument to DDGS
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_proxy_config_logic():
    """
    Test that proxy configuration logic is correctly structured.
    This is a static test that verifies the code structure without actually running DDGS.
    """
    # Read the function to verify it has the correct structure
    script_path = os.path.join(os.path.dirname(__file__), "..", "scriptname.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify that duckduckgo_search_async exists
    assert "async def duckduckgo_search_async" in content, "Function duckduckgo_search_async not found"
    
    # Verify environment variable handling is inside the try block (not before the loop)
    # This ensures environment variables are set on each retry attempt
    ddg_func_start = content.find("async def duckduckgo_search_async")
    ddg_func_end = content.find("\nasync def", ddg_func_start + 1)
    if ddg_func_end == -1:
        ddg_func_end = content.find("\ndef ", ddg_func_start + 1)
    
    ddg_func = content[ddg_func_start:ddg_func_end]
    
    # Verify the structure: environment variables should be set inside the retry loop
    assert 'for attempt in range(1, 4):' in ddg_func, "Retry loop not found"
    assert 'os.environ["no_proxy"] = "*"' in ddg_func, "no_proxy='*' not set"
    assert 'os.environ["NO_PROXY"] = "*"' in ddg_func, "NO_PROXY='*' not set (case-sensitive variant)"
    assert 'os.environ["HTTP_PROXY"] = "socks5://127.0.0.1:9050"' in ddg_func, "TOR HTTP_PROXY not set"
    assert 'os.environ["HTTPS_PROXY"] = "socks5://127.0.0.1:9050"' in ddg_func, "TOR HTTPS_PROXY not set"
    
    # Verify DDGS is initialized without proxies argument
    # Look for DDGS initialization
    ddgs_init_pattern = "with DDGS(timeout=60) as ddgs:"
    assert ddgs_init_pattern in ddg_func, "DDGS not initialized with correct pattern"
    
    # Verify no 'proxies=' argument is passed to DDGS
    assert "DDGS(timeout=60, proxies=" not in ddg_func, "DDGS should not receive proxies argument"
    assert "DDGS(proxies=" not in ddg_func, "DDGS should not receive proxies argument"
    
    print("✓ All proxy configuration checks passed")


def test_recruiter_queries_structure():
    """
    Test that _recruiter_queries has the correct structure with all 6 clusters.
    """
    script_path = os.path.join(os.path.dirname(__file__), "..", "scriptname.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _recruiter_queries function
    func_start = content.find("def _recruiter_queries()")
    assert func_start != -1, "_recruiter_queries function not found"
    
    # Get the function content (approximately)
    func_end = content.find("\n    if selected_industry and", func_start)
    func_content = content[func_start:func_end]
    
    # Verify DOMAIN_EXCLUDES and CONTENT_EXCLUDES are defined
    assert "DOMAIN_EXCLUDES = " in func_content, "DOMAIN_EXCLUDES not defined"
    assert "CONTENT_EXCLUDES = " in func_content, "CONTENT_EXCLUDES not defined"
    
    # Verify all 6 clusters are present
    clusters = [
        "# 1. MESSENGER & DIRECT",
        "# 2. FILE HUNTING",
        "# 3. CLOUD & DEV LEAKS",
        "# 4. MEETING & CALENDAR LINKS",
        "# 5. PRIVATE SITES & IMPRESSUM HACKS",
        "# 6. SOCIAL & PORTALS",
    ]
    
    for cluster in clusters:
        assert cluster in func_content, f"Cluster comment not found: {cluster}"
    
    # Verify specific query patterns
    assert "wa.me/491" in func_content, "WhatsApp query not found"
    assert "t.me/" in func_content, "Telegram query not found"
    assert "filetype:pdf" in func_content, "PDF file hunting not found"
    assert "docs.google.com/spreadsheets" in func_content, "Google Docs query not found"
    assert "trello.com" in func_content, "Trello query not found"
    assert "calendly.com" in func_content, "Calendly query not found"
    assert "zoom.us/j/" in func_content, "Zoom query not found"
    assert "linkedin.com/posts/" in func_content, "LinkedIn query not found"
    assert "kleinanzeigen.de/s-stellengesuche/" in func_content, "Kleinanzeigen query not found"
    
    print("✓ All recruiter query checks passed")


if __name__ == "__main__":
    test_proxy_config_logic()
    test_recruiter_queries_structure()
    print("\n✓✓✓ All tests passed!")
