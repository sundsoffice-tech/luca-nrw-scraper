# Configuration Profiles

This directory contains pre-configured environment profiles for different deployment scenarios.

## 📋 Available Profiles

### 🔒 Production Safe (`production.env`)
**Use for**: Live production systems handling real data

- ✅ Maximum security settings
- ✅ SSL/TLS validation enabled
- ✅ Conservative resource limits
- ✅ Minimal logging (INFO level)
- ✅ Balanced performance

**Security Level**: HIGH  
**Performance**: BALANCED  
**Recommended for**: Production deployments, customer-facing systems

### ⚡ High Volume (`high-volume.env`)
**Use for**: Maximum throughput and aggressive scraping

- ✅ Continuous scraping mode
- ✅ High query limits (QPI=15)
- ✅ Aggressive timeouts and async limits
- ✅ Extended date ranges (90 days)
- ✅ Still maintains security (SSL enabled)

**Security Level**: MEDIUM-HIGH  
**Performance**: MAXIMUM  
**Recommended for**: Bulk lead generation, data collection campaigns

### 🐛 Debug Mode (`debug.env`)
**Use for**: Development and troubleshooting

- ⚠️ DEBUG mode enabled
- ⚠️ Maximum logging (DEBUG level)
- ⚠️ Relaxed security (for local development only)
- ⚠️ Small test batches (QPI=2, 7 days)
- ⚠️ **NEVER use in production!**

**Security Level**: LOW  
**Performance**: LOW (logging overhead)  
**Recommended for**: Local development, debugging, testing

## 🚀 How to Use

### Quick Start

1. **Copy the profile you need**:
   ```bash
   # For production
   cp configs/production.env .env
   
   # For high volume
   cp configs/high-volume.env .env
   
   # For development/debug
   cp configs/debug.env .env
   ```

2. **Edit the configuration**:
   ```bash
   nano .env
   ```

3. **Update critical values**:
   - `SECRET_KEY` - Generate a unique key
   - `ALLOWED_HOSTS` - Set your domain
   - `CSRF_TRUSTED_ORIGINS` - Set your URLs
   - API keys if needed (OpenAI, Perplexity, Brevo, TinyMCE, etc.)

4. **Start your application**:
   ```bash
   # Docker
   docker-compose up -d
   
   # Manual
   cd telis_recruitment
   python manage.py runserver
   ```

### Generating a Secret Key

For production, always generate a unique secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 🔐 Security Checklist

Before deploying to production with any profile:

- [ ] Generated unique `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configured correct `ALLOWED_HOSTS`
- [ ] Configured correct `CSRF_TRUSTED_ORIGINS` with HTTPS
- [ ] Set `ALLOW_INSECURE_SSL=0` (secure by default)
- [ ] Enabled HTTPS security settings if you have SSL
- [ ] Reviewed and set API keys securely
- [ ] Configured proper database (PostgreSQL recommended)
- [ ] Set up log rotation
- [ ] Tested SSL connections work properly

See [docs/SECURITY_CHECKLIST.md](../docs/SECURITY_CHECKLIST.md) for complete security guide.

## 📊 Profile Comparison

| Feature | Production | High Volume | Debug |
|---------|-----------|-------------|-------|
| DEBUG mode | ❌ False | ❌ False | ✅ True |
| SSL validation | ✅ Strict | ✅ Strict | ⚠️ Relaxed |
| Scraper mode | Once | Continuous | Once |
| Queries per industry | 6 | 15 | 2 |
| Date range | 30 days | 90 days | 7 days |
| Async limit | 25 | 50 | 10 |
| Per-host limit | 2 | 5 | 2 |
| Log level | INFO | INFO | DEBUG |
| HTTPS required | ✅ Yes | ✅ Yes | ❌ No |

## 🎯 Customization

### Creating Your Own Profile

1. Copy an existing profile as a starting point
2. Adjust values for your specific needs
3. Document your changes
4. Test thoroughly before production deployment

### Hybrid Configurations

You can mix settings from different profiles:

```bash
# Start with production base
cp configs/production.env .env

# Then adjust specific settings for your needs
# Example: Enable more aggressive scraping while keeping security
SCRAPER_QPI=10
ASYNC_LIMIT=35
```

## 📖 Additional Resources

- **Configuration Guide**: [../docs/CONFIGURATION_PROFILES.md](../docs/CONFIGURATION_PROFILES.md)
- **Security Guide**: [../docs/SECURITY_CHECKLIST.md](../docs/SECURITY_CHECKLIST.md)
- **Deployment Guide**: [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)
- **Installation Guide**: [../docs/INSTALLATION.md](../docs/INSTALLATION.md)

## ⚠️ Important Notes

1. **Never commit `.env` files to git** - They contain secrets
2. **Always use production profile for live systems**
3. **Test configuration changes in a staging environment first**
4. **Monitor system resources** when using high-volume profile
5. **Rotate secrets regularly** in production
6. **Keep backups** of your working configuration

## 🆘 Troubleshooting

### SSL Errors
- Check `ALLOW_INSECURE_SSL=0` is set
- Verify your certificates are valid
- Test with `curl` to verify SSL handshake

### Performance Issues
- Switch to high-volume profile
- Consider PostgreSQL instead of SQLite
- Adjust async limits based on your hardware
- Monitor system resources

### Debug Not Working
- Ensure `DEBUG=True` in debug profile
- Check `LOG_LEVEL=DEBUG`
- Review Django logs in console

### Database Errors
- Verify DATABASE_URL format
- Run migrations: `python manage.py migrate`
- Check database permissions

For more help, generate a support bundle: `python manage.py create_support_bundle`
