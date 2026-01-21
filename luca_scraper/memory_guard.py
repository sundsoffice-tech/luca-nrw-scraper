"""
Memory leak prevention and monitoring.

Provides memory usage monitoring, automatic garbage collection,
and decorators for tracking memory usage of functions.
"""

import gc
import functools
import psutil
import os
from typing import Callable, Optional, Dict, Any
from datetime import datetime


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    import json
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    print(f"[{ts}] [{level.upper():7}] {msg}{ctx_str}", flush=True)


class MemoryGuard:
    """
    Monitor and manage memory usage to prevent leaks.
    
    Features:
    - Memory usage monitoring
    - Automatic garbage collection on threshold
    - Memory statistics for debugging
    - Decorator for tracking function memory usage
    """
    
    # Default thresholds
    DEFAULT_MEMORY_THRESHOLD_PERCENT = 85.0  # Trigger GC at 85% memory usage
    DEFAULT_CRITICAL_THRESHOLD_PERCENT = 95.0  # Critical memory usage
    
    def __init__(
        self,
        memory_threshold_percent: float = DEFAULT_MEMORY_THRESHOLD_PERCENT,
        critical_threshold_percent: float = DEFAULT_CRITICAL_THRESHOLD_PERCENT
    ):
        """
        Initialize memory guard.
        
        Args:
            memory_threshold_percent: Trigger GC at this memory usage percentage
            critical_threshold_percent: Critical memory usage threshold
        """
        self.memory_threshold_percent = memory_threshold_percent
        self.critical_threshold_percent = critical_threshold_percent
        self._process = psutil.Process(os.getpid())
        log(
            "info",
            "MemoryGuard initialized",
            threshold=f"{memory_threshold_percent}%",
            critical=f"{critical_threshold_percent}%"
        )
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory statistics:
            - rss_mb: Resident Set Size in MB
            - vms_mb: Virtual Memory Size in MB
            - percent: Memory usage percentage
            - available_mb: Available system memory in MB
            - total_mb: Total system memory in MB
            
        Example:
            >>> guard = MemoryGuard()
            >>> stats = guard.get_memory_usage()
            >>> print(f"Using {stats['rss_mb']} MB ({stats['percent']}%)")
        """
        try:
            # Process memory
            mem_info = self._process.memory_info()
            rss_mb = mem_info.rss / 1024 / 1024
            vms_mb = mem_info.vms / 1024 / 1024
            
            # System memory
            system_mem = psutil.virtual_memory()
            
            return {
                'rss_mb': round(rss_mb, 2),
                'vms_mb': round(vms_mb, 2),
                'percent': round(system_mem.percent, 2),
                'available_mb': round(system_mem.available / 1024 / 1024, 2),
                'total_mb': round(system_mem.total / 1024 / 1024, 2)
            }
        except Exception as e:
            log("error", "Failed to get memory usage", error=str(e))
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0,
                'total_mb': 0
            }
    
    def check_and_collect(self) -> bool:
        """
        Check memory usage and trigger garbage collection if needed.
        
        Returns:
            True if garbage collection was triggered
            
        Example:
            >>> guard = MemoryGuard()
            >>> if guard.check_and_collect():
            ...     print("Garbage collection triggered")
        """
        stats = self.get_memory_usage()
        memory_percent = stats['percent']
        
        if memory_percent >= self.critical_threshold_percent:
            log(
                "error",
                "CRITICAL memory usage detected!",
                percent=memory_percent,
                rss_mb=stats['rss_mb'],
                threshold=self.critical_threshold_percent
            )
            self._force_gc()
            return True
        
        elif memory_percent >= self.memory_threshold_percent:
            log(
                "warn",
                "High memory usage detected, triggering GC",
                percent=memory_percent,
                rss_mb=stats['rss_mb'],
                threshold=self.memory_threshold_percent
            )
            self._force_gc()
            return True
        
        return False
    
    def _force_gc(self):
        """Force garbage collection and log results."""
        before_stats = self.get_memory_usage()
        
        # Run garbage collection
        collected = gc.collect()
        
        after_stats = self.get_memory_usage()
        freed_mb = before_stats['rss_mb'] - after_stats['rss_mb']
        
        log(
            "info",
            "Garbage collection completed",
            objects_collected=collected,
            freed_mb=round(freed_mb, 2),
            before_mb=before_stats['rss_mb'],
            after_mb=after_stats['rss_mb'],
            percent=after_stats['percent']
        )
    
    def log_memory_stats(self):
        """Log current memory statistics."""
        stats = self.get_memory_usage()
        log(
            "info",
            "Memory statistics",
            rss_mb=stats['rss_mb'],
            vms_mb=stats['vms_mb'],
            percent=stats['percent'],
            available_mb=stats['available_mb'],
            total_mb=stats['total_mb']
        )
    
    def is_memory_critical(self) -> bool:
        """
        Check if memory usage is critical.
        
        Returns:
            True if memory usage exceeds critical threshold
        """
        stats = self.get_memory_usage()
        return stats['percent'] >= self.critical_threshold_percent


# Global memory guard instance
_memory_guard: Optional[MemoryGuard] = None


def get_memory_guard() -> MemoryGuard:
    """
    Get the global memory guard instance.
    
    Returns:
        MemoryGuard instance
        
    Example:
        >>> guard = get_memory_guard()
        >>> guard.check_and_collect()
    """
    global _memory_guard
    if _memory_guard is None:
        _memory_guard = MemoryGuard()
    return _memory_guard


def memory_checked(func: Callable) -> Callable:
    """
    Decorator to check memory before and after function execution.
    
    Logs memory usage before and after the function call,
    and triggers garbage collection if needed.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
        
    Example:
        >>> @memory_checked
        ... def process_large_data():
        ...     # Process data
        ...     pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        guard = get_memory_guard()
        
        # Log memory before
        before_stats = guard.get_memory_usage()
        log(
            "debug",
            f"Memory before {func.__name__}",
            rss_mb=before_stats['rss_mb'],
            percent=before_stats['percent']
        )
        
        # Execute function
        try:
            result = func(*args, **kwargs)
        finally:
            # Log memory after
            after_stats = guard.get_memory_usage()
            delta_mb = after_stats['rss_mb'] - before_stats['rss_mb']
            
            log(
                "debug",
                f"Memory after {func.__name__}",
                rss_mb=after_stats['rss_mb'],
                percent=after_stats['percent'],
                delta_mb=round(delta_mb, 2)
            )
            
            # Check if GC is needed
            guard.check_and_collect()
        
        return result
    
    return wrapper


def memory_checked_async(func: Callable) -> Callable:
    """
    Decorator to check memory before and after async function execution.
    
    Args:
        func: Async function to decorate
        
    Returns:
        Decorated async function
        
    Example:
        >>> @memory_checked_async
        ... async def fetch_data():
        ...     # Fetch data
        ...     pass
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        guard = get_memory_guard()
        
        # Log memory before
        before_stats = guard.get_memory_usage()
        log(
            "debug",
            f"Memory before {func.__name__}",
            rss_mb=before_stats['rss_mb'],
            percent=before_stats['percent']
        )
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
        finally:
            # Log memory after
            after_stats = guard.get_memory_usage()
            delta_mb = after_stats['rss_mb'] - before_stats['rss_mb']
            
            log(
                "debug",
                f"Memory after {func.__name__}",
                rss_mb=after_stats['rss_mb'],
                percent=after_stats['percent'],
                delta_mb=round(delta_mb, 2)
            )
            
            # Check if GC is needed
            guard.check_and_collect()
        
        return result
    
    return wrapper
