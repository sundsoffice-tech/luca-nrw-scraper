"""
Test for phone_email_extraction module
=======================================
Simple smoke test to verify the extraction module works correctly.
"""

import sys
import os
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_extraction_module_imports():
    """Test that extraction module can be imported."""
    from luca_scraper.extraction.phone_email_extraction import (
        extract_phone_numbers,
        extract_email_address,
        extract_whatsapp_number,
    )
    
    assert callable(extract_phone_numbers)
    assert callable(extract_email_address)
    assert callable(extract_whatsapp_number)
    print("✓ All extraction functions are callable")


def test_extract_email_address():
    """Test email extraction functionality."""
    from luca_scraper.extraction.phone_email_extraction import extract_email_address
    
    # Create a simple email regex
    EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    # Test cases
    text1 = "Contact us at test@example.com for more info"
    result1 = extract_email_address(text1, EMAIL_RE)
    assert result1 == "test@example.com", f"Expected 'test@example.com', got '{result1}'"
    
    text2 = "No email here"
    result2 = extract_email_address(text2, EMAIL_RE)
    assert result2 == "", f"Expected empty string, got '{result2}'"
    
    print("✓ Email extraction works correctly")


def test_extract_phone_numbers_basic():
    """Test basic phone number extraction."""
    from luca_scraper.extraction.phone_email_extraction import extract_phone_numbers
    
    # Mock helper functions
    def normalize_phone(phone):
        """Simple normalization."""
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('49'):
            return '+' + digits
        elif digits.startswith('0'):
            return '+49' + digits[1:]
        return '+49' + digits
    
    def validate_phone(phone):
        """Simple validation."""
        return (len(phone) >= 12, 'mobile')
    
    def is_mobile(phone):
        """Check if mobile."""
        return '15' in phone or '16' in phone or '17' in phone
    
    # Test with simple regex
    MOBILE_RE = re.compile(r'01[567]\d{8,9}')
    
    html = "<div>Rufen Sie mich an: 01761234567</div>"
    text = "Rufen Sie mich an: 01761234567"
    
    phones, sources = extract_phone_numbers(
        html=html,
        text=text,
        normalize_phone_func=normalize_phone,
        validate_phone_func=validate_phone,
        is_mobile_number_func=is_mobile,
        MOBILE_RE=MOBILE_RE,
    )
    
    assert len(phones) > 0, "Should extract at least one phone"
    assert '+491761234567' in phones, f"Expected normalized phone, got {phones}"
    assert sources.get('+491761234567') == 'regex_standard'
    
    print("✓ Phone extraction works correctly")


def test_extract_whatsapp_number():
    """Test WhatsApp number extraction."""
    from luca_scraper.extraction.phone_email_extraction import extract_whatsapp_number
    
    # Mock helper functions
    def normalize_phone(phone):
        digits = re.sub(r'\D', '', phone)
        if not digits.startswith('+'):
            return '+' + digits
        return digits
    
    def validate_phone(phone):
        return (len(phone) >= 12, 'mobile')
    
    def is_mobile(phone):
        return '15' in phone or '16' in phone or '17' in phone
    
    # Test HTML with WhatsApp link
    html = '<a href="https://wa.me/491761234567">WhatsApp</a>'
    
    whatsapp, sources = extract_whatsapp_number(
        html=html,
        normalize_phone_func=normalize_phone,
        validate_phone_func=validate_phone,
        is_mobile_number_func=is_mobile,
    )
    
    assert whatsapp == '+491761234567', f"Expected '+491761234567', got '{whatsapp}'"
    assert sources.get('+491761234567') == 'whatsapp_link'
    
    print("✓ WhatsApp extraction works correctly")


if __name__ == '__main__':
    print("\nRunning extraction module tests...\n")
    
    try:
        test_extraction_module_imports()
        test_extract_email_address()
        test_extract_phone_numbers_basic()
        test_extract_whatsapp_number()
        
        print("\n✓ All tests passed!\n")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        raise
