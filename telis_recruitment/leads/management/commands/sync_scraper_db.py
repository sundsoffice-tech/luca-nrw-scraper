"""
Automatic sync wrapper for import_scraper_db command.

This command provides scheduling support and can be used with cron for automatic syncing.

Usage:
    # One-time sync
    python manage.py sync_scraper_db
    
    # Watch mode (runs continuously)
    python manage.py sync_scraper_db --watch --interval 300
    
    # With custom database path
    python manage.py sync_scraper_db --db /path/to/scraper.db --watch --interval 300
    
    # Dry run
    python manage.py sync_scraper_db --dry-run

Cron Setup:
    # Add to crontab for automatic sync every 5 minutes:
    */5 * * * * cd /path/to/telis_recruitment && python manage.py sync_scraper_db >> /var/log/scraper_sync.log 2>&1
    
    # Or every hour:
    0 * * * * cd /path/to/telis_recruitment && python manage.py sync_scraper_db >> /var/log/scraper_sync.log 2>&1
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
import time
from datetime import datetime


class Command(BaseCommand):
    help = 'Sync wrapper for import_scraper_db with scheduling support'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--db',
            type=str,
            help='Path to scraper.db (default: auto-detected)'
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Continuous watch mode - syncs every interval seconds'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes default
            help='Interval in seconds for watch mode (default: 300)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without saving'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force import all leads, ignoring last sync timestamp'
        )
    
    def handle(self, *args, **options):
        db_path = options.get('db')
        watch_mode = options.get('watch', False)
        interval = options.get('interval', 300)
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n' + '=' * 60 +
                '\n  🔄 Scraper DB Auto-Sync\n' +
                '=' * 60 + '\n'
            )
        )
        
        if watch_mode:
            self.stdout.write(
                self.style.WARNING(
                    f'👁️  Watch mode enabled - syncing every {interval} seconds\n'
                    f'   Press Ctrl+C to stop\n'
                )
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  DRY RUN MODE - No changes will be saved\n')
            )
        
        # Build arguments for import_scraper_db
        import_args = []
        import_kwargs = {
            'dry_run': dry_run,
            'force': force,
        }
        
        if db_path:
            import_kwargs['db'] = db_path
        
        try:
            if watch_mode:
                # Continuous sync mode
                iteration = 0
                while True:
                    iteration += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n📅 Sync #{iteration} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                        )
                    )
                    
                    try:
                        call_command('import_scraper_db', *import_args, **import_kwargs)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'\n❌ Sync failed: {str(e)}\n')
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n⏰ Next sync in {interval} seconds...\n'
                        )
                    )
                    
                    time.sleep(interval)
                    
            else:
                # Single sync
                self.stdout.write(
                    self.style.SUCCESS(
                        f'📅 Single sync - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                    )
                )
                call_command('import_scraper_db', *import_args, **import_kwargs)
                
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Sync completed successfully\n')
                )
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n\n⛔ Sync stopped by user\n')
            )
        except Exception as e:
            raise CommandError(f'Sync failed: {str(e)}')
