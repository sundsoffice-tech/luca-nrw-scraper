"""
RetryController - Handles error tracking and retry logic.
Responsible for tracking errors, calculating backoff, and scheduling retries.
"""

import threading
import logging
from typing import Optional, Dict, Any, Callable
from collections import deque
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class RetryController:
    """
    Manages error tracking, retry logic, and backoff calculations.
    Tracks error rates, determines retry eligibility, and schedules retries.
    """

    def __init__(self):
        # Error tracking for retry logic
        self.error_counts: Dict[str, int] = {
            'missing_module': 0,
            'rate_limit': 0,
            'config_error': 0,
            'crash': 0,
            'connection_error': 0,
            'timeout': 0,
            'parsing_error': 0,
            'other': 0
        }
        self.error_timestamps: deque = deque(maxlen=100)  # Track last 100 errors for rate calculation
        self.consecutive_failures: int = 0
        self.retry_count: int = 0
        self.last_failure_time: Optional[datetime] = None

        # Configuration (will be loaded)
        self.max_retry_attempts: int = 3
        self.qpi_reduction_factor: float = 0.7
        self.error_rate_threshold: float = 0.5
        self.retry_backoff_base: float = 30.0
        self.error_rate_window_seconds: int = 300  # 5 minutes

    def load_config(self, config):
        """
        Load configuration from ScraperConfig.

        Args:
            config: ScraperConfig instance
        """
        self.max_retry_attempts = config.process_max_retry_attempts
        self.qpi_reduction_factor = config.process_qpi_reduction_factor
        self.error_rate_threshold = config.process_error_rate_threshold
        self.retry_backoff_base = config.process_retry_backoff_base
        self.error_rate_window_seconds = 300  # 5 minutes window for error rate calculation

        logger.info(f"RetryController config loaded: max_retry={self.max_retry_attempts}, "
                   f"qpi_factor={self.qpi_reduction_factor}, "
                   f"error_threshold={self.error_rate_threshold}, "
                   f"backoff={self.retry_backoff_base}")

    def track_error(self, error_type: str) -> float:
        """
        Track an error for retry logic.

        Args:
            error_type: Type of error ('missing_module', 'rate_limit', 'config_error', 'crash', etc.)

        Returns:
            Current error rate
        """
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.error_timestamps.append(timezone.now())

        logger.info(f"Error tracked: {error_type}, total: {self.error_counts[error_type]}")

        # Calculate and return error rate
        return self.calculate_error_rate()

    def calculate_error_rate(self) -> float:
        """
        Calculate error rate over the configured time window.

        Returns:
            Error rate as a float between 0 and 1
        """
        if not self.error_timestamps:
            return 0.0

        now = timezone.now()
        window_start = now - timedelta(seconds=self.error_rate_window_seconds)

        # Count errors in the time window
        recent_errors = sum(1 for ts in self.error_timestamps if ts >= window_start)

        # Calculate rate (errors per second)
        if recent_errors == 0:
            return 0.0

        # Estimate total operations (assuming at least 1 operation per second)
        total_operations = max(self.error_rate_window_seconds, 1)
        return min(recent_errors / total_operations, 1.0)

    def should_retry(self, circuit_breaker_allows: bool) -> bool:
        """
        Determine if a retry should be attempted.

        Args:
            circuit_breaker_allows: Whether circuit breaker allows the operation

        Returns:
            True if retry should be attempted, False otherwise
        """
        # Don't retry if max attempts reached
        if self.retry_count >= self.max_retry_attempts:
            logger.info(f"Max retry attempts ({self.max_retry_attempts}) reached")
            return False

        # Don't retry if circuit breaker is blocking
        if not circuit_breaker_allows:
            logger.info("Circuit breaker is blocking retry")
            return False

        return True

    def calculate_retry_backoff(self) -> float:
        """
        Calculate exponential backoff for retry with maximum cap.

        Returns:
            Backoff time in seconds (capped at 300s = 5 minutes)
        """
        backoff = self.retry_backoff_base * (2 ** self.retry_count)
        return min(backoff, 300.0)  # Max 5 minutes

    def adjust_qpi_for_rate_limit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust QPI downward if rate limit errors detected.

        Args:
            params: Original scraper parameters

        Returns:
            Updated parameters with adjusted QPI
        """
        if self.error_counts.get('rate_limit', 0) > 0:
            original_qpi = params.get('qpi', 15)
            new_qpi = max(1, int(original_qpi * self.qpi_reduction_factor))

            if new_qpi != original_qpi:
                logger.info(f"Reducing QPI from {original_qpi} to {new_qpi} due to rate limit errors")
                params = params.copy()
                params['qpi'] = new_qpi

        return params

    def schedule_retry(
        self,
        params: Dict[str, Any],
        start_callback: Callable[[Dict[str, Any], Any], None],
        log_callback: Callable[[str], None],
        circuit_breaker_allows: bool,
        user=None
    ):
        """
        Schedule an automatic retry with adjusted parameters.

        Args:
            params: Scraper parameters
            start_callback: Callback to start the scraper
            log_callback: Callback to log messages
            circuit_breaker_allows: Whether circuit breaker allows retry
            user: User who started the scraper
        """
        if not self.should_retry(circuit_breaker_allows):
            logger.info("Retry not scheduled - conditions not met")
            return

        self.retry_count += 1
        backoff_time = self.calculate_retry_backoff()

        logger.info(f"Scheduling retry {self.retry_count}/{self.max_retry_attempts} "
                   f"after {backoff_time:.1f}s backoff")
        log_callback(f"🔄 Scheduling automatic retry {self.retry_count}/{self.max_retry_attempts} "
                    f"in {backoff_time:.1f}s")

        # Adjust parameters if needed
        adjusted_params = self.adjust_qpi_for_rate_limit(params)

        # Schedule retry in a separate thread
        def retry_after_backoff():
            import time
            time.sleep(backoff_time)

            logger.info(f"Executing scheduled retry {self.retry_count}")
            log_callback(f"🔄 Executing automatic retry {self.retry_count}")
            start_callback(adjusted_params, user)

        retry_thread = threading.Thread(target=retry_after_backoff, daemon=True)
        retry_thread.start()

    def record_failure(self):
        """Record a failure occurrence."""
        self.consecutive_failures += 1
        self.last_failure_time = timezone.now()

    def record_success(self):
        """Record a successful operation (resets counters)."""
        self.consecutive_failures = 0
        self.retry_count = 0

    def reset(self):
        """Manually reset error tracking."""
        logger.info("Manually resetting error tracking")

        self.error_counts = {
            'missing_module': 0,
            'rate_limit': 0,
            'config_error': 0,
            'crash': 0,
            'connection_error': 0,
            'timeout': 0,
            'parsing_error': 0,
            'other': 0
        }
        self.error_timestamps.clear()
        self.consecutive_failures = 0
        self.retry_count = 0
        self.last_failure_time = None

        logger.info("Error tracking reset complete")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current retry controller status.

        Returns:
            Dictionary with error tracking and retry information
        """
        return {
            'error_counts': self.error_counts.copy(),
            'consecutive_failures': self.consecutive_failures,
            'retry_count': self.retry_count,
            'max_retry_attempts': self.max_retry_attempts,
            'error_rate': self.calculate_error_rate(),
        }
