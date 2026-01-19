# Generated migration for new models: PageAsset, BrandSettings, PageTemplate

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0003_landingpage_custom_domain_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='page_assets/')),
                ('filename', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField(help_text='File size in bytes')),
                ('width', models.PositiveIntegerField(blank=True, help_text='Image width in pixels', null=True)),
                ('height', models.PositiveIntegerField(blank=True, help_text='Image height in pixels', null=True)),
                ('alt_text', models.CharField(blank=True, help_text='Alt text for SEO', max_length=255)),
                ('folder', models.CharField(blank=True, default='', help_text='Folder organization', max_length=100)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Page Asset',
                'verbose_name_plural': 'Page Assets',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='BrandSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_color', models.CharField(default='#007bff', help_text='Primary brand color', max_length=7)),
                ('secondary_color', models.CharField(default='#6c757d', help_text='Secondary brand color', max_length=7)),
                ('accent_color', models.CharField(default='#28a745', help_text='Accent color', max_length=7)),
                ('text_color', models.CharField(default='#212529', help_text='Default text color', max_length=7)),
                ('background_color', models.CharField(default='#ffffff', help_text='Default background color', max_length=7)),
                ('heading_font', models.CharField(default='Inter', help_text='Font family for headings', max_length=100)),
                ('body_font', models.CharField(default='Open Sans', help_text='Font family for body text', max_length=100)),
                ('base_font_size', models.PositiveIntegerField(default=16, help_text='Base font size in pixels')),
                ('logo', models.ImageField(blank=True, help_text='Primary logo', null=True, upload_to='brand/')),
                ('logo_dark', models.ImageField(blank=True, help_text='Dark version of logo', null=True, upload_to='brand/')),
                ('favicon', models.ImageField(blank=True, help_text='Favicon', null=True, upload_to='brand/')),
                ('facebook_url', models.URLField(blank=True)),
                ('instagram_url', models.URLField(blank=True)),
                ('linkedin_url', models.URLField(blank=True)),
                ('twitter_url', models.URLField(blank=True)),
                ('youtube_url', models.URLField(blank=True)),
                ('company_name', models.CharField(blank=True, max_length=200)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('address', models.TextField(blank=True)),
                ('privacy_url', models.URLField(blank=True, help_text='Privacy policy URL')),
                ('imprint_url', models.URLField(blank=True, help_text='Imprint/Impressum URL')),
                ('terms_url', models.URLField(blank=True, help_text='Terms of service URL')),
            ],
            options={
                'verbose_name': 'Brand Settings',
                'verbose_name_plural': 'Brand Settings',
            },
        ),
        migrations.CreateModel(
            name='PageTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Template name', max_length=100)),
                ('category', models.CharField(choices=[('lead_gen', 'Lead Generation'), ('product', 'Product'), ('service', 'Service'), ('event', 'Event'), ('coming_soon', 'Coming Soon'), ('thank_you', 'Thank You')], max_length=20)),
                ('thumbnail', models.ImageField(help_text='Preview thumbnail', upload_to='templates/thumbnails/')),
                ('html_content', models.TextField(help_text='HTML content of template')),
                ('css_content', models.TextField(blank=True, help_text='CSS content of template')),
                ('gjs_data', models.JSONField(default=dict, help_text='GrapesJS components/styles data')),
                ('usage_count', models.PositiveIntegerField(default=0, help_text='Number of times used')),
                ('is_active', models.BooleanField(default=True, help_text='Whether template is available')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Page Template',
                'verbose_name_plural': 'Page Templates',
                'ordering': ['-usage_count', 'name'],
            },
        ),
    ]
