# Generated migration for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0010_lead_qualifications'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['email'], name='leads_lead_email_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['telefon'], name='leads_lead_telefon_idx'),
        ),
    ]
