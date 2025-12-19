import pytest
import asyncio
import json
from scriptname import (
    _looks_like_company_name,
    should_accept_enrichment,
    get_cached_telefonbuch_result,
    cache_telefonbuch_result,
    enrich_leads_with_telefonbuch,
    normalize_phone,
)


def test_looks_like_company_name():
    """Test company name detection."""
    # Should be detected as company
    assert _looks_like_company_name("Vertrieb GmbH") is True
    assert _looks_like_company_name("Sales Team") is True
    assert _looks_like_company_name("Musterfirma AG") is True
    assert _looks_like_company_name("Test KG") is True
    assert _looks_like_company_name("OnlyOneWord") is True
    assert _looks_like_company_name("Test123") is True
    
    # Should NOT be detected as company (real names)
    assert _looks_like_company_name("Max Mustermann") is False
    assert _looks_like_company_name("Anna Maria Schmidt") is False
    assert _looks_like_company_name("Dr. Hans Meier") is False
    assert _looks_like_company_name("Mehmet Yılmaz") is False


def test_should_accept_enrichment_no_results():
    """Test rejection when no results."""
    accept, result, reason = should_accept_enrichment(
        "Max Mustermann",
        "Düsseldorf",
        []
    )
    assert accept is False
    assert result is None
    assert "Keine Treffer" in reason


def test_should_accept_enrichment_multiple_results():
    """Test rejection when multiple results in strict mode."""
    results = [
        {"name": "Max Mustermann", "phone": "+491761234567", "city": "Düsseldorf"},
        {"name": "Max Mustermann", "phone": "+491769876543", "city": "Düsseldorf"},
    ]
    
    accept, result, reason = should_accept_enrichment(
        "Max Mustermann",
        "Düsseldorf",
        results
    )
    assert accept is False
    assert result is None
    assert "Mehrere Treffer" in reason


def test_should_accept_enrichment_name_mismatch():
    """Test rejection when name doesn't match."""
    results = [
        {"name": "Peter Schmidt", "phone": "+491761234567", "city": "Düsseldorf"},
    ]
    
    accept, result, reason = should_accept_enrichment(
        "Max Mustermann",
        "Düsseldorf",
        results
    )
    assert accept is False
    assert result is None
    assert "Name-Mismatch" in reason


def test_should_accept_enrichment_city_mismatch():
    """Test rejection when city doesn't match."""
    results = [
        {"name": "Max Mustermann", "phone": "+491761234567", "city": "Berlin"},
    ]
    
    accept, result, reason = should_accept_enrichment(
        "Max Mustermann",
        "Düsseldorf",
        results
    )
    assert accept is False
    assert result is None
    assert "Stadt-Mismatch" in reason


def test_should_accept_enrichment_not_mobile():
    """Test rejection when phone is not mobile."""
    results = [
        {"name": "Max Mustermann", "phone": "0211123456", "city": "Düsseldorf"},
    ]
    
    accept, result, reason = should_accept_enrichment(
        "Max Mustermann",
        "Düsseldorf",
        results
    )
    assert accept is False
    assert result is None
    assert "Keine Mobilnummer" in reason


def test_should_accept_enrichment_valid():
    """Test acceptance with valid result."""
    results = [
        {
            "name": "Max Mustermann",
            "phone": "0176 1234567",
            "address": "Musterstraße 1",
            "city": "Düsseldorf"
        },
    ]
    
    accept, result, reason = should_accept_enrichment(
        "Max Mustermann",
        "Düsseldorf",
        results
    )
    assert accept is True
    assert result is not None
    assert result["name"] == "Max Mustermann"
    assert "Akzeptiert" in reason


def test_should_accept_enrichment_name_variations():
    """Test acceptance with name variations (titles, etc)."""
    results = [
        {
            "name": "Dr. Max Mustermann",
            "phone": "+491761234567",
            "city": "Düsseldorf"
        },
    ]
    
    # Should match even with title difference
    accept, result, reason = should_accept_enrichment(
        "Max Mustermann",
        "Düsseldorf",
        results
    )
    assert accept is True
    assert result is not None


@pytest.mark.asyncio
async def test_cache_telefonbuch_result():
    """Test caching mechanism."""
    test_name = "Test Person"
    test_city = "Test Stadt"
    test_results = [
        {"name": "Test Person", "phone": "+491761234567", "city": "Test Stadt"}
    ]
    
    # Cache the result
    await cache_telefonbuch_result(test_name, test_city, test_results)
    
    # Retrieve from cache
    cached = await get_cached_telefonbuch_result(test_name, test_city)
    
    assert cached is not None
    assert len(cached) == 1
    assert cached[0]["name"] == "Test Person"
    assert cached[0]["phone"] == "+491761234567"


@pytest.mark.asyncio
async def test_enrich_leads_with_telefonbuch_skip_company():
    """Test that company names are skipped."""
    leads = [
        {
            "name": "Vertrieb GmbH",
            "region": "Düsseldorf",
            "quelle": "https://example.com"
        }
    ]
    
    enriched = await enrich_leads_with_telefonbuch(leads)
    
    # Should not be enriched (company name)
    assert enriched[0].get("telefon") is None
    assert "telefonbuch_enriched" not in enriched[0].get("tags", "")


@pytest.mark.asyncio
async def test_enrich_leads_with_telefonbuch_skip_has_phone():
    """Test that leads with phone are not enriched."""
    leads = [
        {
            "name": "Max Mustermann",
            "region": "Düsseldorf",
            "telefon": "+491761234567",
            "quelle": "https://example.com"
        }
    ]
    
    enriched = await enrich_leads_with_telefonbuch(leads)
    
    # Should not be enriched (already has phone)
    assert enriched[0]["telefon"] == "+491761234567"
    assert "telefonbuch_enriched" not in enriched[0].get("tags", "")


@pytest.mark.asyncio
async def test_enrich_leads_with_telefonbuch_missing_name_or_city():
    """Test that leads without name or city are not enriched."""
    leads = [
        {
            "name": "Max Mustermann",
            # No region
            "quelle": "https://example.com"
        },
        {
            # No name
            "region": "Düsseldorf",
            "quelle": "https://example.com"
        }
    ]
    
    enriched = await enrich_leads_with_telefonbuch(leads)
    
    # Should not be enriched (missing data)
    assert enriched[0].get("telefon") is None
    assert enriched[1].get("telefon") is None
