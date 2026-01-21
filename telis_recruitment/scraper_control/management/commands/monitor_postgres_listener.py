"""
Django management command to monitor PostgreSQL LISTEN/NOTIFY status.

Usage:
    python manage.py monitor_postgres_listener
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from scraper_control.postgres_listener import get_global_listener
from scraper_control.notification_queue import get_notification_queue
import time


class Command(BaseCommand):
    help = 'Monitor PostgreSQL LISTEN/NOTIFY listener status and queue usage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Monitoring interval in seconds (default: 5)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Check status once and exit',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        once = options['once']
        
        # Check if PostgreSQL is configured
        db_engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
        
        if 'postgresql' not in db_engine:
            self.stdout.write(self.style.WARNING(
                'Database is not PostgreSQL. LISTEN/NOTIFY monitoring not available.'
            ))
            self.stdout.write(f'Current database engine: {db_engine}')
            return
        
        self.stdout.write(self.style.SUCCESS('PostgreSQL LISTEN/NOTIFY Monitor'))
        self.stdout.write('=' * 60)
        
        listener = get_global_listener()
        notif_queue = get_notification_queue()
        
        try:
            while True:
                self._display_status(listener, notif_queue)
                
                if once:
                    break
                
                time.sleep(interval)
                self.stdout.write('\n')
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nMonitoring stopped by user'))
    
    def _display_status(self, listener, notif_queue):
        """Display current status of listener and queues."""
        self.stdout.write(f'\nTimestamp: {time.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('-' * 60)
        
        # Listener status
        if listener._running:
            self.stdout.write(self.style.SUCCESS('✓ Listener: RUNNING'))
            
            # Connection health
            if listener.check_connection_health():
                self.stdout.write(self.style.SUCCESS('✓ Connection: HEALTHY'))
            else:
                self.stdout.write(self.style.ERROR('✗ Connection: UNHEALTHY'))
            
            # Reconnection attempts
            if listener._reconnect_attempts > 0:
                self.stdout.write(self.style.WARNING(
                    f'⚠ Reconnection attempts: {listener._reconnect_attempts}/{listener._max_reconnect_attempts}'
                ))
            
            # PostgreSQL notification queue usage
            queue_usage = listener.get_queue_usage()
            if queue_usage is not None:
                if queue_usage < 50:
                    style = self.style.SUCCESS
                elif queue_usage < 80:
                    style = self.style.WARNING
                else:
                    style = self.style.ERROR
                
                self.stdout.write(style(f'  PG Queue Usage: {queue_usage:.2f}%'))
            
        else:
            self.stdout.write(self.style.ERROR('✗ Listener: NOT RUNNING'))
        
        # Notification queue stats
        stats = notif_queue.get_stats()
        self.stdout.write(f'\nNotification Queues:')
        self.stdout.write(f'  Total queues: {stats["total_queues"]}')
        self.stdout.write(f'  Total notifications: {stats["total_notifications"]}')
        
        if stats['queue_sizes']:
            self.stdout.write('  Queue sizes by run_id:')
            for run_id, size in stats['queue_sizes'].items():
                self.stdout.write(f'    Run #{run_id}: {size} notifications')
