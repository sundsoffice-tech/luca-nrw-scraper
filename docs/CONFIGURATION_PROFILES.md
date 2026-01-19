# Configuration Profiles Guide

This guide explains how to use LUCA NRW Scraper's configuration profiles for different deployment scenarios.

## 📋 Overview

LUCA provides pre-configured environment profiles optimized for different use cases:

1. **Production Safe** - Secure, stable, production-ready
2. **High Volume** - Maximum throughput for bulk operations
3. **Debug Mode** - Development and troubleshooting

Each profile is a complete `.env` configuration file with settings tuned for specific scenarios.

## 🎯 When to Use Each Profile

### Production Safe Profile

**Best for:**
- Production deployments
- Customer-facing systems
- Environments handling real/sensitive data
- Compliance-required systems (GDPR, etc.)
- Small to medium volume operations

**Characteristics:**
- Maximum security (SSL validation, secure cookies, HSTS)
- Conservative resource limits
- Balanced performance
- Minimal logging (INFO level)
- Single-run scraper mode

**Not suitable for:**
- High-volume bulk scraping
- Development/debugging
- Systems behind corporate proxies with self-signed certs (use with caution)

### High Volume Profile

**Best for:**
- Bulk lead generation campaigns
- Data collection projects
- High-throughput requirements
- Continuous operation scenarios
- Systems with robust infrastructure

**Characteristics:**
- Aggressive scraping (continuous mode, QPI=15)
- High async limits (50 concurrent, 5 per host)
- Extended date ranges (90 days)
- Still maintains core security (SSL enabled)
- Moderate logging

**Not suitable for:**
- Limited hardware resources
- Systems with strict rate limiting
- Development/testing
- First-time deployments (start with production profile)

### Debug Mode Profile

**Best for:**
- Local development
- Troubleshooting production issues
- Testing new features
- Learning the system
- Integration development

**Characteristics:**
- DEBUG mode enabled
- Maximum logging (DEBUG level)
- Relaxed security (SSL validation optional)
- Small test batches (QPI=2, 7 days)
- Extended timeouts for debugging

**Not suitable for:**
- Production environments (NEVER!)
- Any system accessible from the internet
- Systems handling real customer data
- Performance testing (logging overhead)

## 🚀 Quick Start

### 1. Choose Your Profile

```bash
# Navigate to project directory
cd luca-nrw-scraper

# Copy the appropriate profile
cp configs/production.env .env      # For production
cp configs/high-volume.env .env     # For high volume
cp configs/debug.env .env           # For development
```

### 2. Customize Required Settings

Edit `.env` and update these critical values:

```bash
nano .env
```

**Required changes:**

1. **SECRET_KEY** - Generate unique key:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **ALLOWED_HOSTS** - Set your domain(s):
   ```env
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   ```

3. **CSRF_TRUSTED_ORIGINS** - Set your URL(s):
   ```env
   CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
   ```

4. **API Keys** - Add your keys (if needed):
   ```env
   OPENAI_API_KEY=sk-...
   PERPLEXITY_API_KEY=pplx-...
   BREVO_API_KEY=xkeysib-...
   ```

### 3. Start Your Application

```bash
# Using Docker (recommended)
docker-compose up -d

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Or manual installation
cd telis_recruitment
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 4. Verify Configuration

Access your application:
- CRM Dashboard: http://localhost:8000/crm/ (or your domain)
- Check version in footer
- Test scraper functionality
- Review logs for issues

## 📊 Detailed Profile Comparison

### Security Settings

| Setting | Production | High Volume | Debug |
|---------|-----------|-------------|-------|
| DEBUG | False | False | True |
| SSL Validation | Strict (0) | Strict (0) | Relaxed (1) |
| SECURE_SSL_REDIRECT | True | True | False |
| SESSION_COOKIE_SECURE | True | True | False |
| CSRF_COOKIE_SECURE | True | True | False |
| HSTS (seconds) | 31536000 | 31536000 | 0 |
| LOG_LEVEL | INFO | INFO | DEBUG |

### Scraper Configuration

| Setting | Production | High Volume | Debug |
|---------|-----------|-------------|-------|
| SCRAPER_MODE | once | continuous | once |
| SCRAPER_QPI | 6 | 15 | 2 |
| SCRAPER_DATE_RESTRICT | d30 | d90 | d7 |
| HTTP_TIMEOUT | 15 | 10 | 30 |
| ASYNC_LIMIT | 25 | 50 | 10 |
| ASYNC_PER_HOST | 2 | 5 | 2 |
| MAX_FETCH_SIZE | 2MB | 5MB | 2MB |

### Performance Characteristics

| Metric | Production | High Volume | Debug |
|--------|-----------|-------------|-------|
| Leads per hour | ~300-500 | ~1000-2000 | ~50-100 |
| Resource usage | Low-Medium | High | Low |
| Network load | Moderate | High | Low |
| Disk I/O | Low | Medium | High (logs) |
| CPU usage | 10-30% | 50-80% | 10-20% |

*Note: Metrics vary based on hardware and network conditions*

## 🔧 Customization

### Creating a Custom Profile

1. **Start with closest profile**:
   ```bash
   cp configs/production.env configs/custom.env
   ```

2. **Adjust specific settings**:
   ```env
   # Example: Production base with higher scraping
   SCRAPER_QPI=10
   ASYNC_LIMIT=35
   ASYNC_PER_HOST=3
   ```

3. **Document your changes**:
   ```env
   # ==========================
   # CUSTOM PROFILE: Production + Enhanced Scraping
   # ==========================
   # Based on: production.env
   # Modified: 2026-01-19
   # Purpose: Production deployment with moderate high-volume scraping
   ```

4. **Test thoroughly**:
   ```bash
   cp configs/custom.env .env
   # Run tests
   # Monitor resources
   # Verify security
   ```

### Common Customizations

#### Moderate Volume (Between Production and High Volume)

```env
# Start with production.env, then adjust:
SCRAPER_MODE=continuous
SCRAPER_QPI=10
ASYNC_LIMIT=35
ASYNC_PER_HOST=3
SCRAPER_DATE_RESTRICT=d60
```

#### Production with Debug Logging (Temporary)

```env
# Start with production.env, then adjust:
LOG_LEVEL=DEBUG
# Remember to change back to INFO after debugging!
```

#### High Volume with Extra Security

```env
# Start with high-volume.env, then adjust:
ASYNC_LIMIT=35  # Reduce from 50
ASYNC_PER_HOST=3  # Reduce from 5
HTTP_TIMEOUT=15  # Increase from 10
```

## 🔍 Profile Selection Decision Tree

```
Are you deploying to production?
├─ Yes → Is this a high-volume use case?
│  ├─ Yes → Use high-volume.env
│  │  └─ Monitor resources closely
│  └─ No → Use production.env ✅
│     └─ Scale up later if needed
│
└─ No → Are you developing/debugging?
   ├─ Yes → Use debug.env
   │  └─ Never deploy this to production!
   └─ No → Are you testing?
      └─ Use debug.env or production.env with LOG_LEVEL=DEBUG
```

## 📈 Migration Between Profiles

### From Debug to Production

1. **Backup current database**:
   ```bash
   cp telis_recruitment/db.sqlite3 telis_recruitment/db.sqlite3.backup
   ```

2. **Switch profile**:
   ```bash
   cp configs/production.env .env
   ```

3. **Update settings**:
   - Generate new SECRET_KEY
   - Set production ALLOWED_HOSTS
   - Set production CSRF_TRUSTED_ORIGINS
   - Add production API keys

4. **Test**:
   ```bash
   # Test SSL works
   python scriptname.py --once --industry recruiter --qpi 1
   
   # Test CRM access
   cd telis_recruitment
   python manage.py check --deploy
   ```

### From Production to High Volume

1. **Monitor baseline**:
   - Note current resource usage
   - Document current lead generation rate
   - Check for any errors in logs

2. **Switch profile**:
   ```bash
   cp configs/high-volume.env .env
   # Update SECRET_KEY, ALLOWED_HOSTS, etc.
   ```

3. **Gradual ramp-up** (recommended):
   ```env
   # Week 1: Moderate increase
   SCRAPER_QPI=8
   ASYNC_LIMIT=30
   
   # Week 2: Further increase
   SCRAPER_QPI=12
   ASYNC_LIMIT=40
   
   # Week 3: Full high volume
   SCRAPER_QPI=15
   ASYNC_LIMIT=50
   ```

4. **Monitor closely**:
   - Watch CPU/memory usage
   - Monitor network bandwidth
   - Check for rate limiting (429 errors)
   - Review lead quality

## ⚠️ Common Pitfalls

### 1. Using Debug Profile in Production
**Problem**: Security vulnerabilities, exposed error pages, performance issues

**Solution**: Always use production.env for production deployments

### 2. Not Updating SECRET_KEY
**Problem**: Security risk, session issues

**Solution**: Generate unique key for each environment:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Insufficient Resources for High Volume
**Problem**: System crashes, slow performance, memory errors

**Solution**: 
- Start with production profile
- Monitor resources
- Scale gradually
- Consider upgrading hardware

### 4. Incorrect ALLOWED_HOSTS
**Problem**: "DisallowedHost" errors

**Solution**: Set all domains that will access your app:
```env
ALLOWED_HOSTS=example.com,www.example.com,api.example.com
```

### 5. Disabling SSL Validation in Production
**Problem**: Security vulnerability (MITM attacks)

**Solution**: Keep `ALLOW_INSECURE_SSL=0` in production

## 🧪 Testing Your Configuration

### Configuration Validation Script

```bash
#!/bin/bash
# Save as: validate_config.sh

echo "🔍 Validating LUCA Configuration..."

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Load .env
source .env

# Check critical settings
echo "Checking DEBUG mode..."
if [ "$DEBUG" = "True" ]; then
    echo "⚠️  WARNING: DEBUG is enabled! Not suitable for production."
else
    echo "✅ DEBUG is disabled"
fi

echo "Checking SSL validation..."
if [ "$ALLOW_INSECURE_SSL" = "1" ]; then
    echo "⚠️  WARNING: SSL validation is disabled!"
else
    echo "✅ SSL validation is enabled"
fi

echo "Checking SECRET_KEY..."
if [[ "$SECRET_KEY" == *"change-me"* ]] || [[ "$SECRET_KEY" == *"dev-secret"* ]]; then
    echo "❌ SECRET_KEY must be changed!"
else
    echo "✅ SECRET_KEY is customized"
fi

echo "Checking ALLOWED_HOSTS..."
if [ -z "$ALLOWED_HOSTS" ]; then
    echo "⚠️  ALLOWED_HOSTS is empty"
else
    echo "✅ ALLOWED_HOSTS: $ALLOWED_HOSTS"
fi

echo ""
echo "✅ Configuration validation complete"
```

Usage:
```bash
chmod +x validate_config.sh
./validate_config.sh
```

### Django Deployment Check

```bash
cd telis_recruitment
python manage.py check --deploy
```

This checks for common deployment issues.

## 📚 Additional Resources

- **Security Checklist**: [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)
- **Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Release Process**: [RELEASE_PROCESS.md](RELEASE_PROCESS.md)

## 🆘 Troubleshooting

### Profile Not Working

1. **Verify .env is loaded**:
   ```bash
   cd telis_recruitment
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('DEBUG'))"
   ```

2. **Check for syntax errors**:
   ```bash
   cat .env | grep -v '^#' | grep -v '^$'
   ```

3. **Restart application**:
   ```bash
   docker-compose restart  # For Docker
   # Or restart Django manually
   ```

### Performance Issues

1. **Generate support bundle**:
   ```bash
   python manage.py create_support_bundle
   ```

2. **Review resource usage**:
   ```bash
   # Check system resources
   top
   htop
   docker stats  # For Docker
   ```

3. **Consider profile adjustment**:
   - Too slow? Switch to high-volume
   - System overloaded? Switch to production
   - Adjust specific settings between profiles

### SSL Issues

1. **Test certificate**:
   ```bash
   curl -I https://your-domain.com
   ```

2. **Check SSL in scraper**:
   ```bash
   python scriptname.py --once --industry recruiter --qpi 1
   ```

3. **Review logs**:
   ```bash
   tail -f telis_recruitment/logs/*.log
   ```

## 💡 Best Practices

1. **Start conservative**: Begin with production profile, scale up as needed
2. **Test in staging**: Always test profile changes in staging first
3. **Monitor after changes**: Watch resources and logs after switching profiles
4. **Document customizations**: Keep notes on why you changed specific settings
5. **Regular reviews**: Review configuration quarterly
6. **Keep profiles updated**: Update profiles when upgrading LUCA

---

**Need help?** Generate a support bundle for faster assistance:
```bash
cd telis_recruitment
python manage.py create_support_bundle
```
