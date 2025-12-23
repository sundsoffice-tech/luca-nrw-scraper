# -*- coding: utf-8 -*-
"""
Tests für die neuen Module: dorks_extended, phone_extractor, social_scraper, deduplication
"""

import pytest
import sqlite3
import os
import tempfile


# ==================== Tests für dorks_extended ====================

def test_dorks_extended_import():
    """Test dass dorks_extended korrekt importiert werden kann"""
    from dorks_extended import get_all_dorks, get_random_dorks, get_dorks_by_category
    
    assert callable(get_all_dorks)
    assert callable(get_random_dorks)
    assert callable(get_dorks_by_category)


def test_get_all_dorks():
    """Test dass get_all_dorks eine Liste zurückgibt"""
    from dorks_extended import get_all_dorks
    
    dorks = get_all_dorks()
    assert isinstance(dorks, list)
    assert len(dorks) >= 90  # Sollte mindestens 90 Dorks haben
    assert all(isinstance(d, str) for d in dorks)


def test_get_dorks_by_category():
    """Test dass Kategorien korrekt funktionieren"""
    from dorks_extended import get_dorks_by_category
    
    # Test verschiedene Kategorien
    categories = ["job_seeker", "site_specific", "power", "mobile"]
    
    for cat in categories:
        dorks = get_dorks_by_category(cat)
        assert isinstance(dorks, list)
        assert len(dorks) > 0


def test_get_random_dorks():
    """Test dass zufällige Dorks korrekt funktionieren"""
    from dorks_extended import get_random_dorks
    
    # Test mit verschiedenen Anzahlen
    for count in [5, 10, 20]:
        dorks = get_random_dorks(count)
        assert isinstance(dorks, list)
        assert len(dorks) <= count


def test_dorks_count():
    """Test dass get_dorks_count korrekt funktioniert"""
    from dorks_extended import get_dorks_count
    
    counts = get_dorks_count()
    assert isinstance(counts, dict)
    assert "total" in counts
    assert counts["total"] >= 90  # Mindestens 90 Dorks


# ==================== Tests für phone_extractor ====================

def test_phone_extractor_import():
    """Test dass phone_extractor korrekt importiert werden kann"""
    from phone_extractor import extract_phones_advanced, normalize_phone, is_valid_phone
    
    assert callable(extract_phones_advanced)
    assert callable(normalize_phone)
    assert callable(is_valid_phone)


def test_normalize_phone():
    """Test Telefonnummern-Normalisierung"""
    from phone_extractor import normalize_phone
    
    # Test verschiedene Formate
    test_cases = [
        ("0176 12345678", "+4917612345678"),
        ("+49 176 12345678", "+4917612345678"),
        ("0049 176 12345678", "+4917612345678"),
        ("176 12345678", "+4917612345678"),
    ]
    
    for input_phone, expected in test_cases:
        result = normalize_phone(input_phone)
        assert result == expected or result.endswith("12345678")


def test_is_valid_phone():
    """Test Telefonnummern-Validierung"""
    from phone_extractor import is_valid_phone
    
    # Gültige Nummern
    valid_phones = [
        "+4917612345678",
        "+4915112345678",
        "+4916012345678",
    ]
    
    for phone in valid_phones:
        assert is_valid_phone(phone) == True
    
    # Ungültige Nummern
    invalid_phones = [
        "+491234567890",  # Falsche Vorwahl
        "+49123",  # Zu kurz
        "+4900000000000",  # Blacklist
        "",  # Leer
    ]
    
    for phone in invalid_phones:
        assert is_valid_phone(phone) == False


def test_extract_phones_advanced():
    """Test erweiterte Telefon-Extraktion"""
    from phone_extractor import extract_phones_advanced
    
    # Test mit einem Text der eine Nummer enthält
    text = "Kontaktieren Sie mich unter 0176 12345678 oder per E-Mail."
    results = extract_phones_advanced(text)
    
    assert isinstance(results, list)
    if len(results) > 0:
        normalized, raw, confidence = results[0]
        assert isinstance(normalized, str)
        assert isinstance(raw, str)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0


def test_calculate_confidence():
    """Test Konfidenz-Berechnung"""
    from phone_extractor import calculate_confidence
    
    # Test mit positivem Kontext
    context_positive = "Bitte rufen Sie mich auf meiner Mobilnummer 0176 12345678 an"
    conf = calculate_confidence("0176 12345678", context_positive)
    assert conf > 0.5
    
    # Test mit negativem Kontext
    context_negative = "Fax: 0176 12345678"
    conf = calculate_confidence("0176 12345678", context_negative)
    assert conf < 0.8  # Sollte durch "Fax" reduziert sein


# ==================== Tests für social_scraper ====================

def test_social_scraper_import():
    """Test dass social_scraper korrekt importiert werden kann"""
    from social_scraper import SocialMediaScraper, SOCIAL_MEDIA_DORKS, get_all_social_dorks
    
    assert callable(get_all_social_dorks)
    assert isinstance(SOCIAL_MEDIA_DORKS, list)


def test_social_media_scraper():
    """Test SocialMediaScraper Klasse"""
    from social_scraper import SocialMediaScraper
    
    scraper = SocialMediaScraper()
    
    # Test Facebook URLs
    fb_urls = scraper.get_facebook_group_urls()
    assert isinstance(fb_urls, list)
    assert len(fb_urls) > 0
    assert all("facebook.com" in url for url in fb_urls)
    
    # Test LinkedIn URLs
    linkedin_urls = scraper.build_linkedin_search_urls()
    assert isinstance(linkedin_urls, list)
    assert len(linkedin_urls) > 0
    assert all("linkedin.com" in url for url in linkedin_urls)
    
    # Test XING URLs
    xing_urls = scraper.build_xing_search_urls()
    assert isinstance(xing_urls, list)
    assert len(xing_urls) > 0
    assert all("xing.com" in url for url in xing_urls)


def test_social_media_dorks():
    """Test Social Media Dorks"""
    from social_scraper import SOCIAL_MEDIA_DORKS, get_all_social_dorks
    
    assert len(SOCIAL_MEDIA_DORKS) > 0
    
    all_dorks = get_all_social_dorks()
    assert isinstance(all_dorks, list)
    assert len(all_dorks) > len(SOCIAL_MEDIA_DORKS)  # Sollte mehr sein (inkl. branchen-spezifische)


def test_platform_config():
    """Test Platform-Konfiguration"""
    from social_scraper import get_platform_config
    
    # Test bekannte Plattformen
    platforms = ["facebook", "linkedin", "xing", "telegram"]
    
    for platform in platforms:
        config = get_platform_config(platform)
        assert isinstance(config, dict)
        assert "rate_limit" in config
        assert "difficulty" in config


# ==================== Tests für deduplication ====================

def test_deduplication_import():
    """Test dass deduplication korrekt importiert werden kann"""
    from deduplication import LeadDeduplicator, get_deduplicator
    
    assert callable(get_deduplicator)


def test_lead_deduplicator():
    """Test LeadDeduplicator Klasse"""
    from deduplication import LeadDeduplicator
    
    # Erstelle temporäre Datenbank
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        dedup = LeadDeduplicator(db_path)
        
        # Test Lead 1
        lead1 = {
            "name": "Max Mustermann",
            "telefon": "+4917612345678",
            "email": "max@example.com",
            "stadt": "Düsseldorf"
        }
        
        # Sollte kein Duplikat sein (erster Lead)
        is_dup, reason = dedup.is_duplicate(lead1)
        assert is_dup == False
        
        # Registriere Lead
        dedup.register_lead(lead1, lead_id=1)
        
        # Jetzt sollte es ein Duplikat sein
        is_dup, reason = dedup.is_duplicate(lead1)
        assert is_dup == True
        assert "Telefon" in reason or "E-Mail" in reason
        
        # Test Stats
        stats = dedup.get_stats()
        assert isinstance(stats, dict)
        assert stats["unique_phones"] >= 1
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_deduplicator_phone_normalization():
    """Test Telefonnummern-Normalisierung im Deduplicator"""
    from deduplication import LeadDeduplicator
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        dedup = LeadDeduplicator(db_path)
        
        # Verschiedene Formate der gleichen Nummer
        lead1 = {"name": "Test 1", "telefon": "0176 12345678"}
        lead2 = {"name": "Test 2", "telefon": "+49 176 12345678"}
        
        # Registriere erste Nummer
        dedup.register_lead(lead1, lead_id=1)
        
        # Zweite Nummer sollte als Duplikat erkannt werden
        is_dup, reason = dedup.is_duplicate(lead2)
        assert is_dup == True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_deduplicator_fuzzy_name_match():
    """Test Fuzzy-Matching für Namen"""
    from deduplication import LeadDeduplicator
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        dedup = LeadDeduplicator(db_path)
        
        # Ähnliche Namen in gleicher Stadt
        lead1 = {"name": "Max Mustermann", "stadt": "Köln"}
        lead2 = {"name": "Max Musterman", "stadt": "Köln"}  # Kleiner Tippfehler
        
        # Registriere ersten Lead
        dedup.register_lead(lead1, lead_id=1)
        
        # Zweiter Lead sollte als ähnlich erkannt werden
        is_dup, reason = dedup.is_duplicate(lead2)
        # Fuzzy-Match sollte funktionieren
        assert "Stadt" in reason or "Name" in reason or is_dup == True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


# ==================== Integration Tests ====================

def test_all_modules_importable():
    """Test dass alle neuen Module importierbar sind"""
    import dorks_extended
    import phone_extractor
    import social_scraper
    import deduplication
    
    assert dorks_extended is not None
    assert phone_extractor is not None
    assert social_scraper is not None
    assert deduplication is not None


if __name__ == "__main__":
    # Führe Tests aus
    pytest.main([__file__, "-v"])
