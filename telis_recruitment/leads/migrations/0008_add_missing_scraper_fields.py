# Generated manually for adding missing scraper.db fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0007_lead_ai_category_lead_ai_summary_lead_availability_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='profile_text',
            field=models.TextField(blank=True, null=True, verbose_name='Profil-Text'),
        ),
        migrations.AddField(
            model_name='lead',
            name='industries_experience',
            field=models.TextField(blank=True, null=True, verbose_name='Branchen-Erfahrung'),
        ),
        migrations.AddField(
            model_name='lead',
            name='source_type',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Quell-Typ'),
        ),
        migrations.AddField(
            model_name='lead',
            name='last_activity',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Letzte Aktivität'),
        ),
        migrations.AddField(
            model_name='lead',
            name='name_validated',
            field=models.BooleanField(blank=True, null=True, verbose_name='Name validiert'),
        ),
        migrations.AddField(
            model_name='lead',
            name='ssl_insecure',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='SSL unsicher'),
        ),
    ]
