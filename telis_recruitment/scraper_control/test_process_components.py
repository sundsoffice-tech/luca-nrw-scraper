"""
Unit tests for the new ProcessManager components.
Tests the individual focused classes: ProcessLauncher, OutputMonitor, RetryController, CircuitBreaker.
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from telis_recruitment.scraper_control.process_launcher import ProcessLauncher
from telis_recruitment.scraper_control.output_monitor import OutputMonitor
from telis_recruitment.scraper_control.retry_controller import RetryController
from telis_recruitment.scraper_control.circuit_breaker import CircuitBreaker, CircuitBreakerState


class ProcessLauncherTest(TestCase):
    """Test ProcessLauncher component."""
    
    def setUp(self):
        self.launcher = ProcessLauncher()
    
    def test_build_command_basic(self):
        """Test building a basic command."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
        }
        cmd = self.launcher.build_command(params, 'script', 'test.py')
        
        self.assertIn('python', cmd)
        self.assertIn('test.py', cmd)
        self.assertIn('--industry', cmd)
        self.assertIn('recruiter', cmd)
        self.assertIn('--qpi', cmd)
        self.assertIn('15', cmd)
    
    def test_build_command_with_mode(self):
        """Test building command with mode."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
            'mode': 'learning',
        }
        cmd = self.launcher.build_command(params, 'script', 'test.py')
        
        self.assertIn('--mode', cmd)
        self.assertIn('learning', cmd)
    
    def test_build_command_with_flags(self):
        """Test building command with boolean flags."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
            'smart': True,
            'force': True,
            'once': True,
        }
        cmd = self.launcher.build_command(params, 'script', 'test.py')
        
        self.assertIn('--smart', cmd)
        self.assertIn('--force', cmd)
        self.assertIn('--once', cmd)
    
    def test_apply_env_overrides(self):
        """Test applying environment overrides."""
        env = {'PATH': '/usr/bin'}
        overrides = {'API_KEY': 'test123', 'DEBUG': '1'}
        
        self.launcher.apply_env_overrides(env, overrides)
        
        self.assertEqual(env['API_KEY'], 'test123')
        self.assertEqual(env['DEBUG'], '1')
        self.assertEqual(env['PATH'], '/usr/bin')  # Preserved


class OutputMonitorTest(TestCase):
    """Test OutputMonitor component."""
    
    def setUp(self):
        self.monitor = OutputMonitor(max_logs=100)
    
    def test_detect_log_level(self):
        """Test log level detection."""
        self.assertEqual(self.monitor._detect_log_level('Error occurred'), 'ERROR')
        self.assertEqual(self.monitor._detect_log_level('Warning: something'), 'WARN')
        self.assertEqual(self.monitor._detect_log_level('Info message'), 'INFO')
    
    def test_detect_error_type(self):
        """Test error type detection."""
        self.assertEqual(self.monitor._detect_error_type('ModuleNotFoundError: no module'), 'missing_module')
        self.assertEqual(self.monitor._detect_error_type('KeyError: missing key'), 'config_error')
        self.assertEqual(self.monitor._detect_error_type('rate limit exceeded'), 'rate_limit')
        self.assertEqual(self.monitor._detect_error_type('ConnectionError'), 'connection_error')
        self.assertEqual(self.monitor._detect_error_type('TimeoutError'), 'timeout')
        self.assertIsNone(self.monitor._detect_error_type('Normal message'))
    
    def test_get_logs(self):
        """Test getting logs."""
        # Add some logs
        self.monitor.logs = [
            {'timestamp': '2024-01-01T10:00:00', 'message': 'Log 1'},
            {'timestamp': '2024-01-01T10:00:01', 'message': 'Log 2'},
            {'timestamp': '2024-01-01T10:00:02', 'message': 'Log 3'},
        ]
        
        logs = self.monitor.get_logs(2)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]['message'], 'Log 2')
        self.assertEqual(logs[1]['message'], 'Log 3')
    
    def test_clear_logs(self):
        """Test clearing logs."""
        self.monitor.logs = [
            {'timestamp': '2024-01-01T10:00:00', 'message': 'Log 1'},
        ]
        
        self.monitor.clear_logs()
        self.assertEqual(len(self.monitor.logs), 0)


class RetryControllerTest(TestCase):
    """Test RetryController component."""
    
    def setUp(self):
        self.controller = RetryController()
        self.controller.max_retry_attempts = 3
        self.controller.retry_backoff_base = 10.0
    
    def test_track_error(self):
        """Test error tracking."""
        error_rate = self.controller.track_error('rate_limit')
        
        self.assertEqual(self.controller.error_counts['rate_limit'], 1)
        self.assertEqual(len(self.controller.error_timestamps), 1)
        self.assertGreaterEqual(error_rate, 0)
    
    def test_should_retry_allowed(self):
        """Test retry is allowed when conditions met."""
        self.controller.retry_count = 0
        
        self.assertTrue(self.controller.should_retry(circuit_breaker_allows=True))
    
    def test_should_retry_max_reached(self):
        """Test retry blocked when max reached."""
        self.controller.retry_count = 3
        
        self.assertFalse(self.controller.should_retry(circuit_breaker_allows=True))
    
    def test_should_retry_circuit_breaker_blocks(self):
        """Test retry blocked by circuit breaker."""
        self.controller.retry_count = 0
        
        self.assertFalse(self.controller.should_retry(circuit_breaker_allows=False))
    
    def test_calculate_retry_backoff(self):
        """Test exponential backoff calculation."""
        self.controller.retry_count = 0
        backoff1 = self.controller.calculate_retry_backoff()
        
        self.controller.retry_count = 1
        backoff2 = self.controller.calculate_retry_backoff()
        
        self.controller.retry_count = 2
        backoff3 = self.controller.calculate_retry_backoff()
        
        self.assertEqual(backoff1, 10.0)
        self.assertEqual(backoff2, 20.0)
        self.assertEqual(backoff3, 40.0)
    
    def test_calculate_retry_backoff_max_cap(self):
        """Test backoff capped at 300 seconds."""
        self.controller.retry_count = 10
        backoff = self.controller.calculate_retry_backoff()
        
        self.assertEqual(backoff, 300.0)
    
    def test_adjust_qpi_for_rate_limit(self):
        """Test QPI adjustment for rate limits."""
        self.controller.qpi_reduction_factor = 0.7
        self.controller.track_error('rate_limit')
        
        params = {'qpi': 20, 'industry': 'recruiter'}
        adjusted = self.controller.adjust_qpi_for_rate_limit(params)
        
        self.assertEqual(adjusted['qpi'], 14)  # 20 * 0.7 = 14
    
    def test_record_failure(self):
        """Test recording a failure."""
        self.controller.record_failure()
        
        self.assertEqual(self.controller.consecutive_failures, 1)
        self.assertIsNotNone(self.controller.last_failure_time)
    
    def test_record_success(self):
        """Test recording a success."""
        self.controller.consecutive_failures = 3
        self.controller.retry_count = 2
        
        self.controller.record_success()
        
        self.assertEqual(self.controller.consecutive_failures, 0)
        self.assertEqual(self.controller.retry_count, 0)
    
    def test_reset(self):
        """Test resetting the controller."""
        self.controller.track_error('crash')
        self.controller.track_error('timeout')
        self.controller.retry_count = 2
        
        self.controller.reset()
        
        self.assertEqual(sum(self.controller.error_counts.values()), 0)
        self.assertEqual(len(self.controller.error_timestamps), 0)
        self.assertEqual(self.controller.retry_count, 0)


class CircuitBreakerTest(TestCase):
    """Test CircuitBreaker component."""
    
    def setUp(self):
        self.breaker = CircuitBreaker()
        self.breaker.failure_threshold = 5
        self.breaker.penalty_seconds = 30
    
    def test_initial_state(self):
        """Test initial circuit breaker state."""
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.failures, 0)
        self.assertIsNone(self.breaker.opened_at)
    
    def test_record_failure(self):
        """Test recording failures."""
        self.breaker.record_failure()
        
        self.assertEqual(self.breaker.failures, 1)
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
    
    def test_open_after_threshold(self):
        """Test circuit breaker opens after threshold."""
        for i in range(5):
            self.breaker.record_failure()
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        self.assertIsNotNone(self.breaker.opened_at)
    
    def test_check_blocks_when_open(self):
        """Test circuit breaker blocks operations when open."""
        self.breaker.open()
        
        self.assertFalse(self.breaker.check_and_update())
    
    def test_transition_to_half_open(self):
        """Test transition to half-open after penalty."""
        self.breaker.open()
        # Set opened time to past
        self.breaker.opened_at = timezone.now() - timedelta(seconds=35)
        
        result = self.breaker.check_and_update()
        
        self.assertTrue(result)
        self.assertEqual(self.breaker.state, CircuitBreakerState.HALF_OPEN)
    
    def test_close_on_success(self):
        """Test circuit breaker closes on success."""
        self.breaker.state = CircuitBreakerState.HALF_OPEN
        self.breaker.failures = 3
        
        self.breaker.record_success()
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.failures, 0)
    
    def test_reset(self):
        """Test resetting circuit breaker."""
        self.breaker.open()
        self.breaker.failures = 5
        
        self.breaker.reset()
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.failures, 0)
        self.assertIsNone(self.breaker.opened_at)
    
    def test_get_remaining_penalty(self):
        """Test getting remaining penalty time."""
        self.breaker.open()
        self.breaker.opened_at = timezone.now() - timedelta(seconds=10)
        
        remaining = self.breaker.get_remaining_penalty()
        
        self.assertGreater(remaining, 0)
        self.assertLess(remaining, 30)
