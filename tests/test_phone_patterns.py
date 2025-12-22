# -*- coding: utf-8 -*-
"""Tests for the phone_patterns module."""

import pytest
from phone_patterns import (
    normalize_phone_from_words,
    extract_whatsapp_number,
    extract_obfuscated_number,
    extract_phone_with_spacing,
    extract_all_phone_patterns,
    get_best_phone_number,
)


class TestPhonePatternExtraction:
    """Tests for advanced phone pattern extraction."""
    
    def test_normalize_phone_from_words(self):
        """Test converting phone numbers written as words."""
        # Test German words
        result = normalize_phone_from_words("null eins sieben sechs eins zwei drei vier fünf sechs sieben")
        assert result == "01761234567"
        
        result = normalize_phone_from_words("null eins fünf null")
        assert result == "0150"
        
        # Test with mixed text
        result = normalize_phone_from_words("Meine Nummer ist null eins sieben sechs")
        assert result == "0176"
        
        # Test empty/invalid
        result = normalize_phone_from_words("keine nummer hier")
        assert result is None
    
    def test_extract_whatsapp_number(self):
        """Test extracting phone numbers from WhatsApp links."""
        # wa.me format
        html = '<a href="https://wa.me/4917612345678">WhatsApp</a>'
        result = extract_whatsapp_number(html)
        assert result == "+4917612345678"
        
        # api.whatsapp.com format
        html = '<a href="https://api.whatsapp.com/send?phone=4917612345678">Contact</a>'
        result = extract_whatsapp_number(html)
        assert result is not None
        assert "176" in result
        
        # No WhatsApp link
        html = '<p>No WhatsApp here</p>'
        result = extract_whatsapp_number(html)
        assert result is None
    
    def test_extract_obfuscated_number(self):
        """Test extracting obfuscated phone numbers."""
        # With asterisks
        text = "Rufen Sie mich an: 0176***4567"
        result = extract_obfuscated_number(text)
        assert result is not None
        assert result.startswith("0176")
        
        # With x
        text = "Telefon: 0176xxx4567"
        result = extract_obfuscated_number(text)
        assert result is not None
        assert result.startswith("0176")
        
        # With spaces
        text = "Tel: 0176 *** 4567"
        result = extract_obfuscated_number(text)
        assert result is not None
        
        # No obfuscated number
        text = "Keine Telefonnummer"
        result = extract_obfuscated_number(text)
        assert result is None
    
    def test_extract_phone_with_spacing(self):
        """Test extracting heavily spaced phone numbers."""
        # Standard spacing
        text = "Meine Nummer: 0 1 7 6 1 2 3 4 5 6 7"
        results = extract_phone_with_spacing(text)
        assert len(results) > 0
        assert results[0] == "01761234567"
        
        # Multiple spaces
        text = "Tel:  0   1   7   6   1   2   3   4   5   6   7  "
        results = extract_phone_with_spacing(text)
        assert len(results) > 0
        
        # No spaced number
        text = "0176 1234567"  # Normal spacing, not heavy
        results = extract_phone_with_spacing(text)
        # Should not match normal spacing
        assert len(results) == 0
    
    def test_extract_all_phone_patterns(self):
        """Test comprehensive phone pattern extraction."""
        html = """
        <html>
            <body>
                <p>WhatsApp: <a href="https://wa.me/4917612345678">Kontakt</a></p>
                <p>Versteckte Nummer: 0176***4567</p>
                <p>Getrennt: 0 1 5 0 1 2 3 4 5 6 7</p>
            </body>
        </html>
        """
        text = "WhatsApp Kontakt Versteckte Nummer: 0176***4567 Getrennt: 0 1 5 0 1 2 3 4 5 6 7"
        
        results = extract_all_phone_patterns(html, text)
        
        assert 'whatsapp' in results
        assert 'obfuscated' in results
        assert 'spaced' in results
        assert 'standard' in results
        
        # Should have found at least the WhatsApp number
        assert len(results['whatsapp']) > 0
    
    def test_get_best_phone_number(self):
        """Test selecting the best phone number from extraction results."""
        # WhatsApp should be prioritized
        results = {
            'whatsapp': ['+4917612345678'],
            'standard': ['01501234567'],
            'obfuscated': [],
            'spaced': [],
        }
        best = get_best_phone_number(results)
        assert best == '+4917612345678'
        
        # Standard should be next priority
        results = {
            'whatsapp': [],
            'standard': ['+4917612345678', '01501234567'],
            'obfuscated': [],
            'spaced': [],
        }
        best = get_best_phone_number(results)
        assert best in ['+4917612345678', '01501234567']
        
        # Spaced should come after standard
        results = {
            'whatsapp': [],
            'standard': [],
            'obfuscated': [],
            'spaced': ['01761234567'],
        }
        best = get_best_phone_number(results)
        assert best == '01761234567'
        
        # No numbers found
        results = {
            'whatsapp': [],
            'standard': [],
            'obfuscated': [],
            'spaced': [],
        }
        best = get_best_phone_number(results)
        assert best is None


class TestPhonePatternEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_input(self):
        """Test handling of empty input."""
        assert normalize_phone_from_words("") is None
        assert extract_whatsapp_number("") is None
        assert extract_obfuscated_number("") is None
        assert extract_phone_with_spacing("") == []
    
    def test_invalid_whatsapp_links(self):
        """Test handling of malformed WhatsApp links."""
        html = '<a href="https://wa.me/invalid">WhatsApp</a>'
        result = extract_whatsapp_number(html)
        # Should handle gracefully (might return None or invalid number)
        # Either is acceptable
        assert result is None or isinstance(result, str)
    
    def test_mixed_content(self):
        """Test extraction from mixed German/English content."""
        html = """
        Call me: 0176 1234567
        WhatsApp: wa.me/4917612345678
        Versteckte Nummer: 0150***789
        """
        text = "Call me: 0176 1234567 WhatsApp: wa.me/4917612345678 Versteckte Nummer: 0150***789"
        
        results = extract_all_phone_patterns(html, text)
        
        # Should find multiple numbers
        total_found = sum(len(v) for v in results.values())
        assert total_found > 0
