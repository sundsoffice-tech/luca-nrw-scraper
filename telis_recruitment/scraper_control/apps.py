from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ScraperControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scraper_control'
    
    def ready(self):
        """
        Initialize the PostgreSQL listener when Django starts.
        
        This is called once when the app is ready and starts the
        background listener for PostgreSQL LISTEN/NOTIFY.
        """
        # Only start listener if not in migration or test mode
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv or 'test' in sys.argv:
            return
        
        # Import here to avoid AppRegistryNotReady errors
        from .postgres_listener import get_global_listener
        from .notification_queue import on_notification_received
        from django.conf import settings
        
        # Check if PostgreSQL is configured
        db_engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
        
        if 'postgresql' in db_engine:
            try:
                listener = get_global_listener()
                
                # Start listener if not already running
                if not listener._running:
                    listener.start(callback=on_notification_received)
                    logger.info("ScraperControl: PostgreSQL LISTEN/NOTIFY listener started successfully")
                else:
                    logger.info("ScraperControl: PostgreSQL listener already running")
                    
            except Exception as e:
                logger.warning(f"ScraperControl: Could not start PostgreSQL listener: {e}")
                logger.warning("ScraperControl: Falling back to polling mode")
        else:
            logger.info("ScraperControl: Using SQLite - polling mode active (PostgreSQL LISTEN/NOTIFY not available)")

