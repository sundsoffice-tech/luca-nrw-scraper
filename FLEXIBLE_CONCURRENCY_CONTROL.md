# Flexible Concurrency Control - Implementation Guide

## Overview

The scraper now supports dynamic configuration of network concurrency settings through the Django CRM admin interface. Users can adjust `async_limit` and `pool_size` in real-time without restarting the scraper.

## Configuration Parameters

### async_limit
- **Purpose**: Controls the maximum number of parallel HTTP requests
- **Default**: 35
- **Range**: 1-100 (validated in Django model)
- **Impact**: Higher values = more aggressive scraping, lower values = gentler on network/target sites

### pool_size
- **Purpose**: Connection pool size for HTTP clients
- **Default**: 12
- **Range**: 1-50 (validated in Django model)
- **Impact**: Reserved for future use (HTTP clients currently manage pooling internally)

### sleep_between_queries
- **Purpose**: Delay between search queries (rate limiting)
- **Default**: 2.7 seconds
- **Range**: 0.5-30 seconds
- **Impact**: Lower values = faster scraping, higher values = better rate limit compliance

## How It Works

### Configuration Priority

The scraper loads configuration in this priority order:

1. **Django Database** (highest priority) - User changes in CRM admin
2. **Environment Variables** - Traditional configuration method
3. **Hardcoded Defaults** - Fallback values

### Configuration Flow

```
User Updates CRM Admin
       ↓
ScraperConfig Model
       ↓
get_scraper_config() in config_loader.py
       ↓
get_performance_params() in scriptname.py
       ↓
Applied to Scraper Runtime
```

### Dynamic Updates

The scraper checks for configuration updates:
- **Initial Load**: When scraper starts (line 8872 in scriptname.py)
- **Periodic Refresh**: Every 30 seconds during runtime (line 9009-9017)
- **Automatic Apply**: If async_limit changes, rate limiter is recreated

## Usage

### Via Django Admin

1. Navigate to: **Admin Panel → Scraper Control → Scraper-Konfiguration**
2. Locate the **HTTP & Networking** section
3. Adjust values:
   - `async_limit`: Max parallel requests (recommended: 25-50 for good network, 15-25 for constrained)
   - `pool_size`: Connection pool size (reserved for future use)
   - `sleep_between_queries`: Delay between queries
4. Click **Save**
5. Changes take effect within 30 seconds for running scrapers

### Via Environment Variables (Fallback)

```bash
export ASYNC_LIMIT=50
export POOL_SIZE=20
export SLEEP_BETWEEN_QUERIES=3.0
python scriptname.py --industry recruiter
```

### Via Defaults (No Configuration)

If neither Django DB nor environment variables are set, the scraper uses:
- async_limit: 35
- pool_size: 12
- sleep_between_queries: 2.7

## Recommendations

### Network Conditions

**Good Network (Stable, High Bandwidth)**
- async_limit: 45-50
- sleep_between_queries: 2.0-2.5

**Average Network (Typical)**
- async_limit: 30-40 (default: 35)
- sleep_between_queries: 2.5-3.0 (default: 2.7)

**Constrained Network (Rate Limited, Unstable)**
- async_limit: 15-25
- sleep_between_queries: 3.5-5.0

**Aggressive Mode (Maximum Speed)**
- async_limit: 60-80
- sleep_between_queries: 1.5-2.0
- ⚠️ Warning: May trigger rate limits

### Troubleshooting

**Issue**: Too many timeout errors
- **Solution**: Decrease async_limit to 20-25

**Issue**: Scraper too slow
- **Solution**: Increase async_limit to 45-50, decrease sleep_between_queries to 2.0

**Issue**: Getting rate limited (429 errors)
- **Solution**: Decrease async_limit to 20, increase sleep_between_queries to 4.0

**Issue**: Configuration not taking effect
- **Solution**: Check that Django is properly configured and database is accessible

## Technical Details

### Implementation

**File**: `scriptname.py`
**Function**: `get_performance_params()` (lines 1155-1196)

```python
def get_performance_params():
    # 1. Start with defaults
    defaults = {'async_limit': 35, 'pool_size': 12, ...}
    
    # 2. Override with environment variables
    params = {
        'async_limit': int(os.getenv("ASYNC_LIMIT", "35")),
        'pool_size': int(os.getenv("POOL_SIZE", "12")),
        ...
    }
    
    # 3. Override with Django DB (highest priority)
    if SCRAPER_CONFIG_AVAILABLE:
        db_config = get_scraper_config()
        if db_config:
            params['async_limit'] = db_config['async_limit']
            params['pool_size'] = db_config['pool_size']
    
    return params
```

### Rate Limiter

The `_Rate` class uses asyncio semaphores to control concurrency:

```python
class _Rate:
    def __init__(self, max_global=ASYNC_LIMIT, max_per_host=ASYNC_PER_HOST):
        self.sem_global = asyncio.Semaphore(max_global)  # Global limit
        self.per_host = {}  # Per-host limits
```

When `async_limit` is updated, the rate limiter is recreated:

```python
if new_async_limit != current_async_limit:
    current_async_limit = new_async_limit
    rate = _Rate(max_global=current_async_limit, max_per_host=ASYNC_PER_HOST)
    log("info", "Performance params updated", async_limit=current_async_limit)
```

## Testing

Run the test suite to verify configuration loading:

```bash
cd /path/to/luca-nrw-scraper
python test_concurrency_config_simple.py
```

Expected output:
```
✅ ALL LOGIC TESTS PASSED

Summary:
  • Configuration loading follows priority: DB > Env > Default
  • async_limit and pool_size are correctly loaded from all sources
  • Partial configurations are handled correctly
```

## Future Enhancements

1. **Connection Pool Integration**: Apply `pool_size` to HTTP client connection pools
2. **Auto-tuning**: Automatically adjust concurrency based on error rates
3. **Per-Portal Limits**: Different concurrency limits for different portals
4. **Live Monitoring**: Real-time dashboard showing current concurrency settings
5. **Historical Tracking**: Track performance metrics per configuration

## Related Files

- `scriptname.py` - Main scraper with configuration loading
- `telis_recruitment/scraper_control/models.py` - ScraperConfig model
- `telis_recruitment/scraper_control/config_loader.py` - Configuration loader
- `luca_scraper/config.py` - Configuration constants and integration
- `test_concurrency_config_simple.py` - Unit tests
