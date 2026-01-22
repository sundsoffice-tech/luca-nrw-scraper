# -*- coding: utf-8 -*-
"""
Tests for German Phone Patterns Module
======================================

Tests for the enhanced German phone number extraction and normalization.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luca_scraper.scoring.german_patterns import (
    normalize_german_phone,
    validate_german_mobile,
    validate_german_landline,
    extract_german_phones,
    extract_phone_with_label,
    is_blacklisted_phone,
    PHONE_PATTERNS_COMPILED,
    PHONE_LABELS,
)


class TestNormalizeGermanPhone:
    """Tests for normalize_german_phone function."""
    
    def test_international_format_with_plus(self):
        """Test +49 format normalization."""
        assert normalize_german_phone("+49 176 1234 5678") == "+4917612345678"
        assert normalize_german_phone("+49 211 123456") == "+49211123456"
        assert normalize_german_phone("+49-176-1234-5678") == "+4917612345678"
    
    def test_international_format_with_0049(self):
        """Test 0049 format normalization."""
        assert normalize_german_phone("0049 176 1234 5678") == "+4917612345678"
        assert normalize_german_phone("0049-176-1234-5678") == "+4917612345678"
        assert normalize_german_phone("0049/176/12345678") == "+4917612345678"
    
    def test_national_format(self):
        """Test 0-prefix national format."""
        assert normalize_german_phone("0176 1234 5678") == "+4917612345678"
        assert normalize_german_phone("0176-1234-5678") == "+4917612345678"
        assert normalize_german_phone("0176/1234/5678") == "+4917612345678"
        assert normalize_german_phone("0211 123456") == "+49211123456"
    
    def test_compact_format(self):
        """Test compact format without separators."""
        assert normalize_german_phone("017612345678") == "+4917612345678"
        assert normalize_german_phone("+4917612345678") == "+4917612345678"
    
    def test_brackets_format(self):
        """Test format with area code in brackets."""
        assert normalize_german_phone("(0176) 1234 5678") == "+4917612345678"
        assert normalize_german_phone("(0211) 123456") == "+49211123456"
    
    def test_mixed_separators(self):
        """Test format with mixed separators."""
        assert normalize_german_phone("0176/1234-5678") == "+4917612345678"
        assert normalize_german_phone("0176 1234/5678") == "+4917612345678"
    
    def test_invalid_formats(self):
        """Test that invalid formats return empty string."""
        assert normalize_german_phone("") == ""
        assert normalize_german_phone("12345") == ""  # Too short
        assert normalize_german_phone("abc") == ""    # No digits
        assert normalize_german_phone("17612345678") == ""  # Missing prefix
    
    def test_edge_cases(self):
        """Test edge cases."""
        assert normalize_german_phone("   +49 176 1234 5678   ") == "+4917612345678"
        assert normalize_german_phone("+49.176.1234.5678") == "+4917612345678"


class TestValidateGermanMobile:
    """Tests for validate_german_mobile function."""
    
    def test_valid_mobile_numbers(self):
        """Test valid German mobile numbers."""
        assert validate_german_mobile("+4917612345678") is True
        assert validate_german_mobile("+4915212345678") is True
        assert validate_german_mobile("+4916012345678") is True
    
    def test_invalid_mobile_numbers(self):
        """Test invalid mobile numbers."""
        assert validate_german_mobile("+49211123456") is False   # Landline
        assert validate_german_mobile("+4912345678") is False    # Invalid prefix
        assert validate_german_mobile("017612345678") is False   # Missing +49
        assert validate_german_mobile("") is False
        assert validate_german_mobile("+4917612345") is False    # Too short


class TestValidateGermanLandline:
    """Tests for validate_german_landline function."""
    
    def test_valid_landline_numbers(self):
        """Test valid German landline numbers."""
        assert validate_german_landline("+49211123456") is True
        assert validate_german_landline("+492212345678") is True
        assert validate_german_landline("+498912345678") is True
    
    def test_invalid_landline_numbers(self):
        """Test invalid landline numbers."""
        assert validate_german_landline("+4917612345678") is False  # Mobile
        assert validate_german_landline("+491234567890") is False   # Mobile prefix
        assert validate_german_landline("") is False


class TestExtractGermanPhones:
    """Tests for extract_german_phones function."""
    
    def test_extract_single_phone(self):
        """Test extracting a single phone number."""
        text = "Rufen Sie mich an: 0176 1234 5678"
        results = extract_german_phones(text)
        assert len(results) >= 1
        assert results[0][0] == "+4917612345678"
    
    def test_extract_multiple_phones(self):
        """Test extracting multiple phone numbers."""
        text = """
        Mobil: 0176 1234 5678
        Festnetz: 0211 123456
        """
        results = extract_german_phones(text)
        assert len(results) >= 2
    
    def test_extract_with_labels(self):
        """Test extracting phones with labels."""
        text = "Tel: 0176 1234 5678, Handy: 0151 9876 5432"
        results = extract_german_phones(text)
        assert len(results) >= 2
    
    def test_extract_international_format(self):
        """Test extracting international format."""
        text = "Erreichbar unter +49 176 1234 5678"
        results = extract_german_phones(text)
        assert len(results) >= 1
        assert results[0][0] == "+4917612345678"
    
    def test_mobile_only_filter(self):
        """Test mobile_only filter."""
        text = """
        Mobil: 0176 1234 5678
        Festnetz: 0211 123456
        """
        results = extract_german_phones(text, mobile_only=True)
        # Should only return mobile
        for r in results:
            assert validate_german_mobile(r[0])
    
    def test_extract_from_html(self):
        """Test extraction from HTML content."""
        text = "Kontakt"
        html = '<a href="tel:+4917612345678">Anrufen</a>'
        results = extract_german_phones(text, html=html)
        assert len(results) >= 1
    
    def test_no_phones(self):
        """Test text without phone numbers."""
        text = "Dies ist ein Text ohne Telefonnummern."
        results = extract_german_phones(text)
        assert len(results) == 0


class TestExtractPhoneWithLabel:
    """Tests for extract_phone_with_label function."""
    
    def test_tel_label(self):
        """Test Tel: label extraction."""
        text = "Tel: 0176 1234 5678"
        results = extract_phone_with_label(text)
        assert len(results) >= 1
        assert results[0][0] == "+4917612345678"
        assert "tel" in results[0][1].lower()
    
    def test_mobil_label(self):
        """Test Mobil: label extraction."""
        text = "Mobil: 0176 1234 5678"
        results = extract_phone_with_label(text)
        assert len(results) >= 1
        assert "mobil" in results[0][1].lower()
    
    def test_handy_label(self):
        """Test Handy: label extraction."""
        text = "Handy: 0176 1234 5678"
        results = extract_phone_with_label(text)
        assert len(results) >= 1
        assert "handy" in results[0][1].lower()
    
    def test_multiple_labels(self):
        """Test multiple labels."""
        text = """
        Tel: 0211 123456
        Mobil: 0176 1234 5678
        """
        results = extract_phone_with_label(text)
        assert len(results) >= 2


class TestIsBlacklistedPhone:
    """Tests for is_blacklisted_phone function."""
    
    def test_fake_numbers(self):
        """Test fake/test numbers."""
        assert is_blacklisted_phone("0123456789") is True
        assert is_blacklisted_phone("1234567890") is True
    
    def test_all_same_digit(self):
        """Test all same digit numbers."""
        assert is_blacklisted_phone("0000000000") is True
        assert is_blacklisted_phone("1111111111") is True
    
    def test_service_numbers(self):
        """Test service number prefixes."""
        assert is_blacklisted_phone("0800123456") is True
        assert is_blacklisted_phone("0900123456") is True
        assert is_blacklisted_phone("0180123456") is True
    
    def test_repeated_digits(self):
        """Test numbers with repeated digits."""
        assert is_blacklisted_phone("+4917611111178") is True
    
    def test_valid_numbers(self):
        """Test that valid numbers are not blacklisted."""
        assert is_blacklisted_phone("+4917612345678") is False
        assert is_blacklisted_phone("017687654321") is False


class TestPhoneLabels:
    """Tests for PHONE_LABELS constant."""
    
    def test_common_labels_present(self):
        """Test that common labels are in the list."""
        labels_lower = [l.lower() for l in PHONE_LABELS]
        assert any("tel" in l for l in labels_lower)
        assert any("mobil" in l for l in labels_lower)
        assert any("handy" in l for l in labels_lower)
        assert any("whatsapp" in l for l in labels_lower)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
