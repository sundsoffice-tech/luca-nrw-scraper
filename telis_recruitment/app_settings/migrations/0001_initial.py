# Generated manually for app_settings

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(default='TELIS CRM', max_length=100, verbose_name='Seitenname')),
                ('site_url', models.URLField(blank=True, verbose_name='Seiten-URL')),
                ('admin_email', models.EmailField(blank=True, max_length=254, verbose_name='Admin E-Mail')),
                ('enable_email_module', models.BooleanField(default=True, verbose_name='E-Mail-Modul aktivieren')),
                ('enable_scraper', models.BooleanField(default=True, verbose_name='Scraper aktivieren')),
                ('enable_ai_features', models.BooleanField(default=True, verbose_name='KI-Funktionen aktivieren')),
                ('enable_landing_pages', models.BooleanField(default=True, verbose_name='Landing Pages aktivieren')),
                ('maintenance_mode', models.BooleanField(default=False, verbose_name='Wartungsmodus')),
                ('maintenance_message', models.TextField(blank=True, verbose_name='Wartungsnachricht')),
                ('session_timeout_minutes', models.IntegerField(default=60, validators=[django.core.validators.MinValueValidator(5), django.core.validators.MaxValueValidator(1440)], verbose_name='Sitzungszeitlimit (Minuten)')),
                ('max_login_attempts', models.IntegerField(default=5, validators=[django.core.validators.MinValueValidator(3), django.core.validators.MaxValueValidator(10)], verbose_name='Max. Login-Versuche')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Systemeinstellung',
                'verbose_name_plural': 'Systemeinstellungen',
            },
        ),
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.CharField(choices=[('dark', 'Dark'), ('light', 'Light')], default='dark', max_length=20, verbose_name='Theme')),
                ('language', models.CharField(choices=[('de', 'Deutsch'), ('en', 'English')], default='de', max_length=10, verbose_name='Sprache')),
                ('email_notifications', models.BooleanField(default=True, verbose_name='E-Mail-Benachrichtigungen')),
                ('items_per_page', models.IntegerField(default=25, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(100)], verbose_name='Elemente pro Seite')),
                ('default_lead_view', models.CharField(choices=[('list', 'Liste'), ('grid', 'Kacheln')], default='list', max_length=20, verbose_name='Standard-Ansicht für Leads')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Benutzereinstellung',
                'verbose_name_plural': 'Benutzereinstellungen',
            },
        ),
    ]
