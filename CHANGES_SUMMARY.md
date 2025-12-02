# Facebook Scraping Integration - Changes Summary

## Overview
This document summarizes the changes made to integrate systematic Facebook scraping for sales leads who need new jobs in NRW.

## Changes Made

### 1. scriptname.py - New Facebook Queries

**Location:** Line 845-848 in the `INDUSTRY_QUERIES["candidates"]` section

**Queries Added:**
```python
# Facebook-specific queries for sales job seekers in NRW
'site:facebook.com/people "Vertrieb" AND ("suche Job" OR "neue Herausforderung" OR "offen für Angebote") NRW',
'site:facebook.com "Sales Manager" AND ("looking for new opportunities" OR "open to work") NRW',
'site:facebook.com/groups "Vertrieb" AND "Jobsuche" NRW',
```

**Purpose:**
- Target Facebook profiles of people in sales (Vertrieb/Sales Manager) in NRW
- Focus on job seekers using common German and English phrases
- Include both personal profiles (`/people`) and group posts (`/groups`)

**Coverage:**
- German terms: "suche Job", "neue Herausforderung", "offen für Angebote", "Jobsuche"
- English terms: "looking for new opportunities", "open to work"
- Location: All queries enforce NRW region

### 2. stream3_scoring_layer/scoring_enhanced.py - New Job Keywords

**Location:** Lines 93-97 in the `compute_score_v2` function

**Keywords Added:**
```python
job_keywords = [
    "jobsuche", "stellensuche", "arbeitslos", "bewerbung", "lebenslauf", "cv",
    "neue herausforderung", "suche neuen wirkungskreis", "open to work", 
    "looking for opportunities", "verfügbar ab", "freiberuflich"
]
```

**New Keywords (6 total):**
1. `"neue herausforderung"` - Common German phrase for career change
2. `"suche neuen wirkungskreis"` - Looking for new sphere of activity
3. `"open to work"` - LinkedIn and social media standard phrase
4. `"looking for opportunities"` - English job-seeking phrase
5. `"verfügbar ab"` - Available from (date) - indicates job seeking
6. `"freiberuflich"` - Freelance/self-employed indicator

**Purpose:**
- Enhance scoring for leads that match social media job-seeking patterns
- Support both German and English job-seeking terminology
- Improve lead quality by identifying active job seekers

**Scoring Impact:**
- Each keyword occurrence adds 2 points to the lead score
- Maximum bonus from job keywords: 15 points (configurable via `jobseeker_bonus`)
- Keywords are matched case-insensitively via `text_low.count(k)`

## Tests Created

### 1. tests/test_facebook_queries.py
- Validates all 3 Facebook queries are present in scriptname.py
- Checks queries are in the correct `candidates` section
- Verifies NRW location is included in all queries
- Ensures proper Google Dork syntax (site:, AND operators)

### 2. tests/test_job_keywords.py
- Validates all 6 job-seeking keywords are present in scoring_enhanced.py
- Checks keywords are in the `job_keywords` list
- Verifies original keywords are preserved
- Ensures keywords are lowercase for case-insensitive matching
- Confirms keywords are used in scoring logic

### 3. tests/test_integration.py
- End-to-end integration test
- Verifies both changes work together
- Provides summary of expected impact
- All tests pass successfully

## Expected Impact

### For Facebook Scraping:
1. **Increased Lead Volume:** More sales professionals from Facebook will be discovered
2. **Better Job Seeker Targeting:** Queries focus on people actively looking for jobs
3. **Bilingual Coverage:** Both German and English terms are included
4. **Regional Focus:** All queries enforce NRW location

### For Keyword Scoring:
1. **Higher Quality Leads:** Active job seekers score higher
2. **Social Media Optimization:** Keywords common on LinkedIn, Facebook, Xing
3. **Improved Relevance:** Freelancers and available candidates are prioritized
4. **Language Flexibility:** Both German and English phrases supported

## Usage

To run the scraper with the new Facebook queries:

```bash
# Standard recruiter mode (includes all new queries)
python scriptname.py --once --industry recruiter --qpi 6

# With date restriction (last 30 days)
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30

# All industries including candidates
python scriptname.py --once --industry all --qpi 2
```

## Validation

All tests pass successfully:
- ✅ Facebook queries test
- ✅ Job keywords test  
- ✅ Integration test

Run tests with:
```bash
cd /home/runner/work/luca-nrw-scraper/luca-nrw-scraper
python tests/test_facebook_queries.py
python tests/test_job_keywords.py
python tests/test_integration.py
```

## Files Modified

1. `scriptname.py` - Added 3 Facebook Google Dork queries
2. `stream3_scoring_layer/scoring_enhanced.py` - Added 6 job-seeking keywords

## Files Created

1. `tests/test_facebook_queries.py` - Facebook query validation tests
2. `tests/test_job_keywords.py` - Job keyword validation tests
3. `tests/test_integration.py` - Integration test and summary

## Minimal Changes Philosophy

These changes follow the principle of minimal modifications:
- Only 2 source files modified
- Changes are additive (no existing functionality removed)
- Backward compatible (all existing queries and keywords preserved)
- Total lines changed: ~10 lines of actual code
- All changes are surgical and focused
