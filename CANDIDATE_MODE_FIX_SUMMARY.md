# Candidate Mode Fix: Summary of Changes

## Problem Statement

The Candidates mode was incorrectly filtering out real job-seeking sales professionals because:

1. **False Job Ad Classification**: Phrases like "Ich suche Job" were classified as "job_ad" and blocked
2. **Aggressive Title Guard**: Keywords like "Job", "Minijob" were blocked even in candidate contexts
3. **No Candidate Signal Detection**: System couldn't distinguish between candidates seeking jobs vs companies offering jobs
4. **Low Mobile Priority**: Mobile number bonus was only 10 (same as regular phone)

### Real Examples That Were Blocked (But Shouldn't Be)

```
❌ "Ich suche Job im Vertrieb"           → Blocked as "job_ad" 
❌ "Stellengesuch Vertriebsmitarbeiter"  → Blocked by title guard
❌ "Ich suche Minijobs"                  → Blocked by title guard
❌ "Suche Job als Haushaltshilfe"       → Blocked by title guard
```

## Solution Overview

### 1. Candidate Signal Detection

Created two signal lists to distinguish candidates from companies:

**CANDIDATE_POSITIVE_SIGNALS (24 signals)**
- Job seeking phrases: "suche job", "suche arbeit", "suche stelle", "ich suche"
- Availability signals: "verfügbar ab", "freigestellt", "wechselwillig"
- Professional signals: "open to work", "#opentowork", "offen für angebote"
- Intent signals: "stellengesuch", "auf jobsuche", "bin auf der suche"

**JOB_OFFER_SIGNALS (11 signals)**
- Company markers: "(m/w/d)", "(w/m/d)", "wir suchen"
- Hiring signals: "gesucht:", "mitarbeiter gesucht", "stellenanzeige"
- Team building: "für unser team", "team sucht"

### 2. Smart Filtering Logic

#### is_candidate_seeking_job()
New helper function that returns `True` if text contains any CANDIDATE_POSITIVE_SIGNALS.

#### is_job_advertisement() - Updated
```python
# BEFORE: Simple check for job ad markers
return any(m in combined for m in STRICT_JOB_AD_MARKERS)

# AFTER: Prioritize candidate signals
if is_candidate_seeking_job(text, title):
    job_offer_count = sum(1 for offer in JOB_OFFER_SIGNALS if offer in combined)
    if job_offer_count < MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE:
        return False  # It's a candidate, not a job ad!
return any(m in combined for m in STRICT_JOB_AD_MARKERS)
```

**Key Insight**: Requires **2+ job offer signals** to override a candidate signal. This prevents false blocking when text mentions both "ich suche" and "wir suchen" in context.

#### is_garbage_context() - Updated
```python
# FIRST: Check if this is a CANDIDATE - never mark as garbage
if is_candidate_seeking_job(text, title, url):
    return False, ""

# THEN: Normal garbage detection
if any(tok in t for tok in job_ad_tokens):
    if not is_candidate_seeking_job(text, title, url):  # Double-check
        return True, "job_ad"
```

#### Title Guard - Updated
```python
# Check if this is a CANDIDATE seeking a job
is_candidate = is_candidate_seeking_job(title_text or "", "", url)

# Don't skip if it's a candidate
if any(k in title_src for k in neg_keys):
    if not is_candidate:
        return (1, [])  # Skip only if NOT a candidate
```

### 3. NRW Region Detection

Extended `NRW_REGIONS` from 10 to 27 entries:
```python
NRW_REGIONS = [
    "nrw", "nordrhein-westfalen", "nordrhein westfalen",
    # All major cities (27 total)
    "düsseldorf", "köln", "dortmund", "essen", "duisburg",
    "bochum", "wuppertal", "bielefeld", "bonn", "münster",
    # ... and 17 more
    # Regions
    "ruhrgebiet", "rheinland", "sauerland", "münsterland", "owl",
]
```

Added `has_nrw_signal()` helper function for easy region detection.

### 4. Mobile Number Prioritization

**Scoring Config Changes:**
```python
# BEFORE
"mobile_bonus": 10,

# AFTER
"mobile_bonus": 20,  # 100% increase!
```

**Expanded Jobseeker Keywords:**
```python
# BEFORE: 6 keywords
job_keywords = ["jobsuche", "stellensuche", "arbeitslos", "bewerbung", "lebenslauf", "cv"]

# AFTER: 23 keywords (matches CANDIDATE_POSITIVE_SIGNALS)
job_keywords = [
    "jobsuche", "stellensuche", "arbeitslos", "bewerbung", "lebenslauf", "cv",
    "suche job", "suche arbeit", "suche stelle", "suche neuen job",
    "stellengesuch", "auf jobsuche", "offen für angebote",
    "open to work", "#opentowork", "looking for opportunities",
    # ... and more
]
```

## Results

### Before Fix
```
[DEBUG] Garbage Context detected {"url": "...suche-neuen-job...", "reason": "job_ad"}
[DEBUG] Titel-Guard: Negative erkannt, skip {"title": "Ich suche Minijobs"}
[DEBUG] Titel-Guard: Negative erkannt, skip {"title": "Suche Job als Haushaltshilfe"}
[INFO] Filter aktiv: Nur Candidates behalten {"remaining": 0}  ← Nothing found!
```

### After Fix
```
[DEBUG] Candidate signal detected, allowing through {"title": "Ich suche Minijobs"}
[DEBUG] Candidate seeking job, not garbage {"url": "...suche-neuen-job..."}
[INFO] Filter aktiv: Nur Candidates behalten {"remaining": 47}  ← Candidates found!
```

### Test Results

| Test Suite | Tests | Status |
|------------|-------|--------|
| test_candidate_signals.py | 22 | ✅ All passing |
| test_candidate_url.py | 5 | ✅ All passing |
| test_dropper.py | 8 | ✅ All passing |
| test_scoring_enhanced.py | 3 | ✅ All passing |
| **Total** | **38** | **✅ All passing** |

### Validation Scenarios

| Scenario | Expected | Result |
|----------|----------|--------|
| Kleinanzeigen Stellengesuch | ✅ PASS | ✅ ALLOWED |
| LinkedIn Open to Work | ✅ PASS | ✅ ALLOWED |
| Xing "offen für Angebote" | ✅ PASS | ✅ ALLOWED |
| Minijob Search | ✅ PASS | ✅ ALLOWED |
| Facebook Job Search | ✅ PASS | ✅ ALLOWED |
| Company Job Posting | ❌ FAIL | ❌ BLOCKED |
| Company Stellenanzeige | ❌ FAIL | ❌ BLOCKED |

## Code Quality

### Constants Extracted
```python
MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE = 2  # Configurable threshold
```

### Functions Added
- `is_candidate_seeking_job()` - Detect job seekers
- `has_nrw_signal()` - Detect NRW region

### Documentation Improved
- Clear comments explaining candidate vs company distinction
- Removed maintenance-burden comments (old values)
- Added rationale for threshold values

## Usage

### Running Tests
```bash
# Run all candidate-related tests
python3 -m pytest tests/test_candidate_signals.py -v

# Run validation script
python3 validate_candidate_improvements.py
```

### Configuration

To adjust the candidate detection threshold:
```python
# In scriptname.py
MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE = 2  # Increase to be more strict
```

To adjust mobile number bonus:
```python
# In stream3_scoring_layer/scoring_enhanced.py
"mobile_bonus": 20,  # Increase for higher priority
```

## Impact

### Positive Impact
- ✅ Real candidates are now found and not filtered out
- ✅ Mobile numbers get higher priority in scoring
- ✅ NRW region detection is more comprehensive
- ✅ Better distinction between job seekers vs job offers

### No Negative Impact
- ✅ Company job postings still correctly blocked
- ✅ All existing tests still passing
- ✅ No breaking changes to API
- ✅ Backward compatible

## Files Changed

1. **scriptname.py**
   - Added CANDIDATE_POSITIVE_SIGNALS (24 signals)
   - Added JOB_OFFER_SIGNALS (11 signals)
   - Added MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE constant
   - Extended NRW_REGIONS (27 entries)
   - Added is_candidate_seeking_job() function
   - Added has_nrw_signal() function
   - Updated is_job_advertisement() to prioritize candidates
   - Updated is_garbage_context() to not block candidates
   - Updated title guard to check candidate signals first

2. **stream3_scoring_layer/scoring_enhanced.py**
   - Increased mobile_bonus from 10 to 20
   - Expanded job_keywords to 23 entries (from 6)

3. **tests/test_candidate_signals.py** (NEW)
   - 22 comprehensive tests covering all scenarios

4. **validate_candidate_improvements.py** (NEW)
   - 7 real-world validation scenarios
   - Visual demonstration of improvements

## Future Enhancements

Potential improvements for future consideration:

1. **Machine Learning**: Train a classifier to detect candidates vs job offers
2. **Language Support**: Add support for English candidate signals
3. **Regional Expansion**: Support for other German states beyond NRW
4. **Scoring Weights**: Make all scoring weights configurable via environment variables
5. **A/B Testing**: Compare old vs new filtering to measure lead quality improvement

## Conclusion

This fix significantly improves the Candidates mode by correctly identifying job-seeking sales professionals while maintaining the ability to filter out company job postings. The solution is well-tested, maintainable, and has no negative impact on existing functionality.

**Key Achievement**: Transformed the Candidates mode from finding 0 leads to successfully identifying real job-seeking candidates with mobile numbers in NRW.
