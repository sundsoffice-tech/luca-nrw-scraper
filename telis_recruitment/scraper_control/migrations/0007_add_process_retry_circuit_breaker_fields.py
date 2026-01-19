# Generated migration for ProcessManager retry and circuit breaker fields

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('scraper_control', '0006_scraperconfig_allow_insecure_ssl'),
    ]

    operations = [
        migrations.AddField(
            model_name='scraperconfig',
            name='process_max_retry_attempts',
            field=models.IntegerField(
                default=3,
                help_text='Maximale automatische Neustarts bei Fehlern',
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(10)
                ],
                verbose_name='Max. Process-Restarts'
            ),
        ),
        migrations.AddField(
            model_name='scraperconfig',
            name='process_qpi_reduction_factor',
            field=models.FloatField(
                default=0.7,
                help_text='QPI-Anpassung bei Rate-Limits (0.7 = 70%)',
                validators=[
                    django.core.validators.MinValueValidator(0.1),
                    django.core.validators.MaxValueValidator(1.0)
                ],
                verbose_name='QPI-Reduktionsfaktor'
            ),
        ),
        migrations.AddField(
            model_name='scraperconfig',
            name='process_error_rate_threshold',
            field=models.FloatField(
                default=0.5,
                help_text='Fehlerrate für Circuit Breaker (0.5 = 50%)',
                validators=[
                    django.core.validators.MinValueValidator(0.0),
                    django.core.validators.MaxValueValidator(1.0)
                ],
                verbose_name='Fehlerquoten-Schwelle'
            ),
        ),
        migrations.AddField(
            model_name='scraperconfig',
            name='process_circuit_breaker_failures',
            field=models.IntegerField(
                default=5,
                help_text='Anzahl Fehler bis Circuit Breaker öffnet',
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(20)
                ],
                verbose_name='Circuit Breaker Fehler-Schwelle'
            ),
        ),
        migrations.AddField(
            model_name='scraperconfig',
            name='process_retry_backoff_base',
            field=models.FloatField(
                default=30.0,
                help_text='Basis-Wartezeit für exponentiellen Backoff',
                validators=[
                    django.core.validators.MinValueValidator(5.0),
                    django.core.validators.MaxValueValidator(300.0)
                ],
                verbose_name='Retry Backoff Basis (Sek)'
            ),
        ),
        migrations.AlterField(
            model_name='scraperconfig',
            name='circuit_breaker_penalty',
            field=models.IntegerField(
                default=30,
                help_text='Pausenzeit wenn Circuit Breaker öffnet',
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Circuit Breaker Penalty (Sek)'
            ),
        ),
    ]
