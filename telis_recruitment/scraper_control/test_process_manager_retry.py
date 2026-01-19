"""
Tests for ProcessManager error tracking, retry logic, and circuit breaker.
"""

from unittest.mock import patch, MagicMock, call
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from telis_recruitment.scraper_control.models import ScraperConfig, ScraperRun, ScraperLog
from telis_recruitment.scraper_control.process_manager import ProcessManager, CircuitBreakerState


class ProcessManagerErrorTrackingTest(TestCase):
    """Test error tracking functionality."""
    
    def setUp(self):
        self.manager = ProcessManager()
        # Reset state
        self.manager.error_counts = {
            'missing_module': 0,
            'rate_limit': 0,
            'config_error': 0,
            'crash': 0,
            'other': 0
        }
        self.manager.error_timestamps.clear()
        self.manager.circuit_breaker_failures = 0
        self.manager.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.manager.consecutive_failures = 0
        self.manager.retry_count = 0
        
        # Create config
        self.config = ScraperConfig.get_config()
        self.config.process_max_retry_attempts = 3
        self.config.process_circuit_breaker_failures = 5
        self.config.save()
        
        self.manager._load_config()
    
    def test_track_error_increments_count(self):
        """Test that tracking an error increments the counter."""
        self.manager._track_error('rate_limit')
        
        self.assertEqual(self.manager.error_counts['rate_limit'], 1)
        self.assertEqual(len(self.manager.error_timestamps), 1)
        self.assertEqual(self.manager.circuit_breaker_failures, 1)
    
    def test_track_multiple_errors(self):
        """Test tracking multiple errors of different types."""
        self.manager._track_error('rate_limit')
        self.manager._track_error('rate_limit')
        self.manager._track_error('missing_module')
        
        self.assertEqual(self.manager.error_counts['rate_limit'], 2)
        self.assertEqual(self.manager.error_counts['missing_module'], 1)
        self.assertEqual(len(self.manager.error_timestamps), 3)
        self.assertEqual(self.manager.circuit_breaker_failures, 3)
    
    def test_error_rate_calculation(self):
        """Test error rate calculation over time window."""
        # Add some errors
        for i in range(10):
            self.manager._track_error('other')
        
        # Calculate error rate
        error_rate = self.manager._calculate_error_rate()
        
        # Should be > 0
        self.assertGreater(error_rate, 0)
        self.assertLessEqual(error_rate, 1.0)
    
    def test_circuit_breaker_opens_after_threshold(self):
        """Test that circuit breaker opens after reaching failure threshold."""
        # Track errors up to threshold
        for i in range(5):
            self.manager._track_error('crash')
        
        # Circuit breaker should be open
        self.assertEqual(self.manager.circuit_breaker_state, CircuitBreakerState.OPEN)
        self.assertIsNotNone(self.manager.circuit_breaker_opened_at)
    
    def test_circuit_breaker_blocks_operations(self):
        """Test that circuit breaker blocks operations when open."""
        # Open the circuit breaker
        self.manager._open_circuit_breaker()
        
        # Check should return False
        self.assertFalse(self.manager._check_circuit_breaker())
    
    def test_circuit_breaker_transitions_to_half_open(self):
        """Test that circuit breaker transitions to half-open after penalty."""
        # Open the circuit breaker
        self.manager._open_circuit_breaker()
        
        # Set opened time to past (beyond penalty)
        self.manager.circuit_breaker_opened_at = timezone.now() - timedelta(seconds=35)
        
        # Check should transition to half-open and return True
        self.assertTrue(self.manager._check_circuit_breaker())
        self.assertEqual(self.manager.circuit_breaker_state, CircuitBreakerState.HALF_OPEN)
    
    def test_circuit_breaker_closes_on_success(self):
        """Test that circuit breaker closes after successful operation."""
        self.manager.circuit_breaker_state = CircuitBreakerState.HALF_OPEN
        self.manager.circuit_breaker_failures = 3
        
        self.manager._close_circuit_breaker()
        
        self.assertEqual(self.manager.circuit_breaker_state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.manager.circuit_breaker_failures, 0)
        self.assertIsNone(self.manager.circuit_breaker_opened_at)


class ProcessManagerRetryLogicTest(TestCase):
    """Test automatic retry logic."""
    
    def setUp(self):
        self.manager = ProcessManager()
        # Reset state
        self.manager.retry_count = 0
        self.manager.consecutive_failures = 0
        self.manager.circuit_breaker_state = CircuitBreakerState.CLOSED
        
        # Create config
        self.config = ScraperConfig.get_config()
        self.config.process_max_retry_attempts = 3
        self.config.process_retry_backoff_base = 10.0
        self.config.save()
        
        self.manager._load_config()
    
    def test_should_retry_returns_true_when_allowed(self):
        """Test that retry is allowed when conditions are met."""
        self.assertTrue(self.manager._should_retry())
    
    def test_should_retry_returns_false_when_max_reached(self):
        """Test that retry is blocked when max attempts reached."""
        self.manager.retry_count = 3
        
        self.assertFalse(self.manager._should_retry())
    
    def test_should_retry_returns_false_when_circuit_open(self):
        """Test that retry is blocked when circuit breaker is open."""
        self.manager._open_circuit_breaker()
        
        self.assertFalse(self.manager._should_retry())
    
    def test_calculate_retry_backoff_exponential(self):
        """Test exponential backoff calculation."""
        self.manager.retry_count = 0
        backoff1 = self.manager._calculate_retry_backoff()
        
        self.manager.retry_count = 1
        backoff2 = self.manager._calculate_retry_backoff()
        
        self.manager.retry_count = 2
        backoff3 = self.manager._calculate_retry_backoff()
        
        # Should increase exponentially
        self.assertEqual(backoff1, 10.0)
        self.assertEqual(backoff2, 20.0)
        self.assertEqual(backoff3, 40.0)
    
    def test_adjust_qpi_for_rate_limit(self):
        """Test QPI adjustment when rate limit errors detected."""
        # Set QPI reduction factor
        self.config.process_qpi_reduction_factor = 0.7
        self.config.save()
        self.manager._load_config()
        
        # Track rate limit error
        self.manager._track_error('rate_limit')
        
        # Adjust parameters
        params = {'qpi': 20, 'industry': 'recruiter'}
        adjusted = self.manager._adjust_qpi_for_rate_limit(params)
        
        # QPI should be reduced to 70%
        self.assertEqual(adjusted['qpi'], 14)  # 20 * 0.7 = 14
    
    def test_adjust_qpi_minimum_is_one(self):
        """Test that QPI never goes below 1."""
        self.manager._track_error('rate_limit')
        
        params = {'qpi': 1, 'industry': 'recruiter'}
        adjusted = self.manager._adjust_qpi_for_rate_limit(params)
        
        # Should stay at 1
        self.assertEqual(adjusted['qpi'], 1)
    
    def test_no_qpi_adjustment_without_rate_limit_errors(self):
        """Test that QPI is not adjusted without rate limit errors."""
        params = {'qpi': 20, 'industry': 'recruiter'}
        adjusted = self.manager._adjust_qpi_for_rate_limit(params)
        
        # Should remain unchanged
        self.assertEqual(adjusted['qpi'], 20)


class ProcessManagerIntegrationTest(TestCase):
    """Integration tests for ProcessManager with error handling."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.manager = ProcessManager()
        # Reset state
        self.manager.retry_count = 0
        self.manager.consecutive_failures = 0
        self.manager.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.manager.circuit_breaker_opened_at = None
        self.manager.circuit_breaker_failures = 0
        
        # Create config
        self.config = ScraperConfig.get_config()
        self.config.process_max_retry_attempts = 3
        self.config.process_circuit_breaker_failures = 5
        self.config.circuit_breaker_penalty = 30
        self.config.save()
        
        self.manager._load_config()
    
    @patch('telis_recruitment.scraper_control.process_manager.ProcessManager.is_running')
    def test_start_blocked_by_circuit_breaker(self, mock_is_running):
        """Test that start is blocked when circuit breaker is open."""
        mock_is_running.return_value = False
        
        # Open circuit breaker
        self.manager._open_circuit_breaker()
        
        # Try to start
        result = self.manager.start({'industry': 'recruiter', 'qpi': 15}, user=self.user)
        
        self.assertFalse(result['success'])
        self.assertIn('Circuit breaker', result['error'])
        self.assertEqual(result['status'], 'circuit_breaker_open')
    
    def test_reset_error_tracking(self):
        """Test manual reset of error tracking."""
        # Add some errors
        for i in range(3):
            self.manager._track_error('crash')
        
        self.manager.retry_count = 2
        self.manager.consecutive_failures = 3
        
        # Reset
        self.manager.reset_error_tracking()
        
        # All counters should be reset
        self.assertEqual(sum(self.manager.error_counts.values()), 0)
        self.assertEqual(len(self.manager.error_timestamps), 0)
        self.assertEqual(self.manager.retry_count, 0)
        self.assertEqual(self.manager.consecutive_failures, 0)
        self.assertEqual(self.manager.circuit_breaker_state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.manager.circuit_breaker_failures, 0)
    
    def test_get_status_includes_error_info(self):
        """Test that get_status includes error tracking information."""
        # Add some errors
        self.manager._track_error('rate_limit')
        self.manager._track_error('crash')
        self.manager.retry_count = 1
        self.manager.consecutive_failures = 2
        
        status = self.manager.get_status()
        
        # Should include error tracking
        self.assertIn('error_counts', status)
        self.assertIn('retry_count', status)
        self.assertIn('consecutive_failures', status)
        self.assertIn('circuit_breaker_state', status)
        self.assertIn('error_rate', status)
        
        self.assertEqual(status['error_counts']['rate_limit'], 1)
        self.assertEqual(status['error_counts']['crash'], 1)
        self.assertEqual(status['retry_count'], 1)
        self.assertEqual(status['consecutive_failures'], 2)
    
    def test_stop_resets_retry_counters(self):
        """Test that manual stop resets retry counters."""
        self.manager.retry_count = 2
        self.manager.consecutive_failures = 3
        self.manager.status = 'stopped'  # Simulate not running
        
        # Stop (will fail since not running, but should still reset counters)
        self.manager.stop()
        
        # Counters should be reset
        self.assertEqual(self.manager.retry_count, 0)
        self.assertEqual(self.manager.consecutive_failures, 0)


class ProcessManagerConfigLoadTest(TestCase):
    """Test configuration loading from database."""
    
    def test_load_config_from_database(self):
        """Test loading configuration values from database."""
        # Create config with specific values
        config = ScraperConfig.get_config()
        config.process_max_retry_attempts = 5
        config.process_qpi_reduction_factor = 0.6
        config.process_error_rate_threshold = 0.4
        config.process_circuit_breaker_failures = 7
        config.process_retry_backoff_base = 60.0
        config.save()
        
        # Create new manager instance
        manager = ProcessManager()
        manager._load_config()
        
        # Values should match config
        self.assertEqual(manager.max_retry_attempts, 5)
        self.assertEqual(manager.qpi_reduction_factor, 0.6)
        self.assertEqual(manager.error_rate_threshold, 0.4)
        self.assertEqual(manager.circuit_breaker_failure_threshold, 7)
        self.assertEqual(manager.retry_backoff_base, 60.0)
