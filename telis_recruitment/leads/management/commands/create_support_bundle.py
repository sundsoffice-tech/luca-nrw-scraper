"""
Django management command to create a support bundle for diagnostics.

This command generates a comprehensive ZIP file containing:
- System information
- Configuration status (sanitized, no secrets)
- Recent logs
- Database statistics
- Application version
- Error reports

Usage:
    python manage.py create_support_bundle
    python manage.py create_support_bundle --output /path/to/bundle.zip
"""

import os
import sys
import json
import platform
import zipfile
from datetime import datetime
from pathlib import Path
from io import StringIO

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.contrib.auth.models import User

from leads.models import Lead


class Command(BaseCommand):
    help = 'Create a support bundle with system diagnostics for troubleshooting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output path for the support bundle ZIP file'
        )
        parser.add_argument(
            '--include-logs',
            action='store_true',
            help='Include log files (last 1000 lines of each)'
        )

    def handle(self, *args, **options):
        """Generate and save support bundle."""
        self.stdout.write(self.style.WARNING('🔧 Creating support bundle...'))
        
        # Determine output path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if options['output']:
            output_path = options['output']
        else:
            output_path = f'support_bundle_{timestamp}.zip'
        
        # Create ZIP file
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all diagnostic files
                self._add_system_info(zipf)
                self._add_version_info(zipf)
                self._add_config_status(zipf)
                self._add_database_stats(zipf)
                self._add_django_checks(zipf)
                
                if options['include_logs']:
                    self._add_logs(zipf)
                
                self._add_environment_info(zipf)
                self._add_readme(zipf)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Support bundle created: {output_path}'))
            self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANT: Review the bundle before sharing!'))
            self.stdout.write('   Ensure no sensitive information is included.')
            
            # Show bundle info
            file_size = os.path.getsize(output_path)
            self.stdout.write(f'\n📦 Bundle size: {file_size / 1024:.2f} KB')
            self.stdout.write(f'📁 Location: {os.path.abspath(output_path)}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating support bundle: {e}'))
            raise

    def _add_system_info(self, zipf):
        """Add system information."""
        info = {
            'timestamp': datetime.now().isoformat(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
            },
            'django_version': self._get_django_version(),
        }
        
        # Add resource info if available
        try:
            import psutil
            info['resources'] = {
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent,
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent,
                }
            }
        except ImportError:
            info['resources'] = 'psutil not available'
        
        zipf.writestr('system_info.json', json.dumps(info, indent=2))
        self.stdout.write('  ✓ System information')

    def _add_version_info(self, zipf):
        """Add application version information."""
        version_file = Path(settings.BASE_DIR).parent / 'VERSION'
        
        version_info = {
            'application': 'LUCA NRW Scraper',
            'version': 'unknown',
        }
        
        if version_file.exists():
            version_info['version'] = version_file.read_text().strip()
        
        # Try to get git info
        try:
            import subprocess
            git_hash = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=settings.BASE_DIR,
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            git_branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=settings.BASE_DIR,
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            version_info['git'] = {
                'commit': git_hash,
                'branch': git_branch,
            }
        except:
            version_info['git'] = 'not available'
        
        zipf.writestr('version_info.json', json.dumps(version_info, indent=2))
        self.stdout.write('  ✓ Version information')

    def _add_config_status(self, zipf):
        """Add sanitized configuration status."""
        config = {
            'debug_mode': settings.DEBUG,
            'allowed_hosts': settings.ALLOWED_HOSTS,
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'static_root': str(settings.STATIC_ROOT) if hasattr(settings, 'STATIC_ROOT') else None,
            'media_root': str(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else None,
            'installed_apps': settings.INSTALLED_APPS,
            'middleware': settings.MIDDLEWARE,
        }
        
        # Add environment variables (sanitized)
        env_vars = {}
        sensitive_keys = ['SECRET_KEY', 'PASSWORD', 'API_KEY', 'TOKEN', 'WEBHOOK_SECRET']
        for key in os.environ:
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                env_vars[key] = '[REDACTED]'
            else:
                env_vars[key] = os.environ[key]
        
        config['environment_variables'] = env_vars
        
        # Security settings
        config['security'] = {
            'allow_insecure_ssl': os.getenv('ALLOW_INSECURE_SSL', '0'),
            'secure_ssl_redirect': getattr(settings, 'SECURE_SSL_REDIRECT', False),
            'session_cookie_secure': getattr(settings, 'SESSION_COOKIE_SECURE', False),
            'csrf_cookie_secure': getattr(settings, 'CSRF_COOKIE_SECURE', False),
            'secure_hsts_seconds': getattr(settings, 'SECURE_HSTS_SECONDS', 0),
        }
        
        zipf.writestr('config_status.json', json.dumps(config, indent=2, default=str))
        self.stdout.write('  ✓ Configuration status (sanitized)')

    def _add_database_stats(self, zipf):
        """Add database statistics."""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'leads': {
                'total': Lead.objects.count(),
                'by_status': {},
                'by_source': {},
                'by_lead_type': {},
            },
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'staff': User.objects.filter(is_staff=True).count(),
                'superusers': User.objects.filter(is_superuser=True).count(),
            }
        }
        
        # Lead statistics
        try:
            from django.db.models import Count
            
            # By status
            status_counts = Lead.objects.values('status').annotate(count=Count('id'))
            for item in status_counts:
                stats['leads']['by_status'][item['status']] = item['count']
            
            # By source
            source_counts = Lead.objects.values('source').annotate(count=Count('id'))
            for item in source_counts:
                stats['leads']['by_source'][item['source']] = item['count']
            
            # By lead type
            type_counts = Lead.objects.values('lead_type').annotate(count=Count('id'))
            for item in type_counts:
                stats['leads']['by_lead_type'][item['lead_type']] = item['count']
            
            # Recent activity
            from datetime import timedelta
            now = datetime.now()
            stats['leads']['recent_activity'] = {
                'last_24h': Lead.objects.filter(
                    created_at__gte=now - timedelta(days=1)
                ).count() if hasattr(Lead, 'created_at') else 'N/A',
                'last_7d': Lead.objects.filter(
                    created_at__gte=now - timedelta(days=7)
                ).count() if hasattr(Lead, 'created_at') else 'N/A',
                'last_30d': Lead.objects.filter(
                    created_at__gte=now - timedelta(days=30)
                ).count() if hasattr(Lead, 'created_at') else 'N/A',
            }
        except Exception as e:
            stats['leads']['error'] = str(e)
        
        zipf.writestr('database_stats.json', json.dumps(stats, indent=2))
        self.stdout.write('  ✓ Database statistics')

    def _add_django_checks(self, zipf):
        """Add Django system check results."""
        from django.core.management import call_command
        
        # Capture check output
        output = StringIO()
        try:
            call_command('check', stdout=output)
            check_result = output.getvalue()
        except Exception as e:
            check_result = f'Error running checks: {e}'
        
        # Capture deployment check output (if not in debug)
        deploy_output = StringIO()
        if not settings.DEBUG:
            try:
                call_command('check', '--deploy', stdout=deploy_output, stderr=deploy_output)
                deploy_check_result = deploy_output.getvalue()
            except Exception as e:
                deploy_check_result = f'Error running deployment checks: {e}'
        else:
            deploy_check_result = 'Skipped (DEBUG=True)'
        
        checks = {
            'system_check': check_result,
            'deployment_check': deploy_check_result,
        }
        
        zipf.writestr('django_checks.txt', 
                      f"System Check:\n{checks['system_check']}\n\n"
                      f"Deployment Check:\n{checks['deployment_check']}")
        self.stdout.write('  ✓ Django system checks')

    def _add_logs(self, zipf):
        """Add recent log files."""
        log_dir = Path(settings.BASE_DIR) / 'logs'
        
        if log_dir.exists():
            for log_file in log_dir.glob('*.log'):
                try:
                    # Read last 1000 lines
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        last_lines = lines[-1000:]  # Last 1000 lines
                        content = ''.join(last_lines)
                    
                    zipf.writestr(f'logs/{log_file.name}', content)
                except Exception as e:
                    zipf.writestr(f'logs/{log_file.name}_error.txt', 
                                  f'Error reading log: {e}')
            
            self.stdout.write('  ✓ Log files (last 1000 lines each)')
        else:
            zipf.writestr('logs/README.txt', 'No log directory found')
            self.stdout.write('  ⚠ No log directory found')

    def _add_environment_info(self, zipf):
        """Add Python environment information."""
        import pkg_resources
        
        # Installed packages
        installed_packages = []
        for dist in pkg_resources.working_set:
            installed_packages.append(f'{dist.key}=={dist.version}')
        
        installed_packages.sort()
        
        env_info = {
            'python_version': sys.version,
            'python_path': sys.executable,
            'installed_packages': installed_packages,
        }
        
        zipf.writestr('environment.json', json.dumps(env_info, indent=2))
        zipf.writestr('requirements.txt', '\n'.join(installed_packages))
        self.stdout.write('  ✓ Python environment')

    def _add_readme(self, zipf):
        """Add README for the support bundle."""
        readme_content = f"""
LUCA NRW Scraper - Support Bundle
==================================

Generated: {datetime.now().isoformat()}

This support bundle contains diagnostic information to help troubleshoot issues
with your LUCA NRW Scraper installation.

Contents:
---------
- system_info.json: Operating system and hardware information
- version_info.json: Application version and git information
- config_status.json: Configuration settings (secrets redacted)
- database_stats.json: Database statistics and lead counts
- django_checks.txt: Django system check results
- environment.json: Python environment and installed packages
- requirements.txt: List of installed Python packages
- logs/: Recent log files (if --include-logs was used)

IMPORTANT - Privacy Notice:
---------------------------
This bundle has been automatically sanitized to remove sensitive information
such as API keys, passwords, and secret keys. However, please review the
contents before sharing to ensure no sensitive data is included.

What to check:
- config_status.json: Verify all secrets are marked [REDACTED]
- logs/*: Review for any accidentally logged sensitive data
- database_stats.json: Ensure no personal data is exposed

How to use this bundle:
-----------------------
1. Review the contents for sensitive information
2. Share with support team or attach to GitHub issue
3. Provide additional context about your issue
4. Include steps to reproduce the problem

For more information:
---------------------
- Documentation: https://github.com/sundsoffice-tech/luca-nrw-scraper
- Security: docs/SECURITY_CHECKLIST.md
- Support: Open a GitHub issue

Generated by: python manage.py create_support_bundle
"""
        zipf.writestr('README.txt', readme_content.strip())
        self.stdout.write('  ✓ README file')

    def _get_django_version(self):
        """Get Django version."""
        import django
        return django.get_version()
