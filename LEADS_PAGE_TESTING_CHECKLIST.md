# Manual Testing Checklist for Leads Page Fix

## Prerequisites
- [ ] Code deployed to test/staging environment
- [ ] Browser cache cleared (Ctrl+Shift+R or Cmd+Shift+R)
- [ ] Logged in as authenticated user with access to CRM

## Test Scenarios

### 1. Page Load
- [ ] Navigate to `/crm/leads/`
- [ ] Page loads without errors
- [ ] No JavaScript errors in browser console (F12)
- [ ] Leads table displays with data
- [ ] Pagination controls visible at bottom

**Expected:** Page loads successfully, no "Fehler beim Laden der Leads" error

### 2. Basic Pagination
- [ ] Check "Showing X to Y of Z leads" displays correctly
- [ ] Click "Next Page" button
- [ ] Verify different leads are shown
- [ ] Click "Previous Page" button
- [ ] Verify returns to previous page
- [ ] Click on page number buttons (1, 2, 3, etc.)
- [ ] Verify correct page loads

**Expected:** All pagination controls work smoothly

### 3. Per-Page Selection
- [ ] Change "Items per page" dropdown to 10
- [ ] Verify only 10 leads show
- [ ] Change to 25
- [ ] Verify 25 leads show
- [ ] Change to 50
- [ ] Verify 50 leads show (if available)

**Expected:** Page size changes work correctly

### 4. Status Filter
- [ ] Select "NEW" from Status filter
- [ ] Verify only NEW leads are shown
- [ ] Verify pagination updates with filtered count
- [ ] Select "CONTACTED"
- [ ] Verify only CONTACTED leads are shown
- [ ] Select "All" to clear filter
- [ ] Verify all leads are shown again

**Expected:** Status filtering works correctly

### 5. Source Filter
- [ ] Select "Scraper" from Source filter
- [ ] Verify only scraper leads are shown
- [ ] Select "Landing Page"
- [ ] Verify only landing page leads are shown
- [ ] Select "All" to clear filter
- [ ] Verify all leads are shown again

**Expected:** Source filtering works correctly

### 6. Score Filter
- [ ] Select "Hot (80+)" from Score filter
- [ ] Verify only leads with score >= 80 are shown
- [ ] Select "Medium (50-79)"
- [ ] Verify only leads with score 50-79 are shown
- [ ] Select "Low (<50)"
- [ ] Verify only leads with score < 50 are shown
- [ ] Select "All" to clear filter

**Expected:** Score filtering works correctly

### 7. Search Filter
- [ ] Type a lead name in search box
- [ ] Wait for debounce (300ms)
- [ ] Verify only matching leads are shown
- [ ] Type an email address
- [ ] Verify only matching leads are shown
- [ ] Type a phone number
- [ ] Verify only matching leads are shown
- [ ] Clear search box
- [ ] Verify all leads return

**Expected:** Search works for name, email, phone, and company

### 8. Combined Filters
- [ ] Apply Status filter: "NEW"
- [ ] Apply Source filter: "Scraper"
- [ ] Apply Score filter: "Hot (80+)"
- [ ] Verify only leads matching all criteria are shown
- [ ] Add search term
- [ ] Verify results are further filtered
- [ ] Clear all filters
- [ ] Verify all leads return

**Expected:** Multiple filters work together correctly

### 9. Export CSV
- [ ] Apply some filters (e.g., Status = NEW)
- [ ] Click "Export CSV" button
- [ ] Verify CSV file downloads
- [ ] Open CSV file
- [ ] Verify it contains ALL filtered leads (not just current page)
- [ ] Verify headers are correct
- [ ] Verify data is accurate

**Expected:** Export includes all filtered results

### 10. Bulk Operations
- [ ] Select 2-3 leads using checkboxes
- [ ] Verify "X leads selected" message appears
- [ ] Click "Change Status" → Select new status
- [ ] Confirm operation
- [ ] Verify leads' status changed
- [ ] Verify page reloads with updated data

**Expected:** Bulk operations work correctly

### 11. Lead Detail View
- [ ] Click "👁️" (eye icon) on a lead
- [ ] Verify slide-over panel opens from right
- [ ] Verify lead details are displayed correctly
- [ ] Click "← Zurück" to close
- [ ] Verify panel closes smoothly

**Expected:** Lead detail view works correctly

### 12. Sort Columns
- [ ] Click "Name" column header
- [ ] Verify leads sort by name (ascending)
- [ ] Click again
- [ ] Verify leads sort by name (descending)
- [ ] Try sorting by other columns (Status, Score, Created)
- [ ] Verify sorting works for each

**Expected:** Column sorting works correctly

### 13. Page Navigation After Filters
- [ ] Apply a filter that has many results
- [ ] Go to page 2
- [ ] Verify correct results for page 2
- [ ] Apply another filter
- [ ] Verify returns to page 1
- [ ] Verify filtered results shown

**Expected:** Pagination resets to page 1 when filters change

### 14. Edge Cases
- [ ] Apply filters that return 0 results
- [ ] Verify "Keine Leads gefunden" message shows
- [ ] Clear filters
- [ ] Verify leads return
- [ ] Navigate to a high page number
- [ ] Apply filter with fewer results
- [ ] Verify doesn't show empty page

**Expected:** Edge cases handled gracefully

### 15. Performance
- [ ] Apply filter with many results (100+)
- [ ] Verify page loads quickly (< 2 seconds)
- [ ] Navigate between pages
- [ ] Verify transitions are smooth
- [ ] Apply multiple filters in quick succession
- [ ] Verify debouncing works (search waits 300ms)

**Expected:** Performance is acceptable

## Browser Compatibility
Repeat key tests in:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Edge

## API Verification
Check browser Network tab (F12 → Network):
- [ ] Request to `/api/leads/?page=1&page_size=25` is made
- [ ] Response includes `count`, `results`, `next`, `previous`
- [ ] Filter parameters are included in URL (e.g., `&status=NEW`)
- [ ] Search parameter is included (e.g., `&search=keyword`)

## Console Verification
Check browser Console (F12 → Console):
- [ ] No JavaScript errors
- [ ] No warnings about pagination
- [ ] `loadLeads()` executes without errors

## Acceptance Criteria (from Problem Statement)
- [ ] ✅ Leads page loads without JavaScript errors
- [ ] ✅ Leads are displayed correctly in the table
- [ ] ✅ Pagination works (prev/next buttons, page numbers)
- [ ] ✅ Filters work correctly (status, source, score, search)
- [ ] ✅ Export CSV still works
- [ ] ✅ Bulk operations still work
- [ ] ✅ Lead detail slide-over still works

## Regression Testing
- [ ] No existing functionality is broken
- [ ] Page styling remains consistent
- [ ] All buttons and controls are functional
- [ ] No console errors or warnings

## Issues Found
Document any issues discovered during testing:

| Issue | Severity | Description | Steps to Reproduce |
|-------|----------|-------------|-------------------|
|       |          |             |                   |

## Sign-Off
- Tester: _______________
- Date: _______________
- Environment: _______________
- Result: [ ] PASS [ ] FAIL [ ] CONDITIONAL PASS

## Notes
Additional observations:
