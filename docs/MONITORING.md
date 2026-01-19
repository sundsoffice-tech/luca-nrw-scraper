# Monitoring & Structured Logging Guide

This document describes the structured logging system implemented in the LUCA NRW Scraper for integration with monitoring systems like Grafana, Kibana, or similar log analysis tools.

## Overview

The scraper now uses structured log event codes that can be used for:
- **Grafana/Kibana visualization** - Create dashboards and alerts based on specific event codes
- **Log aggregation** - Parse and filter logs systematically
- **Error classification** - Categorize errors by type for better debugging
- **Performance monitoring** - Track performance metrics over time

## Event Codes

All log events are assigned a standardized code following the format `CATEGORY_ACTION`.

### Lifecycle Events

| Code | Level | Description |
|------|-------|-------------|
| `SCRAPER_START` | INFO | Scraper process started |
| `SCRAPER_STOP` | INFO | Scraper process stopped gracefully |
| `SCRAPER_KILL` | WARN | Scraper process forcefully terminated |
| `SCRAPER_CRASH` | ERROR | Scraper process crashed unexpectedly |
| `SCRAPER_EARLY_EXIT` | ERROR | Scraper exited prematurely (likely startup error) |

### Crawl Events

| Code | Level | Description |
|------|-------|-------------|
| `CRAWL_START` | INFO | Started crawling a portal/source |
| `CRAWL_COMPLETE` | INFO | Completed crawling a portal/source |
| `CRAWL_SKIP` | DEBUG | Skipped crawling (already done or disabled) |
| `CRAWL_PARTIAL` | WARN | Crawl completed with partial results |

### Extraction Events

| Code | Level | Description |
|------|-------|-------------|
| `EXTRACTION_START` | DEBUG | Started data extraction from page |
| `EXTRACTION_SUCCESS` | INFO | Successfully extracted data |
| `EXTRACTION_FAIL` | ERROR | Failed to extract data from page |
| `EXTRACTION_PARTIAL` | WARN | Partial data extraction (some fields missing) |
| `EXTRACTION_NO_DATA` | DEBUG | No extractable data found on page |

### Network Events

| Code | Level | Description |
|------|-------|-------------|
| `HTTP_REQUEST` | DEBUG | HTTP request sent |
| `HTTP_SUCCESS` | DEBUG | HTTP request successful |
| `HTTP_ERROR` | ERROR | HTTP request failed |
| `HTTP_TIMEOUT` | WARN | HTTP request timed out |
| `HTTP_BLOCK_403` | WARN | Request blocked (403 Forbidden) |
| `HTTP_RATE_LIMIT` | WARN | Rate limit hit (429 Too Many Requests) |
| `HTTP_CAPTCHA` | WARN | Captcha challenge detected |

### Database Events

| Code | Level | Description |
|------|-------|-------------|
| `DB_CONNECT` | DEBUG | Database connection established |
| `DB_DISCONNECT` | DEBUG | Database connection closed |
| `DB_ERROR` | ERROR | Database operation failed |
| `LEAD_SAVED` | INFO | Lead saved to database |
| `LEAD_DUPLICATE` | DEBUG | Duplicate lead skipped |

### Circuit Breaker Events

| Code | Level | Description |
|------|-------|-------------|
| `CB_TRIGGERED` | WARN | Circuit breaker triggered for portal |
| `CB_RESET` | INFO | Circuit breaker reset |
| `CB_HALF_OPEN` | DEBUG | Circuit breaker in half-open state (testing) |

### Validation Events

| Code | Level | Description |
|------|-------|-------------|
| `VALIDATION_PASS` | DEBUG | Data validation passed |
| `VALIDATION_FAIL` | WARN | Data validation failed |
| `SCORE_BELOW_THRESHOLD` | DEBUG | Lead score below minimum threshold |

### Security Events

| Code | Level | Description |
|------|-------|-------------|
| `SSL_WARNING` | WARN | SSL certificate validation issue |
| `AUTH_FAIL` | ERROR | Authentication failed |

### Performance Events

| Code | Level | Description |
|------|-------|-------------|
| `PERF_SLOW_REQUEST` | WARN | Request took longer than expected |
| `PERF_MEMORY_HIGH` | WARN | Memory usage above threshold |

## API Usage

### Filtering Logs by Event Code

```bash
# Get all EXTRACTION_FAIL events
curl -X GET "https://your-domain/crm/scraper/api/logs/?event_code=EXTRACTION_FAIL"

# Get all NETWORK category events
curl -X GET "https://your-domain/crm/scraper/api/logs/?event_category=NETWORK"

# Combine filters
curl -X GET "https://your-domain/crm/scraper/api/logs/?event_code=HTTP_RATE_LIMIT&portal=stepstone"
```

### Log Response Structure

```json
{
  "id": 1234,
  "run_id": 56,
  "level": "WARN",
  "portal": "stepstone",
  "message": "Rate limit hit - reducing request rate",
  "event_code": "HTTP_RATE_LIMIT",
  "event_category": "NETWORK",
  "url": "https://www.stepstone.de/jobs/123",
  "extra_data": {
    "retry_after": 30,
    "response_code": 429
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Grafana Integration

### Example Queries

For Grafana with a PostgreSQL/InfluxDB backend:

```sql
-- Error rate over time
SELECT
  date_trunc('hour', created_at) as time,
  COUNT(*) as error_count
FROM scraper_control_scraperlog
WHERE level = 'ERROR'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;

-- Events by category
SELECT
  event_category,
  COUNT(*) as count
FROM scraper_control_scraperlog
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY event_category;

-- Rate limit incidents by portal
SELECT
  portal,
  COUNT(*) as rate_limit_count
FROM scraper_control_scraperlog
WHERE event_code = 'HTTP_RATE_LIMIT'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY portal
ORDER BY rate_limit_count DESC;
```

### Recommended Dashboards

1. **Scraper Health Dashboard**
   - Panels: Process status, uptime, error rate
   - Alerts: SCRAPER_CRASH, SCRAPER_EARLY_EXIT

2. **Network Performance Dashboard**
   - Panels: Request rate, block rate, timeout rate
   - Alerts: HTTP_RATE_LIMIT > threshold, HTTP_BLOCK_403 spike

3. **Data Quality Dashboard**
   - Panels: Extraction success rate, lead acceptance rate
   - Alerts: EXTRACTION_FAIL spike, VALIDATION_FAIL > threshold

4. **Circuit Breaker Dashboard**
   - Panels: CB triggers by portal, recovery time
   - Alerts: CB_TRIGGERED for critical portals

## Kibana Integration

### Example Index Pattern

For Elasticsearch/Kibana:

```json
{
  "mappings": {
    "properties": {
      "event_code": { "type": "keyword" },
      "event_category": { "type": "keyword" },
      "level": { "type": "keyword" },
      "portal": { "type": "keyword" },
      "message": { "type": "text" },
      "url": { "type": "keyword" },
      "extra_data": { "type": "object" },
      "created_at": { "type": "date" }
    }
  }
}
```

### Useful KQL Queries

```
# All errors
level: "ERROR"

# Rate limit events
event_code: "HTTP_RATE_LIMIT"

# Network issues for a specific portal
event_category: "NETWORK" AND portal: "stepstone"

# Circuit breaker events
event_code: CB_TRIGGERED OR event_code: CB_RESET
```

## Python Usage

```python
from scraper_control.log_codes import LogEvent, format_structured_log

# Create a structured log entry
log_data = format_structured_log(
    LogEvent.EXTRACTION_FAIL,
    "Could not parse contact info",
    portal="stepstone",
    url="https://example.com/job/123",
    extra={"selector": ".contact-info", "error": "Element not found"}
)

# Use with Django ScraperLog model
from scraper_control.models import ScraperLog

ScraperLog.create_structured(
    run=scraper_run,
    event=LogEvent.LEAD_SAVED,
    message=f"Saved lead: {lead.email}",
    portal="indeed",
    extra_data={"lead_id": lead.id, "score": lead.quality_score}
)
```

## Best Practices

1. **Always use event codes** for important events that need monitoring
2. **Include context** in the `extra_data` field (IDs, URLs, counts)
3. **Set appropriate levels** - don't overuse ERROR for expected failures
4. **Use portal field** consistently for per-portal analysis
5. **Set up alerts** for critical events (SCRAPER_CRASH, high error rates)

## Migration

If upgrading from a version without structured logging:

```bash
cd telis_recruitment
python manage.py migrate scraper_control 0009_structured_logging
```

This adds the following fields to `ScraperLog`:
- `event_code` - The structured event code
- `event_category` - The event category for grouping
- `url` - Related URL for debugging
- `extra_data` - JSON field for additional context
