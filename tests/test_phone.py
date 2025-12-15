import pytest
from scriptname import normalize_phone, validate_phone


def test_normalize_phone():
    """Test phone normalization with various formats."""
    assert normalize_phone("0211 123456") == "+49211123456"
    assert normalize_phone("+49 (0) 211-123456") == "+49211123456"
    assert normalize_phone("0049 (0)176 123 45 67") == "+491761234567"
    assert normalize_phone("+49-(0)-176 123 45 67") == "+491761234567"
    assert normalize_phone("0049 211 123456") == "+49211123456"


def test_validate_phone_valid_german():
    """Test validation of valid German phone numbers."""
    # Valid mobile numbers
    is_valid, phone_type = validate_phone("+491761234567")
    assert is_valid is True
    assert phone_type == "mobile"
    
    is_valid, phone_type = validate_phone("0176 1234567")
    assert is_valid is True
    assert phone_type == "mobile"
    
    is_valid, phone_type = validate_phone("+4915012345678")
    assert is_valid is True
    assert phone_type == "mobile"
    
    # Valid landline numbers
    is_valid, phone_type = validate_phone("+49211123456")
    assert is_valid is True
    assert phone_type == "landline"
    
    is_valid, phone_type = validate_phone("0211 123456")
    assert is_valid is True
    assert phone_type == "landline"


def test_validate_phone_invalid():
    """Test rejection of invalid phone numbers."""
    # Too short
    is_valid, phone_type = validate_phone("123")
    assert is_valid is False
    assert phone_type == "invalid"
    
    # Too long
    is_valid, phone_type = validate_phone("12345678901234567890")
    assert is_valid is False
    assert phone_type == "invalid"
    
    # Empty
    is_valid, phone_type = validate_phone("")
    assert is_valid is False
    assert phone_type == "invalid"
    
    # None
    is_valid, phone_type = validate_phone(None)
    assert is_valid is False
    assert phone_type == "invalid"


def test_validate_phone_international():
    """Test validation of international phone numbers."""
    # Valid international
    is_valid, phone_type = validate_phone("+33612345678")
    assert is_valid is True
    assert phone_type == "international"
    
    is_valid, phone_type = validate_phone("+441234567890")
    assert is_valid is True
    assert phone_type == "international"


def test_validate_phone_edge_cases():
    """Test edge cases in phone validation."""
    # With extension markers (should be cleaned)
    is_valid, phone_type = validate_phone("0211 123456 ext. 789")
    assert is_valid is True
    assert phone_type == "landline"
    
    # With (0) notation
    is_valid, phone_type = validate_phone("+49 (0) 176 1234567")
    assert is_valid is True
    assert phone_type == "mobile"
