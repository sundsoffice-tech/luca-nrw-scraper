"""
PostgreSQL LISTEN/NOTIFY Listener for real-time log streaming.

Provides a push-based notification system that eliminates polling overhead.
"""

import json
import logging
import select
import time
import threading
from typing import Optional, Callable, Dict, Any
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class PostgresListener:
    """
    Manages a persistent PostgreSQL connection for LISTEN/NOTIFY.
    
    This class maintains a long-lived database connection outside of Django's
    transaction management to receive real-time notifications from PostgreSQL.
    
    Features:
    - Automatic reconnection on connection loss
    - Exponential backoff for retry attempts
    - Connection health monitoring
    - Thread-safe notification handling
    - Graceful shutdown
    
    Usage:
        listener = PostgresListener(channel='log_updates')
        listener.start(callback=handle_notification)
        # ... later ...
        listener.stop()
    """
    
    def __init__(self, channel: str = 'log_updates', poll_timeout: float = 5.0):
        """
        Initialize the PostgreSQL listener.
        
        Args:
            channel: PostgreSQL channel name to listen on
            poll_timeout: Timeout in seconds for select() polling
        """
        self.channel = channel
        self.poll_timeout = poll_timeout
        self._conn = None
        self._cursor = None
        self._running = False
        self._thread = None
        self._callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._base_backoff = 2.0  # Base seconds for exponential backoff
        self._lock = threading.Lock()
        
    def is_postgresql(self) -> bool:
        """Check if the database backend is PostgreSQL."""
        return 'postgresql' in settings.DATABASES['default']['ENGINE']
    
    def _get_raw_connection(self):
        """
        Get a raw psycopg2 connection outside of Django's connection pool.
        
        This creates a new connection specifically for LISTEN/NOTIFY that
        won't interfere with Django's transaction management.
        """
        if not self.is_postgresql():
            logger.warning("PostgresListener: Database is not PostgreSQL, LISTEN/NOTIFY not available")
            return None
            
        try:
            import psycopg2
            from django.db import connections
            
            # Get connection parameters from Django settings
            db_settings = settings.DATABASES['default']
            
            conn_params = {
                'dbname': db_settings.get('NAME'),
                'user': db_settings.get('USER'),
                'password': db_settings.get('PASSWORD'),
                'host': db_settings.get('HOST', 'localhost'),
                'port': db_settings.get('PORT', 5432),
            }
            
            # Remove None values
            conn_params = {k: v for k, v in conn_params.items() if v is not None}
            
            # Create new connection
            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            logger.info(f"PostgresListener: Created raw connection to PostgreSQL")
            return conn
            
        except Exception as e:
            logger.error(f"PostgresListener: Failed to create raw connection: {e}")
            return None
    
    def connect(self) -> bool:
        """
        Establish connection and execute LISTEN command.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Close existing connection if any
            self.disconnect()
            
            # Create new connection
            self._conn = self._get_raw_connection()
            if not self._conn:
                return False
            
            # Create cursor and execute LISTEN
            self._cursor = self._conn.cursor()
            self._cursor.execute(f"LISTEN {self.channel};")
            
            logger.info(f"PostgresListener: Connected and listening on channel '{self.channel}'")
            self._reconnect_attempts = 0  # Reset on successful connection
            return True
            
        except Exception as e:
            logger.error(f"PostgresListener: Failed to connect: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Close the connection and cursor."""
        try:
            if self._cursor:
                self._cursor.close()
                self._cursor = None
                
            if self._conn:
                self._conn.close()
                self._conn = None
                
            logger.debug("PostgresListener: Disconnected")
            
        except Exception as e:
            logger.error(f"PostgresListener: Error during disconnect: {e}")
    
    def _reconnect_with_backoff(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.
        
        Returns:
            True if reconnection successful, False if max attempts reached
        """
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error(f"PostgresListener: Max reconnection attempts ({self._max_reconnect_attempts}) reached")
            return False
        
        self._reconnect_attempts += 1
        backoff = min(self._base_backoff * (2 ** (self._reconnect_attempts - 1)), 60)
        
        logger.info(f"PostgresListener: Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts} "
                   f"after {backoff:.1f}s backoff")
        
        time.sleep(backoff)
        return self.connect()
    
    def check_connection_health(self) -> bool:
        """
        Check if the connection is still alive.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self._conn or not self._cursor:
                return False
            
            # Try a simple query to check connection
            self._cursor.execute("SELECT 1;")
            return True
            
        except Exception as e:
            logger.warning(f"PostgresListener: Connection health check failed: {e}")
            return False
    
    def _listen_loop(self):
        """
        Main listening loop that polls for notifications.
        
        This runs in a separate thread and continuously checks for new
        notifications using select() with a timeout.
        """
        logger.info("PostgresListener: Starting listen loop")
        
        while self._running:
            try:
                # Check connection health
                if not self.check_connection_health():
                    logger.warning("PostgresListener: Connection unhealthy, attempting reconnection")
                    if not self._reconnect_with_backoff():
                        logger.error("PostgresListener: Failed to reconnect, stopping listener")
                        self._running = False
                        break
                    continue
                
                # Wait for notifications using select()
                # This blocks until a notification arrives or timeout occurs
                if select.select([self._conn], [], [], self.poll_timeout) == ([], [], []):
                    # Timeout - no notifications
                    continue
                
                # Poll for notifications
                self._conn.poll()
                
                # Process all pending notifications
                while self._conn.notifies:
                    notify = self._conn.notifies.pop(0)
                    
                    try:
                        # Parse JSON payload
                        payload = json.loads(notify.payload)
                        
                        logger.debug(f"PostgresListener: Received notification: {payload}")
                        
                        # Call callback with payload
                        if self._callback:
                            self._callback(payload)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"PostgresListener: Failed to parse notification payload: {e}")
                    except Exception as e:
                        logger.error(f"PostgresListener: Error in notification callback: {e}")
                
            except Exception as e:
                logger.error(f"PostgresListener: Error in listen loop: {e}")
                
                # Attempt reconnection
                if not self._reconnect_with_backoff():
                    logger.error("PostgresListener: Failed to recover from error, stopping listener")
                    self._running = False
                    break
        
        logger.info("PostgresListener: Listen loop stopped")
        self.disconnect()
    
    def start(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Start listening for notifications in a background thread.
        
        Args:
            callback: Function to call when a notification is received.
                     Should accept a single dict argument (the notification payload).
        """
        if self._running:
            logger.warning("PostgresListener: Already running")
            return
        
        if not self.is_postgresql():
            logger.warning("PostgresListener: Cannot start - database is not PostgreSQL")
            return
        
        self._callback = callback
        self._running = True
        
        # Connect
        if not self.connect():
            logger.error("PostgresListener: Failed to connect, not starting")
            self._running = False
            return
        
        # Start listening thread
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="PostgresListener")
        self._thread.start()
        
        logger.info("PostgresListener: Started successfully")
    
    def stop(self):
        """Stop listening and clean up resources."""
        logger.info("PostgresListener: Stopping...")
        
        self._running = False
        
        # Wait for thread to finish (with timeout)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            
        self.disconnect()
        logger.info("PostgresListener: Stopped")
    
    def get_queue_usage(self) -> Optional[float]:
        """
        Check PostgreSQL notification queue usage.
        
        Returns:
            Queue usage as a percentage (0-100), or None if unable to check
        """
        try:
            if not self._conn or not self._cursor:
                return None
            
            # Query pg_notification_queue_usage
            self._cursor.execute("SELECT pg_notification_queue_usage();")
            result = self._cursor.fetchone()
            
            if result:
                return result[0] * 100  # Convert to percentage
            return None
            
        except Exception as e:
            logger.error(f"PostgresListener: Failed to check queue usage: {e}")
            return None


# Global listener instance (singleton pattern)
_global_listener: Optional[PostgresListener] = None
_listener_lock = threading.Lock()


def get_global_listener() -> PostgresListener:
    """
    Get or create the global PostgresListener instance.
    
    This ensures a single listener is shared across the application,
    avoiding multiple connections for the same purpose.
    
    Returns:
        The global PostgresListener instance
    """
    global _global_listener
    
    with _listener_lock:
        if _global_listener is None:
            _global_listener = PostgresListener()
        return _global_listener


def cleanup_global_listener():
    """
    Stop and cleanup the global listener.
    
    Should be called on application shutdown.
    """
    global _global_listener
    
    with _listener_lock:
        if _global_listener is not None:
            _global_listener.stop()
            _global_listener = None
