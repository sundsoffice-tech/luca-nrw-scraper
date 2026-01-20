# Generated migration for normalized_phone field

from django.db import migrations, models


def populate_normalized_phone(apps, schema_editor):
    """Populate normalized_phone for existing leads."""
    Lead = apps.get_model('leads', 'Lead')
    for lead in Lead.objects.all():
        if lead.telefon:
            digits = "".join(ch for ch in lead.telefon if ch.isdigit())
            lead.normalized_phone = digits or None
            lead.save(update_fields=['normalized_phone'])


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0010_lead_qualifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='normalized_phone',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Nur Ziffern für Deduplizierung',
                max_length=20,
                null=True,
                verbose_name='Normalisierte Telefonnummer'
            ),
        ),
        migrations.RunPython(populate_normalized_phone, reverse_code=migrations.RunPython.noop),
    ]
