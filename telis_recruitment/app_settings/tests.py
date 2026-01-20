"""Tests for app_settings"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from .models import UserPreferences, SystemSettings, PageView, AnalyticsEvent


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


class AnalyticsModelTest(TestCase):
    """Test Analytics models"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_pageview_creation(self):
        """Test creating a page view"""
        page_view = PageView.objects.create(
            user=self.user,
            session_key='test_session',
            path='/test/',
            page_title='Test Page',
            method='GET'
        )
        self.assertEqual(page_view.path, '/test/')
        self.assertEqual(page_view.user, self.user)
        self.assertIsNotNone(page_view.timestamp)
    
    def test_pageview_without_user(self):
        """Test creating a page view without authenticated user"""
        page_view = PageView.objects.create(
            session_key='anonymous_session',
            path='/public/',
            method='GET'
        )
        self.assertIsNone(page_view.user)
        self.assertEqual(page_view.path, '/public/')
    
    def test_analytics_event_creation(self):
        """Test creating an analytics event"""
        event = AnalyticsEvent.objects.create(
            user=self.user,
            session_key='test_session',
            category='conversion',
            action='lead_created',
            label='CSV Import',
            value=1.0,
            page_path='/crm/leads/',
            metadata={'source': 'csv'}
        )
        self.assertEqual(event.category, 'conversion')
        self.assertEqual(event.action, 'lead_created')
        self.assertEqual(event.value, 1.0)
    
    def test_analytics_event_choices(self):
        """Test analytics event category choices"""
        categories = ['navigation', 'interaction', 'conversion', 'error', 'engagement']
        for category in categories:
            event = AnalyticsEvent.objects.create(
                session_key='test_session',
                category=category,
                action='test_action'
            )
            self.assertEqual(event.category, category)


class SystemSettingsAnalyticsTest(TestCase):
    """Test SystemSettings analytics fields"""
    
    def test_analytics_defaults(self):
        """Test default analytics settings"""
        settings = SystemSettings.get_settings()
        self.assertFalse(settings.enable_analytics)
        self.assertEqual(settings.google_analytics_id, '')
        self.assertEqual(settings.meta_pixel_id, '')
        self.assertEqual(settings.custom_tracking_code, '')
    
    def test_analytics_settings_save(self):
        """Test saving analytics settings"""
        settings = SystemSettings.get_settings()
        settings.enable_analytics = True
        settings.google_analytics_id = 'G-XXXXXXXXXX'
        settings.meta_pixel_id = '123456789012345'
        settings.custom_tracking_code = '<script>console.log("test");</script>'
        settings.save()
        
        # Reload from database
        settings = SystemSettings.get_settings()
        self.assertTrue(settings.enable_analytics)
        self.assertEqual(settings.google_analytics_id, 'G-XXXXXXXXXX')
        self.assertEqual(settings.meta_pixel_id, '123456789012345')


class AnalyticsDashboardViewTest(TestCase):
    """Test analytics dashboard view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create some test data
        PageView.objects.create(
            user=self.user,
            session_key='session1',
            path='/test1/',
            page_title='Test Page 1'
        )
        PageView.objects.create(
            user=self.user,
            session_key='session1',
            path='/test2/',
            page_title='Test Page 2'
        )
        AnalyticsEvent.objects.create(
            user=self.user,
            session_key='session1',
            category='navigation',
            action='click',
            label='menu_item'
        )
    
    def test_analytics_dashboard_requires_login(self):
        """Test that analytics dashboard requires authentication"""
        response = self.client.get(reverse('app_settings:analytics'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_analytics_dashboard_access(self):
        """Test accessing analytics dashboard"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics')
        self.assertContains(response, 'Statistiken')
    
    def test_analytics_dashboard_data(self):
        """Test analytics dashboard shows data"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:analytics'))
        self.assertEqual(response.status_code, 200)
        
        # Check that context contains metrics
        self.assertIn('total_page_views', response.context)
        self.assertIn('unique_visitors', response.context)
        self.assertIn('total_events', response.context)
        
        # Verify counts
        self.assertEqual(response.context['total_page_views'], 2)
        self.assertEqual(response.context['unique_visitors'], 1)
        self.assertEqual(response.context['total_events'], 1)
    
    def test_analytics_dashboard_time_filter(self):
        """Test analytics dashboard time range filter"""
        self.client.login(username='testuser', password='testpass')
        
        # Test 7 days filter
        response = self.client.get(reverse('app_settings:analytics') + '?days=7')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 7)
        
        # Test 30 days filter
        response = self.client.get(reverse('app_settings:analytics') + '?days=30')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 30)
        
        # Test 90 days filter
        response = self.client.get(reverse('app_settings:analytics') + '?days=90')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 90)


class ContextProcessorTest(TestCase):
    """Test tracking_codes context processor"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_tracking_codes_disabled(self):
        """Test context when analytics is disabled"""
        settings = SystemSettings.get_settings()
        settings.enable_analytics = False
        settings.save()
        
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:dashboard'))
        
        self.assertIn('analytics_enabled', response.context)
        self.assertFalse(response.context['analytics_enabled'])
    
    def test_tracking_codes_enabled(self):
        """Test context when analytics is enabled"""
        settings = SystemSettings.get_settings()
        settings.enable_analytics = True
        settings.google_analytics_id = 'G-TEST123'
        settings.meta_pixel_id = '123456'
        settings.save()
        
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('app_settings:dashboard'))
        
        self.assertTrue(response.context['analytics_enabled'])
        self.assertEqual(response.context['google_analytics_id'], 'G-TEST123')
        self.assertEqual(response.context['meta_pixel_id'], '123456')
