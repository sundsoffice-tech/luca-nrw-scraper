# Adaptive Search System Documentation

## Overview

The adaptive search system implements a comprehensive, phase-based ("Wasserfall") approach to lead scraping with strict phone validation requirements. The system adapts its behavior based on performance metrics to optimize lead quality and minimize costs.

## Key Components

### 1. Phone Validation (`scriptname.py`)

**Functions:**
- `normalize_phone(phone: str) -> str`: Normalizes phone numbers to E.164 format
- `validate_phone(phone: str) -> Tuple[bool, str]`: Validates phone numbers with strict requirements
  - Length: 10-15 digits
  - Supports DE/intl formats
  - Detects mobile vs landline
  - Returns: (is_valid, phone_type)

**Usage:**
```python
from scriptname import validate_phone, normalize_phone

# Normalize
normalized = normalize_phone("0176 123 4567")
# Returns: "+491761234567"

# Validate
is_valid, phone_type = validate_phone("+491761234567")
# Returns: (True, "mobile")
```

### 2. Metrics Tracking (`metrics.py`)

**Classes:**
- `MetricsStore`: SQLite-backed metrics storage
- `DorkMetrics`: Per-dork performance metrics
- `HostMetrics`: Per-host drop rates and backoff

**Tracked Metrics:**
- Per-dork: queries_total, serp_hits, urls_fetched, leads_found, leads_kept, accepted_leads
- Per-host: hits_total, drops_by_reason, backoff status

**Usage:**
```python
from metrics import get_metrics_store

metrics = get_metrics_store("metrics.db")

# Record events
metrics.record_query("dork query")
metrics.record_url_fetch("dork query", "example.com")
metrics.record_lead_found("dork query")
metrics.record_accepted_lead("dork query")

# Check host backoff
host_metrics = metrics.get_host_metrics("example.com")
if host_metrics.is_backedoff():
    print("Host is backed off, skip")

# Get top performers
top_dorks = metrics.get_top_dorks(n=5)
```

### 3. Adaptive Dork Selection (`adaptive_dorks.py`)

**Algorithm:**
- ε-greedy bandit approach
- Maintains core_dorks (top performers) and explore_dorks (experimental)
- Dork score = accepted_leads / max(1, queries_total)
- 10-20% exploration rate
- 25% Google / 75% DDG source split

**Usage:**
```python
from adaptive_dorks import AdaptiveDorkSelector

selector = AdaptiveDorkSelector(
    metrics_store,
    all_dorks=["dork1", "dork2", ...],
    explore_rate=0.15
)

# Select dorks for this run
selected = selector.select_dorks(
    num_dorks=8,
    google_ratio=0.25
)

# Each selected dork has: dork, pool, source, score
for item in selected:
    print(f"{item['dork']} from {item['pool']} via {item['source']}")
```

### 4. Wasserfall Modes (`wasserfall.py`)

**Modes:**
- **Conservative**: DDG 15/min, 6-8 dorks, 20% explore
- **Moderate**: DDG 30/min, 6-8 dorks, 15% explore
- **Aggressive**: DDG 50/min, 8-10 dorks, 10% explore

**Transitions:**
- Up: Phone-find-rate ≥ threshold, low errors (after 3+ runs)
- Down: Phone-find-rate drops or high error rate

**Usage:**
```python
from wasserfall import WasserfallManager

manager = WasserfallManager(
    metrics_store,
    initial_mode="conservative",
    phone_find_rate_threshold=0.25
)

# Get current mode
mode = manager.get_current_mode()
print(f"DDG rate: {mode.ddg_bucket_rate}/min")
print(f"Dork slots: {mode.dork_slots_min}-{mode.dork_slots_max}")

# Check for transitions
manager.increment_run()
transition = manager.check_and_transition()
if transition:
    print(f"Transitioned to {transition['to_mode']}")
```

### 5. Caching (`cache.py`)

**Components:**
- `QueryCache`: Cache search results (24-48h TTL)
- `URLSeenSet`: Track seen URLs (7d TTL)
- `TTLCache`: Generic TTL cache

**Usage:**
```python
from cache import get_query_cache, get_url_seen_set

# Query cache
query_cache = get_query_cache(ttl_seconds=86400)

# Check cache
if query_cache.has_cached("test query", source="google"):
    results = query_cache.get_results("test query", source="google")
else:
    results = perform_search("test query")
    query_cache.set_results("test query", results, source="google")

# URL seen set
url_seen = get_url_seen_set(ttl_seconds=604800)

if not url_seen.has("https://example.com/page"):
    url_seen.add("https://example.com/page")
    # Fetch and process URL
```

### 6. Reporting (`reporting.py`)

**Reports:**
- Top-5/Flop-5 dorks by score
- Phone-find-rate
- Host backoff list
- Drops by reason breakdown

**Usage:**
```python
from reporting import ReportGenerator

reporter = ReportGenerator(metrics_store)

# Generate weekly report
report = reporter.generate_weekly_report(
    output_format="json",
    output_path="weekly_report.json"
)

# Log dork selections
reporter.log_dork_selection(
    selected_dorks,
    mode="moderate"
)
```

### 7. Integrated System (`adaptive_system.py`)

**High-level Interface:**

```python
from adaptive_system import create_system_from_env

# Create system with all dorks
system = create_system_from_env(all_dorks=DEFAULT_QUERIES)

# Select dorks for run
selected_dorks = system.select_dorks_for_run()

# During scraping loop
for dork_info in selected_dorks:
    dork = dork_info["dork"]
    source = dork_info["source"]
    
    # Check cache
    cached = system.get_cached_query_results(dork, source)
    if cached:
        results = cached
    else:
        results = perform_search(dork, source)
        system.cache_query_results(dork, source, results)
    
    system.record_query_execution(dork)
    system.record_serp_results(dork, len(results))
    
    for result in results:
        url = result["url"]
        
        # Check if should fetch
        should_fetch, reason = system.should_fetch_url(url)
        if not should_fetch:
            continue
        
        system.mark_url_seen(url)
        
        # Fetch and extract
        content = fetch_url(url)
        system.record_url_fetched(dork, url)
        
        lead = extract_lead(content)
        if lead:
            system.record_lead_found(dork)
            
            # Validate phone
            is_valid, phone_type = validate_phone(lead.get("telefon"))
            if not is_valid:
                system.record_lead_dropped(url, "no_phone")
                continue
            
            # Other validations...
            system.record_lead_kept(dork)
            
            # Final acceptance
            system.record_accepted_lead(dork)

# Complete run
system.complete_run()

# Get status
status = system.get_status()
print(f"Phone find rate: {status['phone_find_rate']:.2%}")
print(f"Wasserfall mode: {status['wasserfall']['current_mode']['name']}")

# Generate report
system.generate_report(output_format="json", output_path="report.json")
```

## Configuration

### Environment Variables

```bash
# Metrics
METRICS_DB=metrics.db

# Cache TTLs
QUERY_CACHE_TTL=86400      # 24 hours
URL_SEEN_TTL=604800        # 7 days

# Wasserfall
WASSERFALL_MODE=conservative  # conservative|moderate|aggressive

# Fetch Controls
HTTP_TIMEOUT=10            # 10 seconds
MAX_FETCH_SIZE=2097152     # 2 MB
ALLOW_PDF_NON_CV=0         # Only allow PDFs with CV hints
```

## Blacklists

### Host Blacklist (`DROP_PORTAL_DOMAINS`)

Portal/job boards that are automatically skipped before fetch:
- stepstone.de, indeed.com, monster.de
- linkedin.com, xing.com (job pages)
- qonto.com, accountable.de, sevdesk.de
- reddit.com, tiktok.com, ok.ru
- And 20+ more...

### Path Pattern Blacklist (`BLACKLIST_PATH_PATTERNS`)

URL path/title patterns that trigger skip:
- lebenslauf, vorlage, muster (templates)
- sitemap, seminar, academy, weiterbildung
- job, stellenangebot, news, blog, ratgeber, portal

### Generic Mailboxes (`DROP_MAILBOX_PREFIXES`)

Email localparts that trigger drop:
- info, kontakt, contact, support, service
- privacy, datenschutz, noreply, no-reply
- jobs, karriere

## Testing

Run tests with pytest:

```bash
# All tests
pytest tests/

# Specific test modules
pytest tests/test_phone.py
pytest tests/test_dropper.py
pytest tests/test_adaptive.py
pytest tests/test_cache.py
pytest tests/test_prefetch.py
```

## Best Practices

1. **Always validate phone numbers** before accepting leads
2. **Use the integrated system** (`AdaptiveSearchSystem`) for automatic coordination
3. **Monitor metrics regularly** to understand system performance
4. **Let Wasserfall adapt** - don't override mode transitions frequently
5. **Review weekly reports** to identify top/flop dorks
6. **Respect backoff periods** - don't force fetch from backed-off hosts
7. **Clear expired cache** periodically to save memory

## Monitoring

Key metrics to watch:
- **Phone find rate**: Should be ≥ 25% in steady state
- **Acceptance rate**: Accepted leads / Total leads found
- **Backoff rate**: Backed-off hosts / Total hosts
- **Dork performance**: Top vs Flop dork gap
- **Mode transitions**: Frequency and reasons

## Troubleshooting

**Low phone find rate:**
- Check if phone extraction regex is working
- Review dropped leads with reason="no_phone"
- Consider adjusting blacklist patterns

**High backoff rate:**
- Review host drop reasons
- May need to adjust backoff threshold (default 0.8)
- Consider adding more diverse sources

**No mode transitions:**
- Check if min_runs threshold is met (default 3)
- Verify phone_find_rate_threshold setting
- Review metrics persistence

**Cache not working:**
- Check TTL settings (may be too short)
- Verify cache.py module is imported
- Check for cache clear operations
