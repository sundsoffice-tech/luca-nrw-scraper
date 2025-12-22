"""
Tests for parallel portal crawling functionality.
Tests the new parallel crawling implementation that processes all portals concurrently.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scriptname import (
    crawl_all_portals_parallel,
    crawl_portals_sequential,
    crawl_portals_smart,
    deduplicate_parallel_leads,
    crawl_kleinanzeigen_portal_async,
    PARALLEL_PORTAL_CRAWL,
)


def test_parallel_crawl_config():
    """Test that parallel crawl configuration variables exist."""
    # Just test that PARALLEL_PORTAL_CRAWL is accessible
    assert isinstance(PARALLEL_PORTAL_CRAWL, bool)


@pytest.mark.asyncio
async def test_deduplicate_removes_phone_duplicates():
    """Test that deduplicate_parallel_leads removes duplicate phone numbers."""
    leads = [
        {"name": "Max Müller", "telefon": "+49176123456", "quelle": "http://example1.com"},
        {"name": "Maria Schmidt", "telefon": "+49176123456", "quelle": "http://example2.com"},  # Duplicate phone
        {"name": "John Doe", "telefon": "+49176999999", "quelle": "http://example3.com"},
    ]
    
    result = deduplicate_parallel_leads(leads)
    
    assert len(result) == 2
    assert result[0]["telefon"] == "+49176123456"
    assert result[1]["telefon"] == "+49176999999"


@pytest.mark.asyncio
async def test_deduplicate_removes_url_duplicates():
    """Test that deduplicate_parallel_leads removes duplicate URLs."""
    leads = [
        {"name": "Max Müller", "telefon": "+49176111111", "quelle": "http://example.com/ad1"},
        {"name": "Maria Schmidt", "telefon": "+49176222222", "quelle": "http://example.com/ad1"},  # Duplicate URL
        {"name": "John Doe", "telefon": "+49176333333", "quelle": "http://example.com/ad2"},
    ]
    
    result = deduplicate_parallel_leads(leads)
    
    assert len(result) == 2
    assert result[0]["quelle"] == "http://example.com/ad1"
    assert result[1]["quelle"] == "http://example.com/ad2"


@pytest.mark.asyncio
async def test_deduplicate_keeps_unique_leads():
    """Test that deduplicate_parallel_leads keeps all unique leads."""
    leads = [
        {"name": "Max Müller", "telefon": "+49176111111", "quelle": "http://example.com/ad1"},
        {"name": "Maria Schmidt", "telefon": "+49176222222", "quelle": "http://example.com/ad2"},
        {"name": "John Doe", "telefon": "+49176333333", "quelle": "http://example.com/ad3"},
    ]
    
    result = deduplicate_parallel_leads(leads)
    
    assert len(result) == 3


@pytest.mark.asyncio
async def test_deduplicate_handles_empty_list():
    """Test that deduplicate_parallel_leads handles empty input."""
    result = deduplicate_parallel_leads([])
    assert result == []


@pytest.mark.asyncio
async def test_deduplicate_handles_missing_fields():
    """Test that deduplicate_parallel_leads handles leads with missing fields."""
    leads = [
        {"name": "Max Müller"},  # No phone or URL
        {"name": "Maria Schmidt", "telefon": "+49176111111"},  # No URL
        {"name": "John Doe", "quelle": "http://example.com/ad1"},  # No phone
    ]
    
    result = deduplicate_parallel_leads(leads)
    
    # All should be kept as they don't have duplicate identifying fields
    assert len(result) == 3


@pytest.mark.asyncio
async def test_parallel_crawl_merges_results():
    """Test that parallel crawling correctly merges results from multiple portals."""
    
    # Mock all portal crawlers to return test data
    kleinanzeigen_leads = [
        {"name": "Lead 1", "telefon": "+49176111111", "quelle": "http://kleinanzeigen.de/1"}
    ]
    markt_leads = [
        {"name": "Lead 2", "telefon": "+49176222222", "quelle": "http://markt.de/1"}
    ]
    quoka_leads = [
        {"name": "Lead 3", "telefon": "+49176333333", "quelle": "http://quoka.de/1"}
    ]
    
    with patch('scriptname.crawl_kleinanzeigen_portal_async', new_callable=AsyncMock) as mock_kleinanzeigen, \
         patch('scriptname.crawl_markt_de_listings_async', new_callable=AsyncMock) as mock_markt, \
         patch('scriptname.crawl_quoka_listings_async', new_callable=AsyncMock) as mock_quoka, \
         patch('scriptname.crawl_kalaydo_listings_async', new_callable=AsyncMock) as mock_kalaydo, \
         patch('scriptname.crawl_meinestadt_listings_async', new_callable=AsyncMock) as mock_meinestadt:
        
        mock_kleinanzeigen.return_value = kleinanzeigen_leads
        mock_markt.return_value = markt_leads
        mock_quoka.return_value = quoka_leads
        mock_kalaydo.return_value = []
        mock_meinestadt.return_value = []
        
        result = await crawl_all_portals_parallel()
        
        # Should have merged all results (3 leads, no duplicates)
        assert len(result) == 3
        assert any(lead["telefon"] == "+49176111111" for lead in result)
        assert any(lead["telefon"] == "+49176222222" for lead in result)
        assert any(lead["telefon"] == "+49176333333" for lead in result)


@pytest.mark.asyncio
async def test_parallel_crawl_handles_portal_failure():
    """Test that parallel crawling continues when one portal fails."""
    
    working_leads = [
        {"name": "Working Lead", "telefon": "+49176111111", "quelle": "http://example.com/1"}
    ]
    
    with patch('scriptname.crawl_kleinanzeigen_portal_async', new_callable=AsyncMock) as mock_kleinanzeigen, \
         patch('scriptname.crawl_markt_de_listings_async', new_callable=AsyncMock) as mock_markt, \
         patch('scriptname.crawl_quoka_listings_async', new_callable=AsyncMock) as mock_quoka, \
         patch('scriptname.crawl_kalaydo_listings_async', new_callable=AsyncMock) as mock_kalaydo, \
         patch('scriptname.crawl_meinestadt_listings_async', new_callable=AsyncMock) as mock_meinestadt:
        
        # One portal succeeds, others fail
        mock_kleinanzeigen.return_value = working_leads
        mock_markt.side_effect = Exception("Network error")
        mock_quoka.side_effect = Exception("Timeout")
        mock_kalaydo.return_value = []
        mock_meinestadt.return_value = []
        
        result = await crawl_all_portals_parallel()
        
        # Should still have the working lead
        assert len(result) == 1
        assert result[0]["telefon"] == "+49176111111"


@pytest.mark.asyncio
async def test_parallel_crawl_returns_empty_when_all_fail():
    """Test that parallel crawling returns empty list when all portals fail."""
    
    with patch('scriptname.crawl_kleinanzeigen_portal_async', new_callable=AsyncMock) as mock_kleinanzeigen, \
         patch('scriptname.crawl_markt_de_listings_async', new_callable=AsyncMock) as mock_markt, \
         patch('scriptname.crawl_quoka_listings_async', new_callable=AsyncMock) as mock_quoka, \
         patch('scriptname.crawl_kalaydo_listings_async', new_callable=AsyncMock) as mock_kalaydo, \
         patch('scriptname.crawl_meinestadt_listings_async', new_callable=AsyncMock) as mock_meinestadt:
        
        # All portals fail
        mock_kleinanzeigen.side_effect = Exception("Error")
        mock_markt.side_effect = Exception("Error")
        mock_quoka.side_effect = Exception("Error")
        mock_kalaydo.side_effect = Exception("Error")
        mock_meinestadt.side_effect = Exception("Error")
        
        result = await crawl_all_portals_parallel()
        
        # Should return empty list
        assert result == []


@pytest.mark.asyncio
async def test_parallel_crawl_deduplicates_results():
    """Test that parallel crawling removes duplicates from merged results."""
    
    # Same lead from multiple portals (simulating duplicate)
    duplicate_lead_1 = {"name": "Duplicate", "telefon": "+49176111111", "quelle": "http://example.com/1"}
    duplicate_lead_2 = {"name": "Duplicate Same", "telefon": "+49176111111", "quelle": "http://example.com/2"}
    unique_lead = {"name": "Unique", "telefon": "+49176222222", "quelle": "http://example.com/3"}
    
    with patch('scriptname.crawl_kleinanzeigen_portal_async', new_callable=AsyncMock) as mock_kleinanzeigen, \
         patch('scriptname.crawl_markt_de_listings_async', new_callable=AsyncMock) as mock_markt, \
         patch('scriptname.crawl_quoka_listings_async', new_callable=AsyncMock) as mock_quoka, \
         patch('scriptname.crawl_kalaydo_listings_async', new_callable=AsyncMock) as mock_kalaydo, \
         patch('scriptname.crawl_meinestadt_listings_async', new_callable=AsyncMock) as mock_meinestadt:
        
        mock_kleinanzeigen.return_value = [duplicate_lead_1, unique_lead]
        mock_markt.return_value = [duplicate_lead_2]  # Duplicate phone
        mock_quoka.return_value = []
        mock_kalaydo.return_value = []
        mock_meinestadt.return_value = []
        
        result = await crawl_all_portals_parallel()
        
        # Should have 2 leads (duplicate removed)
        assert len(result) == 2


@pytest.mark.asyncio
async def test_sequential_crawl_works():
    """Test that sequential crawling fallback works correctly."""
    
    leads = [
        {"name": "Lead 1", "telefon": "+49176111111", "quelle": "http://example.com/1"}
    ]
    
    with patch('scriptname.crawl_kleinanzeigen_portal_async', new_callable=AsyncMock) as mock_kleinanzeigen, \
         patch('scriptname.crawl_markt_de_listings_async', new_callable=AsyncMock) as mock_markt, \
         patch('scriptname.crawl_quoka_listings_async', new_callable=AsyncMock) as mock_quoka, \
         patch('scriptname.crawl_kalaydo_listings_async', new_callable=AsyncMock) as mock_kalaydo, \
         patch('scriptname.crawl_meinestadt_listings_async', new_callable=AsyncMock) as mock_meinestadt:
        
        mock_kleinanzeigen.return_value = leads
        mock_markt.return_value = []
        mock_quoka.return_value = []
        mock_kalaydo.return_value = []
        mock_meinestadt.return_value = []
        
        result = await crawl_portals_sequential()
        
        assert len(result) == 1
        assert result[0]["telefon"] == "+49176111111"


@pytest.mark.asyncio
async def test_smart_crawl_uses_parallel_when_enabled():
    """Test that smart crawling uses parallel mode when enabled."""
    
    with patch('scriptname.PARALLEL_PORTAL_CRAWL', True), \
         patch('scriptname.crawl_all_portals_parallel', new_callable=AsyncMock) as mock_parallel:
        
        mock_parallel.return_value = []
        
        await crawl_portals_smart()
        
        # Should have called parallel
        mock_parallel.assert_called_once()


@pytest.mark.asyncio
async def test_smart_crawl_fallback_on_parallel_error():
    """Test that smart crawling falls back to sequential on parallel error."""
    
    with patch('scriptname.PARALLEL_PORTAL_CRAWL', True), \
         patch('scriptname.crawl_all_portals_parallel', new_callable=AsyncMock) as mock_parallel, \
         patch('scriptname.crawl_portals_sequential', new_callable=AsyncMock) as mock_sequential:
        
        mock_parallel.side_effect = Exception("Parallel failed")
        mock_sequential.return_value = []
        
        result = await crawl_portals_smart()
        
        # Should have tried parallel and fallen back to sequential
        mock_parallel.assert_called_once()
        mock_sequential.assert_called_once()


@pytest.mark.asyncio
async def test_kleinanzeigen_portal_wrapper_disabled():
    """Test that kleinanzeigen wrapper returns empty when disabled."""
    
    with patch.dict('scriptname.DIRECT_CRAWL_SOURCES', {"kleinanzeigen": False}):
        result = await crawl_kleinanzeigen_portal_async()
        assert result == []


@pytest.mark.asyncio
async def test_kleinanzeigen_portal_wrapper_respects_enable_flag():
    """Test that kleinanzeigen wrapper respects ENABLE_KLEINANZEIGEN flag."""
    
    with patch('scriptname.ENABLE_KLEINANZEIGEN', False):
        result = await crawl_kleinanzeigen_portal_async()
        assert result == []


@pytest.mark.asyncio
async def test_parallel_crawl_respects_source_config():
    """Test that parallel crawling only calls enabled portals."""
    
    # Disable some portals
    with patch.dict('scriptname.DIRECT_CRAWL_SOURCES', {
        "kleinanzeigen": True,
        "markt_de": False,  # Disabled
        "quoka": True,
        "kalaydo": False,  # Disabled
        "meinestadt": True,
    }), \
         patch('scriptname.crawl_kleinanzeigen_portal_async', new_callable=AsyncMock) as mock_kleinanzeigen, \
         patch('scriptname.crawl_markt_de_listings_async', new_callable=AsyncMock) as mock_markt, \
         patch('scriptname.crawl_quoka_listings_async', new_callable=AsyncMock) as mock_quoka, \
         patch('scriptname.crawl_kalaydo_listings_async', new_callable=AsyncMock) as mock_kalaydo, \
         patch('scriptname.crawl_meinestadt_listings_async', new_callable=AsyncMock) as mock_meinestadt:
        
        mock_kleinanzeigen.return_value = []
        mock_markt.return_value = []
        mock_quoka.return_value = []
        mock_kalaydo.return_value = []
        mock_meinestadt.return_value = []
        
        await crawl_all_portals_parallel()
        
        # Should only call enabled portals
        mock_kleinanzeigen.assert_called_once()
        mock_markt.assert_not_called()  # Disabled
        mock_quoka.assert_called_once()
        mock_kalaydo.assert_not_called()  # Disabled
        mock_meinestadt.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
