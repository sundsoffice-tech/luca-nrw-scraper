"""
Integration test for telefonbuch enrichment flow.
Tests the complete enrichment pipeline from leads without phone to enriched leads.
"""
import pytest
import asyncio
from scriptname import (
    enrich_leads_with_telefonbuch,
    insert_leads,
    TELEFONBUCH_ENRICHMENT_ENABLED,
)


@pytest.mark.asyncio
async def test_enrichment_flow_with_mock_data():
    """
    Test the complete enrichment flow with mock data.
    This simulates what happens in the actual scraper pipeline.
    """
    # Create test leads without phone numbers
    leads_without_phone = [
        {
            "name": "Max Mustermann",
            "region": "Düsseldorf",
            "email": "max@example.com",
            "quelle": "https://example.com/max",
            "score": 75,
            "tags": "test",
        },
        {
            "name": "Vertrieb GmbH",  # This should be skipped (company name)
            "region": "Köln",
            "email": "info@vertrieb.de",
            "quelle": "https://example.com/vertrieb",
            "score": 80,
            "tags": "test",
        },
        {
            "name": "Anna Schmidt",
            "region": "Essen",
            "telefon": "+491761234567",  # Already has phone
            "email": "anna@example.com",
            "quelle": "https://example.com/anna",
            "score": 85,
            "tags": "test",
        },
    ]
    
    # Run enrichment
    enriched_leads = await enrich_leads_with_telefonbuch(leads_without_phone)
    
    # Verify results
    assert len(enriched_leads) == 3
    
    # Lead 1: Max Mustermann - should be attempted for enrichment
    # (will not find phone in real query, but structure should be correct)
    lead1 = enriched_leads[0]
    assert lead1["name"] == "Max Mustermann"
    assert lead1["region"] == "Düsseldorf"
    # Note: In real execution, this might get enriched if found in dasoertliche.de
    
    # Lead 2: Vertrieb GmbH - should be skipped (company)
    lead2 = enriched_leads[1]
    assert lead2["name"] == "Vertrieb GmbH"
    assert lead2.get("telefon") is None  # Should not be enriched
    assert "telefonbuch_enriched" not in lead2.get("tags", "")
    
    # Lead 3: Anna Schmidt - should not be enriched (already has phone)
    lead3 = enriched_leads[2]
    assert lead3["name"] == "Anna Schmidt"
    assert lead3["telefon"] == "+491761234567"
    assert "telefonbuch_enriched" not in lead3.get("tags", "")


@pytest.mark.asyncio
async def test_enrichment_disabled():
    """Test that enrichment is skipped when disabled."""
    import scriptname
    
    # Save original state
    original_enabled = scriptname.TELEFONBUCH_ENRICHMENT_ENABLED
    
    try:
        # Disable enrichment
        scriptname.TELEFONBUCH_ENRICHMENT_ENABLED = False
        
        leads = [
            {
                "name": "Test Person",
                "region": "Test Stadt",
                "email": "test@example.com",
                "quelle": "https://example.com/test",
                "score": 75,
            }
        ]
        
        enriched = await enrich_leads_with_telefonbuch(leads)
        
        # Should return unchanged
        assert len(enriched) == 1
        assert enriched[0].get("telefon") is None
        assert "telefonbuch_enriched" not in enriched[0].get("tags", "")
        
    finally:
        # Restore original state
        scriptname.TELEFONBUCH_ENRICHMENT_ENABLED = original_enabled


def test_enrichment_configuration():
    """Test that enrichment configuration is properly loaded."""
    import scriptname
    
    # Check that all config variables exist
    assert hasattr(scriptname, 'TELEFONBUCH_ENRICHMENT_ENABLED')
    assert hasattr(scriptname, 'TELEFONBUCH_STRICT_MODE')
    assert hasattr(scriptname, 'TELEFONBUCH_RATE_LIMIT')
    assert hasattr(scriptname, 'TELEFONBUCH_CACHE_DAYS')
    assert hasattr(scriptname, 'TELEFONBUCH_MOBILE_ONLY')
    
    # Check default values
    assert isinstance(scriptname.TELEFONBUCH_ENRICHMENT_ENABLED, bool)
    assert isinstance(scriptname.TELEFONBUCH_STRICT_MODE, bool)
    assert isinstance(scriptname.TELEFONBUCH_RATE_LIMIT, float)
    assert isinstance(scriptname.TELEFONBUCH_CACHE_DAYS, int)
    assert isinstance(scriptname.TELEFONBUCH_MOBILE_ONLY, bool)
    
    # Check reasonable defaults
    assert scriptname.TELEFONBUCH_RATE_LIMIT >= 1.0  # At least 1 second
    assert scriptname.TELEFONBUCH_CACHE_DAYS >= 1  # At least 1 day


@pytest.mark.asyncio
async def test_enrichment_preserves_existing_fields():
    """Test that enrichment doesn't overwrite existing lead fields."""
    leads = [
        {
            "name": "Test Person",
            "region": "Test Stadt",
            "email": "test@example.com",
            "quelle": "https://example.com/test",
            "score": 85,
            "tags": "existing_tag",
            "company_name": "Test Company",
            "role_guess": "Sales Manager",
        }
    ]
    
    enriched = await enrich_leads_with_telefonbuch(leads)
    
    # All original fields should be preserved
    assert enriched[0]["name"] == "Test Person"
    assert enriched[0]["region"] == "Test Stadt"
    assert enriched[0]["email"] == "test@example.com"
    assert enriched[0]["score"] == 85
    assert enriched[0]["company_name"] == "Test Company"
    assert enriched[0]["role_guess"] == "Sales Manager"
    
    # If phone is added, tags should be appended, not replaced
    if enriched[0].get("telefon"):
        assert "existing_tag" in enriched[0]["tags"]
        assert "telefonbuch_enriched" in enriched[0]["tags"]


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test that rate limiter delays requests properly."""
    import time
    from scriptname import _TelefonbuchRateLimiter
    
    # Create a fast rate limiter for testing (0.5 seconds)
    rate_limiter = _TelefonbuchRateLimiter(interval=0.5)
    
    times = []
    
    # Make 3 sequential requests
    for _ in range(3):
        async with rate_limiter:
            times.append(time.time())
    
    # Check that requests were spaced out
    if len(times) >= 2:
        delay1 = times[1] - times[0]
        assert delay1 >= 0.4  # Should be at least 0.4s (allowing for some timing variance)
    
    if len(times) >= 3:
        delay2 = times[2] - times[1]
        assert delay2 >= 0.4


def test_database_schema_includes_cache_table():
    """Verify that the database schema includes the telefonbuch_cache table."""
    import sqlite3
    import scriptname
    
    # Initialize database
    scriptname.init_db()
    
    # Check if table exists
    con = sqlite3.connect(scriptname.DB_PATH)
    cur = con.cursor()
    
    cur.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='telefonbuch_cache'
    """)
    
    result = cur.fetchone()
    con.close()
    
    assert result is not None, "telefonbuch_cache table should exist"
    assert result[0] == "telefonbuch_cache"
