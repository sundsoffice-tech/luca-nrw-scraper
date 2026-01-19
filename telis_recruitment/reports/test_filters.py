"""
Test report filters functionality
"""
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from reports.services.report_generator import ReportGenerator


class ReportFilterTestCase(TestCase):
    """Test report filter functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_report_generator_init_with_filters(self):
        """Test ReportGenerator initialization with filters"""
        filters = {
            'status': ['NEW', 'CONTACTED'],
            'region': ['Berlin', 'Hamburg'],
            'min_score': 50,
        }
        
        generator = ReportGenerator(filters=filters)
        
        self.assertIsNotNone(generator)
        self.assertEqual(generator.filters, filters)
        self.assertIsNotNone(generator.start_date)
        self.assertIsNotNone(generator.end_date)
    
    def test_report_generator_default_filters(self):
        """Test ReportGenerator with no filters"""
        generator = ReportGenerator()
        
        self.assertEqual(generator.filters, {})
    
    def test_api_filter_options_endpoint(self):
        """Test filter options API endpoint"""
        response = self.client.get(reverse('reports:api_filter_options'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that we have the expected keys
        self.assertIn('status', data)
        self.assertIn('regions', data)
        self.assertIn('sources', data)
        self.assertIn('industries', data)
        self.assertIn('score_range', data)
        
        # Check score range structure
        self.assertEqual(data['score_range']['min'], 0)
        self.assertEqual(data['score_range']['max'], 100)
    
    def test_api_report_with_filters(self):
        """Test report API with filter parameters"""
        response = self.client.get(
            reverse('reports:api_report', kwargs={'report_type': 'lead_overview'}),
            {
                'days': 30,
                'status': 'NEW',
                'min_score': 50,
                'with_phone': 'true',
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that filters are included in response
        self.assertIn('applied_filters', data)
        self.assertIn('status', data['applied_filters'])
        self.assertIn('min_score', data['applied_filters'])
        self.assertIn('with_phone', data['applied_filters'])
    
    def test_api_report_with_custom_dates(self):
        """Test report API with custom date range"""
        start_date = (timezone.now() - timedelta(days=60)).date().isoformat()
        end_date = timezone.now().date().isoformat()
        
        response = self.client.get(
            reverse('reports:api_report', kwargs={'report_type': 'lead_overview'}),
            {
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that report has period info
        self.assertIn('period', data)
        self.assertIn('start', data['period'])
        self.assertIn('end', data['period'])


class ParseFiltersTestCase(TestCase):
    """Test filter parsing function"""
    
    def setUp(self):
        """Set up test client"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_parse_single_status_filter(self):
        """Test parsing single status filter"""
        response = self.client.get(
            reverse('reports:api_report', kwargs={'report_type': 'lead_overview'}),
            {'status': 'NEW'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('applied_filters', data)
        # Status should be converted to list
        self.assertIsInstance(data['applied_filters']['status'], list)
    
    def test_parse_multiple_filters(self):
        """Test parsing multiple filters"""
        response = self.client.get(
            reverse('reports:api_report', kwargs={'report_type': 'lead_overview'}),
            {
                'status': 'NEW,CONTACTED',
                'region': 'Berlin',
                'min_score': '60',
                'with_phone': 'true',
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        filters = data['applied_filters']
        self.assertIn('status', filters)
        self.assertIn('region', filters)
        self.assertIn('min_score', filters)
        self.assertIn('with_phone', filters)
        
        # Check boolean conversion
        self.assertTrue(filters['with_phone'])
    
    def test_parse_boolean_filters(self):
        """Test boolean filter parsing"""
        for value in ['true', '1', 'True']:
            response = self.client.get(
                reverse('reports:api_report', kwargs={'report_type': 'lead_overview'}),
                {'with_phone': value}
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertTrue(data['applied_filters'].get('with_phone'))
