#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for lead validation system.

Tests the complete validation flow from raw lead data through validation
to database insertion simulation.
"""

import sys
from lead_validation import (
    validate_lead_before_insert,
    normalize_phone_number,
    extract_person_name,
    validate_lead_name,
    validate_phone_number,
    is_valid_lead_source,
    get_rejection_stats,
    reset_rejection_stats,
)


def test_phone_validation():
    """Test phone number validation."""
    print("\n" + "="*60)
    print("Testing Phone Validation")
    print("="*60)
    
    test_cases = [
        ("01761234567", True, "Valid mobile number"),
        ("+491761234567", True, "Valid mobile with +49"),
        ("00491761234567", True, "Valid mobile with 0049"),
        ("+49610", False, "Too short"),
        ("+491234567890", False, "Fake pattern"),
        ("+49211123456", False, "Landline number"),
        ("01511111111", False, "Repeating digits"),
        ("+4915123456789012345", False, "Too long"),
    ]
    
    passed = 0
    failed = 0
    
    for phone, expected, description in test_cases:
        result = validate_phone_number(phone)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} {description}: {phone} -> {result}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_source_validation():
    """Test source URL validation."""
    print("\n" + "="*60)
    print("Testing Source URL Validation")
    print("="*60)
    
    test_cases = [
        ("https://www.kleinanzeigen.de/s-anzeige/123", True, "Kleinanzeigen"),
        ("https://www.quoka.de/stellengesuche/", True, "Quoka"),
        ("https://www.markt.de/stellengesuche/", True, "Markt.de"),
        ("https://www.facebook.com/profile", False, "Facebook (blocked)"),
        ("https://www.tiktok.com/@user", False, "TikTok (blocked)"),
        ("https://www.indeed.com/job/123", False, "Indeed (blocked)"),
        ("https://example.com/file.pdf", False, "PDF file (blocked)"),
        ("https://storage.googleapis.com/...", False, "Google Storage (blocked)"),
    ]
    
    passed = 0
    failed = 0
    
    for url, expected, description in test_cases:
        result = is_valid_lead_source(url)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} {description} -> {result}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_name_validation():
    """Test name validation."""
    print("\n" + "="*60)
    print("Testing Name Validation")
    print("="*60)
    
    test_cases = [
        ("Max Mustermann", True, "Valid name"),
        ("Anna Schmidt", True, "Valid name"),
        ("Dr. Thomas Müller", True, "Name with title"),
        ("Deine Aufgaben", False, "Job ad headline"),
        ("Flexible Arbeitszeiten", False, "Job benefit phrase"),
        ("_probe_", False, "Test entry"),
        ("Krankenhaus GmbH", False, "Company name"),
        ("Test User", False, "Test account"),
        ("M", False, "Too short"),
        ("Muster Vorlage", False, "Muster template"),
    ]
    
    passed = 0
    failed = 0
    
    for name, expected, description in test_cases:
        result = validate_lead_name(name)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} {description}: '{name}' -> {result}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_complete_validation():
    """Test complete lead validation flow."""
    print("\n" + "="*60)
    print("Testing Complete Lead Validation")
    print("="*60)
    
    # Reset statistics
    reset_rejection_stats()
    
    test_leads = [
        {
            "name": "Max Mustermann",
            "telefon": "01761234567",
            "quelle": "https://www.kleinanzeigen.de/s-anzeige/123",
            "lead_type": "candidate",
            "expected": True,
            "description": "Valid candidate lead"
        },
        {
            "name": "Anna Schmidt",
            "telefon": "+491521234567",
            "quelle": "https://www.quoka.de/stellengesuche/",
            "lead_type": "candidate",
            "expected": True,
            "description": "Valid lead with +49 prefix"
        },
        {
            "name": "John Doe",
            "telefon": "+49610",
            "quelle": "https://www.kleinanzeigen.de/s-anzeige/123",
            "lead_type": "candidate",
            "expected": False,
            "description": "Invalid phone (too short)"
        },
        {
            "name": "Jane Doe",
            "telefon": "01761234567",
            "quelle": "https://www.facebook.com/profile",
            "lead_type": "candidate",
            "expected": False,
            "description": "Blocked source (Facebook)"
        },
        {
            "name": "Deine Aufgaben",
            "telefon": "01761234567",
            "quelle": "https://www.kleinanzeigen.de/s-anzeige/123",
            "lead_type": "candidate",
            "expected": False,
            "description": "Invalid name (headline)"
        },
        {
            "name": "Klaus Weber",
            "telefon": "01761234567",
            "quelle": "https://www.kleinanzeigen.de/s-anzeige/123",
            "lead_type": "employer",
            "expected": False,
            "description": "Wrong lead type"
        },
    ]
    
    passed = 0
    failed = 0
    
    for lead in test_leads:
        expected = lead.pop("expected")
        description = lead.pop("description")
        
        is_valid, reason = validate_lead_before_insert(lead)
        status = "✓" if is_valid == expected else "✗"
        
        if is_valid == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"  {status} {description}")
        print(f"      Result: {is_valid}, Reason: {reason}")
    
    # Show statistics
    stats = get_rejection_stats()
    print(f"\nRejection Statistics:")
    print(f"  Invalid phone: {stats['invalid_phone']}")
    print(f"  Blocked source: {stats['blocked_source']}")
    print(f"  Invalid name: {stats['invalid_name']}")
    print(f"  Wrong type: {stats['wrong_type']}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_name_extraction():
    """Test name extraction functionality."""
    print("\n" + "="*60)
    print("Testing Name Extraction")
    print("="*60)
    
    test_cases = [
        ("Kontakt: Max Mustermann", "Max Mustermann", "Contact prefix"),
        ("Ansprechpartner: Anna Schmidt", "Anna Schmidt", "Contact person prefix"),
        ("Herr Thomas Müller", "Thomas Müller", "Herr prefix"),
        ("Frau Julia Weber", "Julia Weber", "Frau prefix"),
        ("Max Mustermann", "Max Mustermann", "Plain name (no extraction)"),
    ]
    
    passed = 0
    failed = 0
    
    for raw, expected, description in test_cases:
        result = extract_person_name(raw)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"  {status} {description}")
        print(f"      Input: '{raw}' -> Output: '{result}'")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Lead Validation System - Integration Tests")
    print("="*60)
    
    all_passed = True
    
    # Run test suites
    all_passed &= test_phone_validation()
    all_passed &= test_source_validation()
    all_passed &= test_name_validation()
    all_passed &= test_name_extraction()
    all_passed &= test_complete_validation()
    
    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
