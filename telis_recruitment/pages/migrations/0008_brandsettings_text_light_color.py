# Generated manually to add text_light_color field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0007_fileversion_projecttemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandsettings',
            name='text_light_color',
            field=models.CharField(default='#6b7280', max_length=7),
        ),
    ]
