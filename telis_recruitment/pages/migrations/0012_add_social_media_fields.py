# Generated migration for social media integration features
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0011_flexible_template_system'),
    ]

    operations = [
        # Social Media / OpenGraph fields
        migrations.AddField(
            model_name='landingpage',
            name='og_title',
            field=models.CharField(blank=True, help_text='OpenGraph title (defaults to seo_title)', max_length=255),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_description',
            field=models.TextField(blank=True, help_text='OpenGraph description (defaults to seo_description)'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_image',
            field=models.URLField(blank=True, help_text='OpenGraph image URL (defaults to seo_image)'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_type',
            field=models.CharField(default='website', help_text='OpenGraph type (website, article, etc.)', max_length=50),
        ),
        
        # Twitter Card fields
        migrations.AddField(
            model_name='landingpage',
            name='twitter_card',
            field=models.CharField(default='summary_large_image', help_text='Twitter card type', max_length=50),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='twitter_title',
            field=models.CharField(blank=True, help_text='Twitter card title (defaults to og_title)', max_length=255),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='twitter_description',
            field=models.TextField(blank=True, help_text='Twitter card description (defaults to og_description)'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='twitter_image',
            field=models.URLField(blank=True, help_text='Twitter card image (defaults to og_image)'),
        ),
        
        # Share button settings
        migrations.AddField(
            model_name='landingpage',
            name='enable_share_buttons',
            field=models.BooleanField(default=False, help_text='Enable social media share buttons on the page'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='share_button_position',
            field=models.CharField(
                choices=[
                    ('top-left', 'Top Left'),
                    ('top-right', 'Top Right'),
                    ('bottom-left', 'Bottom Left'),
                    ('bottom-right', 'Bottom Right'),
                    ('inline', 'Inline in content'),
                ],
                default='bottom-right',
                help_text='Position of share buttons',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='share_platforms',
            field=models.JSONField(blank=True, default=list, help_text="List of enabled share platforms (e.g., ['facebook', 'twitter', 'whatsapp', 'linkedin'])"),
        ),
    ]
