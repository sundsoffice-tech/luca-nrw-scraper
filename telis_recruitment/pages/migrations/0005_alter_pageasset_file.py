# Generated migration to change FileField to ImageField for security

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0004_pageasset_brandsettings_pagetemplate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pageasset',
            name='file',
            field=models.ImageField(help_text='Image file', upload_to='page_assets/'),
        ),
    ]
