# Direct Kleinanzeigen Crawling

## Overview

The direct crawling feature bypasses Google search and crawls Kleinanzeigen Stellengesuche (job seeker ads) pages directly. This is more efficient and finds higher quality leads since **90% of Stellengesuche ads contain mobile numbers directly in the text**.

## How It Works

### 1. Listing Page Crawling
The scraper crawls predefined Kleinanzeigen Stellengesuche URLs:
- NRW-specific categories (Vertrieb, Sales, Verkauf, Außendienst, etc.)
- Nationwide categories for higher volume
- Supports pagination (up to 5 pages per category)

### 2. Detail Page Extraction
For each ad found on listing pages, the scraper:
- Extracts the ad detail page URL
- Fetches the full ad content
- Extracts contact information:
  - **Mobile phone numbers** (015x, 016x, 017x patterns only)
  - Email addresses
  - WhatsApp links
  - Name (using enhanced name extraction)
  - Location/region

### 3. Lead Validation
- Only mobile numbers are accepted (landlines filtered out)
- Phone numbers validated with `validate_phone()` and `is_mobile_number()`
- Email addresses validated with regex
- Leads without mobile numbers are discarded

### 4. Integration
- Runs **at the beginning** of each scrape session
- Only active in **candidates** or **recruiter** mode
- Results inserted into database via `insert_leads()`
- URL deduplication prevents duplicate processing
- Normal Google search continues after direct crawling

## Configuration

### Environment Variables

```bash
# Enable/disable Kleinanzeigen integration (default: 1)
ENABLE_KLEINANZEIGEN=1

# Set mode to candidates or recruiter to enable direct crawling
INDUSTRY=candidates
# or
INDUSTRY=recruiter
```

### Customizing URLs

Edit the `DIRECT_CRAWL_URLS` constant in `scriptname.py` to add or modify URLs:

```python
DIRECT_CRAWL_URLS = [
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/vertrieb/k0c107l929",
    # Add more URLs here...
]
```

## Rate Limiting

The direct crawling feature includes built-in rate limiting to be respectful to the Kleinanzeigen.de servers:

- **2.5-3.5 seconds** between detail page requests
- **3.0-4.0 seconds** between listing page requests
- Uses existing `http_get_async()` with User-Agent rotation
- Respects existing rate limiter (`_Rate` class)

## Example Output

When a lead is found via direct crawling, it will have:

```python
{
    "name": "Max Mustermann",
    "rolle": "Vertrieb",
    "email": "max@example.com",
    "telefon": "+491761234567",
    "quelle": "https://www.kleinanzeigen.de/s-anzeige/...",
    "score": 85,
    "tags": "kleinanzeigen,candidate,mobile,direct_crawl",
    "lead_type": "candidate",
    "phone_type": "mobile",
    "region": "Düsseldorf",
    "frische": "neu",
    "confidence": 0.85,
    "data_quality": 0.80
}
```

## Monitoring

Watch the logs for direct crawling activity:

```
[INFO] Starte direktes Kleinanzeigen-Crawling (Stellengesuche)...
[INFO] Direct crawl: Listing-Seite url=https://www.kleinanzeigen.de/s-stellengesuche/...
[INFO] Direct crawl: Anzeigen gefunden count=25
[INFO] Extracted lead from Kleinanzeigen ad url=... has_phone=True has_email=True
[INFO] Direct crawl: Leads gefunden count=18
[INFO] Direct crawl: Neue Leads gespeichert count=12
```

## Benefits

1. **Higher Success Rate**: 90% of Stellengesuche contain mobile numbers
2. **No Google Rate Limits**: Bypasses Google CSE quota and 429 errors
3. **Fresh Leads**: Direct access to newest job seeker ads
4. **Quality Candidates**: People actively looking for sales positions
5. **Cost Effective**: No API costs for Kleinanzeigen crawling

## Technical Details

### Functions

#### `crawl_kleinanzeigen_listings_async(listing_url, max_pages=5)`
Crawls listing pages and extracts ad links.

**Parameters:**
- `listing_url`: Base URL for the listing
- `max_pages`: Maximum number of pages to crawl (default: 5)

**Returns:** List of ad detail URLs

#### `extract_kleinanzeigen_detail_async(url)`
Extracts contact information from an ad detail page.

**Parameters:**
- `url`: URL of the ad detail page

**Returns:** Dict with lead data or None if extraction failed

### HTML Selectors

**Listing Page:**
- Ad items: `li.ad-listitem article.aditem`
- Ad link: `data-href` attribute or `a[href]`

**Detail Page:**
- Title: `h1#viewad-title` or `h1.boxedarticle--title`
- Description: `#viewad-description-text` or `.boxedarticle--description`
- Location: `#viewad-locality` or `.boxedarticle--details--locality`
- WhatsApp: `a[href*="wa.me"]` or `a[href*="api.whatsapp.com"]`

## Troubleshooting

### No leads found
- Check that `INDUSTRY` is set to `candidates` or `recruiter`
- Check that `ENABLE_KLEINANZEIGEN=1`
- Check logs for HTTP errors or blocked requests

### Too many requests / Rate limiting
- The scraper has built-in rate limiting
- If still getting 429 errors, increase delays in the code
- Consider reducing `max_pages` parameter

### Missing mobile numbers
- The feature only accepts mobile numbers (015x, 016x, 017x)
- Landline numbers are intentionally filtered out
- Check logs for "No mobile numbers found in ad" messages

## Future Enhancements

Potential improvements for future versions:
- Add more Stellengesuche categories (IT, Marketing, etc.)
- Implement adaptive rate limiting based on response times
- Add support for other job seeker platforms (Markt.de, Quoka.de)
- Extract additional metadata (salary expectations, experience level)
- Implement retry logic for failed detail page fetches
