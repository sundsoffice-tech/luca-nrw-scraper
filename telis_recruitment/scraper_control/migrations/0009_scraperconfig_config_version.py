# Generated migration for live config reload feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper_control', '0008_searchdork_ai_learning_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='scraperconfig',
            name='config_version',
            field=models.PositiveIntegerField(
                default=1,
                verbose_name='Konfigurationsversion',
                help_text='Wird bei jeder Änderung inkrementiert. Ermöglicht Live-Reload.'
            ),
        ),
    ]
