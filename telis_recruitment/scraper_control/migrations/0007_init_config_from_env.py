# Generated migration for initializing ScraperConfig from environment variables

from django.db import migrations
import os


def init_config_from_env(apps, schema_editor):
    """
    Initialize ScraperConfig singleton from environment variables.
    This ensures the database configuration is populated with current environment settings.
    """
    ScraperConfig = apps.get_model('scraper_control', 'ScraperConfig')
    
    # Get or create the singleton config
    config, created = ScraperConfig.objects.get_or_create(pk=1)
    
    # Only update if this is a new config or values are defaults
    # This preserves any manual changes made in the admin UI
    if created:
        # HTTP & Networking
        config.http_timeout = int(os.getenv("HTTP_TIMEOUT", "10"))
        config.async_limit = int(os.getenv("ASYNC_LIMIT", "35"))
        config.pool_size = int(os.getenv("POOL_SIZE", "12"))
        config.http2_enabled = os.getenv("HTTP2", "1") == "1"
        
        # Rate Limiting
        config.sleep_between_queries = float(os.getenv("SLEEP_BETWEEN_QUERIES", "2.7"))
        config.max_google_pages = int(os.getenv("MAX_GOOGLE_PAGES", "2"))
        config.circuit_breaker_penalty = int(os.getenv("CB_BASE_PENALTY", "30"))
        config.retry_max_per_url = int(os.getenv("RETRY_MAX_PER_URL", "2"))
        
        # Scoring
        config.min_score = int(os.getenv("MIN_SCORE", "40"))
        config.max_per_domain = int(os.getenv("MAX_PER_DOMAIN", "5"))
        config.default_quality_score = 50
        config.confidence_threshold = 0.35
        
        # Feature Flags
        config.enable_kleinanzeigen = os.getenv("ENABLE_KLEINANZEIGEN", "1") == "1"
        config.enable_telefonbuch = os.getenv("TELEFONBUCH_ENRICHMENT_ENABLED", "1") == "1"
        config.parallel_portal_crawl = os.getenv("PARALLEL_PORTAL_CRAWL", "1") == "1"
        config.max_concurrent_portals = int(os.getenv("MAX_CONCURRENT_PORTALS", "5"))
        
        # Content
        config.allow_pdf = os.getenv("ALLOW_PDF", "0") == "1"
        config.max_content_length = int(os.getenv("MAX_CONTENT_LENGTH", 
                                                   os.getenv("MAX_FETCH_SIZE", str(2 * 1024 * 1024))))
        
        # Security
        config.allow_insecure_ssl = os.getenv("ALLOW_INSECURE_SSL", "0") == "1"
        
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('scraper_control', '0006_scraperconfig_allow_insecure_ssl'),
    ]

    operations = [
        migrations.RunPython(init_config_from_env, reverse_code=migrations.RunPython.noop),
    ]
