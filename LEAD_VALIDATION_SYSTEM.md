# Lead Validation System Documentation

## Overview

This document describes the self-learning lead validation system implemented to ensure only high-quality leads with mobile contact information are saved, while filtering out job postings and other low-quality content.

⭐ **NEW: Talent Hunt Mode** - See [TALENT_HUNT_MODE.md](TALENT_HUNT_MODE.md) for details on the new mode that finds active sales professionals (not job seekers) and uses different validation rules.

## Core Rules

### 1. Mobile-Only Validation ✅ CRITICAL (Relaxed in Talent Hunt Mode)

**RULE: Only mobile numbers qualify as valid leads.**

⭐ **EXCEPTION IN TALENT HUNT MODE**: Landline numbers and email contacts are also accepted when searching for active professionals.

- **Landline numbers alone**: REJECTED (except in talent_hunt mode)
- **Email-only contacts**: REJECTED (except in talent_hunt mode)
- **Mobile numbers**: ACCEPTED (only valid lead type)

**Implementation:**
- Function: `is_mobile_number()` in `learning_engine.py`
- Validates against complete 3-digit mobile prefix lists:
  - Germany (DE): 150-179 (excluding some ranges)
  - Austria (AT): 660-689 
  - Switzerland (CH): 760-799

**Where Applied:**
- `should_drop_lead()` in scriptname.py (line 2180)
- `insert_leads()` in scriptname.py (line 627)
- Snippet processing in scriptname.py (line 4880+)

**Code Reference:**
```python
# Normalize phone first before checking if it's mobile
normalized_phone = normalize_phone(phone)
if not is_mobile_number(normalized_phone):
    return _drop("not_mobile_number")
```

### 2. Job Posting Detection ✅ CRITICAL (Intelligence Extraction in Talent Hunt Mode)

**RULE: Job postings (Stellenanzeigen) must NEVER be saved as leads - even with mobile numbers!**

⭐ **NEW IN TALENT HUNT MODE**: Job postings are no longer discarded but used for competitive intelligence:
- Extract company information
- Identify HR contacts for referrals
- Track competitor hiring activity
- Analyze salary/benefits offerings

Job postings are company advertisements for hiring, not actual sales leads. They must be filtered out to maintain lead database quality.

**Detection Methods:**
1. **URL Patterns**: `/jobs/`, `/karriere/`, `/stellenangebot/`, `/vacancy/`, `/career/`, etc.
2. **Title Patterns**: "sucht", "gesucht", "Stellenangebot", "Job bei", etc.
3. **Content Signals**: Multiple indicators like "(m/w/d)", "Wir suchen", "Bewerbung", "Job-ID", etc.

**Implementation:**
- Function: `is_job_posting()` in `learning_engine.py` (lines 407-520)
- New Function: `extract_competitor_intel()` in `learning_engine.py` ⭐
- Checked BEFORE lead saving in:
  - `should_drop_lead()` (line 2167)
  - `insert_leads()` (line 613)
  - `should_skip_url_prefetch()` (line 2119)
  - Snippet processing (line 4870)

**Code Reference:**
```python
# CRITICAL: Check for job postings first - NEVER save as lead
if is_job_posting(url=page_url, title=title, snippet=lead.get("opening_line", ""), content=text):
    # NEW: In talent_hunt mode, extract competitive intelligence
    if _is_talent_hunt_mode():
        intel = extract_competitor_intel(url, title, snippet, text)
        # Store intelligence for later analysis
    return _drop("job_posting")
```

### 3. Self-Learning System

The system learns from successful leads (those with mobile numbers) to optimize future searches.

**Learning Database:**
- Table: `success_patterns` in SQLite
- Tracks: domains, query_terms, url_paths, content_signals
- Scoring: confidence_score = success_count / (success_count + fail_count + 1)

**When Learning Occurs:**
- Automatically triggered when a lead with mobile number is successfully inserted
- Function: `learn_from_success()` in `learning_engine.py`
- Called from: `insert_leads()` in scriptname.py (lines 672-680)

**Code Reference:**
```python
# Learn from successful lead (with mobile number)
if learning_engine:
    try:
        query_context = r.get("_query_context", "")
        learning_engine.learn_from_success(r, query=query_context)
    except Exception as e:
        log("debug", "Learning failed", error=str(e))
```

**Pattern Types Tracked:**
1. **domain**: e.g., "example.com"
2. **query_term**: e.g., "vertrieb", "handynummer"
3. **url_path**: e.g., "team", "kontakt"
4. **content_signal**: e.g., "vertrieb", "mobile"

### 4. Snippet-Jackpot Processing

Snippet-jackpots are search results where contact data is already visible in the snippet (without visiting the page).

**Processing Flow:**
1. **Job Posting Check**: First check if snippet is a job posting → REJECT if yes
2. **Mobile Number Check**: Extract and validate mobile numbers from snippet
3. **Decision:**
   - Has mobile number + NOT job posting → Save as lead + trigger learning
   - Has landline only → Skip snippet, allow deep crawl (might find mobile on page)
   - Has neither → Skip

**Code Location:** scriptname.py, lines 4870-4900

### 5. Smart Pre-filtering

**Whitelist Patterns** (always allowed through pre-filter):
```python
ALWAYS_ALLOW_PATTERNS = [
    r'industrievertretung',
    r'handelsvertret',
    r'vertriebspartner',
    r'/ansprechpartner/',
    r'/team/',
    r'/ueber-uns/',
    r'/kontakt/',
    r'/impressum',
]
```

**Snippet-Jackpot Bypass:**
- URLs with contact data in snippets bypass blacklist filtering
- Exception: Job postings are still blocked

**Code Location:** scriptname.py, lines 2111-2151

## Testing

### Test Coverage

1. **Mobile Number Detection**: `tests/test_learning_engine.py::TestMobileNumberDetection`
   - Tests all DE/AT/CH mobile prefixes
   - Tests landline rejection
   - Tests invalid number rejection

2. **Job Posting Detection**: `tests/test_learning_engine.py::TestJobPostingDetection`
   - Tests URL pattern detection
   - Tests title pattern detection
   - Tests content signal detection
   - Tests false positives (personal profiles, contact pages)

3. **Integration Tests**: `tests/test_lead_validation.py`
   - Tests mobile-only validation in lead processing
   - Tests job posting filter in lead processing
   - Tests lead insertion with validation
   - Tests learning integration

### Running Tests

```bash
# All learning engine tests
pytest tests/test_learning_engine.py -v

# All validation tests
pytest tests/test_lead_validation.py -v

# Quick mobile validation check
pytest tests/test_learning_engine.py::TestMobileNumberDetection -v
```

## Expected Results

Based on the problem statement requirements:

| Metric | Before | After |
|--------|--------|-------|
| Leads per Run | 0 | 5-15 (only with mobile) |
| Stellenanzeigen as Leads | possible | 0 (excluded) |
| Verarbeitungsquote | 24% | 60-70% |
| Lernfähigkeit | none | automatic |

## Backward Compatibility

✅ **No breaking changes:**
- Existing `leads` table schema unchanged
- New `success_patterns` table is additive only
- All function signatures backward compatible
- All existing exports continue to work

## Future Enhancements

### Potential Improvements:
1. Query optimization using learned patterns
2. Domain reputation scoring
3. Automatic pattern pruning (remove low-confidence patterns)
4. A/B testing of different filtering strategies
5. Real-time learning dashboard

### Integration Points:
- Query generation should consult `learning_engine.generate_optimized_queries()`
- Failed URL processing should call `learning_engine.increment_fail()`
- Regular analysis of `success_patterns` table for insights

## Troubleshooting

### Common Issues:

1. **No leads being saved**
   - Check: Are phones being normalized before mobile validation?
   - Check: Is `is_mobile_number()` being called with normalized phone?
   - Debug: Log phone numbers at validation points

2. **Job postings being saved as leads**
   - Check: Is `is_job_posting()` called BEFORE lead saving?
   - Check: Are all three detection methods (URL, title, content) active?
   - Debug: Add logging to job posting detection

3. **Learning not working**
   - Check: Is `_LEARNING_ENGINE` initialized?
   - Check: Are leads being saved with `_query_context`?
   - Debug: Check `success_patterns` table for entries

### Debug Commands:

```python
# Check mobile number validation
from learning_engine import is_mobile_number
from scriptname import normalize_phone
phone = "01761234567"
print(f"Normalized: {normalize_phone(phone)}")
print(f"Is mobile: {is_mobile_number(normalize_phone(phone))}")

# Check job posting detection
from learning_engine import is_job_posting
result = is_job_posting(url="https://example.com/jobs/sales")
print(f"Is job posting: {result}")

# Check learning patterns
from scriptname import get_learning_engine
engine = get_learning_engine()
stats = engine.get_pattern_stats()
print(stats)
```

## Contact

For questions or issues with the lead validation system, refer to:
- Code review comments in PR
- Test cases in `tests/test_learning_engine.py` and `tests/test_lead_validation.py`
- This documentation
