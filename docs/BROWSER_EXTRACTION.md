# Browser-Based Phone Extraction

## Overview

The `browser_extractor.py` module provides Selenium-based phone number extraction for websites that hide phone numbers behind JavaScript buttons. This is a critical feature for extracting leads from portals like Kleinanzeigen, Quoka, Markt.de, and DHD24 where phone numbers are revealed only after clicking "Telefonnummer anzeigen" buttons.

## Problem

Many classified ad portals hide phone numbers behind JavaScript to prevent scraping:
- Phone numbers are not in the initial HTML
- Clicking a button triggers an AJAX request to reveal the number
- Standard HTTP scraping cannot extract these numbers

## Solution

The browser extraction module:
1. Opens a headless Chrome browser
2. Navigates to the ad detail page
3. Finds and clicks the phone reveal button
4. Waits for AJAX response
5. Extracts the revealed phone number
6. Returns the normalized phone number

## Usage

### Automatic Fallback (Integrated)

The browser extraction is automatically used as a fallback when standard extraction fails:

```python
# In scriptname.py - extract_kleinanzeigen_detail_async()
phones = extract_phones_advanced(html)

if not phones:
    # Fallback: Browser-based extraction
    browser_phone = extract_phone_with_browser(url, portal='kleinanzeigen')
    if browser_phone:
        phones.append(browser_phone)
```

### Manual Usage

You can also use the browser extraction directly:

```python
from browser_extractor import extract_phone_with_browser

# Extract from Kleinanzeigen
phone = extract_phone_with_browser(
    url='https://www.kleinanzeigen.de/s-anzeige/test/123456',
    portal='kleinanzeigen',
    timeout=15
)

# Auto-detect portal
phone = extract_phone_with_browser(url)

# Extract from multiple URLs
from browser_extractor import extract_phone_with_browser_batch
results = extract_phone_with_browser_batch(urls, portal='quoka')
```

## Portal Support

The module includes specific button selectors for:

- **Kleinanzeigen** (ebay-kleinanzeigen.de): `button[data-testid='contact-phone-button']`, text-based selectors
- **Quoka**: `.contact-reveal-btn`, text-based selectors
- **Markt.de**: Text-based and class selectors
- **DHD24**: Contact button selectors
- **Generic**: Fallback selectors for any portal

## Features

### Anti-Bot Detection

Based on `login_handler.py` configuration:
- Headless Chrome with automation flags disabled
- Custom user-agent
- Excluding automation extensions
- Window size and GPU settings

### Rate Limiting

Built-in rate limiting prevents overloading target sites:
- Minimum 5 seconds between requests
- Automatic enforcement
- Configurable via `_min_request_interval`

### Error Handling

Robust error handling for:
- Browser initialization failures
- Page load timeouts
- Missing buttons
- AJAX failures
- Network errors

### Integration with Phone Extractor

Seamlessly integrates with `phone_extractor.py`:
- Uses `extract_phones_advanced()` to parse revealed HTML
- Applies same validation and normalization
- Returns standardized phone format (+49...)

## Configuration

### Button Selectors

Add custom selectors in `BUTTON_SELECTORS` dict:

```python
BUTTON_SELECTORS = {
    'custom_portal': [
        "//button[contains(text(), 'Show Phone')]",
        ".reveal-phone-btn",
        "#contact-button",
    ]
}
```

### Timeout

Default timeout is 15 seconds, configurable per call:

```python
phone = extract_phone_with_browser(url, timeout=30)
```

### Rate Limiting

Adjust minimum interval between requests:

```python
import browser_extractor
browser_extractor._min_request_interval = 10.0  # 10 seconds
```

## Logging

The module logs extraction attempts and results:

```
INFO: Browser extraction: Loading https://... (portal: kleinanzeigen)
INFO: Browser extraction: Clicked button with selector: ...
INFO: Browser extraction: Successfully extracted phone: +4917612...
DEBUG: Browser extraction: No phone button found on ...
WARNING: Browser extraction: Timeout loading ...
```

## Performance

### Resource Usage

Browser extraction is resource-intensive:
- Chrome process per request
- 2-5 second delay for page load
- 3 second delay for AJAX response
- ~10-15 seconds total per URL

### When to Use

Browser extraction is used as a **fallback only**:
- Standard extraction tries first (fast, < 1 second)
- Browser extraction only when standard fails
- Typical usage: 10-20% of URLs require browser extraction

### Expected Impact

Based on problem statement diagnostics:
- Before: 0 leads per run (phone numbers hidden)
- After: 5-15 leads per run (numbers extracted)
- Success rate improvement: 0% → 30-50% for JS-hidden portals

## Testing

### Unit Tests

See `tests/test_browser_extractor.py`:
- Portal detection
- Chrome options configuration
- Button selector validation
- Mocked extraction flows

### Integration Tests

Run the integration test:

```bash
python3 test_browser_integration.py
```

### E2E Tests

Run end-to-end tests with mocked browser:

```bash
python3 test_browser_e2e.py
```

## Security Considerations

### Anti-Bot Measures

The module uses anti-detection techniques to avoid being blocked:
- Disable automation flags
- Custom user-agent
- Exclude automation extensions
- Normal window size

### Rate Limiting

Respect target site rate limits:
- 5 second minimum between requests
- Avoid overwhelming servers
- Be a good web citizen

### Data Privacy

Extracted phone numbers are:
- Used only for lead generation
- Stored in local database
- Subject to data protection rules

## Troubleshooting

### Chrome Not Found

If Chrome is not installed:

```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser chromium-chromedriver

# Or download Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

### Selenium Version

Ensure Selenium 4.0+ is installed:

```bash
pip install selenium>=4.0.0
```

### Timeout Issues

If timeouts occur frequently:
- Increase timeout parameter
- Check network connectivity
- Verify portal is accessible
- Check for anti-bot detection

### No Button Found

If buttons aren't being found:
- Inspect target page HTML
- Add custom selectors for the portal
- Check if portal changed button structure
- Enable debug logging

## Future Improvements

Potential enhancements:
- Add Playwright support (faster than Selenium)
- Implement browser instance pooling
- Add screenshot capture on failure
- Support for cookie-based authentication
- Parallel browser instances
- Dynamic selector learning
