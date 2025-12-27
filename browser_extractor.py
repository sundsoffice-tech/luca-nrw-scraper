# -*- coding: utf-8 -*-
"""
Browser-based phone extraction for JavaScript-hidden phone numbers.

This module provides Selenium-based phone extraction for portals that hide
phone numbers behind JavaScript buttons like "Telefonnummer anzeigen".
"""

import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Import phone extraction from phone_extractor module
try:
    from phone_extractor import extract_phones_advanced, get_best_phone
except ImportError:
    # Fallback for standalone usage
    def extract_phones_advanced(text, html=""):
        """Fallback function if phone_extractor is not available"""
        return []
    
    def get_best_phone(results):
        """Fallback function if phone_extractor is not available"""
        return results[0][0] if results else None


# Portal-specific button selectors
BUTTON_SELECTORS = {
    'kleinanzeigen': [
        "button[data-testid='contact-phone-button']",
        "//button[contains(text(), 'Telefonnummer anzeigen')]",
        "//button[contains(text(), 'Telefon anzeigen')]",
        "//a[contains(text(), 'Telefonnummer anzeigen')]",
    ],
    'quoka': [
        ".contact-reveal-btn",
        "//button[contains(text(), 'Nummer anzeigen')]",
        "//a[contains(text(), 'Nummer anzeigen')]",
        "//button[contains(text(), 'Telefon anzeigen')]",
    ],
    'markt_de': [
        "//button[contains(text(), 'Telefonnummer anzeigen')]",
        "//a[contains(text(), 'Kontakt anzeigen')]",
        ".show-phone-button",
        "//button[contains(text(), 'Nummer anzeigen')]",
    ],
    'dhd24': [
        "//button[contains(text(), 'Telefon')]",
        "//a[contains(text(), 'Kontakt')]",
        ".contact-button",
        "//button[contains(text(), 'Anrufen')]",
    ],
    'generic': [
        "//button[contains(text(), 'Telefon')]",
        "//button[contains(text(), 'Nummer')]",
        "//a[contains(text(), 'Kontakt')]",
        "//button[contains(text(), 'Anrufen')]",
        "//a[contains(text(), 'Telefonnummer')]",
        ".phone-button",
        ".contact-button",
        ".show-phone",
    ]
}

# Rate limiting
_last_request_time = 0
_min_request_interval = 5.0  # seconds


def _setup_chrome_options() -> Options:
    """
    Setup Chrome options with anti-bot detection measures.
    Based on login_handler.py configuration.
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User-Agent to avoid detection
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    
    # Additional performance options
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    return options


def _rate_limit():
    """Enforce rate limiting between browser requests"""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _min_request_interval:
        sleep_time = _min_request_interval - time_since_last
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def _detect_portal(url: str) -> str:
    """Detect which portal based on URL"""
    url_lower = url.lower()
    if 'kleinanzeigen' in url_lower or 'ebay-kleinanzeigen' in url_lower:
        return 'kleinanzeigen'
    elif 'quoka' in url_lower:
        return 'quoka'
    elif 'markt.de' in url_lower:
        return 'markt_de'
    elif 'dhd24' in url_lower:
        return 'dhd24'
    else:
        return 'generic'


def extract_phone_with_browser(url: str, portal: Optional[str] = None, timeout: int = 15) -> Optional[str]:
    """
    Extract phone number using headless browser to click on reveal buttons.
    
    This function:
    1. Opens the URL in a headless Chrome browser
    2. Waits for the page to load
    3. Tries to find and click phone reveal buttons
    4. Waits for AJAX response
    5. Extracts phone number from updated HTML
    
    Args:
        url: URL of the ad detail page
        portal: Portal name (kleinanzeigen, quoka, markt_de, dhd24, generic)
                If None, will be auto-detected from URL
        timeout: Maximum time to wait for page load and button click (seconds)
    
    Returns:
        Normalized phone number or None if extraction failed
    """
    # Rate limiting
    _rate_limit()
    
    # Auto-detect portal if not specified
    if portal is None:
        portal = _detect_portal(url)
    
    # Get selectors for this portal
    selectors = BUTTON_SELECTORS.get(portal, BUTTON_SELECTORS['generic'])
    
    driver = None
    try:
        # Setup Chrome with anti-bot options
        options = _setup_chrome_options()
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(timeout)
        
        # Navigate to page
        logging.info(f"Browser extraction: Loading {url} (portal: {portal})")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(2)
        
        # Try to find and click the phone reveal button
        button_clicked = False
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    # CSS selector
                    button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                # Click the button
                button.click()
                logging.info(f"Browser extraction: Clicked button with selector: {selector}")
                button_clicked = True
                
                # Wait for AJAX response
                time.sleep(3)
                break
                
            except (TimeoutException, NoSuchElementException):
                # Try next selector
                continue
            except Exception as e:
                logging.debug(f"Browser extraction: Error with selector {selector}: {e}")
                continue
        
        if not button_clicked:
            logging.debug(f"Browser extraction: No phone button found on {url}")
        
        # Extract phone from updated HTML
        html = driver.page_source
        phones = extract_phones_advanced(html, html)
        
        if phones:
            best_phone = get_best_phone(phones)
            if best_phone:
                logging.info(f"Browser extraction: Successfully extracted phone from {url}: {best_phone[:8]}...")
                return best_phone
        
        logging.debug(f"Browser extraction: No phone number found in HTML after button click")
        return None
        
    except TimeoutException:
        logging.warning(f"Browser extraction: Timeout loading {url}")
        return None
    except WebDriverException as e:
        logging.warning(f"Browser extraction: WebDriver error for {url}: {e}")
        return None
    except Exception as e:
        logging.warning(f"Browser extraction: Unexpected error for {url}: {e}")
        return None
    finally:
        # Always close the browser
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def extract_phone_with_browser_batch(urls: list, portal: Optional[str] = None) -> dict:
    """
    Extract phone numbers from multiple URLs using browser.
    
    Args:
        urls: List of URLs to extract from
        portal: Portal name (if all URLs are from same portal)
    
    Returns:
        Dictionary mapping URL to phone number (or None)
    """
    results = {}
    for url in urls:
        phone = extract_phone_with_browser(url, portal=portal)
        results[url] = phone
    return results
