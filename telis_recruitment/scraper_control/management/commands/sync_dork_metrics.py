# -*- coding: utf-8 -*-
"""
Django management command to sync dork metrics from SQLite to Django CRM.

This command synchronizes AI learning data (stored in SQLite for performance)
with the Django SearchDork model for dashboard visibility and CRM integration.

Usage:
    python manage.py sync_dork_metrics
    python manage.py sync_dork_metrics --create-new
    python manage.py sync_dork_metrics --db-path=/path/to/scraper.db
"""

from django.core.management.base import BaseCommand, CommandError
from telis_recruitment.scraper_control.services.dork_sync import DorkSyncService


class Command(BaseCommand):
    help = 'Synchronize dork performance metrics from SQLite learning DB to Django CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-path',
            type=str,
            default='scraper.db',
            help='Path to the SQLite learning database (default: scraper.db)'
        )
        parser.add_argument(
            '--create-new',
            action='store_true',
            help='Create new SearchDork entries for successful AI-learned dorks'
        )
        parser.add_argument(
            '--min-uses',
            type=int,
            default=2,
            help='Minimum times a dork must be used to be synced (default: 2)'
        )
        parser.add_argument(
            '--min-phone-leads',
            type=int,
            default=1,
            help='Minimum phone leads required to create new entries (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes'
        )

    def handle(self, *args, **options):
        db_path = options['db_path']
        create_new = options['create_new']
        min_uses = options['min_uses']
        min_phone_leads = options['min_phone_leads']
        dry_run = options['dry_run']

        self.stdout.write(f'Syncing dork metrics from {db_path}...')
        
        sync_service = DorkSyncService(sqlite_db_path=db_path)
        
        # Get metrics to preview in dry-run mode
        if dry_run:
            metrics = sync_service.get_sqlite_dork_metrics()
            qualifying = [m for m in metrics if m['times_used'] >= min_uses]
            
            self.stdout.write(f'\n--- DRY RUN ---')
            self.stdout.write(f'Total dorks in SQLite: {len(metrics)}')
            self.stdout.write(f'Qualifying dorks (used >= {min_uses}x): {len(qualifying)}')
            
            # Show top performing dorks
            self.stdout.write(f'\nTop 10 dorks by success rate:')
            for i, m in enumerate(qualifying[:10], 1):
                status = '✓ (would create)' if (
                    create_new and 
                    m['leads_with_phone'] >= min_phone_leads and 
                    m['pool'] == 'core'
                ) else '○ (update only)'
                
                self.stdout.write(
                    f'  {i}. [{m["pool"]:7}] Score: {m["score"]:.2%}, '
                    f'Uses: {m["times_used"]}, Leads+Phone: {m["leads_with_phone"]} '
                    f'{status}'
                )
                self.stdout.write(f'      Query: {m["dork"][:60]}...')
            
            return
        
        # Perform actual sync
        summary = sync_service.sync_all_dorks(
            create_successful=create_new,
            min_times_used=min_uses,
            min_leads_with_phone=min_phone_leads,
        )
        
        # Report results
        self.stdout.write(self.style.SUCCESS(f'\nSync complete!'))
        self.stdout.write(f'  Processed: {summary["total_processed"]}')
        self.stdout.write(f'  Updated:   {summary["updated"]}')
        self.stdout.write(f'  Created:   {summary["created"]}')
        self.stdout.write(f'  Skipped:   {summary["skipped"]}')
        
        if summary['errors']:
            self.stdout.write(self.style.WARNING(f'\nErrors ({len(summary["errors"])}):'))
            for error in summary['errors'][:5]:  # Show first 5 errors
                self.stdout.write(f'  - {error}')
            if len(summary['errors']) > 5:
                self.stdout.write(f'  ... and {len(summary["errors"]) - 5} more')
