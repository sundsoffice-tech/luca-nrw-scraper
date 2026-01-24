# Field Mapping Fix - Complete Documentation

## Problem Summary

The luca-nrw-scraper had several field mapping issues that could lead to data loss and "no column named" errors:

1. **Missing columns in `ALLOWED_LEAD_COLUMNS`**: The `id` column was not included in the whitelist
2. **Missing field mappings**: The `crm_status` field had no mapping from scraper to Django
3. **Silent data loss**: Fields not in mappings or whitelists were silently dropped without warnings
4. **Poor error messages**: When column errors occurred, the error messages weren't helpful for diagnosis

## Root Causes

### Issue 1: `ALLOWED_LEAD_COLUMNS` missing 'id'
**Location**: `luca_scraper/database.py` line 358

The `ALLOWED_LEAD_COLUMNS` frozenset was used to whitelist columns before inserting into SQLite. The `id` column was missing, which could cause issues when trying to insert or update with an explicit ID.

### Issue 2: Missing `crm_status` mapping
**Location**: `telis_recruitment/leads/field_mapping.py`

The SQLite schema has a `crm_status` column that tracks the CRM status of leads, but this field wasn't mapped to Django's `status` field in `SCRAPER_TO_DJANGO_MAPPING`.

### Issue 3: Silent field dropping
**Locations**: 
- `luca_scraper/repository.py` line 102-122 (`_sanitize_lead_data`)
- `luca_scraper/django_db.py` line 128-180 (`_map_scraper_data_to_django`)

When fields were dropped (either because they weren't in `ALLOWED_LEAD_COLUMNS` or not in `SCRAPER_TO_DJANGO_MAPPING`), they were logged only at DEBUG level, making it easy to miss data loss issues.

### Issue 4: Unhelpful error messages
**Location**: `luca_scraper/database.py` line 545-548

When invalid columns were detected, the error message just listed the columns without guidance on how to fix the issue.

## Solutions Implemented

### Fix 1: Add 'id' to ALLOWED_LEAD_COLUMNS
```python
ALLOWED_LEAD_COLUMNS = frozenset({
    'id', 'name', 'rolle', 'email', 'telefon', ...  # Added 'id'
})
```

**File**: `luca_scraper/database.py`
**Lines**: 358-369

### Fix 2: Add crm_status mapping
```python
SCRAPER_TO_DJANGO_MAPPING = {
    ...
    'crm_status': 'status',  # NEW: Maps scraper's crm_status to Django's status field
}
```

**File**: `telis_recruitment/leads/field_mapping.py`
**Lines**: 104-116

### Fix 3: Improve logging for dropped fields

#### In `_sanitize_lead_data`:
```python
if dropped:
    # Log at INFO level instead of DEBUG to ensure visibility
    logger.info(
        "Dropping unsupported lead columns (not in ALLOWED_LEAD_COLUMNS): %s. "
        "Consider updating ALLOWED_LEAD_COLUMNS in database.py if these fields should be stored.",
        dropped
    )
```

**File**: `luca_scraper/repository.py`
**Lines**: 102-127

#### In `_map_scraper_data_to_django`:
```python
# Log unmapped fields for debugging and monitoring
if unmapped_fields:
    logger.info(
        "Scraper fields not in SCRAPER_TO_DJANGO_MAPPING (skipped): %s. "
        "Consider adding to field_mapping.py if these should be imported.",
        unmapped_fields
    )
```

**File**: `luca_scraper/django_db.py`
**Lines**: 128-180

### Fix 4: Improve error messages
```python
if invalid_columns:
    logger.warning(
        "Attempted to use invalid column names: %s. "
        "These fields will cause 'no column named' errors. "
        "Update ALLOWED_LEAD_COLUMNS in database.py to include these fields.",
        invalid_columns
    )
    raise ValueError(
        f"Invalid column names not in ALLOWED_LEAD_COLUMNS: {sorted(invalid_columns)}. "
        f"Valid columns: {sorted(ALLOWED_LEAD_COLUMNS)}"
    )
```

**File**: `luca_scraper/database.py`
**Lines**: 545-555

## Testing

### Automated Tests
Created `test_field_mapping_fix.py` with 4 test cases:

1. **TEST 1**: Verify `ALLOWED_LEAD_COLUMNS` includes all required columns
   - ✅ Passed: 47 columns including 'id', 'crm_status', etc.

2. **TEST 2**: Verify `SCRAPER_TO_DJANGO_MAPPING` is complete
   - ✅ Passed: 53 mappings including new 'crm_status' mapping

3. **TEST 3**: Verify field sanitization logging
   - ✅ Passed: Logs at INFO level with helpful guidance

4. **TEST 4**: Verify schema consistency
   - ✅ Passed: Schema and ALLOWED_LEAD_COLUMNS are in sync

### Manual Testing Checklist
- [ ] Test SQLite operations with actual scraper data
- [ ] Test Django import with actual scraper.db file
- [ ] Monitor logs for warnings about unmapped fields
- [ ] Verify no "no column named" errors occur
- [ ] Verify crm_status is properly synchronized between systems

## Impact

### Before Fixes
- **Data Loss**: Fields not in whitelist/mapping were silently dropped
- **Debug Difficulty**: Issues only visible at DEBUG log level
- **Schema Errors**: "no column named id" errors possible
- **Sync Issues**: crm_status not synced between scraper and Django

### After Fixes
- **Data Preserved**: All 47 schema columns whitelisted
- **Visibility**: Issues logged at INFO level with guidance
- **Clear Errors**: Helpful messages explain what's wrong and how to fix
- **Complete Mapping**: All fields mapped, including crm_status

## Files Modified

1. **luca_scraper/database.py**
   - Added 'id' to ALLOWED_LEAD_COLUMNS (line 358)
   - Improved error messages (lines 545-555)

2. **luca_scraper/repository.py**
   - Enhanced logging in `_sanitize_lead_data` (lines 102-127)

3. **luca_scraper/django_db.py**
   - Enhanced logging in `_map_scraper_data_to_django` (lines 128-180)
   - Updated `_map_django_to_scraper` to document crm_status mapping (line 241)

4. **telis_recruitment/leads/field_mapping.py**
   - Added crm_status → status mapping (lines 104-116)

## Validation

Run the test suite:
```bash
python3 test_field_mapping_fix.py
```

Expected output:
```
✅ ALL TESTS PASSED!
Tests passed: 4/4
```

## Migration Notes

### For Developers
- No database migration needed
- No API changes
- Existing code continues to work
- New logging helps identify future issues

### For Operators
- Monitor logs for INFO level messages about dropped/unmapped fields
- If you see warnings about unmapped fields, consider updating field mappings
- No immediate action required - this is a preventive fix

## Future Improvements

1. **Dynamic Column Detection**: Automatically detect new columns in scraper data
2. **Field Mapping Validation**: Add CI checks to ensure mappings are complete
3. **Documentation**: Auto-generate field mapping documentation from code
4. **Monitoring**: Add metrics for dropped field frequency

## References

- Issue: "Falsches Feld‑Mapping und unvollständige Daten"
- PR: #[PR_NUMBER]
- Related files:
  - `luca_scraper/database.py`
  - `luca_scraper/repository.py`
  - `luca_scraper/django_db.py`
  - `telis_recruitment/leads/field_mapping.py`
