# Generated migration for analytics and tracking functionality

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_settings', '0001_initial'),
    ]

    operations = [
        # Add tracking fields to SystemSettings
        migrations.AddField(
            model_name='systemsettings',
            name='enable_analytics',
            field=models.BooleanField(default=False, verbose_name='Analytics aktivieren'),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='google_analytics_id',
            field=models.CharField(blank=True, help_text='z.B. G-XXXXXXXXXX oder UA-XXXXXXXXX-X', max_length=50, verbose_name='Google Analytics ID'),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='meta_pixel_id',
            field=models.CharField(blank=True, help_text='Facebook/Meta Pixel ID', max_length=50, verbose_name='Meta Pixel ID'),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='custom_tracking_code',
            field=models.TextField(blank=True, help_text='Benutzerdefinierte Tracking-Scripts (z.B. Matomo, Plausible, etc.)', verbose_name='Benutzerdefinierter Tracking-Code'),
        ),
        # Create PageView model
        migrations.CreateModel(
            name='PageView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40, verbose_name='Sitzungsschlüssel')),
                ('path', models.CharField(db_index=True, max_length=500, verbose_name='Pfad')),
                ('page_title', models.CharField(blank=True, max_length=200, verbose_name='Seitentitel')),
                ('method', models.CharField(default='GET', max_length=10, verbose_name='HTTP-Methode')),
                ('referrer', models.URLField(blank=True, max_length=500, verbose_name='Referrer')),
                ('user_agent', models.CharField(blank=True, max_length=500, verbose_name='User-Agent')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP-Adresse')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Zeitstempel')),
                ('load_time', models.FloatField(blank=True, null=True, verbose_name='Ladezeit (ms)')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Benutzer')),
            ],
            options={
                'verbose_name': 'Seitenaufruf',
                'verbose_name_plural': 'Seitenaufrufe',
                'ordering': ['-timestamp'],
            },
        ),
        # Create AnalyticsEvent model
        migrations.CreateModel(
            name='AnalyticsEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40, verbose_name='Sitzungsschlüssel')),
                ('category', models.CharField(choices=[('navigation', 'Navigation'), ('interaction', 'Interaktion'), ('conversion', 'Conversion'), ('error', 'Fehler'), ('engagement', 'Engagement')], db_index=True, max_length=50, verbose_name='Kategorie')),
                ('action', models.CharField(db_index=True, max_length=100, verbose_name='Aktion')),
                ('label', models.CharField(blank=True, max_length=200, verbose_name='Label')),
                ('value', models.FloatField(blank=True, null=True, verbose_name='Wert')),
                ('page_path', models.CharField(blank=True, max_length=500, verbose_name='Seitenpfad')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadaten')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Zeitstempel')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Benutzer')),
            ],
            options={
                'verbose_name': 'Analytics-Event',
                'verbose_name_plural': 'Analytics-Events',
                'ordering': ['-timestamp'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='pageview',
            index=models.Index(fields=['-timestamp', 'path'], name='app_setting_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='pageview',
            index=models.Index(fields=['session_key', '-timestamp'], name='app_setting_session_idx'),
        ),
        migrations.AddIndex(
            model_name='analyticsevent',
            index=models.Index(fields=['-timestamp', 'category'], name='app_setting_timesta_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='analyticsevent',
            index=models.Index(fields=['action', '-timestamp'], name='app_setting_action_idx'),
        ),
    ]
