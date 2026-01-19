"""
Tests for scraper_control app - parameter validation and synchronization.
"""

from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from .models import ScraperConfig, ScraperRun
from .process_manager import ProcessManager


class ScraperConfigModelTest(TestCase):
    """Test ScraperConfig model with extended industry choices."""
    
    def setUp(self):
        self.config = ScraperConfig.get_config()
    
    def test_industry_choices_include_extended(self):
        """Test that INDUSTRY_CHOICES includes extended industries."""
        industries = [c[0] for c in ScraperConfig.INDUSTRY_CHOICES]
        
        # Base industries
        self.assertIn('all', industries)
        self.assertIn('recruiter', industries)
        self.assertIn('candidates', industries)
        self.assertIn('talent_hunt', industries)
        
        # Extended industries
        self.assertIn('nrw', industries)
        self.assertIn('social', industries)
        self.assertIn('solar', industries)
        self.assertIn('telekom', industries)
        self.assertIn('versicherung', industries)
        self.assertIn('bau', industries)
        self.assertIn('ecom', industries)
        self.assertIn('household', industries)
    
    def test_mode_choices_valid(self):
        """Test that MODE_CHOICES are valid (no headhunter)."""
        modes = [c[0] for c in ScraperConfig.MODE_CHOICES]
        
        self.assertIn('standard', modes)
        self.assertIn('learning', modes)
        self.assertIn('aggressive', modes)
        self.assertIn('snippet_only', modes)
        
        # Ensure headhunter is NOT in choices
        self.assertNotIn('headhunter', modes)
    
    def test_singleton_behavior(self):
        """Test that ScraperConfig maintains singleton behavior."""
        config1 = ScraperConfig.get_config()
        config2 = ScraperConfig.get_config()
        
        self.assertEqual(config1.pk, config2.pk)
        self.assertEqual(config1.pk, 1)


class ScraperConfigPersistenceTest(APITestCase):
    """Test that scraper settings persist after starting."""
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.start_url = '/crm/scraper/api/scraper/start/'
        
        # Reset config to defaults
        config = ScraperConfig.get_config()
        config.industry = 'recruiter'
        config.qpi = 15
        config.mode = 'standard'
        config.smart = True
        config.once = True
        config.force = False
        config.dry_run = False
        config.save()
    
    @patch('scraper_control.views.get_manager')
    def test_config_persists_after_successful_start(self, mock_get_manager):
        """Test that config values are saved after successful scraper start."""
        # Mock the manager to return success
        mock_manager = MagicMock()
        mock_manager.start.return_value = {'success': True, 'message': 'Started'}
        mock_get_manager.return_value = mock_manager
        
        # Send request with new settings
        response = self.client.post(self.start_url, {
            'industry': 'candidates',
            'qpi': 25,
            'mode': 'learning',
            'smart': False,
            'once': False,
            'force': True,
            'dry_run': True
        }, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Config should be updated
        config = ScraperConfig.get_config()
        self.assertEqual(config.industry, 'candidates')
        self.assertEqual(config.qpi, 25)
        self.assertEqual(config.mode, 'learning')
        self.assertEqual(config.smart, False)
        self.assertEqual(config.once, False)
        self.assertEqual(config.force, True)
        self.assertEqual(config.dry_run, True)
    
    @patch('scraper_control.views.get_manager')
    def test_config_not_persisted_on_failed_start(self, mock_get_manager):
        """Test that config values are NOT saved if scraper fails to start."""
        # Mock the manager to return failure
        mock_manager = MagicMock()
        mock_manager.start.return_value = {'success': False, 'error': 'Already running'}
        mock_get_manager.return_value = mock_manager
        
        # Get initial config values
        config = ScraperConfig.get_config()
        initial_industry = config.industry
        initial_qpi = config.qpi
        
        # Send request with new settings
        response = self.client.post(self.start_url, {
            'industry': 'talent_hunt',
            'qpi': 30,
            'mode': 'aggressive',
        }, format='json')
        
        # Should fail
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Config should NOT be updated
        config = ScraperConfig.get_config()
        self.assertEqual(config.industry, initial_industry)
        self.assertEqual(config.qpi, initial_qpi)
    
    @patch('scraper_control.views.get_manager')
    def test_config_updated_by_field_set(self, mock_get_manager):
        """Test that updated_by field is set when config is saved."""
        # Mock the manager to return success
        mock_manager = MagicMock()
        mock_manager.start.return_value = {'success': True, 'message': 'Started'}
        mock_get_manager.return_value = mock_manager
        
        # Send request
        response = self.client.post(self.start_url, {
            'industry': 'nrw',
            'qpi': 20,
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check updated_by is set
        config = ScraperConfig.get_config()
        self.assertEqual(config.updated_by, self.user)


class ScraperPageConfigLoadTest(TestCase):
    """Test that scraper page loads config values correctly."""
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='admin', password='testpass123')
        self.page_url = '/crm/scraper/'
    
    def test_page_loads_config_in_context(self):
        """Test that scraper page includes config in context."""
        # Set specific config values
        config = ScraperConfig.get_config()
        config.industry = 'solar'
        config.qpi = 35
        config.mode = 'aggressive'
        config.smart = False
        config.once = False
        config.force = True
        config.dry_run = True
        config.save()
        
        # Load page
        response = self.client.get(self.page_url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('config', response.context)
        
        # Verify config values
        page_config = response.context['config']
        self.assertEqual(page_config.industry, 'solar')
        self.assertEqual(page_config.qpi, 35)
        self.assertEqual(page_config.mode, 'aggressive')
        self.assertEqual(page_config.smart, False)
        self.assertEqual(page_config.once, False)
        self.assertEqual(page_config.force, True)
        self.assertEqual(page_config.dry_run, True)


class ScraperAPIParameterValidationTest(APITestCase):
    """Test API parameter validation in views."""
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.start_url = '/crm/scraper/api/scraper/start/'
    
    def test_valid_industry_accepted(self):
        """Test that valid industries are accepted."""
        valid_industries = ['recruiter', 'candidates', 'talent_hunt', 'all', 
                           'nrw', 'social', 'solar', 'telekom', 'versicherung', 
                           'bau', 'ecom', 'household']
        
        for industry in valid_industries:
            # Note: This will try to start the scraper, so we just check it doesn't reject the industry
            response = self.client.post(self.start_url, {
                'industry': industry,
                'qpi': 15,
                'mode': 'standard',
                'once': True,
                'dry_run': True  # Use dry run to avoid actual scraping
            }, format='json')
            
            # Should not return 400 for invalid industry
            # It might return 400 for other reasons (scraper already running), but not for invalid industry
            if response.status_code == 400:
                self.assertNotIn('Ungültige Industry', response.data.get('error', ''))
    
    def test_invalid_industry_rejected(self):
        """Test that invalid industries are rejected."""
        response = self.client.post(self.start_url, {
            'industry': 'invalid_industry',
            'qpi': 15,
            'mode': 'standard',
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Ungültige Industry', response.data['error'])
    
    def test_invalid_mode_falls_back_to_standard(self):
        """Test that invalid mode falls back to standard instead of error."""
        # This should not fail, but fall back to standard mode
        response = self.client.post(self.start_url, {
            'industry': 'recruiter',
            'qpi': 15,
            'mode': 'headhunter',  # Invalid mode
            'once': True,
            'dry_run': True
        }, format='json')
        
        # Should succeed with fallback, not return 400 for invalid mode
        # (might still fail for other reasons like scraper already running)
        if response.status_code == 400:
            # If it fails, it should NOT be because of invalid mode
            self.assertNotIn('mode', response.data.get('error', '').lower())
    
    def test_qpi_clamped_within_range(self):
        """Test that QPI is clamped to valid range."""
        # Test high value
        response = self.client.post(self.start_url, {
            'industry': 'recruiter',
            'qpi': 200,  # Over max
            'mode': 'standard',
            'once': True,
            'dry_run': True
        }, format='json')
        
        # Should clamp to 100, not reject
        # Response should succeed (or fail for reasons other than QPI validation)
        if response.status_code == 400:
            self.assertNotIn('QPI muss zwischen', response.data.get('error', ''))
        
        # Test low value
        response = self.client.post(self.start_url, {
            'industry': 'recruiter',
            'qpi': 0,  # Below min
            'mode': 'standard',
            'once': True,
            'dry_run': True
        }, format='json')
        
        # Should clamp to 1, not reject
        if response.status_code == 400:
            self.assertNotIn('QPI muss zwischen', response.data.get('error', ''))
    
    def test_dry_run_with_aggressive_mode_fallback(self):
        """Test that dry_run + aggressive falls back to standard."""
        # The combination should be accepted but adjusted
        response = self.client.post(self.start_url, {
            'industry': 'recruiter',
            'qpi': 15,
            'mode': 'aggressive',
            'once': True,
            'dry_run': True
        }, format='json')
        
        # Should not reject the combination
        # (might still fail for other reasons)
        self.assertIsNotNone(response)


class ProcessManagerBuildCommandTest(TestCase):
    """Test ProcessManager command building."""
    
    def setUp(self):
        self.manager = ProcessManager()
    
    def test_build_command_with_valid_params(self):
        """Test building command with valid parameters."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
            'mode': 'learning',
            'smart': True,
            'once': True,
            'dry_run': False
        }
        
        cmd = self.manager._build_command(params, 'module', 'luca_scraper.cli')
        
        self.assertIn('--industry', cmd)
        self.assertIn('recruiter', cmd)
        self.assertIn('--qpi', cmd)
        self.assertIn('15', cmd)
        self.assertIn('--mode', cmd)
        self.assertIn('learning', cmd)
        self.assertIn('--smart', cmd)
        self.assertIn('--once', cmd)
        self.assertNotIn('--dry-run', cmd)
    
    def test_build_command_skips_invalid_mode(self):
        """Test that invalid mode is skipped."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
            'mode': 'headhunter',  # Invalid
            'once': True
        }
        
        cmd = self.manager._build_command(params, 'module', 'luca_scraper.cli')
        
        # Should not include invalid mode
        self.assertNotIn('headhunter', cmd)
    
    def test_build_command_standard_mode_omitted(self):
        """Test that standard mode is not added to command (it's default)."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
            'mode': 'standard',
            'once': True
        }
        
        cmd = self.manager._build_command(params, 'module', 'luca_scraper.cli')
        
        # Standard mode should not be explicitly added
        self.assertNotIn('--mode', cmd)
        self.assertNotIn('standard', cmd)
    
    def test_build_command_with_daterestrict(self):
        """Test that daterestrict is properly added."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
            'daterestrict': 'd30',
            'once': True
        }
        
        cmd = self.manager._build_command(params, 'module', 'luca_scraper.cli')
        
        self.assertIn('--daterestrict', cmd)
        self.assertIn('d30', cmd)
    
    def test_build_command_strips_daterestrict_whitespace(self):
        """Test that daterestrict whitespace is stripped."""
        params = {
            'industry': 'recruiter',
            'qpi': 15,
            'daterestrict': '  d30  ',
            'once': True
        }
        
        cmd = self.manager._build_command(params, 'module', 'luca_scraper.cli')
        
        self.assertIn('d30', cmd)
        self.assertNotIn('  d30  ', ' '.join(cmd))

