"""
Comprehensive tests for phone_extractor.py
Testing phone number extraction, deobfuscation, and validation.

Note: This test file requires the project root to be in PYTHONPATH.
Run from project root: pytest tests/test_phone_extraction.py
"""

import pytest
from phone_extractor import (
    extract_phones_advanced,
    normalize_phone,
    is_valid_phone,
    extract_phone_simple,
    PHONE_BLACKLIST,
    OBFUSCATION_REPLACEMENTS,
)


class TestPhoneExtraction:
    """Test phone number extraction"""

    def test_extract_mobile_standard(self):
        """Test extraction of standard mobile number"""
        text = "Kontakt: 0151 12345678"
        result = extract_phone_simple(text)
        assert result is not None
        # Check that it's a German mobile number
        assert "151" in result or "01511234" in result

    def test_extract_mobile_with_plus(self):
        """Test extraction with +49 prefix"""
        text = "Call me at +49 151 12345678"
        result = extract_phone_simple(text)
        assert result is not None

    def test_extract_mobile_various_separators(self):
        """Test extraction with different separators"""
        test_cases = [
            "0151-12345678",
            "0151.12345678",
            "0151/12345678",
            "0151 123 45678",
        ]
        for text in test_cases:
            result = extract_phone_simple(text)
            assert result is not None, f"Failed to extract from: {text}"

    def test_extract_mobile_in_parentheses(self):
        """Test extraction with parentheses format"""
        text = "Mobil: (0151) 12345678"
        result = extract_phone_simple(text)
        assert result is not None

    def test_extract_whatsapp_number(self):
        """Test extraction of WhatsApp number"""
        text = "WhatsApp: 0151 12345678"
        result = extract_phone_simple(text)
        assert result is not None

    def test_extract_landline(self):
        """Test extraction of landline number"""
        text = "Tel: 0221 1234567"
        result = extract_phone_simple(text)
        assert result is not None

    def test_extract_compact_format(self):
        """Test extraction of number without separators"""
        text = "Rufnummer: 015112345678"
        result = extract_phone_simple(text)
        assert result is not None

    def test_no_phone_found(self):
        """Test when no phone number is present"""
        text = "This text has no phone number"
        result = extract_phone_simple(text)
        assert result is None


class TestPhoneNormalization:
    """Test phone number normalization"""

    def test_normalize_removes_spaces(self):
        """Test normalization removes spaces"""
        result = normalize_phone("0151 123 456 78")
        assert " " not in result

    def test_normalize_removes_dashes(self):
        """Test normalization removes dashes"""
        result = normalize_phone("0151-123-456-78")
        assert "-" not in result

    def test_normalize_removes_dots(self):
        """Test normalization removes dots"""
        result = normalize_phone("0151.123.456.78")
        assert "." not in result

    def test_normalize_removes_slashes(self):
        """Test normalization removes slashes"""
        result = normalize_phone("0151/123/456/78")
        assert "/" not in result

    def test_normalize_removes_parentheses(self):
        """Test normalization removes parentheses"""
        result = normalize_phone("(0151) 12345678")
        assert "(" not in result and ")" not in result

    def test_normalize_handles_plus_prefix(self):
        """Test normalization handles +49 prefix"""
        result = normalize_phone("+49 151 12345678")
        # Should either keep +49 or convert to 0
        assert result.startswith("+49") or result.startswith("0049") or result.startswith("0")


class TestPhoneValidation:
    """Test phone number validation"""

    def test_validate_correct_mobile(self):
        """Test validation of correct mobile number"""
        assert is_valid_phone("015112345678") or is_valid_phone("0151 12345678")

    def test_validate_correct_landline(self):
        """Test validation of correct landline"""
        assert is_valid_phone("02211234567") or is_valid_phone("0221 1234567")

    def test_reject_blacklisted_sequence(self):
        """Test rejection of blacklisted sequences"""
        for blacklisted in ["0123456789", "1111111111", "0000000000"]:
            result = is_valid_phone(blacklisted)
            assert result is False, f"Should reject blacklisted: {blacklisted}"

    def test_reject_service_numbers(self):
        """Test rejection of service numbers"""
        service_numbers = ["0800123456", "0900123456", "0180123456"]
        for num in service_numbers:
            result = is_valid_phone(num)
            assert result is False, f"Should reject service number: {num}"

    def test_reject_too_short(self):
        """Test rejection of too short numbers"""
        result = is_valid_phone("0151")
        assert result is False

    def test_reject_too_long(self):
        """Test rejection of too long numbers"""
        result = is_valid_phone("015112345678901234567890")
        assert result is False

    def test_reject_invalid_format(self):
        """Test rejection of invalid format"""
        result = is_valid_phone("abc123def456")
        assert result is False


class TestAdvancedPhoneExtraction:
    """Test advanced phone extraction with confidence"""

    def test_extract_phones_advanced_returns_tuples(self):
        """Test that advanced extraction returns tuples with confidence"""
        text = "Tel: 0151 12345678"
        results = extract_phones_advanced(text)
        if results:
            assert isinstance(results, list)
            if len(results) > 0:
                assert isinstance(results[0], tuple)
                assert len(results[0]) == 3  # (phone, context, confidence)

    def test_extract_phones_with_context(self):
        """Test extraction with context"""
        text = "Mobil: 0151 12345678"
        results = extract_phones_advanced(text)
        if results:
            # Should include context information
            assert len(results) > 0


class TestPhoneBlacklist:
    """Test phone blacklist"""

    def test_blacklist_exists(self):
        """Test that blacklist is defined"""
        assert len(PHONE_BLACKLIST) > 0

    def test_blacklist_contains_common_fakes(self):
        """Test blacklist contains common fake numbers"""
        assert "0123456789" in PHONE_BLACKLIST
        assert "1111111111" in PHONE_BLACKLIST

    def test_blacklist_contains_service_prefixes(self):
        """Test blacklist contains service number prefixes"""
        assert "0800" in PHONE_BLACKLIST or any("0800" in item for item in PHONE_BLACKLIST)
        assert "0900" in PHONE_BLACKLIST or any("0900" in item for item in PHONE_BLACKLIST)


class TestObfuscationPatterns:
    """Test phone number deobfuscation patterns"""

    def test_obfuscation_patterns_exist(self):
        """Test that obfuscation replacement patterns are defined"""
        assert len(OBFUSCATION_REPLACEMENTS) > 0
        # Check that common patterns are present
        patterns = [p[0] for p in OBFUSCATION_REPLACEMENTS]
        assert any("null" in p for p in patterns)
        assert any("eins" in p for p in patterns)


@pytest.mark.integration
class TestIntegratedPhoneExtraction:
    """Integration tests for phone extraction"""

    def test_extract_multiple_phones(self):
        """Test extraction of multiple phone numbers"""
        text = """
        Kontakt:
        Mobil: 0151 12345678
        Büro: 0221 7654321
        WhatsApp: +49 152 98765432
        """
        results = extract_phones_advanced(text)
        assert len(results) >= 2  # Should find at least 2 numbers

    def test_extract_from_contact_card(self):
        """Test extraction from a contact card"""
        text = """
        Max Mustermann
        Vertriebsleiter
        Tel: 0221 123456
        Mobil: 0151 12345678
        E-Mail: max@firma.de
        """
        result = extract_phone_simple(text)
        assert result is not None

    def test_extract_mixed_formats(self):
        """Test extraction with mixed formats"""
        text = "Festnetz: 0221-1234567, Handy: +49 151 12345678, Fax: 0221/1234568"
        results = extract_phones_advanced(text)
        # Should extract multiple numbers
        assert len(results) >= 2

    def test_filter_invalid_from_results(self):
        """Test that invalid numbers are filtered from results"""
        text = "Tel: 0800123456 oder 0151 12345678"
        result = extract_phone_simple(text)
        # Should not include 0800 number
        if result:
            assert "0800" not in result


@pytest.mark.parametrize(
    "text,should_find",
    [
        ("Mobil: 0151 12345678", True),
        ("Tel: +49 151 12345678", True),
        ("Phone: 015112345678", True),
        ("Kontakt: (0151) 12345678", True),
        ("WhatsApp 0152-98765432", True),
        ("No phone here", False),
        ("Invalid: 123", False),
    ],
)
def test_phone_extraction_parametrized(text, should_find):
    """Parametrized test for various phone extraction scenarios"""
    result = extract_phone_simple(text)
    if should_find:
        assert result is not None, f"Should find phone in: {text}"
    else:
        assert result is None, f"Should not find phone in: {text}"
