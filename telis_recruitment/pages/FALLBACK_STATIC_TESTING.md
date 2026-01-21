# Manual Verification Guide for Fallback Static File Handler

## Overview
This guide helps verify that the fallback static file handler is working correctly.

## Prerequisites
- Django development server running
- A landing page created in the Page Builder

## Test Cases

### 1. Test CSS File Request
**URL:** `http://localhost:8000/src/main.css`

**Expected Response:**
- Status: 200 OK
- Content-Type: text/css
- Body: `/* File not found - placeholder */`

**Test Command:**
```bash
curl -i http://localhost:8000/src/main.css
```

### 2. Test JS File Request
**URL:** `http://localhost:8000/dist/bundle.js`

**Expected Response:**
- Status: 200 OK
- Content-Type: application/javascript
- Body: `// File not found - placeholder`

**Test Command:**
```bash
curl -i http://localhost:8000/dist/bundle.js
```

### 3. Test Source Map Request
**URL:** `http://localhost:8000/src/main.css.map`

**Expected Response:**
- Status: 200 OK
- Content-Type: application/json
- Body: `{}`

**Test Command:**
```bash
curl -i http://localhost:8000/src/main.css.map
```

### 4. Test All Routes
Test that all configured routes work:
```bash
# Test src/ route
curl -i http://localhost:8000/src/test.css

# Test dist/ route
curl -i http://localhost:8000/dist/test.js

# Test assets/ route
curl -i http://localhost:8000/assets/test.css

# Test css/ route
curl -i http://localhost:8000/css/test.css

# Test js/ route
curl -i http://localhost:8000/js/test.js
```

### 5. Test Nested Paths
**URL:** `http://localhost:8000/src/components/header.css`

**Expected Response:**
- Status: 200 OK
- Content-Type: text/css

**Test Command:**
```bash
curl -i http://localhost:8000/src/components/header.css
```

### 6. Verify Logging
After making requests, check the Django logs to ensure the warning messages are logged:

```bash
# Look for log entries like:
# WARNING - Missing static file requested: /src/main.css - Referer: unknown
grep "Missing static file requested" /path/to/django.log
```

### 7. Test with Referer Header
Test that the referer is logged correctly:

```bash
curl -i -H "Referer: http://localhost:8000/p/test-page/" http://localhost:8000/src/main.css
# Check logs for: Referer: http://localhost:8000/p/test-page/
```

## Automated Tests
Run the automated test suite:

```bash
cd telis_recruitment
python manage.py test pages.tests_fallback_static
```

Expected output:
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..........
----------------------------------------------------------------------
Ran 14 tests in 0.XXXs

OK
```

## Asset Validation Utility

### Test the validate_asset_references function
```python
from pages.utils import validate_asset_references

# Test HTML with suspicious paths
html = '''
<html>
    <head>
        <link rel="stylesheet" href="/src/main.css">
        <script src="/dist/bundle.js"></script>
    </head>
</html>
'''

warnings = validate_asset_references(html)
print(warnings)
# Expected: ['Möglicherweise fehlende Datei referenziert: /src/main.css', 
#            'Möglicherweise fehlende Datei referenziert: /dist/bundle.js']
```

## Integration Test
1. Create a landing page in the Page Builder with this HTML:
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/src/main.css">
    <script src="/dist/bundle.js"></script>
</head>
<body>
    <h1>Test Page</h1>
</body>
</html>
```

2. Publish the page

3. Visit the page in a browser

4. Check the browser console - you should see no 404 errors

5. Check the Django logs - you should see warning messages about the missing files

## Verification Checklist
- [ ] CSS files return 200 with text/css content type
- [ ] JS files return 200 with application/javascript content type
- [ ] Source map files return 200 with application/json content type
- [ ] Unknown file types return 200 with text/plain content type
- [ ] All configured routes (src, dist, assets, css, js) work
- [ ] Nested paths work correctly
- [ ] Missing files are logged with warning level
- [ ] Referer header is logged correctly
- [ ] Automated tests pass
- [ ] No 404 errors in browser console when viewing landing pages
- [ ] Existing functionality is not affected

## Rollback Plan
If issues are found:
1. Comment out the fallback routes in `telis_recruitment/telis/urls.py`
2. Restart the Django server
3. Missing static files will return to showing 404 errors
