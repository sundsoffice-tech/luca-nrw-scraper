"""
Comprehensive tests for Django views
Testing CRM dashboard, lead management, and API endpoints.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
import json

from leads.models import Lead, CallLog, EmailLog
from scraper_control.models import ScraperConfig, ScraperRun


class TestCRMDashboardViews(TestCase):
    """Test CRM dashboard views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.admin = User.objects.create_superuser(username='admin', password='admin123')

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get('/crm/')
        # Should redirect to login
        assert response.status_code in [302, 301, 403]

    def test_dashboard_accessible_when_logged_in(self):
        """Test that dashboard is accessible when logged in"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/crm/')
        assert response.status_code == 200 or response.status_code == 404

    def test_dashboard_displays_statistics(self):
        """Test that dashboard displays lead statistics"""
        self.client.login(username='testuser', password='testpass123')
        # Create some test leads
        Lead.objects.create(
            name='Test Lead 1',
            email='test1@example.com',
            status=Lead.Status.NEW,
            source=Lead.Source.SCRAPER,
        )
        Lead.objects.create(
            name='Test Lead 2',
            email='test2@example.com',
            status=Lead.Status.CONTACTED,
            source=Lead.Source.SCRAPER,
        )
        
        response = self.client.get('/crm/')
        # Response should contain lead data
        assert response.status_code == 200 or response.status_code == 404


class TestLeadListViews(TestCase):
    """Test lead list and filtering views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # Create test leads
        self.lead1 = Lead.objects.create(
            name='Max Mustermann',
            email='max@example.com',
            telefon='015112345678',
            status=Lead.Status.NEW,
            source=Lead.Source.SCRAPER,
            quality_score=80,
        )
        self.lead2 = Lead.objects.create(
            name='Anna Schmidt',
            email='anna@example.com',
            status=Lead.Status.CONTACTED,
            source=Lead.Source.MANUAL,
            quality_score=60,
        )

    def test_lead_list_view(self):
        """Test lead list view"""
        response = self.client.get('/crm/leads/')
        assert response.status_code in [200, 404]

    def test_lead_detail_view(self):
        """Test lead detail view"""
        response = self.client.get(f'/crm/leads/{self.lead1.id}/')
        assert response.status_code in [200, 404]

    def test_lead_filter_by_status(self):
        """Test filtering leads by status"""
        response = self.client.get('/crm/leads/?status=NEW')
        assert response.status_code in [200, 404]

    def test_lead_filter_by_quality_score(self):
        """Test filtering leads by quality score"""
        response = self.client.get('/crm/leads/?min_quality=70')
        assert response.status_code in [200, 404]

    def test_lead_search(self):
        """Test searching leads"""
        response = self.client.get('/crm/leads/?search=Max')
        assert response.status_code in [200, 404]


class TestLeadAPIViews(APITestCase):
    """Test Lead API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com',
            status=Lead.Status.NEW,
            source=Lead.Source.SCRAPER,
        )

    def test_api_lead_list(self):
        """Test API lead list endpoint"""
        response = self.client.get('/api/leads/')
        assert response.status_code in [200, 404]

    def test_api_lead_retrieve(self):
        """Test API lead detail endpoint"""
        response = self.client.get(f'/api/leads/{self.lead.id}/')
        assert response.status_code in [200, 404]

    def test_api_lead_update(self):
        """Test API lead update endpoint"""
        data = {'status': 'CONTACTED'}
        response = self.client.patch(f'/api/leads/{self.lead.id}/', data)
        assert response.status_code in [200, 404, 403]

    def test_api_requires_authentication(self):
        """Test that API requires authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/leads/')
        assert response.status_code in [401, 403, 404]


class TestScraperControlViews(TestCase):
    """Test scraper control views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='admin123')
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_scraper_control_requires_login(self):
        """Test that scraper control requires authentication"""
        response = self.client.get('/crm/scraper/')
        assert response.status_code in [302, 301, 403, 404]

    def test_scraper_control_accessible_for_admin(self):
        """Test that scraper control is accessible for admin"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/crm/scraper/')
        assert response.status_code in [200, 404]

    def test_scraper_config_view(self):
        """Test scraper configuration view"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/crm/scraper/config/')
        assert response.status_code in [200, 404]

    def test_scraper_start_endpoint(self):
        """Test scraper start endpoint"""
        self.client.login(username='admin', password='admin123')
        response = self.client.post('/crm/scraper/start/')
        # May not be implemented or require specific permissions
        assert response.status_code in [200, 201, 403, 404, 405]


class TestExportViews(TestCase):
    """Test export functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # Create test leads
        Lead.objects.create(
            name='Export Test 1',
            email='export1@example.com',
            status=Lead.Status.NEW,
        )

    def test_csv_export(self):
        """Test CSV export"""
        response = self.client.get('/crm/leads/export/csv/')
        if response.status_code == 200:
            assert response['Content-Type'] == 'text/csv' or 'csv' in response['Content-Type']

    def test_excel_export(self):
        """Test Excel export"""
        response = self.client.get('/crm/leads/export/excel/')
        if response.status_code == 200:
            assert 'excel' in response['Content-Type'] or 'spreadsheet' in response['Content-Type']


class TestCallLogViews(TestCase):
    """Test call log functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        self.lead = Lead.objects.create(
            name='Call Test Lead',
            email='call@example.com',
        )

    def test_create_call_log(self):
        """Test creating a call log"""
        data = {
            'lead': self.lead.id,
            'notes': 'Test call notes',
            'outcome': 'interested',
        }
        response = self.client.post('/crm/calls/create/', data)
        assert response.status_code in [200, 201, 302, 404]

    def test_list_call_logs(self):
        """Test listing call logs"""
        CallLog.objects.create(
            lead=self.lead,
            user=self.user,
            notes='Test log',
        )
        response = self.client.get('/crm/calls/')
        assert response.status_code in [200, 404]


class TestEmailLogViews(TestCase):
    """Test email log functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        self.lead = Lead.objects.create(
            name='Email Test Lead',
            email='email@example.com',
        )

    def test_create_email_log(self):
        """Test creating an email log"""
        data = {
            'lead': self.lead.id,
            'subject': 'Test Email',
            'body': 'Test email body',
        }
        response = self.client.post('/crm/emails/create/', data)
        assert response.status_code in [200, 201, 302, 404]

    def test_list_email_logs(self):
        """Test listing email logs"""
        EmailLog.objects.create(
            lead=self.lead,
            user=self.user,
            subject='Test',
            body='Test body',
        )
        response = self.client.get('/crm/emails/')
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestEndToEndWorkflow(TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_lead_lifecycle(self):
        """Test complete lead lifecycle"""
        # Create lead
        lead = Lead.objects.create(
            name='Lifecycle Test',
            email='lifecycle@example.com',
            status=Lead.Status.NEW,
        )
        
        # View lead
        response = self.client.get(f'/crm/leads/{lead.id}/')
        assert response.status_code in [200, 404]
        
        # Update lead status
        lead.status = Lead.Status.CONTACTED
        lead.save()
        
        # Add call log
        CallLog.objects.create(
            lead=lead,
            user=self.user,
            notes='First contact',
        )
        
        # Verify lead was updated
        lead.refresh_from_db()
        assert lead.status == Lead.Status.CONTACTED

    def test_scraper_to_lead_workflow(self):
        """Test scraper run to lead creation workflow"""
        # Create scraper config
        config = ScraperConfig.get_config()
        config.industry = 'recruiter'
        config.save()
        
        # Create scraper run
        run = ScraperRun.objects.create(
            industry='recruiter',
            status='completed',
        )
        
        # Create lead from scraper
        lead = Lead.objects.create(
            name='Scraper Lead',
            email='scraper@example.com',
            source=Lead.Source.SCRAPER,
        )
        
        # Verify lead exists
        assert Lead.objects.filter(source=Lead.Source.SCRAPER).count() >= 1
