# -*- coding: utf-8 -*-
"""
Tests for dashboard scraper control module
"""

import os
import sys
import time
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.scraper_control import ScraperController


class TestScraperController(unittest.TestCase):
    """Test cases for ScraperController"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.controller = ScraperController()
    
    def test_initialization(self):
        """Test controller initialization"""
        self.assertIsNone(self.controller.process)
        self.assertIsNone(self.controller.pid)
        self.assertEqual(self.controller.status, 'stopped')
        self.assertIsNone(self.controller.start_time)
        self.assertFalse(self.controller.paused)
        self.assertEqual(self.controller.params, {})
        self.assertIsNotNone(self.controller.output_queue)
        self.assertIsNone(self.controller.output_thread)
    
    def test_get_output_empty(self):
        """Test get_output when queue is empty"""
        output = self.controller.get_output(lines=10)
        self.assertEqual(output, [])
    
    def test_get_output_with_data(self):
        """Test get_output when queue has data"""
        # Add some test data to queue
        test_lines = ['line 1', 'line 2', 'line 3', 'line 4', 'line 5']
        for line in test_lines:
            self.controller.output_queue.put(line)
        
        # Get output
        output = self.controller.get_output(lines=3)
        self.assertEqual(len(output), 3)
        self.assertEqual(output, ['line 1', 'line 2', 'line 3'])
    
    def test_get_output_respects_lines_limit(self):
        """Test get_output respects the lines parameter"""
        # Add more data than requested
        for i in range(10):
            self.controller.output_queue.put(f'line {i}')
        
        # Request only 5 lines
        output = self.controller.get_output(lines=5)
        self.assertEqual(len(output), 5)
    
    def test_is_running_when_stopped(self):
        """Test is_running returns False when stopped"""
        self.assertFalse(self.controller.is_running())
    
    def test_get_status_stopped(self):
        """Test get_status when controller is stopped"""
        status = self.controller.get_status()
        self.assertEqual(status['status'], 'stopped')
        self.assertIsNone(status['pid'])
        self.assertFalse(status['paused'])
        self.assertEqual(status['params'], {})
    
    @patch.object(ScraperController, 'is_running')
    def test_start_when_already_running(self, mock_is_running):
        """Test start returns error when already running"""
        # Mock is_running to return True
        mock_is_running.return_value = True
        self.controller.status = 'running'
        self.controller.pid = 12345
        
        result = self.controller.start({})
        self.assertFalse(result['success'])
        self.assertIn('already running', result['error'])
    
    @patch('subprocess.Popen')
    @patch('os.path.exists')
    def test_start_sets_working_directory(self, mock_exists, mock_popen):
        """Test that start sets the working directory correctly"""
        # Mock .env file doesn't exist to simplify test
        mock_exists.return_value = False
        
        # Mock the process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.return_value = ''
        mock_popen.return_value = mock_process
        
        # Start the controller
        params = {'industry': 'recruiter', 'qpi': 10}
        result = self.controller.start(params)
        
        # Verify Popen was called with cwd parameter
        self.assertTrue(mock_popen.called)
        call_kwargs = mock_popen.call_args[1]
        self.assertIn('cwd', call_kwargs)
        self.assertIsNotNone(call_kwargs['cwd'])
        
        # Verify success
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'running')
        self.assertEqual(result['pid'], 12345)
    
    @patch('subprocess.Popen')
    @patch('os.path.exists')
    @patch('dotenv.dotenv_values')
    def test_start_loads_env_file(self, mock_dotenv_values, mock_exists, mock_popen):
        """Test that start loads .env file when it exists"""
        # Mock .env file exists
        mock_exists.return_value = True
        mock_dotenv_values.return_value = {
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_CSE_API_KEY': 'test_cse_key'
        }
        
        # Mock the process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.stdout.readline.return_value = ''
        mock_popen.return_value = mock_process
        
        # Start the controller
        result = self.controller.start({})
        
        # Verify Popen was called with env parameter
        self.assertTrue(mock_popen.called)
        call_kwargs = mock_popen.call_args[1]
        self.assertIn('env', call_kwargs)
        env = call_kwargs['env']
        self.assertIn('OPENAI_API_KEY', env)
        self.assertEqual(env['OPENAI_API_KEY'], 'test_key')
    
    @patch('subprocess.Popen')
    @patch('os.path.exists')
    def test_start_detects_immediate_termination(self, mock_exists, mock_popen):
        """Test that start detects when process terminates immediately"""
        # Mock .env file doesn't exist
        mock_exists.return_value = False
        
        # Mock the process that terminates immediately
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = 1  # Process has terminated
        mock_process.stdout.readline.side_effect = ['Error: Missing API key\n', '']
        mock_popen.return_value = mock_process
        
        # Start the controller
        result = self.controller.start({})
        
        # Verify failure is detected
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'error')
        self.assertIn('terminated immediately', result['error'])


if __name__ == '__main__':
    unittest.main()
