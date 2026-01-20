# Generated migration for flexible template system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0010_extended_multipage_project_management'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagetemplate',
            name='layout_config',
            field=models.JSONField(blank=True, default=dict, help_text='Flexible Layout-Konfiguration (Sektionen, Einstellungen, Optionen)'),
        ),
        migrations.AlterField(
            model_name='pagetemplate',
            name='category',
            field=models.CharField(
                choices=[
                    ('landing', 'Landingpage'),
                    ('contact', 'Kontaktseite'),
                    ('sales', 'Verkaufsseite'),
                    ('info', 'Infoseite'),
                    ('lead_gen', 'Lead Generation'),
                    ('product', 'Produktseite'),
                    ('coming_soon', 'Coming Soon'),
                    ('thank_you', 'Danke-Seite'),
                ],
                max_length=50
            ),
        ),
    ]
