#!/usr/bin/env python3
"""
Test for centralized configuration system.

Tests the priority system: DB → Env → Defaults
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCentralizedConfiguration(unittest.TestCase):
    """Test centralized configuration loading with proper priority."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear any existing environment variables
        self.original_env = {}
        test_vars = ['HTTP_TIMEOUT', 'ASYNC_LIMIT', 'POOL_SIZE', 'MIN_SCORE', 
                     'ENABLE_KLEINANZEIGEN', 'PARALLEL_PORTAL_CRAWL']
        for var in test_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def tearDown(self):
        """Restore original environment."""
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    def test_defaults_when_no_env_no_db(self):
        """Test that defaults are used when no env vars and no DB."""
        # Force reload of config module
        if 'luca_scraper.config' in sys.modules:
            del sys.modules['luca_scraper.config']
        
        # Mock the Django import to fail
        with patch.dict('sys.modules', {'telis_recruitment.scraper_control.config_loader': None}):
            from luca_scraper.config import get_scraper_config
            
            config = get_scraper_config()
            
            # Check defaults
            self.assertEqual(config['http_timeout'], 10)
            self.assertEqual(config['async_limit'], 35)
            self.assertEqual(config['pool_size'], 12)
            self.assertEqual(config['min_score'], 40)
            self.assertTrue(config['enable_kleinanzeigen'])
    
    def test_env_overrides_defaults(self):
        """Test that environment variables override defaults."""
        # Set environment variables
        os.environ['HTTP_TIMEOUT'] = '20'
        os.environ['ASYNC_LIMIT'] = '50'
        os.environ['MIN_SCORE'] = '60'
        os.environ['ENABLE_KLEINANZEIGEN'] = '0'
        
        # Force reload
        if 'luca_scraper.config' in sys.modules:
            del sys.modules['luca_scraper.config']
        
        # Mock the Django import to fail
        with patch.dict('sys.modules', {'telis_recruitment.scraper_control.config_loader': None}):
            from luca_scraper.config import get_scraper_config
            
            config = get_scraper_config()
            
            # Check env overrides
            self.assertEqual(config['http_timeout'], 20)
            self.assertEqual(config['async_limit'], 50)
            self.assertEqual(config['min_score'], 60)
            self.assertFalse(config['enable_kleinanzeigen'])
    
    def test_db_overrides_env_and_defaults(self):
        """Test that DB configuration overrides env vars and defaults."""
        # Set environment variables
        os.environ['HTTP_TIMEOUT'] = '20'
        os.environ['ASYNC_LIMIT'] = '50'
        
        # Mock Django config loader
        mock_django_config = {
            'http_timeout': 30,  # DB value differs from env (20) and default (10)
            'async_limit': 100,  # DB value differs from env (50) and default (35)
            'min_score': 70,     # DB value differs from default (40)
        }
        
        # Force reload
        if 'luca_scraper.config' in sys.modules:
            del sys.modules['luca_scraper.config']
        
        # Mock the Django import
        with patch('luca_scraper.config._get_scraper_config_django', return_value=mock_django_config):
            with patch('luca_scraper.config.SCRAPER_CONFIG_AVAILABLE', True):
                from luca_scraper.config import get_scraper_config
                
                config = get_scraper_config()
                
                # Check DB overrides everything
                self.assertEqual(config['http_timeout'], 30)  # From DB
                self.assertEqual(config['async_limit'], 100)  # From DB
                self.assertEqual(config['min_score'], 70)     # From DB
    
    def test_get_specific_param(self):
        """Test getting a specific parameter."""
        if 'luca_scraper.config' in sys.modules:
            del sys.modules['luca_scraper.config']
        
        with patch.dict('sys.modules', {'telis_recruitment.scraper_control.config_loader': None}):
            from luca_scraper.config import get_scraper_config
            
            # Get specific param
            timeout = get_scraper_config('http_timeout')
            self.assertEqual(timeout, 10)  # Default value
            
            # Get non-existent param
            missing = get_scraper_config('non_existent_param')
            self.assertIsNone(missing)
    
    def test_invalid_env_value_uses_default(self):
        """Test that invalid env values fall back to defaults."""
        os.environ['HTTP_TIMEOUT'] = 'invalid'
        os.environ['ASYNC_LIMIT'] = 'not_a_number'
        
        if 'luca_scraper.config' in sys.modules:
            del sys.modules['luca_scraper.config']
        
        with patch.dict('sys.modules', {'telis_recruitment.scraper_control.config_loader': None}):
            from luca_scraper.config import get_scraper_config
            
            config = get_scraper_config()
            
            # Should use defaults due to invalid env values
            self.assertEqual(config['http_timeout'], 10)
            self.assertEqual(config['async_limit'], 35)
    
    def test_global_variables_use_centralized_config(self):
        """Test that global variables are set from centralized config."""
        os.environ['HTTP_TIMEOUT'] = '25'
        os.environ['ASYNC_LIMIT'] = '45'
        
        if 'luca_scraper.config' in sys.modules:
            del sys.modules['luca_scraper.config']
        
        with patch.dict('sys.modules', {'telis_recruitment.scraper_control.config_loader': None}):
            from luca_scraper.config import HTTP_TIMEOUT, ASYNC_LIMIT
            
            # Check that global vars match config
            self.assertEqual(HTTP_TIMEOUT, 25)
            self.assertEqual(ASYNC_LIMIT, 45)


class TestScriptnameFallback(unittest.TestCase):
    """Test that scriptname.py properly uses centralized config."""
    
    def test_scriptname_uses_luca_scraper_config(self):
        """Test that scriptname.py uses luca_scraper config when available."""
        # Import scriptname module
        import scriptname
        
        # Check that _LUCA_SCRAPER_AVAILABLE is True (if luca_scraper is installed)
        if hasattr(scriptname, '_LUCA_SCRAPER_AVAILABLE') and scriptname._LUCA_SCRAPER_AVAILABLE:
            # Verify that scriptname is using imported values
            self.assertIsInstance(scriptname.HTTP_TIMEOUT, int)
            self.assertIsInstance(scriptname.ASYNC_LIMIT, int)
            self.assertIsInstance(scriptname.POOL_SIZE, int)


def run_tests():
    """
    Run all configuration centralization tests.
    
    Creates and executes test suites for:
    - TestCentralizedConfiguration
    - TestScriptnameFallback
    
    Returns:
        int: 0 if all tests pass, 1 if any tests fail
    """
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestCentralizedConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestScriptnameFallback))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    print("=" * 70)
    print("Testing Centralized Configuration System")
    print("=" * 70)
    print()
    
    exit_code = run_tests()
    
    print()
    print("=" * 70)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 70)
    
    sys.exit(exit_code)
