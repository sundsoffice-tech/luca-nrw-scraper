"""
Unit tests for enhanced error capture functionality.
Tests OutputMonitor.get_final_output(), ProcessLauncher.validate_script(),
and ProcessManager early exit error capture.
"""

import unittest
import tempfile
import os
from unittest.mock import MagicMock, patch, Mock
from django.test import TestCase
from django.utils import timezone

from telis_recruitment.scraper_control.output_monitor import OutputMonitor
from telis_recruitment.scraper_control.process_launcher import ProcessLauncher


class OutputMonitorErrorCaptureTest(TestCase):
    """Test OutputMonitor error capture functionality."""
    
    def setUp(self):
        self.monitor = OutputMonitor(max_logs=100)
    
    def test_get_final_output_empty(self):
        """Test get_final_output with no logs."""
        result = self.monitor.get_final_output()
        self.assertEqual(result, "")
    
    def test_get_final_output_single_log(self):
        """Test get_final_output with a single log entry."""
        # Manually add a log entry
        self.monitor._process_log_line("Error: ModuleNotFoundError: No module named 'test'")
        
        result = self.monitor.get_final_output()
        self.assertIn("ModuleNotFoundError", result)
        self.assertIn("No module named 'test'", result)
    
    def test_get_final_output_multiple_logs(self):
        """Test get_final_output with multiple log entries."""
        error_lines = [
            "Traceback (most recent call last):",
            "  File 'test.py', line 1, in <module>",
            "    import nonexistent_module",
            "ModuleNotFoundError: No module named 'nonexistent_module'"
        ]
        
        for line in error_lines:
            self.monitor._process_log_line(line)
        
        result = self.monitor.get_final_output()
        
        # All lines should be present
        for line in error_lines:
            self.assertIn(line, result)
    
    def test_get_final_output_respects_max_chars(self):
        """Test that get_final_output respects max_chars limit."""
        # Add many log entries
        for i in range(100):
            self.monitor._process_log_line(f"Log line number {i}" + " " * 50)
        
        result = self.monitor.get_final_output(max_chars=500)
        self.assertLessEqual(len(result), 500)
    
    def test_get_final_output_thread_safe(self):
        """Test that get_final_output is thread-safe."""
        import threading
        
        def add_logs():
            for i in range(50):
                self.monitor._process_log_line(f"Thread log {i}")
        
        # Start multiple threads adding logs
        threads = [threading.Thread(target=add_logs) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should be able to get output without errors
        result = self.monitor.get_final_output()
        self.assertIsInstance(result, str)


class ProcessLauncherValidationTest(TestCase):
    """Test ProcessLauncher validation functionality."""
    
    def setUp(self):
        self.launcher = ProcessLauncher()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_script_valid_syntax(self):
        """Test validation of a script with valid syntax."""
        # Create a valid Python script
        script_path = os.path.join(self.temp_dir, 'valid_script.py')
        with open(script_path, 'w') as f:
            f.write("print('Hello, World!')\n")
        
        is_valid, error = self.launcher.validate_script('script', script_path)
        
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_validate_script_syntax_error(self):
        """Test validation of a script with syntax error."""
        # Create a script with syntax error
        script_path = os.path.join(self.temp_dir, 'invalid_script.py')
        with open(script_path, 'w') as f:
            f.write("print('Missing closing quote)\n")
        
        is_valid, error = self.launcher.validate_script('script', script_path)
        
        self.assertFalse(is_valid)
        self.assertIn("SyntaxError", error)
    
    def test_validate_script_import_error(self):
        """Test validation of a script with import error."""
        # Create a script that imports a non-existent module
        script_path = os.path.join(self.temp_dir, 'import_error_script.py')
        with open(script_path, 'w') as f:
            f.write("import this_module_does_not_exist_xyz123\n")
            f.write("print('Hello')\n")
        
        is_valid, error = self.launcher.validate_script('script', script_path)
        
        # py_compile only checks syntax, not imports
        # So this should pass syntax check
        # For module imports, we'd need to test the module validation path
        self.assertTrue(is_valid)  # py_compile passes for import errors
    
    def test_validate_module_import_error(self):
        """Test validation of a module with import error."""
        # Test module validation path
        is_valid, error = self.launcher.validate_script('module', 'nonexistent_module_xyz123')
        
        self.assertFalse(is_valid)
        self.assertIn("ModuleNotFoundError", error)
    
    def test_validate_script_nonexistent_file(self):
        """Test validation of a nonexistent script file."""
        script_path = os.path.join(self.temp_dir, 'nonexistent.py')
        
        is_valid, error = self.launcher.validate_script('script', script_path)
        
        self.assertFalse(is_valid)
        # Error should indicate file not found
        self.assertTrue(len(error) > 0)
    
    def test_validate_script_with_multiline_error(self):
        """Test validation captures multiline error messages."""
        # Create a script with multiple syntax errors
        script_path = os.path.join(self.temp_dir, 'multi_error_script.py')
        with open(script_path, 'w') as f:
            f.write("def broken_function(\n")  # Missing closing paren
            f.write("    pass\n")
        
        is_valid, error = self.launcher.validate_script('script', script_path)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(error), 0)


class ProcessManagerErrorCaptureIntegrationTest(TestCase):
    """Integration tests for ProcessManager error capture."""
    
    def setUp(self):
        # Import here to avoid Django setup issues
        from telis_recruitment.scraper_control.process_manager import ProcessManager
        self.manager = ProcessManager()
        
        # Create test ScraperConfig
        from telis_recruitment.scraper_control.models import ScraperConfig
        try:
            ScraperConfig.objects.get_or_create(
                defaults={
                    'max_retry_attempts': 3,
                    'circuit_breaker_threshold': 5,
                    'circuit_breaker_timeout': 60,
                }
            )
        except Exception:
            pass  # May already exist or DB not ready
    
    @patch('telis_recruitment.scraper_control.process_launcher.ProcessLauncher.start_process')
    @patch('telis_recruitment.scraper_control.process_launcher.ProcessLauncher.find_scraper_script')
    def test_validation_failure_captured_in_error(self, mock_find, mock_start):
        """Test that validation failures are captured in error response."""
        # Setup mocks
        mock_find.return_value = ('script', '/tmp/test_script.py')
        
        # Mock validation to fail
        with patch.object(
            self.manager.launcher,
            'validate_script',
            return_value=(False, "SyntaxError: invalid syntax")
        ):
            # Try to start with validation failure
            params = {'industry': 'recruiter', 'qpi': 15}
            
            # Create a mock user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.create_user(username='testuser')
            except Exception:
                user = None
            
            result = self.manager.start(params, user=user)
            
            # Should fail with validation error
            self.assertFalse(result.get('success'))
            self.assertIn('Validation error', result.get('error_details', ''))
            self.assertIn('SyntaxError', result.get('error_details', ''))
    
    def test_early_exit_captures_final_output(self):
        """Test that early exit captures final output from OutputMonitor."""
        # Add some error logs to the output monitor
        error_lines = [
            "Starting scraper...",
            "Traceback (most recent call last):",
            "  File 'scriptname.py', line 10, in <module>",
            "ModuleNotFoundError: No module named 'requests'"
        ]
        
        for line in error_lines:
            self.manager.output_monitor._process_log_line(line)
        
        # Simulate early exit
        self.manager._handle_process_completion(exit_code=1, runtime=1.5)
        
        # Error context should contain the captured output
        self.assertIsNotNone(self.manager.last_error_details)
        self.assertIn("Error Output", self.manager.last_error_details)
        self.assertIn("ModuleNotFoundError", self.manager.last_error_details)


if __name__ == '__main__':
    unittest.main()
