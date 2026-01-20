# Form Submit CSRF Exemption - Security Documentation

## Overview

The `form_submit` view in `pages/views.py` is decorated with `@csrf_exempt`, which disables Django's built-in Cross-Site Request Forgery (CSRF) protection for this endpoint.

## Why CSRF Exemption is Necessary

The CSRF exemption is required because:

1. **External Embedding**: Landing pages may be embedded in external websites, email campaigns, or third-party platforms where establishing a prior session with CSRF tokens is not feasible.

2. **Custom Domains**: Landing pages can be served from custom domains (configured via the domain management system), which may not share cookies with the main application domain.

3. **Marketing Channels**: Forms may be accessed from various marketing channels (social media, ads, QR codes) where users don't have an existing session.

4. **Cross-Domain Submissions**: When a form is hosted on `customer-domain.com` but submits to `app-domain.com/p/page-slug/submit/`, CSRF tokens won't work without complex cross-domain cookie setup.

## Alternative Security Measures

Since CSRF protection is disabled, the following alternative security measures are implemented:

### 1. Origin and Referer Validation
```python
origin = request.META.get('HTTP_ORIGIN', '')
referer = request.META.get('HTTP_REFERER', '')
```
- Logs the origin and referer of all submissions for security monitoring
- Can be extended to validate against allowed domains

### 2. Authentication Requirements
- The endpoint is PUBLIC and does not require authentication (by design for lead capture)
- However, it can only submit to PUBLISHED landing pages (not drafts)

### 3. Input Validation
- All form data is validated before processing
- Email format validation
- Required fields validation (email, name)
- Data is never executed as code

### 4. Rate Limiting (Recommended - TODO)
**Not yet implemented**. Consider adding:

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST')
@csrf_exempt
@require_POST
def form_submit(request, slug):
    # ...
```

Install: `pip install django-ratelimit`

### 5. ReCaptcha Integration (Recommended - TODO)
For production deployments with high traffic, consider adding Google ReCaptcha:

```python
from django.conf import settings
import requests

def verify_recaptcha(token):
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': token
        }
    )
    return response.json().get('success', False)
```

Frontend integration in landing page template:
```html
<script src="https://www.google.com/recaptcha/api.js"></script>
<div class="g-recaptcha" data-sitekey="YOUR_SITE_KEY"></div>
```

### 6. Lead Deduplication
- Duplicate submissions from the same email are merged (UPDATE instead of INSERT)
- Prevents spam submissions from creating multiple records

### 7. Security Logging
- All form submissions are logged with origin and referer
- Failed submissions are logged with error details
- Logs can be monitored for suspicious patterns

## Security Monitoring

### What to Monitor

1. **Suspicious Patterns**:
   - High volume of submissions from single IP
   - Submissions with missing or suspicious referers
   - Repeated failed submissions
   - Unusual data patterns (e.g., same email with different names)

2. **Abuse Indicators**:
   - Form submissions to unpublished pages (these are blocked)
   - Submissions with extremely long field values
   - Submissions with script tags or SQL injection attempts

3. **Log Analysis**:
   ```bash
   # Check recent submissions
   grep "Form submission" /var/log/django/app.log | tail -100
   
   # Find high-volume IPs
   grep "Form submission" /var/log/django/app.log | \
     awk '{print $NF}' | sort | uniq -c | sort -rn | head -20
   ```

## Production Recommendations

### Immediate Actions

1. **Enable HTTPS**:
   - Forms should ONLY be accessible over HTTPS
   - Set `SECURE_SSL_REDIRECT=True` in production settings
   - Configure `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`

2. **Implement Rate Limiting**:
   ```bash
   pip install django-ratelimit
   ```
   
   Update `form_submit` view to include rate limiting decorator.

3. **Add ReCaptcha** (if experiencing spam):
   - Sign up for Google ReCaptcha v3
   - Add ReCaptcha verification to form_submit
   - Update landing page templates to include ReCaptcha widget

### Long-term Improvements

1. **Web Application Firewall (WAF)**:
   - Deploy behind Cloudflare or AWS WAF
   - Configure bot detection and rate limiting at edge

2. **Honeypot Fields**:
   - Add hidden fields to forms that bots will fill but humans won't
   - Reject submissions with honeypot fields filled

3. **Submission Fingerprinting**:
   - Track browser fingerprints to detect automated submissions
   - Use libraries like `django-tracking2` or custom fingerprinting

4. **Email Verification**:
   - Send verification emails before considering leads as valid
   - Mark unverified leads differently in CRM

## Testing CSRF Protection

### Test that Regular CSRF-Protected Endpoints Work

```python
# Test that builder endpoints require CSRF token
import requests

response = requests.post(
    'https://your-domain.com/crm/pages/api/page-slug/save/',
    json={'html': '<div>test</div>'},
    headers={'Content-Type': 'application/json'}
)
# Should return 403 Forbidden without CSRF token
assert response.status_code == 403
```

### Test that form_submit Accepts Requests Without CSRF

```python
# Test that form_submit works without CSRF token
import requests

response = requests.post(
    'https://your-domain.com/p/page-slug/submit/',
    data={'email': 'test@example.com', 'name': 'Test User'},
)
# Should return 200 OK or redirect
assert response.status_code in [200, 302]
```

## Alternative Approaches Considered

### 1. SameSite Cookies with CSRF Tokens
**Why not used**: Doesn't work for cross-domain submissions, which is a key requirement.

### 2. Double Submit Cookie Pattern
**Why not used**: Requires JavaScript on the landing page and doesn't work for embedded forms.

### 3. Origin Header Validation
**Partially used**: We log origin headers but don't enforce them, as legitimate submissions may come from many domains.

### 4. Signed Form Tokens
**Could be implemented**: Generate a signed token when the landing page is rendered, include it in the form, and verify it on submission. This would work even without cookies.

Example implementation:
```python
from django.core.signing import TimestampSigner

signer = TimestampSigner()

# When rendering the landing page
form_token = signer.sign(f"{page.id}:{page.slug}")

# In form_submit view
try:
    page_data = signer.unsign(submitted_token, max_age=3600)  # 1 hour expiry
    page_id, page_slug = page_data.split(':')
    # Verify matches current page
except Exception:
    return JsonResponse({'success': False, 'error': 'Invalid or expired form'}, status=400)
```

This would provide CSRF-like protection without requiring cookies. Consider implementing if abuse becomes a problem.

## References

- [Django CSRF Documentation](https://docs.djangoproject.com/en/stable/ref/csrf/)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [django-ratelimit Documentation](https://django-ratelimit.readthedocs.io/)
- [Google reCAPTCHA Documentation](https://developers.google.com/recaptcha/docs/display)

## Questions?

For questions about this security decision, contact the security team or system administrator.
