# Production Security Checklist

This comprehensive checklist ensures your LUCA NRW Scraper deployment is secure and production-ready.

## 🔐 Pre-Deployment Security Checklist

### Django Core Security

- [ ] **SECRET_KEY**: Generated unique key (never use default)
  - Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
  - Minimum 50 characters
  - Never commit to version control

- [ ] **DEBUG Mode**: Disabled in production
  - Set `DEBUG=False` in `.env`
  - Verify error pages don't leak sensitive information
  - Test 404 and 500 error pages

- [ ] **ALLOWED_HOSTS**: Properly configured
  - List all production domains
  - Don't use wildcards (`*`)
  - Include both www and non-www versions if applicable
  - Example: `ALLOWED_HOSTS=example.com,www.example.com`

- [ ] **CSRF Protection**: Enabled and configured
  - Set `CSRF_TRUSTED_ORIGINS` with HTTPS URLs
  - Example: `CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com`
  - Verify CSRF tokens in forms work correctly

### HTTPS/SSL Configuration

- [ ] **SSL Certificate**: Valid and installed
  - Not self-signed (use Let's Encrypt, commercial CA, etc.)
  - Not expired
  - Covers all your domains/subdomains
  - Test with: `curl -I https://your-domain.com`

- [ ] **HTTPS Enforcement**: Enabled
  - Set `SECURE_SSL_REDIRECT=True`
  - Set `SESSION_COOKIE_SECURE=True`
  - Set `CSRF_COOKIE_SECURE=True`
  - Set `SECURE_HSTS_SECONDS=31536000` (1 year)

- [ ] **SSL Validation**: Strictly enabled
  - Set `ALLOW_INSECURE_SSL=0` (secure by default)
  - **Never** set to `1` in production
  - Verify scraper works with SSL validation enabled
  - Test scraping against HTTPS websites

### Secret Management

- [ ] **API Keys**: Securely stored
  - Never hardcode in source code
  - Use environment variables only
  - Rotate keys regularly (every 90 days recommended)
  - Use separate keys for dev/staging/production

- [ ] **Database Credentials**: Protected
  - Strong password (16+ characters, mixed case, numbers, symbols)
  - Not using default passwords
  - Stored in environment variables
  - Limited to application user only

- [ ] **No Secrets in Logs**: Verified
  - Review log files for accidentally logged secrets
  - Check Django error pages (with DEBUG=False)
  - Verify API keys not in scraper logs
  - Test error scenarios don't leak credentials

- [ ] **Environment Variables**: Secured
  - `.env` file has proper permissions (600)
  - `.env` file not committed to git (in `.gitignore`)
  - Environment variables not exposed via web interface
  - Secrets not passed in URLs or GET parameters

### Database Security

- [ ] **Database Configuration**: Hardened
  - Use PostgreSQL or MySQL (not SQLite) for production
  - Database on private network or localhost only
  - Enable SSL/TLS for database connections
  - Regular automated backups configured

- [ ] **Database User Permissions**: Restricted
  - Application user has minimum required permissions
  - No SUPERUSER privileges
  - Separate user for migrations vs. runtime
  - Read-only user for reporting if applicable

- [ ] **SQL Injection Protection**: Verified
  - Using Django ORM (no raw SQL)
  - If using raw SQL, using parameterized queries
  - Input validation on all user inputs
  - Test with common SQL injection payloads

### Authentication & Authorization

- [ ] **Admin Access**: Secured
  - Strong admin password (20+ characters)
  - Changed from default
  - 2FA enabled (if available)
  - Admin URL changed from `/admin/` (optional but recommended)

- [ ] **User Roles**: Properly configured
  - **Admin**: Full access, can manage all settings
  - **Manager**: Can manage leads, view reports, configure scraper
  - **Operator**: Can manage leads, start/stop scraper
  - **Viewer**: Read-only access to leads and reports

- [ ] **Password Policy**: Enforced
  - Minimum 12 characters
  - Complexity requirements
  - No common passwords
  - Regular password rotation (90 days)

- [ ] **Session Security**: Configured
  - `SESSION_COOKIE_HTTPONLY=True` (default in Django)
  - `SESSION_COOKIE_SECURE=True` (in production with HTTPS)
  - `SESSION_COOKIE_SAMESITE='Lax'` or `'Strict'`
  - Reasonable session timeout (e.g., 2 weeks)

### Network Security

- [ ] **Proxy Configuration**: If using proxies
  - Authenticated proxies only
  - Credentials stored securely
  - Test proxy connection security
  - Monitor for proxy failures

- [ ] **Rate Limiting**: Configured
  - `ASYNC_LIMIT` set appropriately (25-35 for production)
  - `ASYNC_PER_HOST` limited (2-3 for production)
  - Avoid overwhelming target servers
  - Monitor for 429 (Too Many Requests) responses

- [ ] **Firewall Rules**: Implemented
  - Only necessary ports open (80, 443)
  - Admin interfaces not exposed to internet
  - Database port not exposed to internet
  - SSH restricted to known IPs (if applicable)

- [ ] **CORS Configuration**: If using API
  - Whitelist specific origins only
  - Don't use `CORS_ALLOW_ALL_ORIGINS=True`
  - Verify allowed methods (GET, POST, etc.)
  - Test cross-origin requests

### Data Protection

- [ ] **Sensitive Data Handling**: Proper procedures
  - Personal data encrypted at rest (if required by GDPR)
  - Secure data deletion procedures
  - Data retention policy implemented
  - Privacy policy in place

- [ ] **File Uploads**: Secured
  - Validate file types (if applicable)
  - Scan for malware (if applicable)
  - Store outside web root
  - Limit file sizes

- [ ] **Backup Security**: Implemented
  - Automated backups scheduled
  - Backups encrypted
  - Backups stored off-site
  - Backup restoration tested

### Email Security (If using Brevo/Email features)

- [ ] **Email Authentication**: Configured
  - SPF records configured
  - DKIM signing enabled
  - DMARC policy set
  - Test with mail-tester.com

- [ ] **Brevo API Key**: Secured
  - Stored in environment variables
  - Not exposed in logs
  - Separate key for production
  - Monitor API usage

### Monitoring & Logging

- [ ] **Logging**: Properly configured
  - Log level set to `INFO` or `WARNING` (not DEBUG)
  - Logs rotated automatically
  - Logs don't contain secrets
  - Failed login attempts logged

- [ ] **Monitoring**: Active
  - Uptime monitoring configured
  - Error tracking set up (Sentry, etc.)
  - Resource monitoring (CPU, memory, disk)
  - SSL certificate expiration monitoring

- [ ] **Security Monitoring**: Enabled
  - Failed authentication attempts tracked
  - Unusual activity alerts
  - Scraper errors monitored
  - API rate limit monitoring

### Deployment Security

- [ ] **Server Hardening**: Applied
  - OS patches up to date
  - Unnecessary services disabled
  - Root login disabled
  - SSH key-based authentication only

- [ ] **Application Updates**: Managed
  - Dependency updates scheduled
  - Security patches applied promptly
  - Change management process in place
  - Rollback plan documented

- [ ] **Docker Security**: If using Docker
  - Images from trusted sources only
  - Images regularly updated
  - No secrets in Dockerfiles
  - Proper container isolation

## 🛡️ Role-Based Access Control (RBAC)

### CRM Permission Levels

| Role | Leads | Reports | Scraper | Settings | Users | API |
|------|-------|---------|---------|----------|-------|-----|
| **Admin** | Full | Full | Full | Full | Full | Full |
| **Manager** | Full | Full | Control | View | View | Limited |
| **Operator** | Full | View | Control | View | None | Limited |
| **Viewer** | View | View | View | None | None | None |

### Recommended Role Assignment

- **Limit Admin access**: Only 1-2 trusted administrators
- **Most users should be Operators**: Can work with leads and scraper
- **Use Manager for team leads**: Can access reports and analytics
- **Use Viewer for stakeholders**: Read-only access for oversight

## 📋 Security Review Schedule

### Daily
- [ ] Review failed login attempts
- [ ] Check scraper errors
- [ ] Monitor API usage

### Weekly
- [ ] Review access logs
- [ ] Check for unusual activity
- [ ] Verify backups completed

### Monthly
- [ ] Update dependencies
- [ ] Review user permissions
- [ ] Check SSL certificate expiration
- [ ] Test backup restoration

### Quarterly
- [ ] Rotate API keys
- [ ] Security audit
- [ ] Penetration testing (if applicable)
- [ ] Update documentation

## 🚨 Incident Response Plan

### If Security Breach Suspected

1. **Immediate Actions**:
   - Disable affected accounts
   - Change all credentials
   - Review access logs
   - Document everything

2. **Investigation**:
   - Determine scope of breach
   - Identify compromised data
   - Find entry point
   - Generate support bundle for analysis

3. **Recovery**:
   - Patch vulnerabilities
   - Restore from clean backup if needed
   - Notify affected parties if required
   - Update security measures

4. **Post-Incident**:
   - Document lessons learned
   - Update security procedures
   - Train team on new measures
   - Consider external security audit

## 🔍 Security Testing

### Before Going Live

```bash
# Test SSL configuration
curl -I https://your-domain.com

# Test SSL validation in scraper
python scriptname.py --once --industry recruiter --qpi 1

# Verify no secrets in logs
cat /path/to/logs | grep -i "api_key\|secret\|password"

# Check file permissions
ls -la .env

# Test authentication
# Try accessing admin with invalid credentials
# Verify lockout after multiple failures

# Generate support bundle and review for secrets
python manage.py create_support_bundle
```

### Security Scanning Tools

- **OWASP ZAP**: Web application security scanner
- **Bandit**: Python security linter
- **Safety**: Python dependency vulnerability checker
- **SSL Labs**: SSL/TLS configuration testing

```bash
# Check Python dependencies for vulnerabilities
pip install safety
safety check

# Scan code for security issues
pip install bandit
bandit -r telis_recruitment/
```

## ✅ Production Approval

Before deploying to production, this checklist must be completed and approved by:

- [ ] Technical lead
- [ ] Security officer (if applicable)
- [ ] System administrator

**Approval Date**: _______________  
**Approved By**: _______________  
**Next Review Date**: _______________

## 📚 Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [Configuration Profiles](../configs/README.md)

## 🆘 Support

If you need assistance with security configuration:

1. Generate a support bundle: `python manage.py create_support_bundle`
2. Review logs and configuration (redact secrets before sharing)
3. Contact your security team or create a GitHub issue

---

**Remember**: Security is an ongoing process, not a one-time checklist. Regular reviews and updates are essential.
