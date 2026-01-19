# Generated manually for observability enhancements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraper_control', '0006_scraperconfig_allow_insecure_ssl'),
    ]

    operations = [
        # Add new status choice to ScraperRun
        migrations.AlterField(
            model_name='scraperrun',
            name='status',
            field=models.CharField(
                choices=[
                    ('running', 'Läuft'),
                    ('completed', 'Abgeschlossen'),
                    ('stopped', 'Gestoppt'),
                    ('failed', 'Fehlgeschlagen'),
                    ('error', 'Fehler'),
                    ('partial', 'Teilweise erfolgreich')
                ],
                default='running',
                max_length=20,
                verbose_name='Status'
            ),
        ),
        
        # Add enhanced metrics to ScraperRun
        migrations.AddField(
            model_name='scraperrun',
            name='links_checked',
            field=models.IntegerField(default=0, verbose_name='Links geprüft'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='links_successful',
            field=models.IntegerField(default=0, verbose_name='Links erfolgreich'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='links_failed',
            field=models.IntegerField(default=0, verbose_name='Links fehlgeschlagen'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='leads_accepted',
            field=models.IntegerField(default=0, verbose_name='Leads akzeptiert'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='leads_rejected',
            field=models.IntegerField(default=0, verbose_name='Leads verworfen'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='avg_request_time_ms',
            field=models.FloatField(default=0.0, help_text='Durchschnittliche Zeit pro Request in Millisekunden', verbose_name='Ø Request-Zeit (ms)'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='block_rate',
            field=models.FloatField(default=0.0, help_text='Prozentsatz blockierter Requests (403, 429, etc.)', verbose_name='Block-Rate (%)'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='timeout_rate',
            field=models.FloatField(default=0.0, help_text='Prozentsatz der Timeout-Fehler', verbose_name='Timeout-Rate (%)'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='error_rate',
            field=models.FloatField(default=0.0, help_text='Gesamtfehlerrate', verbose_name='Fehler-Rate (%)'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='circuit_breaker_triggered',
            field=models.BooleanField(default=False, verbose_name='Circuit Breaker ausgelöst'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='circuit_breaker_count',
            field=models.IntegerField(default=0, verbose_name='Circuit Breaker Auslösungen'),
        ),
        migrations.AddField(
            model_name='scraperrun',
            name='portal_stats',
            field=models.JSONField(blank=True, default=dict, help_text='Statistiken pro Portal/Quelle', verbose_name='Portal-Statistiken'),
        ),
        
        # Enhance ScraperLog with portal field
        migrations.AddField(
            model_name='scraperlog',
            name='portal',
            field=models.CharField(blank=True, default='', help_text='Portal oder Datenquelle', max_length=100, verbose_name='Portal/Quelle'),
        ),
        migrations.AlterField(
            model_name='scraperlog',
            name='level',
            field=models.CharField(
                choices=[
                    ('DEBUG', 'Debug'),
                    ('INFO', 'Info'),
                    ('WARN', 'Warning'),
                    ('ERROR', 'Error'),
                    ('CRITICAL', 'Critical')
                ],
                default='INFO',
                max_length=10,
                verbose_name='Level'
            ),
        ),
        
        # Add indexes for ScraperLog
        migrations.AddIndex(
            model_name='scraperlog',
            index=models.Index(fields=['level', 'created_at'], name='scraper_con_level_0a1b2c_idx'),
        ),
        migrations.AddIndex(
            model_name='scraperlog',
            index=models.Index(fields=['portal', 'created_at'], name='scraper_con_portal_0d1e2f_idx'),
        ),
        
        # Create ErrorLog model
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_type', models.CharField(
                    choices=[
                        ('block_403', 'Block/403 - Zugriff verweigert'),
                        ('block_429', 'Block/429 - Rate Limit'),
                        ('captcha', 'Captcha/Login erforderlich'),
                        ('parsing', 'Parsing fehlgeschlagen'),
                        ('network_timeout', 'Netzwerk/Timeout'),
                        ('network_connection', 'Netzwerk/Verbindung'),
                        ('data_quality', 'Datenqualität zu niedrig'),
                        ('validation', 'Validierung fehlgeschlagen'),
                        ('unknown', 'Unbekannt')
                    ],
                    max_length=30,
                    verbose_name='Fehler-Typ'
                )),
                ('severity', models.CharField(
                    choices=[
                        ('low', 'Niedrig'),
                        ('medium', 'Mittel'),
                        ('high', 'Hoch'),
                        ('critical', 'Kritisch')
                    ],
                    default='medium',
                    max_length=10,
                    verbose_name='Schweregrad'
                )),
                ('portal', models.CharField(blank=True, default='', max_length=100, verbose_name='Portal/Quelle')),
                ('url', models.URLField(blank=True, default='', max_length=500, verbose_name='Betroffene URL')),
                ('message', models.TextField(verbose_name='Fehlermeldung')),
                ('details', models.JSONField(blank=True, default=dict, help_text='Zusätzliche Fehlerdetails (Stack Trace, Headers, etc.)', verbose_name='Details')),
                ('count', models.IntegerField(default=1, help_text='Wie oft dieser Fehler aufgetreten ist', verbose_name='Anzahl')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('last_occurrence', models.DateTimeField(auto_now=True, verbose_name='Letztes Auftreten')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='errors', to='scraper_control.scraperrun', verbose_name='Scraper-Lauf')),
            ],
            options={
                'verbose_name': 'Fehler-Log',
                'verbose_name_plural': 'Fehler-Logs',
                'ordering': ['-last_occurrence'],
            },
        ),
        
        # Add indexes for ErrorLog
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['run', 'error_type'], name='scraper_con_run_id_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['severity', 'created_at'], name='scraper_con_severity_2b3c4d_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['portal', 'error_type'], name='scraper_con_portal_3c4d5e_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['error_type', 'last_occurrence'], name='scraper_con_error_t_4d5e6f_idx'),
        ),
        
        # Enhance PortalSource with circuit breaker fields
        migrations.AddField(
            model_name='portalsource',
            name='circuit_breaker_enabled',
            field=models.BooleanField(default=True, verbose_name='Circuit Breaker aktiv'),
        ),
        migrations.AddField(
            model_name='portalsource',
            name='circuit_breaker_threshold',
            field=models.IntegerField(default=5, help_text='Anzahl Fehler bevor Portal pausiert wird', verbose_name='Circuit Breaker Schwellwert'),
        ),
        migrations.AddField(
            model_name='portalsource',
            name='circuit_breaker_cooldown',
            field=models.IntegerField(default=300, help_text='Pause nach Auslösung in Sekunden', verbose_name='Circuit Breaker Cooldown (Sek)'),
        ),
        migrations.AddField(
            model_name='portalsource',
            name='circuit_breaker_tripped',
            field=models.BooleanField(default=False, verbose_name='Circuit Breaker ausgelöst'),
        ),
        migrations.AddField(
            model_name='portalsource',
            name='circuit_breaker_reset_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Circuit Breaker Reset'),
        ),
        migrations.AddField(
            model_name='portalsource',
            name='consecutive_errors',
            field=models.IntegerField(default=0, verbose_name='Aufeinanderfolgende Fehler'),
        ),
    ]
