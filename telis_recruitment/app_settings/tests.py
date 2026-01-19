"""Tests for app_settings"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import UserPreferences, SystemSettings


class UserPreferencesModelTest(TestCase):
    """Test UserPreferences model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_user_preferences_creation(self):
        """Test creating user preferences"""
        prefs = UserPreferences.objects.create(
            user=self.user,
            theme='dark',
            language='de'
        )
        self.assertEqual(prefs.theme, 'dark')
        self.assertEqual(prefs.language, 'de')
        self.assertTrue(prefs.email_notifications)
    
    def test_user_preferences_defaults(self):
        """Test default values"""
        prefs = UserPreferences.objects.create(user=self.user)
        self.assertEqual(prefs.theme, 'dark')
        self.assertEqual(prefs.language, 'de')
        self.assertEqual(prefs.items_per_page, 25)
        self.assertEqual(prefs.default_lead_view, 'list')


class SystemSettingsModelTest(TestCase):
    """Test SystemSettings model"""
    
    def test_system_settings_singleton(self):
        """Test that SystemSettings is a singleton"""
        settings1 = SystemSettings.get_settings()
        settings2 = SystemSettings.get_settings()
        self.assertEqual(settings1.pk, settings2.pk)
        self.assertEqual(settings1.pk, 1)
    
    def test_system_settings_defaults(self):
        """Test default values"""
        settings = SystemSettings.get_settings()
        self.assertEqual(settings.site_name, 'TELIS CRM')
        self.assertTrue(settings.enable_email_module)
        self.assertTrue(settings.enable_scraper)
        self.assertTrue(settings.enable_ai_features)
        self.assertFalse(settings.maintenance_mode)
        self.assertEqual(settings.session_timeout_minutes, 60)


class SettingsViewsTest(TestCase):
    """Test settings views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin_user = User.objects.create_user(username='admin', password='adminpass')
        admin_group = Group.objects.create(name='Admin')
        self.admin_user.groups.add(admin_group)
    
    def test_settings_dashboard_requires_login(self):
        """Test that settings dashboard requires authentication"""
        response = self.client.get(reverse('app_settings:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_settings_dashboard_access(self):
        """Test accessing settings dashboard"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Einstellungen')
    
    def test_user_preferences_view(self):
        """Test user preferences view"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:user-preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Benutzereinstellungen')
    
    def test_user_preferences_save(self):
        """Test saving user preferences"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('app_settings:user-preferences'), {
            'theme': 'light',
            'language': 'en',
            'email_notifications': 'on',
            'items_per_page': '50',
            'default_lead_view': 'grid',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after save
        
        prefs = UserPreferences.objects.get(user=self.user)
        self.assertEqual(prefs.theme, 'light')
        self.assertEqual(prefs.language, 'en')
        self.assertEqual(prefs.items_per_page, 50)
        self.assertEqual(prefs.default_lead_view, 'grid')
    
    def test_system_settings_requires_admin(self):
        """Test that system settings require admin access"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:system-settings'))
        self.assertEqual(response.status_code, 302)  # Redirect with error
    
    def test_system_settings_admin_access(self):
        """Test admin access to system settings"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('app_settings:system-settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Systemeinstellungen')
    
    def test_system_settings_save(self):
        """Test saving system settings"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('app_settings:system-settings'), {
            'site_name': 'Test CRM',
            'site_url': 'https://test.com',
            'admin_email': 'admin@test.com',
            'enable_email_module': 'on',
            'enable_scraper': 'on',
            'enable_ai_features': '',  # Unchecked
            'enable_landing_pages': 'on',
            'maintenance_mode': '',
            'maintenance_message': '',
            'session_timeout_minutes': '120',
            'max_login_attempts': '3',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after save
        
        settings = SystemSettings.get_settings()
        self.assertEqual(settings.site_name, 'Test CRM')
        self.assertEqual(settings.admin_email, 'admin@test.com')
        self.assertTrue(settings.enable_email_module)
        self.assertFalse(settings.enable_ai_features)
        self.assertEqual(settings.session_timeout_minutes, 120)
    
    def test_integrations_view_requires_admin(self):
        """Test that integrations view requires admin access"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:integrations'))
        self.assertEqual(response.status_code, 302)  # Redirect with error
    
    def test_integrations_view_admin_access(self):
        """Test admin access to integrations view"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('app_settings:integrations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integrationen')
