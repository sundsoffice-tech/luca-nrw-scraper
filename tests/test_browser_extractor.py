"""
Tests for browser_extractor module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import WebDriverException
from browser_extractor import (
    extract_phone_with_browser,
    _detect_portal,
    _setup_chrome_options,
    _setup_chrome_options_headless_fallback,
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


def test_chrome_options_headless_fallback():
    """Test headless fallback Chrome options configuration"""
    options = _setup_chrome_options_headless_fallback()
    
    # Check that key anti-bot options are set (from base options)
    args = options.arguments
    assert '--headless' in args
    assert '--no-sandbox' in args
    assert '--disable-gpu' in args
    
    # Check that fallback-specific options are set
    assert '--disable-software-rasterizer' in args
    assert '--disable-webgl' in args
    assert '--disable-webgl2' in args
    assert '--disable-notifications' in args
    assert '--disable-push-messaging' in args
    assert '--disable-background-networking' in args
    assert '--log-level=3' in args
    assert '--disable-logging' in args


@patch('browser_extractor.webdriver.Chrome')
@patch('browser_extractor.extract_phones_advanced')
@patch('browser_extractor.get_best_phone')
@patch('browser_extractor.time.sleep')
def test_extract_phone_with_fallback_options_parameter(mock_sleep, mock_get_best_phone, mock_extract_phones, mock_chrome):
    """Test extraction with use_fallback_options=True parameter"""
    # Setup mocks
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver.page_source = '<html><body>Phone: 0176 12345678</body></html>'
    
    mock_extract_phones.return_value = [('+491761234567', '0176 12345678', 0.9)]
    mock_get_best_phone.return_value = '+491761234567'
    
    # Execute with fallback options forced
    url = 'https://www.kleinanzeigen.de/s-anzeige/test/123456'
    result = extract_phone_with_browser(url, use_fallback_options=True)
    
    # Verify
    assert result == '+491761234567'
    mock_driver.get.assert_called_once_with(url)
    # Chrome should be called with fallback options
    mock_chrome.assert_called_once()
    call_args = mock_chrome.call_args
    # Get options from either kwargs or args
    options_used = call_args.kwargs.get('options') if call_args.kwargs else call_args[1] if len(call_args[0]) > 0 else call_args[0][0]
    assert '--disable-webgl' in options_used.arguments


@patch('browser_extractor.webdriver.Chrome')
@patch('browser_extractor.extract_phones_advanced')
@patch('browser_extractor.get_best_phone')
@patch('browser_extractor.time.sleep')
def test_extract_phone_with_browser_fallback_on_webdriver_exception(mock_sleep, mock_get_best_phone, mock_extract_phones, mock_chrome):
    """Test that fallback options are used when WebDriverException occurs"""
    # Setup mocks - first call raises WebDriverException, second succeeds
    mock_driver_fail = MagicMock()
    mock_driver_success = MagicMock()
    
    # First Chrome instance raises WebDriverException
    mock_driver_fail.get.side_effect = WebDriverException("Chrome error")
    
    # Second Chrome instance succeeds
    mock_driver_success.page_source = '<html><body>Phone: 0176 12345678</body></html>'
    
    # Setup Chrome mock to return different drivers
    mock_chrome.side_effect = [mock_driver_fail, mock_driver_success]
    
    mock_extract_phones.return_value = [('+491761234567', '0176 12345678', 0.9)]
    mock_get_best_phone.return_value = '+491761234567'
    
    # Execute - should retry with fallback options
    url = 'https://www.kleinanzeigen.de/s-anzeige/test/123456'
    result = extract_phone_with_browser(url)
    
    # Verify
    assert result == '+491761234567'
    # Chrome should be called twice (standard then fallback)
    assert mock_chrome.call_count == 2
    # Both drivers should be quit
    mock_driver_fail.quit.assert_called_once()
    mock_driver_success.quit.assert_called_once()


@patch('browser_extractor.webdriver.Chrome')
@patch('browser_extractor.time.sleep')
def test_extract_phone_with_browser_fallback_also_fails(mock_sleep, mock_chrome):
    """Test when both standard and fallback options fail"""
    # Setup mocks - both calls raise WebDriverException
    mock_driver_fail1 = MagicMock()
    mock_driver_fail2 = MagicMock()
    
    mock_driver_fail1.get.side_effect = WebDriverException("Chrome error 1")
    mock_driver_fail2.get.side_effect = WebDriverException("Chrome error 2")
    
    mock_chrome.side_effect = [mock_driver_fail1, mock_driver_fail2]
    
    # Execute - should retry and fail
    url = 'https://www.kleinanzeigen.de/s-anzeige/test/123456'
    result = extract_phone_with_browser(url)
    
    # Verify
    assert result is None
    # Chrome should be called twice
    assert mock_chrome.call_count == 2
    # Both drivers should be quit
    mock_driver_fail1.quit.assert_called_once()
    mock_driver_fail2.quit.assert_called_once()
