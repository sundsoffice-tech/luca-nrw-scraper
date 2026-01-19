# Generated migration for model updates - Teil 1

from django.conf import settings
from django.db import migrations, models
from django.utils.text import slugify
import django.db.models.deletion


def populate_template_slugs(apps, schema_editor):
    """Populate slug field from name for existing templates"""
    PageTemplate = apps.get_model('pages', 'PageTemplate')
    for template in PageTemplate.objects.all():
        if not template.slug:
            base_slug = slugify(template.name)
            slug = base_slug
            counter = 1
            # Ensure uniqueness
            while PageTemplate.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            template.slug = slug
            template.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0005_alter_pageasset_file'),
    ]

    operations = [
        # PageAsset updates
        migrations.RenameField(
            model_name='pageasset',
            old_name='filename',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='pageasset',
            old_name='uploaded_at',
            new_name='created_at',
        ),
        migrations.AddField(
            model_name='pageasset',
            name='landing_page',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='pages.landingpage'),
        ),
        migrations.AddField(
            model_name='pageasset',
            name='asset_type',
            field=models.CharField(choices=[('image', 'Bild'), ('video', 'Video'), ('document', 'Dokument')], default='image', max_length=20),
        ),
        migrations.AddField(
            model_name='pageasset',
            name='mime_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='pageasset',
            name='file',
            field=models.FileField(upload_to='landing_pages/assets/%Y/%m/'),
        ),
        migrations.AlterField(
            model_name='pageasset',
            name='file_size',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='pageasset',
            name='width',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pageasset',
            name='height',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name='pageasset',
            options={'ordering': ['-created_at'], 'verbose_name': 'Seiten-Asset', 'verbose_name_plural': 'Seiten-Assets'},
        ),
        
        # BrandSettings updates
        migrations.RemoveField(
            model_name='brandsettings',
            name='base_font_size',
        ),
        migrations.RemoveField(
            model_name='brandsettings',
            name='twitter_url',
        ),
        migrations.RemoveField(
            model_name='brandsettings',
            name='youtube_url',
        ),
        migrations.RemoveField(
            model_name='brandsettings',
            name='email',
        ),
        migrations.RemoveField(
            model_name='brandsettings',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='brandsettings',
            name='address',
        ),
        migrations.RemoveField(
            model_name='brandsettings',
            name='terms_url',
        ),
        migrations.AddField(
            model_name='brandsettings',
            name='text_light_color',
            field=models.CharField(default='#6b7280', max_length=7),
        ),
        migrations.AddField(
            model_name='brandsettings',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='brandsettings',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='brandsettings',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='primary_color',
            field=models.CharField(default='#6366f1', max_length=7),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='secondary_color',
            field=models.CharField(default='#06b6d4', max_length=7),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='accent_color',
            field=models.CharField(default='#22c55e', max_length=7),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='text_color',
            field=models.CharField(default='#1f2937', max_length=7),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='background_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='heading_font',
            field=models.CharField(default='Inter', max_length=100),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='body_font',
            field=models.CharField(default='Inter', max_length=100),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='company_name',
            field=models.CharField(default='LUCA', max_length=255),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='logo',
            field=models.ImageField(blank=True, upload_to='brand/'),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='logo_dark',
            field=models.ImageField(blank=True, upload_to='brand/'),
        ),
        migrations.AlterField(
            model_name='brandsettings',
            name='favicon',
            field=models.ImageField(blank=True, upload_to='brand/'),
        ),
        migrations.AlterModelOptions(
            name='brandsettings',
            options={'verbose_name': 'Marken-Einstellungen'},
        ),
        
        # PageTemplate updates
        # First add slug field as nullable
        migrations.AddField(
            model_name='pagetemplate',
            name='slug',
            field=models.SlugField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='pagetemplate',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.RenameField(
            model_name='pagetemplate',
            old_name='html_content',
            new_name='html',
        ),
        migrations.RenameField(
            model_name='pagetemplate',
            old_name='css_content',
            new_name='css',
        ),
        migrations.RenameField(
            model_name='pagetemplate',
            old_name='gjs_data',
            new_name='html_json',
        ),
        migrations.AlterField(
            model_name='pagetemplate',
            name='category',
            field=models.CharField(choices=[('lead_gen', 'Lead Generation'), ('product', 'Produktseite'), ('coming_soon', 'Coming Soon'), ('thank_you', 'Danke-Seite')], max_length=50),
        ),
        migrations.AlterField(
            model_name='pagetemplate',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to='templates/thumbnails/'),
        ),
        migrations.AlterField(
            model_name='pagetemplate',
            name='usage_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='pagetemplate',
            options={'ordering': ['category', 'name'], 'verbose_name': 'Seiten-Template'},
        ),
        
        # Populate slugs for existing templates
        migrations.RunPython(populate_template_slugs, migrations.RunPython.noop),
        
        # Now make slug unique and non-nullable
        migrations.AlterField(
            model_name='pagetemplate',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
