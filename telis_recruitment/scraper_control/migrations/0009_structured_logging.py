# Generated migration for structured logging fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper_control', '0008_searchdork_ai_learning_fields'),
    ]

    operations = [
        # Add event_code field to ScraperLog for structured logging
        migrations.AddField(
            model_name='scraperlog',
            name='event_code',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                help_text='Structured event code (e.g., CRAWL_START, EXTRACTION_FAIL)',
                max_length=50,
                verbose_name='Event Code',
            ),
        ),
        # Add event_category field to ScraperLog for filtering
        migrations.AddField(
            model_name='scraperlog',
            name='event_category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('LIFECYCLE', 'Lifecycle'),
                    ('CRAWL', 'Crawl'),
                    ('EXTRACTION', 'Extraction'),
                    ('NETWORK', 'Network'),
                    ('DATABASE', 'Database'),
                    ('CIRCUIT_BREAKER', 'Circuit Breaker'),
                    ('VALIDATION', 'Validation'),
                    ('SECURITY', 'Security'),
                    ('PERFORMANCE', 'Performance'),
                ],
                default='',
                help_text='Category for filtering in monitoring dashboards',
                max_length=20,
                verbose_name='Event Category',
            ),
        ),
        # Add url field to ScraperLog
        migrations.AddField(
            model_name='scraperlog',
            name='url',
            field=models.URLField(
                blank=True,
                default='',
                help_text='Related URL for this log entry',
                max_length=500,
                verbose_name='URL',
            ),
        ),
        # Add extra_data JSON field for flexible logging
        migrations.AddField(
            model_name='scraperlog',
            name='extra_data',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Additional structured data for monitoring',
                verbose_name='Extra Data',
            ),
        ),
        # Add indexes for efficient filtering in Grafana/Kibana
        migrations.AddIndex(
            model_name='scraperlog',
            index=models.Index(fields=['event_code', 'created_at'], name='scraper_con_event_c_idx'),
        ),
        migrations.AddIndex(
            model_name='scraperlog',
            index=models.Index(fields=['event_category', 'created_at'], name='scraper_con_event_cat_idx'),
        ),
    ]
