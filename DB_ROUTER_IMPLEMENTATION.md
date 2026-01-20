# DB Router Implementation Summary

## Overview

This implementation creates a database routing layer that enables the luca-nrw-scraper to write directly to either SQLite (default) or Django CRM based on the `SCRAPER_DB_BACKEND` environment variable.

## Changes Made

### 1. Created `luca_scraper/db_router.py`

Central abstraction layer that routes database operations to the appropriate backend:

**Exported Functions:**
- `upsert_lead(data)` - Insert or update a lead
- `lead_exists(email, telefon)` - Check if a lead exists
- `get_lead_count()` - Get total lead count
- `is_url_seen(url)` - Check if URL has been seen
- `mark_url_seen(url, run_id)` - Mark URL as seen
- `is_query_done(query)` - Check if query has been executed
- `mark_query_done(query, run_id)` - Mark query as executed
- `start_scraper_run()` - Start a new scraper run
- `finish_scraper_run(run_id, ...)` - Finish a scraper run

### 2. Extended `luca_scraper/database.py`

Added SQLite-specific implementations:

- `upsert_lead_sqlite(data)` - SQLite upsert with deduplication by email/phone
- `lead_exists_sqlite(email, telefon)` - SQLite lead existence check
- `get_lead_count_sqlite()` - SQLite lead count
- `is_url_seen_sqlite(url)` - SQLite URL tracking check
- `mark_url_seen_sqlite(url, run_id)` - SQLite URL tracking mark
- `is_query_done_sqlite(query)` - SQLite query tracking check
- `mark_query_done_sqlite(query, run_id)` - SQLite query tracking mark
- `start_scraper_run_sqlite()` - SQLite run start
- `finish_scraper_run_sqlite(run_id, ...)` - SQLite run finish

### 3. Extended `luca_scraper/django_db.py`

Added Django ORM implementations:

- `is_url_seen(url)` - Django URL tracking check via UrlSeen model
- `mark_url_seen(url, run_id)` - Django URL tracking mark
- `is_query_done(query)` - Django query tracking check via QueryDone model
- `mark_query_done(query, run_id)` - Django query tracking mark
- `start_scraper_run()` - Django run start via ScraperRun model
- `finish_scraper_run(run_id, ...)` - Django run finish with metrics

### 4. Created Django Models in `telis_recruitment/scraper_control/models.py`

Added two new models for tracking:

**UrlSeen Model:**
- `url` (URLField, unique) - The seen URL
- `first_run` (ForeignKey to ScraperRun) - First scraper run that saw this URL
- `created_at` (DateTimeField) - When first seen

**QueryDone Model:**
- `query` (TextField, unique) - The executed search query
- `last_run` (ForeignKey to ScraperRun) - Last scraper run that used this query
- `created_at` (DateTimeField) - When first executed
- `last_executed_at` (DateTimeField) - Last execution time

### 5. Created Django Migration

Migration file: `telis_recruitment/scraper_control/migrations/0010_urlseen_querydone.py`

Creates both models with appropriate indexes for performance.

### 6. Updated `telis_recruitment/scraper_control/admin.py`

Registered admin interfaces for the new models:

**UrlSeenAdmin:**
- List display: URL preview, first run, created date
- Search by URL
- Read-only (automatically tracked)

**QueryDoneAdmin:**
- List display: Query preview, last run, created/executed dates
- Search by query text
- Read-only (automatically tracked)

### 7. Updated `scriptname.py`

Modified the main scraper script to use the db_router:

**Functions Updated:**
- `is_query_done()` - Now uses `_is_query_done_router()` when available
- `mark_query_done()` - Now uses `_mark_query_done_router()`
- `mark_url_seen()` - Now uses `_mark_url_seen_router()`
- `url_seen()` - Now uses `_is_url_seen_router()`
- `start_run()` - Now uses `_start_scraper_run_router()`
- `finish_run()` - Now uses `_finish_scraper_run_router()`

All functions maintain backward compatibility with fallback to direct SQLite implementation.

## Usage

### SQLite Backend (Default)

```bash
# Use SQLite (default)
export SCRAPER_DB_BACKEND=sqlite
export SCRAPER_DB=scraper.db

python scriptname.py --industry=recruiter --qpi=10
```

### Django Backend

```bash
# Use Django ORM to write directly to CRM
export SCRAPER_DB_BACKEND=django
export DJANGO_SETTINGS_MODULE=telis_recruitment.telis.settings

python scriptname.py --industry=recruiter --qpi=10
```

## Benefits

1. **Unified API**: Single interface for all database operations
2. **Backend Flexibility**: Easy switching between SQLite and Django
3. **Direct CRM Integration**: Can write directly to the Django CRM database
4. **Backward Compatibility**: Existing SQLite code continues to work
5. **Clean Separation**: Database logic isolated from scraper logic

## Migration Path

### Phase 1: Current State (Completed)
- ✅ Router layer created
- ✅ SQLite implementations added
- ✅ Django implementations added
- ✅ Models and migrations created
- ✅ scriptname.py updated

### Phase 2: Testing
- Test SQLite backend with existing workflows
- Test Django backend with CRM integration
- Verify data consistency
- Performance testing

### Phase 3: Deployment
- Deploy migrations to production
- Update environment configuration
- Monitor scraper runs
- Gradual rollout to Django backend

## Architecture

```
scriptname.py
    ↓
db_router.py (routes based on DATABASE_BACKEND)
    ↓
    ├─→ database.py (SQLite implementations)
    │       ↓
    │   SQLite Database
    │
    └─→ django_db.py (Django ORM implementations)
            ↓
        Django Models (Lead, ScraperRun, UrlSeen, QueryDone)
            ↓
        PostgreSQL/MySQL Database
```

## Configuration

The routing is controlled by the `SCRAPER_DB_BACKEND` environment variable:

- `sqlite` (default): Uses SQLite database via `database.py`
- `django`: Uses Django ORM via `django_db.py`

Set in `luca_scraper/config.py` line 103:
```python
DATABASE_BACKEND = os.getenv('SCRAPER_DB_BACKEND', 'sqlite').lower()
```

## Security Considerations

- All Django database operations use Django ORM transactions
- Input validation via Django model validators
- Proper deduplication to prevent duplicate entries
- ForeignKey constraints ensure data integrity

## Performance

- SQLite: Direct database access, minimal overhead
- Django: Uses ORM with connection pooling
- Both backends use appropriate indexes
- URL/Query caching in memory for fast lookups

## Future Enhancements

1. Add database sync command to migrate SQLite data to Django
2. Implement read operations from both backends (fallback pattern)
3. Add analytics dashboard using Django models
4. Real-time monitoring of scraper runs via Django admin
