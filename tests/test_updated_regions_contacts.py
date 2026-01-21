"""Tests for updated NRW_REGIONS and CONTACT patterns."""

import pytest
from luca_scraper import NRW_REGIONS, CONTACT


def test_nrw_regions_contains_bundeslaender():
    """Test that NRW_REGIONS now includes all German Bundesländer."""
    # Check original NRW regions are still present
    assert "nrw" in NRW_REGIONS
    assert "düsseldorf" in NRW_REGIONS
    assert "köln" in NRW_REGIONS
    
    # Check new Bundesländer are added
    assert "baden-württemberg" in NRW_REGIONS
    assert "bayern" in NRW_REGIONS
    assert "berlin" in NRW_REGIONS
    assert "brandenburg" in NRW_REGIONS
    assert "bremen" in NRW_REGIONS
    assert "hamburg" in NRW_REGIONS
    assert "hessen" in NRW_REGIONS
    assert "mecklenburg-vorpommern" in NRW_REGIONS
    assert "niedersachsen" in NRW_REGIONS
    assert "rheinland-pfalz" in NRW_REGIONS
    assert "saarland" in NRW_REGIONS
    assert "sachsen" in NRW_REGIONS
    assert "sachsen-anhalt" in NRW_REGIONS
    assert "schleswig-holstein" in NRW_REGIONS
    assert "thüringen" in NRW_REGIONS


def test_nrw_regions_contains_major_cities():
    """Test that NRW_REGIONS includes major cities from other Bundesländer."""
    # Check some major cities from different states
    assert "münchen" in NRW_REGIONS  # Bayern
    assert "stuttgart" in NRW_REGIONS  # Baden-Württemberg
    assert "frankfurt" in NRW_REGIONS  # Hessen
    assert "hannover" in NRW_REGIONS  # Niedersachsen
    assert "leipzig" in NRW_REGIONS  # Sachsen
    assert "dresden" in NRW_REGIONS  # Sachsen


def test_nrw_regions_contains_plz_areas():
    """Test that NRW_REGIONS includes PLZ (postal code) areas."""
    # Check PLZ areas 0-9
    assert "plz 0" in NRW_REGIONS
    assert "plz 1" in NRW_REGIONS
    assert "plz 2" in NRW_REGIONS
    assert "plz 3" in NRW_REGIONS
    assert "plz 4" in NRW_REGIONS
    assert "plz 5" in NRW_REGIONS
    assert "plz 6" in NRW_REGIONS
    assert "plz 7" in NRW_REGIONS
    assert "plz 8" in NRW_REGIONS
    assert "plz 9" in NRW_REGIONS


def test_contact_pattern_includes_modern_apps():
    """Test that CONTACT pattern includes modern communication apps."""
    # Check original contact methods are still present
    assert "kontakt" in CONTACT
    assert "email" in CONTACT
    assert "telefon" in CONTACT
    assert "whatsapp" in CONTACT
    
    # Check new communication apps are added
    assert "signal" in CONTACT
    assert "telegram" in CONTACT


def test_contact_pattern_is_valid_search_syntax():
    """Test that CONTACT pattern is valid search query syntax."""
    # Should start with ( and end with )
    assert CONTACT.startswith("(")
    assert CONTACT.endswith(")")
    
    # Should contain OR operators
    assert " OR " in CONTACT


def test_nrw_regions_is_list():
    """Test that NRW_REGIONS is a list for random selection."""
    assert isinstance(NRW_REGIONS, list)
    assert len(NRW_REGIONS) > 0


def test_nrw_regions_expanded_properly():
    """Test that NRW_REGIONS has been expanded with new entries."""
    # Original list had about 30 entries, new list should have significantly more
    # With Bundesländer (16), major cities (~30), and PLZ areas (10), 
    # total should be around 85+ entries
    assert len(NRW_REGIONS) >= 75, f"Expected at least 75 regions, got {len(NRW_REGIONS)}"
