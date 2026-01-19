from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from datetime import date, datetime, timedelta
from reports.models import ReportSchedule, ReportHistory


class ReportModelsTestCase(TestCase):
    """Test case for Report models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_report_schedule_creation(self):
        """Test creating a ReportSchedule"""
        schedule = ReportSchedule.objects.create(
            name='Test Weekly Report',
            report_type='lead_overview',
            frequency='weekly',
            recipients=['test@example.com'],
            is_active=True,
            created_by=self.user
        )
        
        self.assertEqual(schedule.name, 'Test Weekly Report')
        self.assertEqual(schedule.report_type, 'lead_overview')
        self.assertEqual(schedule.frequency, 'weekly')
        self.assertTrue(schedule.is_active)
        self.assertEqual(schedule.created_by, self.user)
        
        # Test __str__ method
        str_repr = str(schedule)
        self.assertIn('Test Weekly Report', str_repr)
        self.assertIn('Wöchentlich', str_repr)
    
    def test_report_history_creation(self):
        """Test creating a ReportHistory"""
        schedule = ReportSchedule.objects.create(
            name='Test Report',
            report_type='scraper_performance',
            frequency='daily',
            recipients=['test@example.com'],
            created_by=self.user
        )
        
        history = ReportHistory.objects.create(
            schedule=schedule,
            report_type='scraper_performance',
            generated_by=self.user,
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            data={'total_runs': 100, 'success_rate': 95.0},
            file_path='/reports/test.pdf',
            file_format='pdf'
        )
        
        self.assertEqual(history.schedule, schedule)
        self.assertEqual(history.report_type, 'scraper_performance')
        self.assertEqual(history.generated_by, self.user)
        self.assertEqual(history.file_format, 'pdf')
        self.assertIsInstance(history.data, dict)
        
        # Test __str__ method
        str_repr = str(history)
        self.assertIn('scraper_performance', str_repr)


class ReportViewsTestCase(TestCase):
    """Test case for Report views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create Admin group and add user to it
        admin_group = Group.objects.create(name='Admin')
        self.user.groups.add(admin_group)
        
        # Create test data
        self.schedule = ReportSchedule.objects.create(
            name='Test Schedule',
            report_type='lead_overview',
            frequency='weekly',
            recipients=['test@example.com'],
            is_active=True,
            created_by=self.user
        )
        
        self.history = ReportHistory.objects.create(
            schedule=self.schedule,
            report_type='lead_overview',
            generated_by=self.user,
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            data={'total': 100},
            file_format='pdf'
        )
    
    def test_reports_dashboard_requires_login(self):
        """Test that reports dashboard requires login"""
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)
    
    def test_reports_dashboard_authenticated(self):
        """Test reports dashboard with authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('reports:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/dashboard.html')
        
        # Check context
        self.assertIn('schedules', response.context)
        self.assertIn('recent_reports', response.context)
        
        # Verify our test data is in context
        schedules = list(response.context['schedules'])
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0].name, 'Test Schedule')
        
        reports = list(response.context['recent_reports'])
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].report_type, 'lead_overview')


class ReportScheduleModelTestCase(TestCase):
    """Test ReportSchedule model choices and meta"""
    
    def test_frequency_choices(self):
        """Test frequency choices are valid"""
        valid_frequencies = ['daily', 'weekly', 'monthly']
        for freq_value, freq_display in ReportSchedule.FREQUENCY_CHOICES:
            self.assertIn(freq_value, valid_frequencies)
    
    def test_report_type_choices(self):
        """Test report type choices are valid"""
        valid_types = [
            'lead_overview',
            'scraper_performance', 
            'conversion_funnel',
            'source_analysis',
            'cost_analysis'
        ]
        for type_value, type_display in ReportSchedule.REPORT_TYPE_CHOICES:
            self.assertIn(type_value, valid_types)
    
    def test_model_meta(self):
        """Test model meta settings"""
        self.assertEqual(ReportSchedule._meta.verbose_name, 'Report-Zeitplan')
        self.assertEqual(ReportSchedule._meta.verbose_name_plural, 'Report-Zeitpläne')
        self.assertEqual(ReportSchedule._meta.ordering, ['-created_at'])


class ReportHistoryModelTestCase(TestCase):
    """Test ReportHistory model choices and meta"""
    
    def test_file_format_choices(self):
        """Test file format choices"""
        history = ReportHistory()
        valid_formats = ['pdf', 'xlsx', 'csv']
        
        for format_value, format_display in history._meta.get_field('file_format').choices:
            self.assertIn(format_value, valid_formats)
    
    def test_model_meta(self):
        """Test model meta settings"""
        self.assertEqual(ReportHistory._meta.verbose_name, 'Report-Historie')
        self.assertEqual(ReportHistory._meta.verbose_name_plural, 'Report-Historien')
        self.assertEqual(ReportHistory._meta.ordering, ['-generated_at'])
