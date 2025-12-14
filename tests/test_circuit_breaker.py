"""
Test for Circuit Breaker and 429 Fallback improvements.

This test verifies that:
1. Circuit breaker penalties are reduced for API hosts
2. Google CSE can be disabled via ENABLE_GOOGLE_CSE
3. Fallbacks activate immediately when Google returns 429
4. Default environment variable values are conservative
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_circuit_breaker_config():
    """
    Verify circuit breaker configuration has been updated with shorter penalties.
    """
    script_path = os.path.join(os.path.dirname(__file__), "..", "scriptname.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify CB_BASE_PENALTY default is reduced from 90 to 30
    assert 'CB_BASE_PENALTY = int(os.getenv("CB_BASE_PENALTY", "30"))' in content, \
        "CB_BASE_PENALTY should default to 30 seconds"
    
    # Verify CB_API_PENALTY is defined
    assert 'CB_API_PENALTY = int(os.getenv("CB_API_PENALTY"' in content, \
        "CB_API_PENALTY should be defined for API hosts"
    
    # Verify _penalize_host uses shorter penalty for API hosts
    assert 'is_api_host = "googleapis.com" in host or "api." in host' in content, \
        "_penalize_host should detect API hosts"
    
    assert 'base_penalty = CB_API_PENALTY if is_api_host else CB_BASE_PENALTY' in content, \
        "_penalize_host should use CB_API_PENALTY for API hosts"
    
    print("✓ Circuit breaker configuration checks passed")


def test_google_cse_disable_flag():
    """
    Verify ENABLE_GOOGLE_CSE flag exists and is used.
    """
    script_path = os.path.join(os.path.dirname(__file__), "..", "scriptname.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify ENABLE_GOOGLE_CSE is defined
    assert 'ENABLE_GOOGLE_CSE = (os.getenv("ENABLE_GOOGLE_CSE"' in content, \
        "ENABLE_GOOGLE_CSE should be defined"
    
    # Verify google_cse_search_async checks ENABLE_GOOGLE_CSE
    google_func_start = content.find("async def google_cse_search_async")
    google_func_end = content.find("\nasync def", google_func_start + 1)
    if google_func_end == -1:
        google_func_end = content.find("\ndef ", google_func_start + 1)
    
    google_func = content[google_func_start:google_func_end]
    
    assert "if not ENABLE_GOOGLE_CSE:" in google_func, \
        "google_cse_search_async should check ENABLE_GOOGLE_CSE flag"
    
    print("✓ Google CSE disable flag checks passed")


def test_conservative_defaults():
    """
    Verify that default values have been made more conservative.
    """
    script_path = os.path.join(os.path.dirname(__file__), "..", "scriptname.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # MAX_GOOGLE_PAGES reduced from 12 to 4
    assert 'MAX_GOOGLE_PAGES = int(os.getenv("MAX_GOOGLE_PAGES","4"))' in content, \
        "MAX_GOOGLE_PAGES should default to 4"
    
    # SLEEP_BETWEEN_QUERIES increased from 1.6 to 2.5
    assert 'SLEEP_BETWEEN_QUERIES = float(os.getenv("SLEEP_BETWEEN_QUERIES", "2.5"))' in content, \
        "SLEEP_BETWEEN_QUERIES should default to 2.5"
    
    # ASYNC_LIMIT reduced from 50 to 35
    assert 'ASYNC_LIMIT = int(os.getenv("ASYNC_LIMIT", "35"))' in content, \
        "ASYNC_LIMIT should default to 35"
    
    # Verify google_cse_search_async uses the global constant
    google_func_start = content.find("async def google_cse_search_async")
    google_func_end = content.find("\nasync def", google_func_start + 1)
    if google_func_end == -1:
        google_func_end = content.find("\ndef ", google_func_start + 1)
    
    google_func = content[google_func_start:google_func_end]
    assert 'page_cap = MAX_GOOGLE_PAGES' in google_func, \
        "google_cse_search_async should use global MAX_GOOGLE_PAGES constant"
    
    print("✓ Conservative defaults checks passed")


def test_immediate_fallback_on_429():
    """
    Verify that fallbacks activate immediately when Google returns 429.
    """
    script_path = os.path.join(os.path.dirname(__file__), "..", "scriptname.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find run_scrape_once_async function
    run_scrape_start = content.find("async def run_scrape_once_async")
    assert run_scrape_start != -1, "run_scrape_once_async function not found"
    
    # Get a reasonable chunk of the function (look for the query loop)
    query_loop_start = content.find("for q in QUERIES:", run_scrape_start)
    assert query_loop_start != -1, "Query loop not found in run_scrape_once_async"
    
    # Get the section that handles Google CSE and fallbacks
    fallback_section_end = content.find("if not links:", query_loop_start) + 500
    fallback_section = content[query_loop_start:fallback_section_end]
    
    # Verify had_429_flag is tracked
    assert "had_429_flag |= had_429" in fallback_section, \
        "had_429 flag should be tracked"
    
    # Verify fallbacks activate on 429
    assert "use_fallbacks = had_429_flag or len(links) < 3" in fallback_section, \
        "Fallbacks should activate when had_429_flag is True or links < 3"
    
    # Verify Perplexity is called when use_fallbacks is True
    assert "if use_fallbacks:" in fallback_section, \
        "Fallback logic should check use_fallbacks flag"
    
    # Verify logging explains why fallbacks are activated
    assert '"429" if had_429_flag else "insufficient_results"' in fallback_section, \
        "Logging should explain why fallbacks are activated"
    
    print("✓ Immediate fallback on 429 checks passed")


if __name__ == "__main__":
    test_circuit_breaker_config()
    test_google_cse_disable_flag()
    test_conservative_defaults()
    test_immediate_fallback_on_429()
    print("\n✓✓✓ All circuit breaker tests passed!")
