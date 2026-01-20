"""
CircuitBreaker - Handles circuit breaker pattern for error resilience.
Responsible for managing circuit breaker state transitions (CLOSED, OPEN, HALF_OPEN).
"""

import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from django.utils import timezone
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states for error handling."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Too many errors, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Implements circuit breaker pattern for reliable error handling.
    Manages state transitions between CLOSED, OPEN, and HALF_OPEN states.
    """

    def __init__(self):
        self.state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self.opened_at: Optional[datetime] = None
        self.failures: int = 0

        # Configuration (will be loaded)
        self.failure_threshold: int = 5
        self.penalty_seconds: int = 30

    def load_config(self, config):
        """
        Load configuration from ScraperConfig.

        Args:
            config: ScraperConfig instance
        """
        self.failure_threshold = config.process_circuit_breaker_failures
        self.penalty_seconds = config.circuit_breaker_penalty

        logger.info(f"CircuitBreaker config loaded: threshold={self.failure_threshold}, "
                   f"penalty={self.penalty_seconds}s")

    def record_failure(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        Record a failure and potentially open the circuit breaker.

        Args:
            log_callback: Optional callback to log messages
        """
        self.failures += 1

        logger.info(f"Circuit breaker failure recorded: {self.failures}/{self.failure_threshold}")

        # Check if circuit breaker should open
        if self.state == CircuitBreakerState.CLOSED and self.failures >= self.failure_threshold:
            self.open(log_callback)

    def record_success(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        Record a success and potentially close the circuit breaker.

        Args:
            log_callback: Optional callback to log messages
        """
        # If circuit breaker is half-open, close it on success
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.close(log_callback)

    def open(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        Open the circuit breaker to prevent further operations.

        Args:
            log_callback: Optional callback to log messages
        """
        self.state = CircuitBreakerState.OPEN
        self.opened_at = timezone.now()

        logger.error(f"Circuit breaker OPENED after {self.failures} failures")
        if log_callback:
            log_callback(f"🔴 Circuit breaker OPENED - too many errors detected. "
                        f"Pausing operations for safety.")

    def close(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        Close the circuit breaker after successful operation.

        Args:
            log_callback: Optional callback to log messages
        """
        self.state = CircuitBreakerState.CLOSED
        self.failures = 0
        self.opened_at = None
        logger.info("Circuit breaker CLOSED - normal operation resumed")
        if log_callback:
            log_callback("✅ Circuit breaker CLOSED - operations resumed successfully")

    def check_and_update(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Check if circuit breaker allows operation and update state if needed.

        Args:
            log_callback: Optional callback to log messages

        Returns:
            True if operation is allowed, False if blocked
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Allow one test operation
            return True

        # State is OPEN - check if enough time has passed to try again
        if self.opened_at:
            elapsed = (timezone.now() - self.opened_at).total_seconds()
            if elapsed >= self.penalty_seconds:
                # Transition to half-open state
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker transitioning to HALF_OPEN after {elapsed:.1f}s penalty")
                if log_callback:
                    log_callback(f"⚠️ Circuit breaker HALF_OPEN - attempting test operation")
                return True

        logger.warning("Circuit breaker is OPEN - operation blocked")
        return False

    def auto_transition_if_ready(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        Auto-transition from OPEN to HALF_OPEN if penalty time has expired.

        Args:
            log_callback: Optional callback to log messages
        """
        if self.state == CircuitBreakerState.OPEN and self.opened_at:
            elapsed = (timezone.now() - self.opened_at).total_seconds()
            remaining = max(0, self.penalty_seconds - elapsed)

            # Auto-transition to HALF_OPEN when penalty time has expired
            if remaining == 0:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker auto-transitioning to HALF_OPEN (penalty expired)")
                if log_callback:
                    log_callback("⚠️ Circuit breaker HALF_OPEN - ready for test operation")

    def reset(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        Manually reset circuit breaker.

        Args:
            log_callback: Optional callback to log messages
        """
        logger.info("Manually resetting circuit breaker")

        if self.state != CircuitBreakerState.CLOSED and log_callback:
            log_callback("🔧 Manual reset: Circuit breaker closed")

        self.state = CircuitBreakerState.CLOSED
        self.opened_at = None
        self.failures = 0

        logger.info("Circuit breaker reset complete")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status.

        Returns:
            Dictionary with circuit breaker state information
        """
        status = {
            'circuit_breaker_state': self.state.value,
            'circuit_breaker_failures': self.failures,
        }

        # Add penalty info if open
        if self.state != CircuitBreakerState.CLOSED and self.opened_at:
            elapsed = (timezone.now() - self.opened_at).total_seconds()
            remaining = max(0, self.penalty_seconds - elapsed)

            status['circuit_breaker_penalty_seconds'] = self.penalty_seconds
            status['circuit_breaker_elapsed_seconds'] = elapsed
            status['circuit_breaker_remaining_seconds'] = remaining

        return status

    def get_remaining_penalty(self) -> float:
        """
        Get remaining penalty time in seconds.

        Returns:
            Remaining penalty time in seconds, or 0 if not applicable
        """
        if self.state != CircuitBreakerState.CLOSED and self.opened_at:
            elapsed = (timezone.now() - self.opened_at).total_seconds()
            return max(0, self.penalty_seconds - elapsed)
        return 0
