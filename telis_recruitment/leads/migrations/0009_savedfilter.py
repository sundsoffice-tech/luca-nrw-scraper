# Generated migration for SavedFilter model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('leads', '0008_add_missing_scraper_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedFilter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='z.B. \'Callcenter NRW, mobile only, Score > 70\'', max_length=100, verbose_name='Filter-Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Beschreibung')),
                ('filter_params', models.JSONField(help_text='JSON object with filter parameters', verbose_name='Filter-Parameter')),
                ('is_shared', models.BooleanField(default=False, help_text='Für alle Benutzer sichtbar', verbose_name='Geteilt')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_filters', to=settings.AUTH_USER_MODEL, verbose_name='Benutzer')),
            ],
            options={
                'verbose_name': 'Gespeicherter Filter',
                'verbose_name_plural': 'Gespeicherte Filter',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='savedfilter',
            unique_together={('user', 'name')},
        ),
    ]
