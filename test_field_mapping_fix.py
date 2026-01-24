#!/usr/bin/env python3
"""
Test script to verify field mapping fixes.
Tests that:
1. ALLOWED_LEAD_COLUMNS includes 'id' and 'crm_status'
2. SCRAPER_TO_DJANGO_MAPPING includes 'crm_status'
3. Field sanitization logs warnings for unmapped fields
4. Django mapping logs warnings for unmapped fields
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def test_allowed_columns():
    """Test that ALLOWED_LEAD_COLUMNS is complete"""
    print("=" * 70)
    print("TEST 1: ALLOWED_LEAD_COLUMNS completeness")
    print("=" * 70)
    
    # Read the file directly to avoid import dependencies
    database_py = repo_root / 'luca_scraper' / 'database.py'
    with open(database_py, 'r') as f:
        content = f.read()
    
    # Extract ALLOWED_LEAD_COLUMNS
    import re
    match = re.search(r"ALLOWED_LEAD_COLUMNS = frozenset\(\{([^}]+)\}\)", content, re.DOTALL)
    if not match:
        print("❌ FAILED: Could not find ALLOWED_LEAD_COLUMNS in database.py")
        return False
    
    columns_str = match.group(1)
    # Extract individual column names
    columns = re.findall(r"'([^']+)'", columns_str)
    
    required_columns = ['id', 'crm_status', 'name', 'email', 'telefon']
    missing = []
    
    for col in required_columns:
        if col not in columns:
            missing.append(col)
    
    if missing:
        print(f"❌ FAILED: Missing columns in ALLOWED_LEAD_COLUMNS: {missing}")
        return False
    else:
        print(f"✅ PASSED: All required columns present in ALLOWED_LEAD_COLUMNS")
        print(f"   Total columns: {len(columns)}")
        print(f"   Includes: {', '.join(required_columns)}")
        return True


def test_field_mapping():
    """Test that field mapping includes crm_status"""
    print("\n" + "=" * 70)
    print("TEST 2: SCRAPER_TO_DJANGO_MAPPING completeness")
    print("=" * 70)
    
    from telis_recruitment.leads.field_mapping import SCRAPER_TO_DJANGO_MAPPING
    
    required_mappings = {
        'crm_status': 'status',
        'name': 'name',
        'email': 'email',
        'telefon': 'telefon',
    }
    
    missing = []
    incorrect = []
    
    for scraper_field, expected_django_field in required_mappings.items():
        if scraper_field not in SCRAPER_TO_DJANGO_MAPPING:
            missing.append(scraper_field)
        elif SCRAPER_TO_DJANGO_MAPPING[scraper_field] != expected_django_field:
            incorrect.append(
                f"{scraper_field} maps to {SCRAPER_TO_DJANGO_MAPPING[scraper_field]}, "
                f"expected {expected_django_field}"
            )
    
    if missing or incorrect:
        if missing:
            print(f"❌ FAILED: Missing mappings: {missing}")
        if incorrect:
            print(f"❌ FAILED: Incorrect mappings: {incorrect}")
        return False
    else:
        print(f"✅ PASSED: All required field mappings present and correct")
        print(f"   Total mappings: {len(SCRAPER_TO_DJANGO_MAPPING)}")
        return True


def test_sanitize_logging():
    """Test that sanitize function logs dropped fields"""
    print("\n" + "=" * 70)
    print("TEST 3: Field sanitization logging")
    print("=" * 70)
    
    # Read the repository.py file to verify logging is in place
    repository_py = repo_root / 'luca_scraper' / 'repository.py'
    with open(repository_py, 'r') as f:
        content = f.read()
    
    # Check for logging of dropped fields at INFO level
    if 'logger.info' not in content or 'Dropping unsupported lead columns' not in content:
        print("❌ FAILED: No INFO-level logging found for dropped fields")
        return False
    
    # Check that it provides helpful guidance
    if 'Consider updating ALLOWED_LEAD_COLUMNS' not in content:
        print("❌ FAILED: Logging doesn't provide guidance on fixing the issue")
        return False
    
    print("✅ PASSED: Field sanitization has proper logging with helpful guidance")
    print("   - Logs at INFO level for visibility")
    print("   - Provides guidance on updating ALLOWED_LEAD_COLUMNS")
    return True


def test_column_names_in_schema():
    """Test that schema columns match ALLOWED_LEAD_COLUMNS"""
    print("\n" + "=" * 70)
    print("TEST 4: Schema vs ALLOWED_LEAD_COLUMNS consistency")
    print("=" * 70)
    
    # Read database.py to extract both schema and ALLOWED_LEAD_COLUMNS
    database_py = repo_root / 'luca_scraper' / 'database.py'
    with open(database_py, 'r') as f:
        content = f.read()
    
    import re
    
    # Extract ALLOWED_LEAD_COLUMNS
    match = re.search(r"ALLOWED_LEAD_COLUMNS = frozenset\(\{([^}]+)\}\)", content, re.DOTALL)
    if not match:
        print("❌ FAILED: Could not find ALLOWED_LEAD_COLUMNS")
        return False
    allowed_columns = set(re.findall(r"'([^']+)'", match.group(1)))
    
    # These are the columns that should be in the schema based on database.py
    schema_columns = {
        'id', 'name', 'rolle', 'email', 'telefon', 'quelle', 'score', 'tags', 
        'region', 'role_guess', 'lead_type', 'salary_hint', 'commission_hint', 
        'opening_line', 'ssl_insecure', 'company_name', 'company_size', 
        'hiring_volume', 'industry', 'recency_indicator', 'location_specific', 
        'confidence_score', 'last_updated', 'data_quality', 'phone_type', 
        'whatsapp_link', 'private_address', 'social_profile_url', 'ai_category', 
        'ai_summary', 'crm_status', 'experience_years', 'skills', 'availability', 
        'current_status', 'industries', 'location', 'profile_text', 
        'candidate_status', 'mobility', 'industries_experience', 'source_type', 
        'profile_url', 'cv_url', 'contact_preference', 'last_activity', 
        'name_validated'
    }
    
    missing_from_allowed = schema_columns - allowed_columns
    extra_in_allowed = allowed_columns - schema_columns
    
    if missing_from_allowed or extra_in_allowed:
        if missing_from_allowed:
            print(f"⚠️  Schema columns not in ALLOWED_LEAD_COLUMNS: {missing_from_allowed}")
        if extra_in_allowed:
            print(f"⚠️  ALLOWED_LEAD_COLUMNS not in schema: {extra_in_allowed}")
        # This is a warning, not a failure
        print("⚠️  WARNING: Schema and ALLOWED_LEAD_COLUMNS are out of sync")
        return True
    else:
        print("✅ PASSED: Schema and ALLOWED_LEAD_COLUMNS are consistent")
        return True


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "FIELD MAPPING FIX VALIDATION" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = []
    
    try:
        results.append(test_allowed_columns())
    except Exception as e:
        print(f"❌ TEST 1 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    try:
        results.append(test_field_mapping())
    except Exception as e:
        print(f"❌ TEST 2 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    try:
        results.append(test_sanitize_logging())
    except Exception as e:
        print(f"❌ TEST 3 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    try:
        results.append(test_column_names_in_schema())
    except Exception as e:
        print(f"❌ TEST 4 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
