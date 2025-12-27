"""
Tests for browser_extractor module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from browser_extractor import (
    extract_phone_with_browser,
    _detect_portal,
    _setup_chrome_options,
    BUTTON_SELECTORS,
)


def test_detect_portal():
    """Test portal detection from URLs"""
    assert _detect_portal('https://www.kleinanzeigen.de/s-anzeige/test/123456') == 'kleinanzeigen'
    assert _detect_portal('https://www.ebay-kleinanzeigen.de/s-anzeige/test/123456') == 'kleinanzeigen'
    assert _detect_portal('https://www.quoka.de/test/123') == 'quoka'
    assert _detect_portal('https://www.markt.de/test/123') == 'markt_de'
    assert _detect_portal('https://www.dhd24.com/test/123') == 'dhd24'
    assert _detect_portal('https://www.example.com/test/123') == 'generic'


def test_button_selectors_exist():
    """Test that button selectors are defined for all portals"""
    assert 'kleinanzeigen' in BUTTON_SELECTORS
    assert 'quoka' in BUTTON_SELECTORS
    assert 'markt_de' in BUTTON_SELECTORS
    assert 'dhd24' in BUTTON_SELECTORS
    assert 'generic' in BUTTON_SELECTORS
    
    # Check that each portal has at least one selector
    for portal, selectors in BUTTON_SELECTORS.items():
        assert len(selectors) > 0, f"Portal {portal} has no selectors"


def test_chrome_options_setup():
    """Test Chrome options configuration"""
    options = _setup_chrome_options()
    
    # Check that key anti-bot options are set
    args = options.arguments
    assert '--headless' in args
    assert '--no-sandbox' in args
    assert '--disable-blink-features=AutomationControlled' in args
    
    # Check user agent is set
    user_agent_args = [arg for arg in args if '--user-agent=' in arg]
    assert len(user_agent_args) > 0


@patch('browser_extractor.webdriver.Chrome')
@patch('browser_extractor.extract_phones_advanced')
@patch('browser_extractor.get_best_phone')
@patch('browser_extractor.time.sleep')  # Mock sleep to speed up tests
def test_extract_phone_with_browser_success(mock_sleep, mock_get_best_phone, mock_extract_phones, mock_chrome):
    """Test successful phone extraction with browser"""
    # Setup mocks
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver.page_source = '<html><body>Telefon: 0176 12345678</body></html>'
    
    # Mock phone extraction
    mock_extract_phones.return_value = [('+491761234567', '0176 12345678', 0.9)]
    mock_get_best_phone.return_value = '+491761234567'
    
    # Mock button click - simulate success on first selector
    mock_button = MagicMock()
    mock_driver.find_element.return_value = mock_button
    
    # Execute
    url = 'https://www.kleinanzeigen.de/s-anzeige/test/123456'
    result = extract_phone_with_browser(url)
    
    # Verify
    assert result == '+491761234567'
    mock_driver.get.assert_called_once_with(url)
    mock_driver.quit.assert_called_once()


@patch('browser_extractor.webdriver.Chrome')
@patch('browser_extractor.extract_phones_advanced')
@patch('browser_extractor.time.sleep')
def test_extract_phone_with_browser_no_phone_found(mock_sleep, mock_extract_phones, mock_chrome):
    """Test browser extraction when no phone is found"""
    # Setup mocks
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver.page_source = '<html><body>No phone here</body></html>'
    
    # Mock phone extraction returns empty
    mock_extract_phones.return_value = []
    
    # Execute
    url = 'https://www.kleinanzeigen.de/s-anzeige/test/123456'
    result = extract_phone_with_browser(url)
    
    # Verify
    assert result is None
    mock_driver.quit.assert_called_once()


@patch('browser_extractor.webdriver.Chrome')
@patch('browser_extractor.time.sleep')
def test_extract_phone_with_browser_timeout(mock_sleep, mock_chrome):
    """Test browser extraction with timeout"""
    # Setup mock to raise timeout
    mock_chrome.side_effect = Exception("Timeout")
    
    # Execute
    url = 'https://www.kleinanzeigen.de/s-anzeige/test/123456'
    result = extract_phone_with_browser(url)
    
    # Verify
    assert result is None


@patch('browser_extractor.webdriver.Chrome')
@patch('browser_extractor.extract_phones_advanced')
@patch('browser_extractor.get_best_phone')
@patch('browser_extractor.time.sleep')
def test_extract_phone_with_browser_custom_portal(mock_sleep, mock_get_best_phone, mock_extract_phones, mock_chrome):
    """Test extraction with custom portal specified"""
    # Setup mocks
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver.page_source = '<html><body>Phone: 0176 12345678</body></html>'
    
    mock_extract_phones.return_value = [('+491761234567', '0176 12345678', 0.9)]
    mock_get_best_phone.return_value = '+491761234567'
    
    # Execute with custom portal
    url = 'https://www.example.com/test'
    result = extract_phone_with_browser(url, portal='quoka')
    
    # Verify
    assert result == '+491761234567'
    mock_driver.get.assert_called_once_with(url)
