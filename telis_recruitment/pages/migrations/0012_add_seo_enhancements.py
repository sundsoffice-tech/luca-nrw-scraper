# Generated migration for SEO enhancements
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0011_flexible_template_system'),
    ]

    operations = [
        # Add new SEO fields
        migrations.AddField(
            model_name='landingpage',
            name='seo_keywords',
            field=models.TextField(blank=True, help_text='SEO keywords (comma-separated)'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='canonical_url',
            field=models.URLField(blank=True, help_text='Canonical URL for this page'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='robots_meta',
            field=models.CharField(blank=True, default='index, follow', help_text="Robots meta tag (e.g., 'index, follow', 'noindex, nofollow')", max_length=100),
        ),
        
        # Add Open Graph fields
        migrations.AddField(
            model_name='landingpage',
            name='og_title',
            field=models.CharField(blank=True, help_text='Open Graph title (defaults to seo_title)', max_length=255),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_description',
            field=models.TextField(blank=True, help_text='Open Graph description (defaults to seo_description)'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_image',
            field=models.URLField(blank=True, help_text='Open Graph image URL (defaults to seo_image)'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_type',
            field=models.CharField(blank=True, default='website', help_text='Open Graph type (website, article, etc.)', max_length=50),
        ),
        
        # Add Twitter Card fields
        migrations.AddField(
            model_name='landingpage',
            name='twitter_card',
            field=models.CharField(blank=True, default='summary_large_image', help_text='Twitter card type', max_length=50),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='twitter_site',
            field=models.CharField(blank=True, help_text='Twitter @username for site', max_length=100),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='twitter_creator',
            field=models.CharField(blank=True, help_text='Twitter @username for creator', max_length=100),
        ),
        
        # Add Sitemap fields
        migrations.AddField(
            model_name='landingpage',
            name='sitemap_priority',
            field=models.DecimalField(decimal_places=1, default=0.5, help_text='Sitemap priority (0.0 to 1.0)', max_digits=2),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='sitemap_changefreq',
            field=models.CharField(blank=True, default='weekly', help_text='Sitemap change frequency', max_length=20),
        ),
    ]
