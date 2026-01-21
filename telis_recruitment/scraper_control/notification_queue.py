"""
Notification queue manager for distributing PostgreSQL notifications to SSE clients.

This module provides a thread-safe queue system that allows multiple SSE
connections to receive notifications from a single PostgreSQL listener.
"""

import logging
import queue
import threading
from typing import Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class NotificationQueue:
    """
    Thread-safe queue for distributing notifications to multiple consumers.
    
    This allows multiple SSE clients to receive notifications from a single
    PostgreSQL listener without interfering with each other.
    
    Features:
    - Per-run_id queue distribution
    - Automatic queue cleanup
    - Thread-safe operations
    - Bounded queue size to prevent memory issues
    """
    
    def __init__(self, maxsize: int = 100):
        """
        Initialize the notification queue.
        
        Args:
            maxsize: Maximum number of notifications per queue
        """
        self._queues: Dict[int, list] = defaultdict(list)
        self._lock = threading.Lock()
        self._maxsize = maxsize
        
    def put(self, notification: Dict[str, Any]):
        """
        Add a notification to the appropriate queue(s).
        
        Args:
            notification: Notification payload from PostgreSQL
        """
        run_id = notification.get('run_id')
        if not run_id:
            logger.warning(f"NotificationQueue: Notification missing run_id: {notification}")
            return
        
        with self._lock:
            # Add to run-specific queue
            if len(self._queues[run_id]) >= self._maxsize:
                # Queue full, remove oldest
                self._queues[run_id].pop(0)
                logger.warning(f"NotificationQueue: Queue for run_id={run_id} full, dropping oldest notification")
            
            self._queues[run_id].append(notification)
            logger.debug(f"NotificationQueue: Added notification for run_id={run_id}, queue size: {len(self._queues[run_id])}")
    
    def get(self, run_id: int, timeout: Optional[float] = None, last_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get the next notification for a specific run_id.
        
        Args:
            run_id: The scraper run ID to get notifications for
            timeout: Maximum time to wait for a notification (in seconds)
            last_id: Last notification ID seen (for filtering)
        
        Returns:
            Notification dict or None if timeout
        """
        # Simple implementation: return first available notification
        # that's newer than last_id
        with self._lock:
            notifications = self._queues.get(run_id, [])
            
            for notification in notifications:
                notif_id = notification.get('id')
                if last_id is None or (notif_id and notif_id > last_id):
                    # Found new notification
                    return notification
        
        return None
    
    def get_all_new(self, run_id: int, last_id: Optional[int] = None) -> list:
        """
        Get all new notifications for a specific run_id.
        
        Args:
            run_id: The scraper run ID to get notifications for
            last_id: Last notification ID seen (for filtering)
        
        Returns:
            List of notification dicts
        """
        with self._lock:
            notifications = self._queues.get(run_id, [])
            
            if last_id is None:
                return list(notifications)
            
            # Return notifications newer than last_id
            return [n for n in notifications if n.get('id', 0) > last_id]
    
    def clear(self, run_id: Optional[int] = None):
        """
        Clear notifications for a specific run or all runs.
        
        Args:
            run_id: Run ID to clear, or None to clear all
        """
        with self._lock:
            if run_id is None:
                self._queues.clear()
                logger.debug("NotificationQueue: Cleared all queues")
            else:
                if run_id in self._queues:
                    del self._queues[run_id]
                    logger.debug(f"NotificationQueue: Cleared queue for run_id={run_id}")
    
    def get_queue_size(self, run_id: int) -> int:
        """
        Get the current size of a queue.
        
        Args:
            run_id: Run ID to check
        
        Returns:
            Number of notifications in queue
        """
        with self._lock:
            return len(self._queues.get(run_id, []))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all queues.
        
        Returns:
            Dict with queue statistics
        """
        with self._lock:
            return {
                'total_queues': len(self._queues),
                'queue_sizes': {run_id: len(notifs) for run_id, notifs in self._queues.items()},
                'total_notifications': sum(len(notifs) for notifs in self._queues.values()),
            }


# Global notification queue
_global_queue: Optional[NotificationQueue] = None
_queue_lock = threading.Lock()


def get_notification_queue() -> NotificationQueue:
    """
    Get or create the global notification queue.
    
    Returns:
        The global NotificationQueue instance
    """
    global _global_queue
    
    with _queue_lock:
        if _global_queue is None:
            _global_queue = NotificationQueue()
        return _global_queue


def on_notification_received(payload: Dict[str, Any]):
    """
    Callback function for PostgresListener.
    
    This is called by the PostgresListener when a notification is received
    and distributes it to the appropriate queues.
    
    Args:
        payload: Notification payload from PostgreSQL
    """
    try:
        queue = get_notification_queue()
        queue.put(payload)
        
        logger.debug(f"on_notification_received: Distributed notification: {payload}")
        
    except Exception as e:
        logger.error(f"on_notification_received: Error distributing notification: {e}")
