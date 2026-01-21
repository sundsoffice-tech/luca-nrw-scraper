"""
Graceful shutdown handler for SIGTERM and SIGINT signals.

Provides controlled shutdown with task tracking, cleanup callbacks,
and configurable timeout.
"""

import asyncio
import signal
import threading
from typing import Optional, Callable, Set, Any, List
from datetime import datetime


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    import json
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    print(f"[{ts}] [{level.upper():7}] {msg}{ctx_str}", flush=True)


class GracefulShutdown:
    """
    Singleton class for graceful shutdown handling.
    
    Features:
    - Signal handlers for SIGTERM and SIGINT
    - Task tracking for active requests
    - Cleanup callbacks for database connections
    - Configurable shutdown timeout
    - Thread-safe singleton pattern
    
    Example:
        >>> shutdown = GracefulShutdown()
        >>> shutdown.register_cleanup(cleanup_database)
        >>> shutdown.track_task("fetch_data")
        >>> # ... do work ...
        >>> shutdown.untrack_task("fetch_data")
    """
    
    _instance: Optional['GracefulShutdown'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, shutdown_timeout: float = 30.0):
        """
        Initialize graceful shutdown handler.
        
        Args:
            shutdown_timeout: Maximum time to wait for graceful shutdown (seconds)
        """
        # Prevent re-initialization of singleton
        if self._initialized:
            return
        
        self._shutdown_timeout = shutdown_timeout
        self._shutdown_requested = False
        self._active_tasks: Set[str] = set()
        self._cleanup_callbacks: List[Callable] = []
        self._tasks_lock = threading.Lock()
        self._callbacks_lock = threading.Lock()
        
        # Register signal handlers
        self._register_signal_handlers()
        
        self._initialized = True
        log("info", "GracefulShutdown initialized", timeout=shutdown_timeout)
    
    def _register_signal_handlers(self):
        """Register handlers for SIGTERM and SIGINT."""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            log("info", "Signal handlers registered for SIGTERM and SIGINT")
        except Exception as e:
            log("warn", "Failed to register signal handlers", error=str(e))
    
    def _signal_handler(self, signum: int, frame: Any):
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        log("info", f"Received {signal_name}, initiating graceful shutdown")
        self.shutdown()
    
    def track_task(self, task_id: str):
        """
        Track an active task/request.
        
        Args:
            task_id: Unique identifier for the task
            
        Example:
            >>> shutdown.track_task("fetch_url_123")
        """
        with self._tasks_lock:
            self._active_tasks.add(task_id)
            log("debug", "Task tracked", task_id=task_id, active_tasks=len(self._active_tasks))
    
    def untrack_task(self, task_id: str):
        """
        Remove a task from tracking.
        
        Args:
            task_id: Unique identifier for the task
            
        Example:
            >>> shutdown.untrack_task("fetch_url_123")
        """
        with self._tasks_lock:
            self._active_tasks.discard(task_id)
            log("debug", "Task untracked", task_id=task_id, active_tasks=len(self._active_tasks))
    
    def register_cleanup(self, callback: Callable):
        """
        Register a cleanup callback to be called during shutdown.
        
        Args:
            callback: Function to call during shutdown
            
        Example:
            >>> def cleanup_db():
            ...     db.close()
            >>> shutdown.register_cleanup(cleanup_db)
        """
        with self._callbacks_lock:
            self._cleanup_callbacks.append(callback)
            log("debug", "Cleanup callback registered", total_callbacks=len(self._cleanup_callbacks))
    
    def is_shutdown_requested(self) -> bool:
        """
        Check if shutdown has been requested.
        
        Returns:
            True if shutdown requested
        """
        return self._shutdown_requested
    
    def get_active_tasks_count(self) -> int:
        """
        Get the number of active tasks.
        
        Returns:
            Number of active tasks
        """
        with self._tasks_lock:
            return len(self._active_tasks)
    
    def shutdown(self):
        """
        Initiate graceful shutdown sequence.
        
        Steps:
        1. Set shutdown flag
        2. Wait for active tasks to complete (with timeout)
        3. Execute cleanup callbacks
        """
        if self._shutdown_requested:
            log("warn", "Shutdown already in progress")
            return
        
        self._shutdown_requested = True
        log("info", "Graceful shutdown initiated")
        
        # Wait for active tasks to complete
        self._wait_for_tasks()
        
        # Execute cleanup callbacks
        self._execute_cleanups()
        
        log("info", "Graceful shutdown completed")
    
    def _wait_for_tasks(self):
        """Wait for active tasks to complete with timeout."""
        start_time = datetime.now()
        
        while True:
            with self._tasks_lock:
                active_count = len(self._active_tasks)
            
            if active_count == 0:
                log("info", "All tasks completed")
                break
            
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= self._shutdown_timeout:
                log(
                    "warn",
                    "Shutdown timeout reached, forcing shutdown",
                    active_tasks=active_count,
                    timeout=self._shutdown_timeout
                )
                break
            
            log(
                "info",
                "Waiting for tasks to complete",
                active_tasks=active_count,
                elapsed=f"{elapsed:.1f}s",
                timeout=self._shutdown_timeout
            )
            
            # Sleep briefly before checking again
            import time
            time.sleep(1.0)
    
    def _execute_cleanups(self):
        """Execute all registered cleanup callbacks."""
        with self._callbacks_lock:
            callback_count = len(self._cleanup_callbacks)
        
        if callback_count == 0:
            log("info", "No cleanup callbacks to execute")
            return
        
        log("info", f"Executing {callback_count} cleanup callback(s)")
        
        with self._callbacks_lock:
            for i, callback in enumerate(self._cleanup_callbacks):
                try:
                    log("debug", f"Executing cleanup callback {i + 1}/{callback_count}")
                    callback()
                except Exception as e:
                    log(
                        "error",
                        f"Cleanup callback {i + 1} failed",
                        error=str(e),
                        callback=callback.__name__ if hasattr(callback, '__name__') else str(callback)
                    )


# Global instance
_shutdown_instance: Optional[GracefulShutdown] = None


def get_shutdown_handler(shutdown_timeout: float = 30.0) -> GracefulShutdown:
    """
    Get the global graceful shutdown handler instance.
    
    Args:
        shutdown_timeout: Maximum time to wait for graceful shutdown (seconds)
        
    Returns:
        GracefulShutdown instance
        
    Example:
        >>> shutdown = get_shutdown_handler()
        >>> shutdown.track_task("my_task")
    """
    global _shutdown_instance
    if _shutdown_instance is None:
        _shutdown_instance = GracefulShutdown(shutdown_timeout=shutdown_timeout)
    return _shutdown_instance
