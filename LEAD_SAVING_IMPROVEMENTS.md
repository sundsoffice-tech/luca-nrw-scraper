# Lead Saving Improvements and Data Store Sync

## Problem Statement (German)
"sorge dafür das es keine probleme beim leadspeichern gibt und alle datenspeicher secündlich aktualisiert werden"

Translation: "make sure there are no problems when saving leads and all data stores are updated every second"

## Changes Implemented

### 1. Improved Lead Saving with Retry Logic

#### Django ORM Backend (`luca_scraper/django_db.py`)

Added retry logic to `upsert_lead()` function with the following improvements:

- **Automatic Retry on Transient Errors**: The function now retries up to 3 times (configurable) when encountering database lock errors, connection issues, timeouts, or deadlocks.

- **Exponential Backoff**: Retry delays increase exponentially (0.1s, 0.2s, 0.4s by default) to avoid overwhelming the database during high contention.

- **Smart Error Detection**: Distinguishes between transient errors (that should be retried) and permanent errors (that should fail immediately).

- **Enhanced Logging**: All save operations, retries, and errors are logged with detailed context for troubleshooting.

**Function Signature:**
```python
def upsert_lead(data: Dict, max_retries: int = 3, retry_delay: float = 0.1) -> Tuple[int, bool]
```

**Usage:**
```python
# Standard usage (uses default retry settings)
lead_id, created = upsert_lead(lead_data)

# Custom retry settings
lead_id, created = upsert_lead(lead_data, max_retries=5, retry_delay=0.2)
```

#### SQLite Backend (`luca_scraper/repository.py`)

Added the same retry logic to `upsert_lead_sqlite()` function with specific handling for SQLite database lock errors.

**Key Features:**
- Handles "database is locked" errors common in SQLite under concurrent access
- Properly closes database connections even on failures
- Uses exponential backoff to reduce lock contention

### 2. Support for 1-Second Data Store Updates

#### Sync Command (`telis_recruitment/leads/management/commands/sync_scraper_db.py`)

Enhanced the sync command to support intervals as low as 1 second:

- **Minimum Interval Validation**: Ensures interval is at least 1 second, prevents invalid configurations
- **Performance Warnings**: Warns users when using high-frequency sync modes (≤5 seconds)
- **Real-time Mode**: Special messaging for 1-second intervals to indicate real-time sync

**Usage:**
```bash
# Sync every second (real-time mode)
python manage.py sync_scraper_db --watch --interval 1

# Sync every 5 seconds
python manage.py sync_scraper_db --watch --interval 5

# Default: sync every 5 minutes
python manage.py sync_scraper_db --watch
```

## Error Handling Details

### Transient Errors (Will Retry)
- Database is locked
- Connection errors
- Timeout errors
- Deadlock errors
- Temporary errors

### Permanent Errors (Fail Immediately)
- Unique constraint violations (when not recoverable)
- Invalid data format
- Schema errors
- Permission errors

### Retry Behavior

| Attempt | Delay Before Attempt | Action |
|---------|---------------------|--------|
| 1       | 0s (immediate)      | First try |
| 2       | 0.1s (retry_delay × 2⁰) | First retry |
| 3       | 0.2s (retry_delay × 2¹) | Second retry |
| 4+      | Exponentially increasing | Additional retries if max_retries > 3 |

## Testing

### Manual Verification

1. **Test Retry Logic:**
```python
# Simulate a database lock scenario
from luca_scraper.repository import upsert_lead_sqlite

# This will automatically retry if locks occur
lead_id, created = upsert_lead_sqlite({
    'name': 'Test Lead',
    'email': 'test@example.com',
    'score': 85
})
print(f"Lead {lead_id} {'created' if created else 'updated'}")
```

2. **Test 1-Second Sync:**
```bash
# Start the sync in watch mode with 1-second interval
cd telis_recruitment
python manage.py sync_scraper_db --watch --interval 1

# You should see:
# - Warning about high-frequency mode
# - Sync operations happening every second
# - Real-time updates to the Django database
```

3. **Monitor Logs:**
```bash
# Check for retry messages in logs
grep -i "retry" /path/to/logs/*.log

# Check for successful saves
grep -i "successfully.*lead" /path/to/logs/*.log
```

## Performance Considerations

### 1-Second Sync Interval

- **Database Load**: Running syncs every second increases database I/O. Ensure your database server can handle the load.
- **Network**: More frequent syncs mean more network traffic between scraper and CRM database.
- **CPU Usage**: Background sync process will use more CPU with frequent operations.

**Recommendations:**
- Use 1-second interval only when real-time updates are critical
- For most use cases, 5-60 second intervals are sufficient
- Monitor database performance metrics when using high-frequency sync

### Retry Logic

- **Default Settings (3 retries, 0.1s initial delay)**: Suitable for most scenarios
- **High Contention**: Increase `max_retries` to 5-7
- **Low Contention**: Can reduce to 2 retries
- **Timeout**: Total retry time is approximately `retry_delay × (2^max_retries - 1)` seconds

## Logging

All lead save operations now include detailed logging:

```
DEBUG: Successfully updated lead 123
DEBUG: Successfully created lead 456
WARNING: Transient error on attempt 1/3 for lead save: database is locked. Retrying in 0.10 seconds...
WARNING: Transient error on attempt 2/3 for lead save: database is locked. Retrying in 0.20 seconds...
DEBUG: Successfully created lead 457
ERROR: Failed to save lead after 3 attempts. Last error: database is locked
```

## Benefits

1. **Improved Reliability**: Automatic retry on transient errors reduces data loss
2. **Better Concurrency**: Exponential backoff reduces database contention
3. **Real-time Updates**: 1-second sync enables near real-time data synchronization
4. **Enhanced Debugging**: Comprehensive logging helps troubleshoot issues
5. **Backward Compatible**: Default parameters maintain existing behavior

## Backward Compatibility

All changes are backward compatible:

- `upsert_lead()` and `upsert_lead_sqlite()` can be called without new parameters
- Existing code continues to work without modifications
- Default retry behavior is sensible for most use cases
- Sync command defaults to 5-minute intervals (existing behavior)

## Future Enhancements

Potential improvements for consideration:

1. **Configurable Retry Settings**: Add environment variables for retry parameters
2. **Metrics Collection**: Track retry rates and success/failure statistics
3. **Circuit Breaker**: Temporarily stop retries if failure rate is too high
4. **Adaptive Intervals**: Automatically adjust sync intervals based on load
5. **Batch Operations**: Group multiple lead saves into single transactions
