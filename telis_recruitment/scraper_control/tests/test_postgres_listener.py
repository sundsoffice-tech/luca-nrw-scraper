"""
Unit tests for PostgreSQL LISTEN/NOTIFY listener.
"""

import pytest
from unittest.mock import Mock, patch
from scraper_control.postgres_listener import PostgresListener, get_global_listener, cleanup_global_listener
from scraper_control.notification_queue import NotificationQueue, get_notification_queue, on_notification_received


class TestPostgresListener:
    """Test cases for PostgresListener class."""
    
    @pytest.fixture
    def listener(self):
        """Create a test listener instance."""
        return PostgresListener(channel='test_channel', poll_timeout=1.0)
    
    def test_init(self, listener):
        """Test listener initialization."""
        assert listener.channel == 'test_channel'
        assert listener.poll_timeout == 1.0
        assert listener._running is False
        assert listener._conn is None
        assert listener._cursor is None
    
    @patch('scraper_control.postgres_listener.settings')
    def test_is_postgresql_true(self, mock_settings, listener):
        """Test is_postgresql returns True for PostgreSQL."""
        mock_settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql'
            }
        }
        assert listener.is_postgresql() is True
    
    @patch('scraper_control.postgres_listener.settings')
    def test_is_postgresql_false(self, mock_settings, listener):
        """Test is_postgresql returns False for SQLite."""
        mock_settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3'
            }
        }
        assert listener.is_postgresql() is False


class TestNotificationQueue:
    """Test cases for NotificationQueue class."""
    
    @pytest.fixture
    def queue(self):
        """Create a test notification queue."""
        return NotificationQueue(maxsize=5)
    
    def test_init(self, queue):
        """Test queue initialization."""
        assert queue._maxsize == 5
        assert len(queue._queues) == 0
    
    def test_put_notification(self, queue):
        """Test adding notification to queue."""
        notification = {
            'id': 1,
            'run_id': 100,
            'level': 'INFO',
            'message': 'Test message'
        }
        
        queue.put(notification)
        
        assert len(queue._queues[100]) == 1
        assert queue._queues[100][0] == notification
    
    def test_put_without_run_id(self, queue):
        """Test adding notification without run_id is ignored."""
        notification = {'id': 1, 'message': 'Test'}
        
        queue.put(notification)
        
        assert len(queue._queues) == 0
