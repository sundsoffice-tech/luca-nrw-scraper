"""
Tests for social media job-seeking keywords in scoring_enhanced.py

These tests verify that the correct job-seeking keywords have been added to the scoring function.
"""
import re


def test_job_keywords_in_file():
    """Test that job-seeking keywords are present in scoring_enhanced.py"""
    with open("stream3_scoring_layer/scoring_enhanced.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for the presence of the required keywords
    expected_keywords = [
        "neue herausforderung",
        "suche neuen wirkungskreis",
        "open to work",
        "looking for opportunities",
        "verfügbar ab",
        "freiberuflich",
    ]
    
    for keyword in expected_keywords:
        assert keyword in content, f"Keyword not found in scoring_enhanced.py: {keyword}"
    
    print(f"✓ All {len(expected_keywords)} job-seeking keywords found in scoring_enhanced.py")


def test_job_keywords_in_list():
    """Test that keywords are in the job_keywords list"""
    with open("stream3_scoring_layer/scoring_enhanced.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the job_keywords list
    job_keywords_match = re.search(r'job_keywords\s*=\s*\[(.*?)\]', content, re.DOTALL)
    assert job_keywords_match, "Could not find job_keywords list in scoring_enhanced.py"
    
    job_keywords_section = job_keywords_match.group(1)
    
    # Check that new keywords are in this list
    new_keywords = [
        "neue herausforderung",
        "suche neuen wirkungskreis",
        "open to work",
        "looking for opportunities",
        "verfügbar ab",
        "freiberuflich",
    ]
    
    for keyword in new_keywords:
        assert keyword in job_keywords_section, f"Keyword not in job_keywords list: {keyword}"
    
    print("✓ All job-seeking keywords are correctly placed in the job_keywords list")


def test_original_keywords_preserved():
    """Test that original job keywords are still present"""
    with open("stream3_scoring_layer/scoring_enhanced.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the job_keywords list
    job_keywords_match = re.search(r'job_keywords\s*=\s*\[(.*?)\]', content, re.DOTALL)
    assert job_keywords_match, "Could not find job_keywords list in scoring_enhanced.py"
    
    job_keywords_section = job_keywords_match.group(1)
    
    # Check that original keywords are still there
    original_keywords = ["jobsuche", "stellensuche", "arbeitslos", "bewerbung", "lebenslauf", "cv"]
    
    for keyword in original_keywords:
        assert keyword in job_keywords_section, f"Original keyword missing: {keyword}"
    
    print("✓ Original job keywords are preserved")


def test_keywords_case_appropriate():
    """Test that keywords are lowercase (for case-insensitive matching)"""
    with open("stream3_scoring_layer/scoring_enhanced.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the job_keywords list
    job_keywords_match = re.search(r'job_keywords\s*=\s*\[(.*?)\]', content, re.DOTALL)
    assert job_keywords_match, "Could not find job_keywords list"
    
    job_keywords_section = job_keywords_match.group(1)
    
    # Extract all string literals from the list
    keyword_strings = re.findall(r'"([^"]*)"', job_keywords_section)
    
    # Check that all keywords are lowercase
    for keyword in keyword_strings:
        assert keyword == keyword.lower(), f"Keyword should be lowercase: {keyword}"
    
    print("✓ All keywords are properly lowercase for case-insensitive matching")


def test_compute_score_v2_uses_job_keywords():
    """Test that compute_score_v2 function uses job_keywords"""
    with open("stream3_scoring_layer/scoring_enhanced.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the compute_score_v2 function
    func_match = re.search(r'def compute_score_v2\((.*?)\):', content, re.DOTALL)
    assert func_match, "Could not find compute_score_v2 function"
    
    # Check that the function includes job_keywords and scoring logic
    assert "job_keywords" in content, "job_keywords not referenced in file"
    assert "job_hits" in content, "job_hits variable not found (keyword scoring logic missing)"
    assert "text_low.count(k) for k in job_keywords" in content, "Keyword counting logic not found"
    
    print("✓ compute_score_v2 function properly uses job_keywords for scoring")


if __name__ == "__main__":
    test_job_keywords_in_file()
    test_job_keywords_in_list()
    test_original_keywords_preserved()
    test_keywords_case_appropriate()
    test_compute_score_v2_uses_job_keywords()
    print("\n✅ All job-seeking keyword tests passed!")
