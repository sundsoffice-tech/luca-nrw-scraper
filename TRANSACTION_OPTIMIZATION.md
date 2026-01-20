# Transaction Management Optimization

## Problem

Many functions in the codebase opened one transaction per update (e.g., `mark_url_seen`), which increased latency significantly. When processing multiple URLs during a scraping run, each call would:
1. Open a new database connection
2. Execute a single INSERT
3. Commit the transaction
4. Close the connection

This resulted in excessive database overhead, especially when marking hundreds or thousands of URLs as seen during a single scraper run.

## Solution

We implemented batch operations that allow marking multiple URLs or queries in a single transaction. This dramatically reduces the number of database connections and commits required.

### New Functions

#### SQLite Backend

- **`mark_urls_seen_batch_sqlite(urls: list, run_id: Optional[int] = None)`**
  - Mark multiple URLs as seen in a single transaction
  - Uses SQLite's `executemany()` for efficient batch inserts
  
- **`mark_queries_done_batch_sqlite(queries: list, run_id: Optional[int] = None)`**
  - Mark multiple queries as done in a single transaction
  - Uses SQLite's `executemany()` for efficient batch inserts

#### Django ORM Backend

- **`mark_urls_seen_batch(urls: list, run_id: Optional[int] = None)`**
  - Mark multiple URLs as seen in a single transaction
  - Uses Django's `bulk_create()` with `ignore_conflicts=True`
  - Filters out existing URLs before insertion to avoid duplicates
  
- **`mark_queries_done_batch(queries: list, run_id: Optional[int] = None)`**
  - Mark multiple queries as done in a single transaction
  - Uses Django's `bulk_create()` for new queries
  - Uses `update()` for existing queries if run_id changes

#### Database Router

The db_router module automatically exposes the correct batch functions based on the configured backend:

```python
from luca_scraper.db_router import mark_urls_seen_batch, mark_queries_done_batch

# These will use either SQLite or Django backend automatically
mark_urls_seen_batch(urls, run_id=1)
mark_queries_done_batch(queries, run_id=1)
```

## Performance Improvement

**71.60x faster** for batch operations compared to individual calls (tested with 100 URLs):

- **Individual marking**: 100 URLs in 0.1509s (using 100 separate transactions)
- **Batch marking**: 100 URLs in 0.0021s (using 1 transaction)

### Why is it faster?

1. **Single Connection**: Opens database connection once instead of N times
2. **Single Transaction**: Commits once instead of N times
3. **Reduced Overhead**: Less context switching and I/O operations
4. **Optimized Inserts**: Database can optimize a batch insert better than individual inserts

## Usage Examples

### Example 1: Batch URL Marking in Crawler

**Before:**
```python
for url in urls_to_process:
    # Process the URL
    lead_data = extract_lead(url)
    if lead_data:
        save_lead(lead_data)
    
    # Mark as seen (opens new transaction each time)
    mark_url_seen(url, run_id)
```

**After:**
```python
processed_urls = []

for url in urls_to_process:
    # Process the URL
    lead_data = extract_lead(url)
    if lead_data:
        save_lead(lead_data)
    
    # Collect URLs to mark
    processed_urls.append(url)

# Mark all URLs in a single batch transaction
mark_urls_seen_batch(processed_urls, run_id)
```

### Example 2: Batch Query Marking

**Before:**
```python
for query in queries:
    # Execute the query
    results = execute_search(query)
    process_results(results)
    
    # Mark as done (separate transaction)
    mark_query_done(query, run_id)
```

**After:**
```python
executed_queries = []

for query in queries:
    # Execute the query
    results = execute_search(query)
    process_results(results)
    
    # Collect queries
    executed_queries.append(query)

# Mark all queries in a single batch
mark_queries_done_batch(executed_queries, run_id)
```

### Example 3: Mixed Usage

You can still use individual operations when processing one item at a time, and batch operations when processing multiple items:

```python
# Single item - use individual function
if not is_url_seen(special_url):
    lead = process_special_url(special_url)
    mark_url_seen(special_url, run_id)

# Multiple items - use batch function
batch_urls = get_urls_from_portal()
leads = process_urls(batch_urls)
mark_urls_seen_batch(batch_urls, run_id)
```

## Implementation Details

### SQLite Implementation

```python
def mark_urls_seen_batch_sqlite(urls: list, run_id: Optional[int] = None) -> None:
    if not urls:
        return
    
    con = db()
    cur = con.cursor()
    try:
        # Use executemany for batch insert
        cur.executemany(
            "INSERT OR IGNORE INTO urls_seen(url, first_run_id, ts) VALUES(?, ?, datetime('now'))",
            [(url, run_id) for url in urls]
        )
        con.commit()
    finally:
        con.close()
```

### Django ORM Implementation

```python
def mark_urls_seen_batch(urls: list, run_id: Optional[int] = None) -> None:
    from telis_recruitment.scraper_control.models import UrlSeen, ScraperRun
    
    if not urls:
        return
    
    # Get ScraperRun if provided
    scraper_run = None
    if run_id:
        try:
            scraper_run = ScraperRun.objects.get(id=run_id)
        except ScraperRun.DoesNotExist:
            logger.warning(f"ScraperRun with id {run_id} not found")
    
    # Filter out URLs that already exist
    existing_urls = set(UrlSeen.objects.filter(url__in=urls).values_list('url', flat=True))
    new_urls = [url for url in urls if url not in existing_urls]
    
    if not new_urls:
        return
    
    # Bulk create UrlSeen entries
    url_seen_objects = [
        UrlSeen(url=url, first_run=scraper_run)
        for url in new_urls
    ]
    UrlSeen.objects.bulk_create(url_seen_objects, ignore_conflicts=True)
```

## Backward Compatibility

The existing individual functions (`mark_url_seen`, `mark_query_done`) remain unchanged and continue to work as before. This ensures:

- No breaking changes to existing code
- Gradual migration is possible
- Both patterns can coexist

## Testing

A comprehensive test suite (`test_batch_operations.py`) validates:

- ✓ Batch URL operations work correctly
- ✓ Batch query operations work correctly
- ✓ Empty batches are handled gracefully
- ✓ Duplicate entries are handled correctly
- ✓ Performance improvement is measurable

Run the tests:

```bash
python test_batch_operations.py
```

## Future Considerations

### Potential Optimizations

1. **Automatic Batching**: Could implement a context manager that automatically batches operations:
   ```python
   with batch_context(run_id):
       for url in urls:
           mark_url_seen(url)  # Automatically batched
   ```

2. **Adaptive Batch Size**: For very large batches (10,000+ items), could split into smaller chunks to avoid memory issues

3. **Lead Operations**: Could add batch operations for lead insertion/updates as well

### Migration Strategy

For code that processes many URLs/queries:

1. Identify loops that call `mark_url_seen` or `mark_query_done`
2. Collect items in a list instead of marking immediately
3. Call batch function after the loop
4. Test to verify behavior is unchanged
5. Measure performance improvement

## Summary

The batch transaction operations provide a simple way to dramatically improve performance when marking multiple URLs or queries. The 71x speedup demonstrates the importance of minimizing database transactions, and the backward-compatible implementation allows for gradual adoption across the codebase.
