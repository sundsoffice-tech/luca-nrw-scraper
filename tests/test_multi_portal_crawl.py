"""
Test for multi-portal direct crawling functionality.
Tests Markt.de, Quoka.de, Kalaydo.de, and Meinestadt.de crawlers.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scriptname import (
    crawl_markt_de_listings_async,
    crawl_quoka_listings_async,
    crawl_kalaydo_listings_async,
    crawl_meinestadt_listings_async,
    extract_generic_detail_async,
    MARKT_DE_URLS,
    QUOKA_DE_URLS,
    KALAYDO_DE_URLS,
    MEINESTADT_DE_URLS,
    DIRECT_CRAWL_SOURCES,
)


def test_url_constants_defined():
    """Test that all URL constants are properly defined."""
    assert isinstance(MARKT_DE_URLS, list)
    assert len(MARKT_DE_URLS) > 0
    assert all("markt.de" in url for url in MARKT_DE_URLS)
    
    assert isinstance(QUOKA_DE_URLS, list)
    assert len(QUOKA_DE_URLS) > 0
    assert all("quoka.de" in url for url in QUOKA_DE_URLS)
    
    assert isinstance(KALAYDO_DE_URLS, list)
    assert len(KALAYDO_DE_URLS) > 0
    assert all("kalaydo.de" in url for url in KALAYDO_DE_URLS)
    
    assert isinstance(MEINESTADT_DE_URLS, list)
    assert len(MEINESTADT_DE_URLS) > 0
    assert all("meinestadt.de" in url for url in MEINESTADT_DE_URLS)


def test_source_configuration():
    """Test that DIRECT_CRAWL_SOURCES configuration exists."""
    assert isinstance(DIRECT_CRAWL_SOURCES, dict)
    assert "kleinanzeigen" in DIRECT_CRAWL_SOURCES
    assert "markt_de" in DIRECT_CRAWL_SOURCES
    assert "quoka" in DIRECT_CRAWL_SOURCES
    assert "kalaydo" in DIRECT_CRAWL_SOURCES
    assert "meinestadt" in DIRECT_CRAWL_SOURCES


@pytest.mark.asyncio
async def test_extract_generic_detail_with_mobile():
    """Test extract_generic_detail_async with mobile number."""
    
    mock_html = """
    <html>
        <body>
            <h1>Vertriebsprofi sucht neue Position</h1>
            <div class="description">
                Erfahrener Vertriebsmitarbeiter sucht neue Herausforderung.
                Kontakt: 0176 98765432
                E-Mail: test@example.com
            </div>
        </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch('scriptname.http_get_async', new_callable=AsyncMock) as mock_http:
        mock_http.return_value = mock_response
        
        result = await extract_generic_detail_async(
            "https://www.example.com/test",
            source_tag="test_portal"
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert result.get("telefon")
        assert result.get("lead_type") == "candidate"
        assert result.get("phone_type") == "mobile"
        assert "test_portal" in result.get("tags", "")
        assert "direct_crawl" in result.get("tags", "")


@pytest.mark.asyncio
async def test_extract_generic_detail_no_mobile():
    """Test that extraction returns None when no mobile number is found."""
    
    mock_html = """
    <html>
        <body>
            <h1>Vertriebsprofi sucht Job</h1>
            <div>Nur Festnetz: 0211 123456</div>
        </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch('scriptname.http_get_async', new_callable=AsyncMock) as mock_http:
        mock_http.return_value = mock_response
        
        result = await extract_generic_detail_async(
            "https://www.example.com/test",
            source_tag="test_portal"
        )
        
        # Should return None since no mobile number found
        assert result is None


@pytest.mark.asyncio
async def test_crawl_markt_de_disabled():
    """Test that crawl_markt_de_listings_async returns empty list when disabled."""
    
    with patch.dict('scriptname.DIRECT_CRAWL_SOURCES', {"markt_de": False}):
        result = await crawl_markt_de_listings_async()
        assert result == []


@pytest.mark.asyncio
async def test_crawl_markt_de_mock():
    """Test crawl_markt_de_listings_async with mocked response."""
    
    # Mock listing page
    mock_listing_html = """
    <html>
        <body>
            <div class="ad-list-item">
                <a href="/anzeige/vertrieb-sales-12345">Vertrieb gesucht</a>
            </div>
            <div class="ad-list-item">
                <a href="/anzeige/sales-position-67890">Sales Position</a>
            </div>
        </body>
    </html>
    """
    
    # Mock detail page with mobile number
    mock_detail_html = """
    <html>
        <body>
            <h1>Vertrieb Job gesucht</h1>
            <div>Mobil: 0176 11223344</div>
        </body>
    </html>
    """
    
    mock_listing_response = Mock()
    mock_listing_response.status_code = 200
    mock_listing_response.text = mock_listing_html
    
    mock_detail_response = Mock()
    mock_detail_response.status_code = 200
    mock_detail_response.text = mock_detail_html
    
    # Mock database operations
    mock_db_con = Mock()
    mock_cursor = Mock()
    mock_db_con.cursor.return_value = mock_cursor
    
    with patch('scriptname.http_get_async', new_callable=AsyncMock) as mock_http, \
         patch('scriptname.asyncio.sleep', new_callable=AsyncMock), \
         patch('scriptname.url_seen', return_value=False), \
         patch('scriptname.db', return_value=mock_db_con), \
         patch('scriptname.MARKT_DE_URLS', ["https://www.markt.de/stellengesuche/test/"]):
        
        # First call returns listing, subsequent calls return details
        mock_http.side_effect = [mock_listing_response, mock_detail_response, mock_detail_response]
        
        result = await crawl_markt_de_listings_async()
        
        assert isinstance(result, list)
        # Should have found leads (mocked to succeed)


@pytest.mark.asyncio
async def test_crawl_quoka_disabled():
    """Test that crawl_quoka_listings_async returns empty list when disabled."""
    
    with patch.dict('scriptname.DIRECT_CRAWL_SOURCES', {"quoka": False}):
        result = await crawl_quoka_listings_async()
        assert result == []


@pytest.mark.asyncio
async def test_crawl_kalaydo_disabled():
    """Test that crawl_kalaydo_listings_async returns empty list when disabled."""
    
    with patch.dict('scriptname.DIRECT_CRAWL_SOURCES', {"kalaydo": False}):
        result = await crawl_kalaydo_listings_async()
        assert result == []


@pytest.mark.asyncio
async def test_crawl_meinestadt_disabled():
    """Test that crawl_meinestadt_listings_async returns empty list when disabled."""
    
    with patch.dict('scriptname.DIRECT_CRAWL_SOURCES', {"meinestadt": False}):
        result = await crawl_meinestadt_listings_async()
        assert result == []


@pytest.mark.asyncio
async def test_extract_generic_detail_with_whatsapp():
    """Test extraction with WhatsApp link."""
    
    mock_html = """
    <html>
        <body>
            <h1>Sales Job gesucht</h1>
            <div>Kontaktiere mich via WhatsApp</div>
            <a href="https://wa.me/491761234567">WhatsApp</a>
        </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch('scriptname.http_get_async', new_callable=AsyncMock) as mock_http:
        mock_http.return_value = mock_response
        
        result = await extract_generic_detail_async(
            "https://www.example.com/test",
            source_tag="test_portal"
        )
        
        # Should extract phone from WhatsApp link
        assert result is not None
        assert result.get("telefon")


@pytest.mark.asyncio
async def test_extract_generic_detail_http_error():
    """Test that extraction handles HTTP errors gracefully."""
    
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch('scriptname.http_get_async', new_callable=AsyncMock) as mock_http:
        mock_http.return_value = mock_response
        
        result = await extract_generic_detail_async(
            "https://www.example.com/test",
            source_tag="test_portal"
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_crawl_with_pagination():
    """Test that crawlers stop pagination when no ads found."""
    
    # First page has ads, second page is empty
    mock_page1_html = """
    <html>
        <body>
            <a href="/anzeige/test-123">Test Ad</a>
        </body>
    </html>
    """
    
    mock_page2_html = """
    <html>
        <body>
            <!-- No ads -->
        </body>
    </html>
    """
    
    mock_response1 = Mock()
    mock_response1.status_code = 200
    mock_response1.text = mock_page1_html
    
    mock_response2 = Mock()
    mock_response2.status_code = 200
    mock_response2.text = mock_page2_html
    
    mock_db_con = Mock()
    mock_cursor = Mock()
    mock_db_con.cursor.return_value = mock_cursor
    
    with patch('scriptname.http_get_async', new_callable=AsyncMock) as mock_http, \
         patch('scriptname.asyncio.sleep', new_callable=AsyncMock), \
         patch('scriptname.url_seen', return_value=False), \
         patch('scriptname.db', return_value=mock_db_con), \
         patch('scriptname.MARKT_DE_URLS', ["https://www.markt.de/test/"]):
        
        # Return page1, then page2 (empty)
        mock_http.side_effect = [mock_response1, mock_response2]
        
        result = await crawl_markt_de_listings_async()
        
        # Should have stopped after page 2 (no ads found)
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
