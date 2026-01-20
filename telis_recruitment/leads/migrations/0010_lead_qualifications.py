from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0009_savedfilter'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='qualifications',
            field=models.JSONField(
                blank=True,
                null=True,
                verbose_name='Qualifikationen',
                help_text='Array von Qualifikationen',
            ),
        ),
    ]
