from django.db import migrations, models


def normalize_email(value):
    if not value:
        return None
    return value.strip().lower()


def populate_email_normalized(apps, schema_editor):
    Lead = apps.get_model('leads', 'Lead')
    for lead in Lead.objects.all().iterator():
        Lead.objects.filter(pk=lead.pk).update(
            email_normalized=normalize_email(lead.email)
        )


class Migration(migrations.Migration):
    dependencies = [
        ('leads', '0010_lead_qualifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='email_normalized',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                verbose_name='Normalisierte E-Mail',
                help_text='Klein geschrieben und getrimmt für schnelle Duplikatssuche',
                db_index=True,
            ),
        ),
        migrations.RunPython(
            populate_email_normalized,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
