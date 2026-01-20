# Generated manually for extended multipage project management

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0009_project_landingpage_project'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_seo_title_suffix', models.CharField(blank=True, max_length=100)),
                ('default_seo_description', models.TextField(blank=True)),
                ('default_seo_image', models.URLField(blank=True)),
                ('google_analytics_id', models.CharField(blank=True, max_length=50)),
                ('facebook_pixel_id', models.CharField(blank=True, max_length=50)),
                ('custom_head_code', models.TextField(blank=True, help_text='Wird in <head> eingefügt')),
                ('custom_body_code', models.TextField(blank=True, help_text='Wird vor </body> eingefügt')),
                ('primary_color', models.CharField(default='#3B82F6', max_length=7)),
                ('secondary_color', models.CharField(default='#10B981', max_length=7)),
                ('font_family', models.CharField(default='Inter, sans-serif', max_length=100)),
                ('favicon', models.ImageField(blank=True, upload_to='projects/favicons/')),
                ('custom_404_page', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pages.landingpage')),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='pages.project')),
            ],
            options={
                'verbose_name': 'Project Settings',
                'verbose_name_plural': 'Project Settings',
            },
        ),
        migrations.CreateModel(
            name='ProjectNavigation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Angezeigter Menütext', max_length=100)),
                ('external_url', models.URLField(blank=True, help_text='Externe URL (überschreibt Seiten-Link)')),
                ('icon', models.CharField(blank=True, help_text="Icon-Klasse (z.B. 'fa-home')", max_length=50)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_visible', models.BooleanField(default=True)),
                ('open_in_new_tab', models.BooleanField(default=False)),
                ('page', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pages.landingpage')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='pages.projectnavigation')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nav_items', to='pages.project')),
            ],
            options={
                'verbose_name': 'Project Navigation',
                'verbose_name_plural': 'Project Navigations',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ProjectDeployment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Ausstehend'), ('building', 'Wird erstellt'), ('deploying', 'Wird deployed'), ('success', 'Erfolgreich'), ('failed', 'Fehlgeschlagen')], default='pending', max_length=20)),
                ('version', models.CharField(blank=True, max_length=50)),
                ('target_domain', models.CharField(blank=True, max_length=255)),
                ('target_path', models.CharField(default='/', max_length=255)),
                ('build_log', models.TextField(blank=True)),
                ('deployed_files_count', models.PositiveIntegerField(default=0)),
                ('deployed_size_bytes', models.PositiveBigIntegerField(default=0)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('deployed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deployments', to='pages.project')),
            ],
            options={
                'verbose_name': 'Project Deployment',
                'verbose_name_plural': 'Project Deployments',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='ProjectAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='projects/assets/%Y/%m/')),
                ('asset_type', models.CharField(choices=[('css', 'Stylesheet'), ('js', 'JavaScript'), ('font', 'Font'), ('image', 'Bild'), ('other', 'Sonstiges')], max_length=20)),
                ('name', models.CharField(max_length=255)),
                ('relative_path', models.CharField(max_length=500)),
                ('include_globally', models.BooleanField(default=False, help_text='In alle Projekt-Seiten einbinden')),
                ('load_order', models.PositiveIntegerField(default=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_assets', to='pages.project')),
            ],
            options={
                'verbose_name': 'Project Asset',
                'verbose_name_plural': 'Project Assets',
                'ordering': ['load_order', 'name'],
            },
        ),
    ]
