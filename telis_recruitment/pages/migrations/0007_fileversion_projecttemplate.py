# Generated migration for FileVersion and ProjectTemplate models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0006_update_models_to_match_spec'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='File content at this version')),
                ('version', models.PositiveIntegerField(help_text='Sequential version number')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.CharField(blank=True, help_text='Optional note about changes', max_length=255)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('uploaded_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='pages.uploadedfile')),
            ],
            options={
                'verbose_name': 'File Version',
                'verbose_name_plural': 'File Versions',
                'ordering': ['-version'],
                'unique_together': {('uploaded_file', 'version')},
            },
        ),
        migrations.CreateModel(
            name='ProjectTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Template name', max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='Template description')),
                ('category', models.CharField(choices=[('blank', 'Blank Template'), ('basic', 'Basic HTML'), ('bootstrap', 'Bootstrap'), ('tailwind', 'Tailwind CSS'), ('business', 'Business'), ('portfolio', 'Portfolio'), ('landing', 'Landing Page'), ('blog', 'Blog'), ('ecommerce', 'E-Commerce'), ('other', 'Other')], default='other', max_length=50)),
                ('thumbnail', models.ImageField(blank=True, help_text='Preview thumbnail', upload_to='templates/thumbnails/')),
                ('files_data', models.JSONField(default=dict, help_text='Serialized file structure and content')),
                ('is_active', models.BooleanField(default=True)),
                ('usage_count', models.PositiveIntegerField(default=0, help_text='Number of times used')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Project Template',
                'verbose_name_plural': 'Project Templates',
                'ordering': ['category', 'name'],
            },
        ),
    ]
