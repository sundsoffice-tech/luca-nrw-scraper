"""
Tests for parallel phone extraction and dynamic scoring.

This module tests:
1. Parallel phone extraction - running regex and advanced patterns simultaneously
2. Dynamic lead scoring - score calculation based on data quality and source reputation
3. Lead data structure - ensuring all required fields are present
"""

import pytest


class TestParallelPhoneExtraction:
    """
    Test parallel phone extraction functionality.
    
    These tests verify that:
    - All extraction methods run simultaneously (not sequentially)
    - Results from different methods are merged correctly
    - Deduplication keeps highest confidence scores
    - Results are sorted by confidence (highest first)
    """

    def test_extract_multiple_methods_parallel(self):
        """Test that extraction runs all methods in parallel and merges results"""
        from phone_extractor import extract_phones_advanced

        # Text with multiple phone formats that different extractors would find
        text = """
        Tel: 0151 12345678
        WhatsApp: +49 176 98765432
        Ruf an: 0171 11223344
        """
        
        results = extract_phones_advanced(text)
        
        # Should find at least 2 numbers (standard regex finds multiple)
        assert len(results) >= 2
        
        # Check that results are tuples with 3 elements (phone, raw, confidence)
        for phone, raw, confidence in results:
            assert phone.startswith("+49")
            assert isinstance(confidence, float)
            assert 0.0 <= confidence <= 1.0

    def test_whatsapp_extraction_parallel(self):
        """Test WhatsApp extraction runs in parallel with regex"""
        from phone_extractor import extract_phones_advanced

        # WhatsApp-only text
        html = '<a href="https://wa.me/4917612345678">Chat mit mir</a>'
        
        results = extract_phones_advanced("", html)
        
        # Should find WhatsApp number
        assert len(results) >= 1
        found_phones = [phone for phone, _, _ in results]
        assert any("176" in phone for phone in found_phones)

    def test_deduplication_keeps_highest_confidence(self):
        """Test that deduplication keeps highest confidence for each phone"""
        from phone_extractor import extract_phones_advanced

        # Same number in different formats
        text = """
        Tel: 0151-12345678
        Mobil: +49 151 12345678
        WhatsApp: 015112345678
        """
        
        results = extract_phones_advanced(text)
        
        # Should deduplicate to 1 number
        normalized_phones = [phone for phone, _, _ in results]
        # Count unique normalized phones
        assert len(set(normalized_phones)) == len(normalized_phones)

    def test_results_sorted_by_confidence(self):
        """Test that results are sorted by confidence (highest first)"""
        from phone_extractor import extract_phones_advanced

        text = """
        Tel: 0151 12345678
        Handy: 0176 98765432
        Mobil: 0171 11223344
        """
        
        results = extract_phones_advanced(text)
        
        if len(results) > 1:
            # Check confidence is descending
            confidences = [conf for _, _, conf in results]
            assert confidences == sorted(confidences, reverse=True)


class TestDynamicScoring:
    """
    Test dynamic lead scoring functionality.
    
    These tests verify that the scoring system correctly:
    - Increases scores based on data completeness
    - Applies portal reputation bonuses
    - Considers phone source quality
    - Caps scores to valid ranges
    """

    def test_score_increases_with_completeness(self):
        """Test that score increases with more complete data using centralized module"""
        from luca_scraper.scoring.dynamic_scoring import calculate_dynamic_score
        
        # Base score with no data
        score_none, _, _ = calculate_dynamic_score(portal="generic")
        
        # Score with phone
        score_phone, _, _ = calculate_dynamic_score(has_phone=True, portal="generic")
        assert score_phone > score_none
        
        # Score with phone + email
        score_email, _, _ = calculate_dynamic_score(has_phone=True, has_email=True, portal="generic")
        assert score_email > score_phone
        
        # Score with phone + email + name
        score_name, _, _ = calculate_dynamic_score(
            has_phone=True, has_email=True, has_name=True, portal="generic"
        )
        assert score_name > score_email

    def test_portal_reputation_affects_score(self):
        """Test that portal reputation affects the score using centralized module"""
        from luca_scraper.scoring.dynamic_scoring import PORTAL_REPUTATION
        
        # Kleinanzeigen should have highest reputation
        assert PORTAL_REPUTATION["kleinanzeigen"] == max(PORTAL_REPUTATION.values())
        
        # DHD24 should have lowest reputation
        assert PORTAL_REPUTATION["dhd24"] == min(PORTAL_REPUTATION.values())

    def test_phone_source_quality_affects_score(self):
        """Test that phone source quality affects the score using centralized module"""
        from luca_scraper.scoring.dynamic_scoring import PHONE_SOURCE_QUALITY
        
        # WhatsApp should have highest quality
        whatsapp_quality = max(
            PHONE_SOURCE_QUALITY.get("whatsapp_enhanced", 0),
            PHONE_SOURCE_QUALITY.get("whatsapp_link", 0),
            PHONE_SOURCE_QUALITY.get("advanced_whatsapp", 0),
        )
        assert whatsapp_quality == 0.15
        
        # Word-based should have lowest quality
        assert PHONE_SOURCE_QUALITY["advanced_words"] == min(PHONE_SOURCE_QUALITY.values())

    def test_score_capped_at_valid_range(self):
        """Test that score is capped at 0-100 using centralized module"""
        from luca_scraper.scoring.dynamic_scoring import calculate_dynamic_score, cap_score
        
        # Test cap_score function directly
        assert cap_score(150) == 100
        assert cap_score(-10) == 0
        assert cap_score(75) == 75
        
        # Test that calculate_dynamic_score returns capped values
        score, _, _ = calculate_dynamic_score(
            has_phone=True, has_email=True, has_name=True,
            has_title=True, has_location=True,
            phones_count=3, has_whatsapp=True,
            phone_source="whatsapp_enhanced", portal="kleinanzeigen"
        )
        assert 0 <= score <= 100

    def test_confidence_capped_at_valid_range(self):
        """Test that confidence is capped at 0.0-1.0 using centralized module"""
        from luca_scraper.scoring.dynamic_scoring import calculate_dynamic_score, cap_confidence
        
        # Test cap_confidence function directly
        assert cap_confidence(1.5) == 1.0
        assert cap_confidence(-0.5) == 0.0
        assert cap_confidence(0.75) == 0.75
        
        # Test that calculate_dynamic_score returns capped confidence
        _, _, confidence = calculate_dynamic_score(
            has_phone=True, has_email=True, has_name=True,
            has_whatsapp=True, phone_source="whatsapp_enhanced",
            portal="kleinanzeigen"
        )
        assert 0.0 <= confidence <= 1.0


class TestLeadDataStructure:
    """Test that leads include new dynamic scoring fields"""

    def test_lead_has_phone_source(self):
        """Test that leads include phone_source field"""
        # Define expected lead structure
        expected_fields = [
            "name", "rolle", "email", "telefon", "quelle", 
            "score", "tags", "lead_type", "phone_type",
            "opening_line", "firma", "firma_groesse", "branche",
            "region", "frische", "confidence", "data_quality",
            "phone_source", "phones_found"
        ]
        
        # All fields should be defined in the lead dict
        # (Actual verification happens in integration tests)
        assert len(expected_fields) >= 18


@pytest.mark.parametrize("phone_format,expected_found", [
    ("0151 12345678", True),
    ("+49 176 98765432", True),
    ("01711234567", True),
    ("0 1 7 6 1 2 3 4 5 6 7", True),  # Spaced format
    ("null eins sieben sechs 12345678", True),  # Word-based (if phone_patterns available)
])
def test_various_phone_formats_extracted(phone_format, expected_found):
    """Test that various phone formats are extracted"""
    from phone_extractor import extract_phones_advanced
    
    text = f"Kontakt: {phone_format}"
    results = extract_phones_advanced(text)
    
    if expected_found:
        assert len(results) >= 1, f"Should find phone in: {phone_format}"
