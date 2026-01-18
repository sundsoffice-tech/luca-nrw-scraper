from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import io
import csv
import json
import tempfile
import sqlite3
import shutil
from pathlib import Path
from .models import Lead, CallLog, EmailLog, SyncStatus


class LeadModelTest(TestCase):
    """Tests for Lead model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.lead = Lead.objects.create(
            name='Max Mustermann',
            email='max@example.com',
            telefon='0123456789',
            status=Lead.Status.NEW,
            source=Lead.Source.SCRAPER,
            quality_score=75,
            lead_type=Lead.LeadType.ACTIVE_SALESPERSON,
            company='Test GmbH',
            role='Vertriebsleiter',
            assigned_to=self.user
        )
    
    def test_lead_creation(self):
        """Test that a lead can be created"""
        self.assertEqual(self.lead.name, 'Max Mustermann')
        self.assertEqual(self.lead.email, 'max@example.com')
        self.assertEqual(self.lead.status, Lead.Status.NEW)
        self.assertEqual(self.lead.source, Lead.Source.SCRAPER)
        self.assertEqual(self.lead.quality_score, 75)
    
    def test_lead_str(self):
        """Test the string representation of a lead"""
        expected = f"{self.lead.name} ({self.lead.get_status_display()})"
        self.assertEqual(str(self.lead), expected)
    
    def test_has_contact_info(self):
        """Test has_contact_info property"""
        self.assertTrue(self.lead.has_contact_info)
        
        lead_no_contact = Lead.objects.create(name='No Contact')
        self.assertFalse(lead_no_contact.has_contact_info)
    
    def test_is_hot_lead(self):
        """Test is_hot_lead property"""
        self.assertFalse(self.lead.is_hot_lead)
        
        self.lead.quality_score = 85
        self.lead.interest_level = 4
        self.lead.save()
        self.assertTrue(self.lead.is_hot_lead)
    
    def test_lead_ordering(self):
        """Test that leads are ordered by quality score and creation date"""
        lead2 = Lead.objects.create(
            name='Second Lead',
            quality_score=90
        )
        
        leads = list(Lead.objects.all())
        self.assertEqual(leads[0], lead2)  # Higher quality score first
        self.assertEqual(leads[1], self.lead)


class CallLogModelTest(TestCase):
    """Tests for CallLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.lead = Lead.objects.create(
            name='Test Lead',
            status=Lead.Status.NEW
        )
    
    def test_calllog_creation(self):
        """Test that a call log can be created"""
        call_log = CallLog.objects.create(
            lead=self.lead,
            outcome=CallLog.Outcome.CONNECTED,
            duration_seconds=120,
            interest_level=4,
            notes='Very interested in the position',
            called_by=self.user
        )
        
        self.assertEqual(call_log.lead, self.lead)
        self.assertEqual(call_log.outcome, CallLog.Outcome.CONNECTED)
        self.assertEqual(call_log.duration_seconds, 120)
        self.assertEqual(call_log.interest_level, 4)
    
    def test_calllog_updates_lead(self):
        """Test that creating a call log updates the lead"""
        initial_call_count = self.lead.call_count
        
        CallLog.objects.create(
            lead=self.lead,
            outcome=CallLog.Outcome.CONNECTED,
            interest_level=3,
            called_by=self.user
        )
        
        # Refresh lead from database
        self.lead.refresh_from_db()
        
        self.assertEqual(self.lead.call_count, initial_call_count + 1)
        self.assertEqual(self.lead.interest_level, 3)
        self.assertEqual(self.lead.status, Lead.Status.INTERESTED)
        self.assertIsNotNone(self.lead.last_called_at)
    
    def test_calllog_voicemail_status(self):
        """Test that voicemail outcome updates status correctly"""
        CallLog.objects.create(
            lead=self.lead,
            outcome=CallLog.Outcome.VOICEMAIL,
            called_by=self.user
        )
        
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.VOICEMAIL)
    
    def test_calllog_wrong_number_status(self):
        """Test that wrong number outcome marks lead as invalid"""
        CallLog.objects.create(
            lead=self.lead,
            outcome=CallLog.Outcome.WRONG_NUMBER,
            called_by=self.user
        )
        
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.INVALID)


class EmailLogModelTest(TestCase):
    """Tests for EmailLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com'
        )
    
    def test_emaillog_creation(self):
        """Test that an email log can be created"""
        email_log = EmailLog.objects.create(
            lead=self.lead,
            email_type=EmailLog.EmailType.WELCOME,
            subject='Welcome to our recruitment process',
            brevo_message_id='msg123'
        )
        
        self.assertEqual(email_log.lead, self.lead)
        self.assertEqual(email_log.email_type, EmailLog.EmailType.WELCOME)
        self.assertEqual(email_log.subject, 'Welcome to our recruitment process')
        self.assertEqual(email_log.brevo_message_id, 'msg123')
    
    def test_emaillog_str(self):
        """Test the string representation of an email log"""
        email_log = EmailLog.objects.create(
            lead=self.lead,
            email_type=EmailLog.EmailType.FOLLOWUP_1,
            subject='Follow-up email'
        )
        
        expected = f"{self.lead.name} - {email_log.get_email_type_display()}"
        self.assertEqual(str(email_log), expected)
    
    def test_emaillog_ordering(self):
        """Test that email logs are ordered by sent_at date"""
        email1 = EmailLog.objects.create(
            lead=self.lead,
            email_type=EmailLog.EmailType.WELCOME,
            subject='Welcome'
        )
        
        email2 = EmailLog.objects.create(
            lead=self.lead,
            email_type=EmailLog.EmailType.FOLLOWUP_1,
            subject='Follow-up'
        )
        
        email_logs = list(EmailLog.objects.all())
        self.assertEqual(email_logs[0], email2)  # Most recent first
        self.assertEqual(email_logs[1], email1)


class AdminIntegrationTest(TestCase):
    """Tests for admin integration"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_superuser(
            username='admin', 
            email='admin@example.com',
            password='adminpass'
        )
        self.lead = Lead.objects.create(
            name='Admin Test Lead',
            email='test@example.com',
            telefon='0123456789',
            status=Lead.Status.NEW,
            quality_score=85,
            interest_level=3
        )
    
    def test_admin_registered(self):
        """Test that admin classes are registered"""
        from django.contrib import admin
        from .models import Lead, CallLog, EmailLog
        
        self.assertTrue(admin.site.is_registered(Lead))
        self.assertTrue(admin.site.is_registered(CallLog))
        self.assertTrue(admin.site.is_registered(EmailLog))
    
    def test_lead_admin_display_methods(self):
        """Test that custom display methods work"""
        from django.contrib import admin
        from .admin import LeadAdmin
        
        admin_instance = LeadAdmin(Lead, admin.site)
        
        # Test status_badge - check it contains status display and has color styling
        badge = admin_instance.status_badge(self.lead)
        self.assertIn(self.lead.get_status_display(), badge)
        self.assertIn('background-color:', badge)
        self.assertIn('#', badge)  # Contains hex color
        
        # Test source_badge - check it contains source display and has an icon
        source = admin_instance.source_badge(self.lead)
        self.assertIn(self.lead.get_source_display(), source)
        # Check for presence of emoji characters (icons)
        self.assertTrue(any(ord(c) > 127 for c in source))
        
        # Test quality_bar - check it contains the score and has color styling
        quality = admin_instance.quality_bar(self.lead)
        self.assertIn('85', quality)
        self.assertIn('background:', quality)
        self.assertIn('#', quality)  # Contains hex color
        
        # Test interest_badge - check star count matches interest level
        interest = admin_instance.interest_badge(self.lead)
        self.assertIn('⭐', interest)
        self.assertEqual(interest.count('⭐'), 3)
    
    def test_calllog_admin_display_methods(self):
        """Test CallLog admin display methods"""
        from django.contrib import admin
        from .admin import CallLogAdmin
        
        call_log = CallLog.objects.create(
            lead=self.lead,
            outcome=CallLog.Outcome.CONNECTED,
            duration_seconds=125,
            interest_level=4,
            called_by=self.user
        )
        
        admin_instance = CallLogAdmin(CallLog, admin.site)
        
        # Test outcome_badge - check it contains outcome and has color styling
        badge = admin_instance.outcome_badge(call_log)
        self.assertIn(call_log.get_outcome_display(), badge)
        self.assertIn('background-color:', badge)
        self.assertIn('#', badge)  # Contains hex color
        
        # Test duration_display
        duration = admin_instance.duration_display(call_log)
        self.assertEqual(duration, '2:05')
        
        # Test interest_display
        interest = admin_instance.interest_display(call_log)
        self.assertEqual(interest.count('⭐'), 4)
    
    def test_emaillog_admin_display_methods(self):
        """Test EmailLog admin display methods"""
        from django.contrib import admin
        from .admin import EmailLogAdmin
        from django.utils import timezone
        
        email_log = EmailLog.objects.create(
            lead=self.lead,
            email_type=EmailLog.EmailType.WELCOME,
            subject='Welcome Email',
            opened_at=timezone.now()
        )
        
        admin_instance = EmailLogAdmin(EmailLog, admin.site)
        
        # Test email_type_badge
        badge = admin_instance.email_type_badge(email_log)
        self.assertIn('👋', badge)
        
        # Test opened_badge
        opened = admin_instance.opened_badge(email_log)
        self.assertIn('✓', opened)
        
        # Test clicked_badge (not clicked)
        clicked = admin_instance.clicked_badge(email_log)
        self.assertIn('-', clicked)


# ==========================
# REST API Tests
# ==========================

class LeadAPITest(APITestCase):
    """Tests for Lead API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.lead1 = Lead.objects.create(
            name='Test Lead 1',
            email='test1@example.com',
            telefon='0123456789',
            status=Lead.Status.NEW,
            source=Lead.Source.SCRAPER,
            quality_score=85,
            lead_type=Lead.LeadType.ACTIVE_SALESPERSON,
            company='Test Company 1',
            interest_level=4
        )
        
        self.lead2 = Lead.objects.create(
            name='Test Lead 2',
            email='test2@example.com',
            status=Lead.Status.INTERESTED,
            source=Lead.Source.LANDING_PAGE,
            quality_score=60,
            lead_type=Lead.LeadType.CANDIDATE
        )
    
    def test_list_leads(self):
        """Test listing all leads"""
        url = reverse('lead-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_leads_requires_auth(self):
        """Test that listing leads requires authentication"""
        self.client.force_authenticate(user=None)
        url = reverse('lead-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_lead_detail(self):
        """Test getting a specific lead"""
        url = reverse('lead-detail', kwargs={'pk': self.lead1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Lead 1')
        self.assertEqual(response.data['email'], 'test1@example.com')
        self.assertIn('call_logs', response.data)
        self.assertIn('email_logs', response.data)
    
    def test_create_lead(self):
        """Test creating a new lead"""
        url = reverse('lead-list')
        data = {
            'name': 'New Lead',
            'email': 'new@example.com',
            'telefon': '0987654321',
            'status': Lead.Status.NEW,
            'source': Lead.Source.MANUAL,
            'quality_score': 70
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lead.objects.count(), 3)
        self.assertEqual(response.data['name'], 'New Lead')
    
    def test_update_lead(self):
        """Test updating a lead"""
        url = reverse('lead-detail', kwargs={'pk': self.lead1.pk})
        data = {
            'name': 'Updated Lead',
            'email': self.lead1.email,
            'status': Lead.Status.CONTACTED,
            'quality_score': 90
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.name, 'Updated Lead')
        self.assertEqual(self.lead1.status, Lead.Status.CONTACTED)
    
    def test_delete_lead(self):
        """Test deleting a lead"""
        url = reverse('lead-detail', kwargs={'pk': self.lead1.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lead.objects.count(), 1)
    
    def test_filter_leads_by_status(self):
        """Test filtering leads by status"""
        url = reverse('lead-list')
        response = self.client.get(url, {'status': Lead.Status.NEW})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], Lead.Status.NEW)
    
    def test_filter_leads_by_source(self):
        """Test filtering leads by source"""
        url = reverse('lead-list')
        response = self.client.get(url, {'source': Lead.Source.SCRAPER})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['source'], Lead.Source.SCRAPER)
    
    def test_filter_leads_by_min_score(self):
        """Test filtering leads by minimum score"""
        url = reverse('lead-list')
        response = self.client.get(url, {'min_score': '70'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertGreaterEqual(response.data['results'][0]['quality_score'], 70)
    
    def test_filter_leads_by_has_phone(self):
        """Test filtering leads by has_phone"""
        url = reverse('lead-list')
        response = self.client.get(url, {'has_phone': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['results'][0]['telefon'])
    
    def test_search_leads(self):
        """Test searching leads"""
        url = reverse('lead-list')
        response = self.client.get(url, {'search': 'Test Lead 1'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('Test Lead 1', response.data['results'][0]['name'])
    
    def test_stats_endpoint(self):
        """Test the stats endpoint"""
        url = reverse('lead-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('today', response.data)
        self.assertIn('hot_leads', response.data)
        self.assertIn('by_status', response.data)
        self.assertIn('by_source', response.data)
        self.assertIn('avg_score', response.data)
        self.assertIn('funnel', response.data)
        self.assertEqual(response.data['total'], 2)
    
    def test_log_call_endpoint(self):
        """Test the log_call endpoint"""
        url = reverse('lead-log-call', kwargs={'pk': self.lead1.pk})
        data = {
            'outcome': CallLog.Outcome.CONNECTED,
            'duration_seconds': 180,
            'interest_level': 4,
            'notes': 'Very interested'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('call_log', response.data)
        self.assertIn('lead', response.data)
        self.assertEqual(response.data['call_log']['outcome'], CallLog.Outcome.CONNECTED)
        
        # Verify that the lead was updated
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.call_count, 1)
        self.assertEqual(self.lead1.interest_level, 4)
    
    def test_next_to_call_endpoint(self):
        """Test the next_to_call endpoint"""
        url = reverse('lead-next-to-call')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return the lead with phone number and highest quality score
        self.assertEqual(response.data['id'], self.lead1.id)
    
    def test_next_to_call_no_leads(self):
        """Test next_to_call when no leads are available"""
        # Update lead1 to remove phone
        self.lead1.telefon = None
        self.lead1.save()
        
        url = reverse('lead-next-to-call')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', response.data)


class CallLogAPITest(APITestCase):
    """Tests for CallLog API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com'
        )
        
        self.call_log = CallLog.objects.create(
            lead=self.lead,
            outcome=CallLog.Outcome.CONNECTED,
            duration_seconds=120,
            interest_level=3,
            called_by=self.user
        )
    
    def test_list_call_logs(self):
        """Test listing all call logs"""
        url = reverse('calllog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_call_logs_by_lead(self):
        """Test filtering call logs by lead"""
        url = reverse('calllog-list')
        response = self.client.get(url, {'lead': self.lead.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['lead'], self.lead.id)
    
    def test_create_call_log(self):
        """Test creating a new call log"""
        url = reverse('calllog-list')
        data = {
            'lead': self.lead.id,
            'outcome': CallLog.Outcome.VOICEMAIL,
            'duration_seconds': 0,
            'interest_level': 0,
            'notes': 'Left a message',
            'called_by': self.user.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CallLog.objects.count(), 2)


class EmailLogAPITest(APITestCase):
    """Tests for EmailLog API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com'
        )
        
        self.email_log = EmailLog.objects.create(
            lead=self.lead,
            email_type=EmailLog.EmailType.WELCOME,
            subject='Welcome Email'
        )
    
    def test_list_email_logs(self):
        """Test listing all email logs"""
        url = reverse('emaillog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_email_logs_by_lead(self):
        """Test filtering email logs by lead"""
        url = reverse('emaillog-list')
        response = self.client.get(url, {'lead': self.lead.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['lead'], self.lead.id)


class CSVImportAPITest(APITestCase):
    """Tests for CSV import endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.url = reverse('import-csv')
    
    def test_import_csv_success(self):
        """Test successful CSV import"""
        csv_content = """name,email,telefon,score,lead_type,company_name,rolle,region
John Doe,john@example.com,0123456789,85,active_salesperson,Company A,Sales Manager,Berlin
Jane Smith,jane@example.com,0987654321,75,candidate,Company B,Developer,Munich"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'leads.csv'
        
        response = self.client.post(self.url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['imported'], 2)
        self.assertEqual(Lead.objects.count(), 2)
    
    def test_import_csv_deduplication(self):
        """Test CSV import with deduplication"""
        # Create an existing lead
        Lead.objects.create(
            name='John Doe',
            email='john@example.com',
            quality_score=70
        )
        
        csv_content = """name,email,telefon,score,lead_type
John Doe,john@example.com,0123456789,85,active_salesperson
Jane Smith,jane@example.com,0987654321,75,candidate"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'leads.csv'
        
        response = self.client.post(self.url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['imported'], 1)
        self.assertEqual(data['updated'], 1)
        self.assertEqual(Lead.objects.count(), 2)
        
        # Verify that the score was updated
        updated_lead = Lead.objects.get(email='john@example.com')
        self.assertEqual(updated_lead.quality_score, 85)
    
    def test_import_csv_skip_no_contact(self):
        """Test CSV import skips leads without contact info"""
        csv_content = """name,email,telefon,score
John Doe,john@example.com,0123456789,85
No Contact,,,75"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'leads.csv'
        
        response = self.client.post(self.url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['imported'], 1)
        self.assertEqual(data['skipped'], 1)
    
    def test_import_csv_no_file(self):
        """Test CSV import without file"""
        response = self.client.post(self.url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)


class HealthCheckAPITest(APITestCase):
    """Tests for health check endpoint"""
    
    def test_health_check(self):
        """Test the health check endpoint"""
        url = reverse('api-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['service'], 'telis-recruitment-api')


class ImportScraperCSVCommandTest(TestCase):
    """Tests for import_scraper_csv management command"""
    
    def setUp(self):
        """Set up test data"""
        # Create a temporary directory for test CSV files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class SyncStatusModelTest(TestCase):
    """Tests for SyncStatus model"""
    
    def test_sync_status_creation(self):
        """Test that a sync status can be created"""
        sync_status = SyncStatus.objects.create(
            source='scraper_db',
            last_sync_at=timezone.now(),
            last_lead_id=100,
            leads_imported=50,
            leads_updated=10,
            leads_skipped=5
        )
        
        self.assertEqual(sync_status.source, 'scraper_db')
        self.assertEqual(sync_status.last_lead_id, 100)
        self.assertEqual(sync_status.leads_imported, 50)
        self.assertEqual(sync_status.leads_updated, 10)
        self.assertEqual(sync_status.leads_skipped, 5)
    
    def test_sync_status_str(self):
        """Test the string representation of sync status"""
        now = timezone.now()
        sync_status = SyncStatus.objects.create(
            source='scraper_db',
            last_sync_at=now,
            last_lead_id=50
        )
        
        expected = f"scraper_db (letzter Sync: {now})"
        self.assertEqual(str(sync_status), expected)
    
    def test_sync_status_unique_source(self):
        """Test that source is unique"""
        SyncStatus.objects.create(
            source='scraper_db',
            last_sync_at=timezone.now(),
            last_lead_id=50
        )
        
        # Try to create another with same source
        with self.assertRaises(Exception):
            SyncStatus.objects.create(
                source='scraper_db',
                last_sync_at=timezone.now(),
                last_lead_id=100
            )
    
    def test_sync_status_ordering(self):
        """Test that sync statuses are ordered by last_sync_at descending"""
        from datetime import timedelta
        
        now = timezone.now()
        old_sync = SyncStatus.objects.create(
            source='source_old',
            last_sync_at=now - timedelta(days=1),
            last_lead_id=50
        )
        
        new_sync = SyncStatus.objects.create(
            source='source_new',
            last_sync_at=now,
            last_lead_id=100
        )
        
        sync_list = list(SyncStatus.objects.all())
        self.assertEqual(sync_list[0], new_sync)  # Most recent first
        self.assertEqual(sync_list[1], old_sync)


class ImportScraperDBCommandTest(TestCase):
    """Tests for import_scraper_db management command"""
    
    def setUp(self):
        """Set up test data"""
        # Create a temporary directory for test database
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.test_db_path = self.temp_path / 'test_scraper.db'
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_scraper_db(self, leads_data):
        """Helper to create a test scraper database"""
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        
        # Create leads table with scraper schema
        cursor.execute("""
            CREATE TABLE leads(
                id INTEGER PRIMARY KEY,
                name TEXT,
                rolle TEXT,
                email TEXT,
                telefon TEXT,
                quelle TEXT,
                score INT,
                tags TEXT,
                region TEXT,
                role_guess TEXT,
                lead_type TEXT,
                company_name TEXT,
                location_specific TEXT,
                confidence_score INT,
                social_profile_url TEXT,
                last_updated TEXT
            )
        """)
        
        # Insert test data
        for lead in leads_data:
            cursor.execute("""
                INSERT INTO leads (
                    id, name, rolle, email, telefon, quelle, score, tags, region,
                    role_guess, lead_type, company_name, location_specific,
                    confidence_score, social_profile_url, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.get('id'),
                lead.get('name'),
                lead.get('rolle'),
                lead.get('email'),
                lead.get('telefon'),
                lead.get('quelle'),
                lead.get('score', 50),
                lead.get('tags'),
                lead.get('region'),
                lead.get('role_guess'),
                lead.get('lead_type'),
                lead.get('company_name'),
                lead.get('location_specific'),
                lead.get('confidence_score'),
                lead.get('social_profile_url'),
                lead.get('last_updated')
            ))
        
        conn.commit()
        conn.close()
    
    def test_import_new_leads_from_db(self):
        """Test importing new leads from scraper.db"""
        test_leads = [
            {
                'id': 1,
                'name': 'Max Mustermann',
                'email': 'max@example.com',
                'telefon': '0123456789',
                'score': 85,
                'company_name': 'Test GmbH',
                'role_guess': 'Vertriebsleiter',
                'location_specific': 'Köln',
                'lead_type': 'active_salesperson',
                'quelle': 'https://example.com/profile',
            },
            {
                'id': 2,
                'name': 'Anna Schmidt',
                'email': 'anna@example.com',
                'telefon': '0987654321',
                'score': 70,
                'company_name': 'Demo AG',
                'role_guess': 'Sales Manager',
                'lead_type': 'candidate',
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify leads were created
        self.assertEqual(Lead.objects.count(), 2)
        
        lead1 = Lead.objects.get(email='max@example.com')
        self.assertEqual(lead1.name, 'Max Mustermann')
        self.assertEqual(lead1.quality_score, 85)
        self.assertEqual(lead1.source, Lead.Source.SCRAPER)
        self.assertEqual(lead1.company, 'Test GmbH')
        self.assertEqual(lead1.role, 'Vertriebsleiter')
        self.assertEqual(lead1.location, 'Köln')
        self.assertEqual(lead1.lead_type, Lead.LeadType.ACTIVE_SALESPERSON)
        
        lead2 = Lead.objects.get(email='anna@example.com')
        self.assertEqual(lead2.name, 'Anna Schmidt')
        self.assertEqual(lead2.quality_score, 70)
        self.assertEqual(lead2.lead_type, Lead.LeadType.CANDIDATE)
        
        # Check sync status was created
        sync_status = SyncStatus.objects.get(source='scraper_db')
        self.assertEqual(sync_status.last_lead_id, 2)
        self.assertEqual(sync_status.leads_imported, 2)
        self.assertEqual(sync_status.leads_updated, 0)
        
        # Check output
        output = out.getvalue()
        self.assertIn('🆕 NEU:', output)
        self.assertIn('✅ Import abgeschlossen', output)
    
    def test_import_deduplication_by_email(self):
        """Test deduplication by email"""
        # Create existing lead
        Lead.objects.create(
            name='Existing Lead',
            email='test@example.com',
            quality_score=50
        )
        
        test_leads = [
            {
                'id': 1,
                'name': 'Updated Lead',
                'email': 'test@example.com',
                'score': 80,
                'company_name': 'New Company'
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify lead was updated
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 80)
        self.assertEqual(lead.company, 'New Company')
        
        # Check output shows update
        output = out.getvalue()
        self.assertIn('🔄 UPDATE:', output)
    
    def test_import_deduplication_by_phone(self):
        """Test deduplication by phone number"""
        # Create existing lead
        Lead.objects.create(
            name='Existing Lead',
            telefon='0123456789',
            quality_score=50
        )
        
        test_leads = [
            {
                'id': 1,
                'name': 'Updated Lead',
                'telefon': '0123456789',
                'score': 75
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify lead was updated
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 75)
    
    def test_import_skip_lower_score(self):
        """Test that lower scores don't update existing leads"""
        # Create existing lead with high score
        Lead.objects.create(
            name='High Score Lead',
            email='test@example.com',
            quality_score=90
        )
        
        test_leads = [
            {
                'id': 1,
                'name': 'Lower Score',
                'email': 'test@example.com',
                'score': 60
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify lead was not updated
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 90)
    
    def test_import_force_mode(self):
        """Test force mode reimports all leads"""
        # Create existing lead
        existing = Lead.objects.create(
            name='Existing',
            email='test@example.com',
            quality_score=50
        )
        
        # Create sync status
        SyncStatus.objects.create(
            source='scraper_db',
            last_sync_at=timezone.now(),
            last_lead_id=1,
            leads_imported=1
        )
        
        test_leads = [
            {
                'id': 1,
                'name': 'Existing',
                'email': 'test@example.com',
                'score': 80
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command with force
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), '--force', stdout=out)
        
        # Verify lead was updated even though last_lead_id was already 1
        lead = Lead.objects.get(email='test@example.com')
        self.assertEqual(lead.quality_score, 80)
        
        # Check output
        output = out.getvalue()
        self.assertIn('Force-Modus', output)
    
    def test_import_dry_run(self):
        """Test dry-run mode doesn't save changes"""
        test_leads = [
            {
                'id': 1,
                'name': 'Dry Run Lead',
                'email': 'dryrun@example.com',
                'score': 75
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command with dry-run
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), '--dry-run', stdout=out)
        
        # Verify no leads were created
        self.assertEqual(Lead.objects.count(), 0)
        
        # Verify no sync status was created
        self.assertEqual(SyncStatus.objects.count(), 0)
        
        # Check output shows dry run
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
    
    def test_import_incremental(self):
        """Test incremental import only imports new leads"""
        # First import
        test_leads = [
            {
                'id': 1,
                'name': 'Lead 1',
                'email': 'lead1@example.com',
                'score': 70
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        self.assertEqual(Lead.objects.count(), 1)
        
        # Add more leads to database
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leads (id, name, email, score)
            VALUES (2, 'Lead 2', 'lead2@example.com', 80)
        """)
        conn.commit()
        conn.close()
        
        # Second import (incremental)
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Should only import the new lead
        self.assertEqual(Lead.objects.count(), 2)
        
        output = out.getvalue()
        self.assertIn('Letzter Sync:', output)
        self.assertIn('Lead-ID: 1', output)
    
    def test_import_skip_no_contact(self):
        """Test that leads without email or phone are skipped"""
        test_leads = [
            {
                'id': 1,
                'name': 'No Contact',
                'score': 80
            },
            {
                'id': 2,
                'name': 'Has Email',
                'email': 'valid@example.com',
                'score': 70
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify only lead with contact was created
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.name, 'Has Email')
    
    def test_import_linkedin_url(self):
        """Test LinkedIn URL extraction"""
        test_leads = [
            {
                'id': 1,
                'name': 'LinkedIn User',
                'email': 'linkedin@example.com',
                'social_profile_url': 'https://linkedin.com/in/testuser',
                'score': 75
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify LinkedIn URL was extracted
        lead = Lead.objects.first()
        self.assertEqual(lead.linkedin_url, 'https://linkedin.com/in/testuser')
        self.assertIsNone(lead.xing_url)
    
    def test_import_xing_url(self):
        """Test XING URL extraction"""
        test_leads = [
            {
                'id': 1,
                'name': 'XING User',
                'email': 'xing@example.com',
                'social_profile_url': 'https://xing.com/profile/testuser',
                'score': 75
            }
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify XING URL was extracted
        lead = Lead.objects.first()
        self.assertEqual(lead.xing_url, 'https://xing.com/profile/testuser')
        self.assertIsNone(lead.linkedin_url)
    
    def test_import_lead_type_mapping(self):
        """Test lead type mapping from scraper to Django"""
        test_leads = [
            {'id': 1, 'name': 'Lead 1', 'email': 'lead1@example.com', 'lead_type': 'active_salesperson'},
            {'id': 2, 'name': 'Lead 2', 'email': 'lead2@example.com', 'lead_type': 'candidate'},
            {'id': 3, 'name': 'Lead 3', 'email': 'lead3@example.com', 'lead_type': 'freelancer'},
            {'id': 4, 'name': 'Lead 4', 'email': 'lead4@example.com', 'lead_type': 'unknown_type'},
        ]
        
        self._create_test_scraper_db(test_leads)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_db', '--db', str(self.test_db_path), stdout=out)
        
        # Verify lead types were mapped correctly
        lead1 = Lead.objects.get(email='lead1@example.com')
        self.assertEqual(lead1.lead_type, Lead.LeadType.ACTIVE_SALESPERSON)
        
        lead2 = Lead.objects.get(email='lead2@example.com')
        self.assertEqual(lead2.lead_type, Lead.LeadType.CANDIDATE)
        
        lead3 = Lead.objects.get(email='lead3@example.com')
        self.assertEqual(lead3.lead_type, Lead.LeadType.FREELANCER)
        
        # Unknown type should default to UNKNOWN
        lead4 = Lead.objects.get(email='lead4@example.com')
        self.assertEqual(lead4.lead_type, Lead.LeadType.UNKNOWN)
    
    def test_import_nonexistent_file(self):
        """Test error handling for non-existent file"""
        from django.core.management.base import CommandError
        
        with self.assertRaises(CommandError) as context:
            call_command('import_scraper_db', '--db', '/nonexistent/scraper.db')
        
        self.assertIn('nicht gefunden', str(context.exception))


class TriggerSyncAPITest(APITestCase):
    """Tests for trigger_sync API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('trigger-sync')
        
        # Create a temporary test database
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.test_db_path = self.temp_path / 'test_scraper.db'
        
        # Create test database
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE leads(
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                score INT
            )
        """)
        cursor.execute("""
            INSERT INTO leads (id, name, email, score)
            VALUES (1, 'Test Lead', 'test@example.com', 75)
        """)
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_trigger_sync_success(self):
        """Test successful sync trigger"""
        response = self.client.post(
            self.url,
            {'db_path': str(self.test_db_path)},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('message', response.data)
        self.assertIn('sync_status', response.data)
        
        # Verify lead was imported
        self.assertEqual(Lead.objects.count(), 1)
        
        # Verify sync status
        sync_status = SyncStatus.objects.get(source='scraper_db')
        self.assertEqual(sync_status.leads_imported, 1)
    
    def test_trigger_sync_requires_authentication(self):
        """Test that sync endpoint requires authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_trigger_sync_with_force(self):
        """Test sync with force parameter"""
        # First sync
        self.client.post(
            self.url,
            {'db_path': str(self.test_db_path)},
            format='json'
        )
        
        # Second sync with force
        response = self.client.post(
            self.url,
            {'db_path': str(self.test_db_path), 'force': True},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class ImportScraperCSVCommandTest(TestCase):
    """Tests for import_scraper_csv management command"""
    
    def setUp(self):
        """Set up test data"""
        # Create a temporary directory for test CSV files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_csv_file(self, filename, rows, delimiter=','):
        """Helper to create a test CSV file"""
        filepath = self.temp_path / filename
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=delimiter)
                writer.writeheader()
                writer.writerows(rows)
        return str(filepath)
    
    def test_import_new_leads(self):
        """Test importing new leads from CSV"""
        csv_data = [
            {
                'name': 'Max Mustermann',
                'email': 'max@example.com',
                'telefon': '0123456789',
                'score': '85',
                'company_name': 'Test GmbH',
                'rolle': 'Vertriebsleiter',
                'region': 'Köln'
            },
            {
                'name': 'Anna Schmidt',
                'email': 'anna@example.com',
                'telefon': '0987654321',
                'score': '70',
                'company_name': 'Demo AG',
                'rolle': 'Sales Manager'
            }
        ]
        
        csv_path = self._create_csv_file('test_leads.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify leads were created
        self.assertEqual(Lead.objects.count(), 2)
        
        lead1 = Lead.objects.get(email='max@example.com')
        self.assertEqual(lead1.name, 'Max Mustermann')
        self.assertEqual(lead1.quality_score, 85)
        self.assertEqual(lead1.source, Lead.Source.SCRAPER)
        self.assertEqual(lead1.company, 'Test GmbH')
        self.assertEqual(lead1.role, 'Vertriebsleiter')
        self.assertEqual(lead1.location, 'Köln')
        
        lead2 = Lead.objects.get(email='anna@example.com')
        self.assertEqual(lead2.name, 'Anna Schmidt')
        self.assertEqual(lead2.quality_score, 70)
        
        # Check output
        output = out.getvalue()
        self.assertIn('🆕 Neu importiert: 2', output)
        self.assertIn('✅ Import abgeschlossen', output)
    
    def test_import_with_semicolon_delimiter(self):
        """Test CSV import with semicolon delimiter"""
        csv_data = [
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'score': '60'
            }
        ]
        
        csv_path = self._create_csv_file('test_semicolon.csv', csv_data, delimiter=';')
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify lead was created
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.name, 'Test User')
    
    def test_import_duplicate_email(self):
        """Test deduplication by email"""
        # Create existing lead
        Lead.objects.create(
            name='Existing Lead',
            email='test@example.com',
            quality_score=50
        )
        
        csv_data = [
            {
                'name': 'Updated Lead',
                'email': 'test@example.com',
                'score': '80'
            }
        ]
        
        csv_path = self._create_csv_file('test_duplicate.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify lead was updated (higher score)
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 80)
        
        # Check output shows update
        output = out.getvalue()
        self.assertIn('🔄 Aktualisiert:   1', output)
    
    def test_import_duplicate_phone(self):
        """Test deduplication by phone number"""
        # Create existing lead
        Lead.objects.create(
            name='Existing Lead',
            telefon='0123456789',
            quality_score=50
        )
        
        csv_data = [
            {
                'name': 'Updated Lead',
                'telefon': '0123456789',
                'score': '75'
            }
        ]
        
        csv_path = self._create_csv_file('test_duplicate_phone.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify lead was updated
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 75)
    
    def test_import_skip_lower_score(self):
        """Test that lower scores are skipped without force-update"""
        # Create existing lead with high score
        Lead.objects.create(
            name='High Score Lead',
            email='test@example.com',
            quality_score=90
        )
        
        csv_data = [
            {
                'name': 'Lower Score',
                'email': 'test@example.com',
                'score': '60'
            }
        ]
        
        csv_path = self._create_csv_file('test_lower_score.csv', csv_data)
        
        # Run the command without force-update
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify lead was not updated
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 90)
        
        # Check output shows skipped
        output = out.getvalue()
        self.assertIn('⏭️  Übersprungen:   1', output)
    
    def test_import_force_update(self):
        """Test force-update flag updates even with lower score"""
        # Create existing lead
        Lead.objects.create(
            name='Existing Lead',
            email='test@example.com',
            quality_score=90
        )
        
        csv_data = [
            {
                'name': 'Updated Lead',
                'email': 'test@example.com',
                'score': '60'
            }
        ]
        
        csv_path = self._create_csv_file('test_force.csv', csv_data)
        
        # Run the command with force-update
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, force_update=True, stdout=out)
        
        # Verify lead was updated despite lower score
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 60)
    
    def test_import_dry_run(self):
        """Test dry-run mode doesn't save changes"""
        csv_data = [
            {
                'name': 'Dry Run Lead',
                'email': 'dryrun@example.com',
                'score': '75'
            }
        ]
        
        csv_path = self._create_csv_file('test_dryrun.csv', csv_data)
        
        # Run the command with dry-run
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, dry_run=True, stdout=out)
        
        # Verify no leads were created
        self.assertEqual(Lead.objects.count(), 0)
        
        # Check output shows dry run
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
    
    def test_import_field_mapping(self):
        """Test German field name mapping"""
        csv_data = [
            {
                'Name': 'Test Person',
                'E-Mail': 'person@example.com',
                'Telefon': '0123456789',
                'Score': '85',
                'Firma': 'Test Firma',
                'Position': 'Manager',
                'Standort': 'Berlin'
            }
        ]
        
        csv_path = self._create_csv_file('test_german.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify lead was created with mapped fields
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.name, 'Test Person')
        self.assertEqual(lead.email, 'person@example.com')
        self.assertEqual(lead.company, 'Test Firma')
        self.assertEqual(lead.role, 'Manager')
        self.assertEqual(lead.location, 'Berlin')
    
    def test_import_score_clamping(self):
        """Test that scores are clamped to 0-100 range"""
        csv_data = [
            {
                'name': 'High Score',
                'email': 'high@example.com',
                'score': '150'
            },
            {
                'name': 'Low Score',
                'email': 'low@example.com',
                'score': '-10'
            }
        ]
        
        csv_path = self._create_csv_file('test_clamp.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify scores are clamped
        lead_high = Lead.objects.get(email='high@example.com')
        self.assertEqual(lead_high.quality_score, 100)
        
        lead_low = Lead.objects.get(email='low@example.com')
        self.assertEqual(lead_low.quality_score, 0)
    
    def test_import_skip_no_contact(self):
        """Test that rows without email or phone are skipped"""
        csv_data = [
            {
                'name': 'No Contact',
                'email': '',
                'telefon': '',
                'score': '80'
            },
            {
                'name': 'Has Email',
                'email': 'valid@example.com',
                'telefon': '',
                'score': '70'
            }
        ]
        
        csv_path = self._create_csv_file('test_no_contact.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify only lead with contact was created
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.name, 'Has Email')
    
    def test_import_linkedin_url(self):
        """Test LinkedIn URL extraction"""
        csv_data = [
            {
                'name': 'LinkedIn User',
                'email': 'linkedin@example.com',
                'social_profile_url': 'https://linkedin.com/in/testuser',
                'score': '75'
            }
        ]
        
        csv_path = self._create_csv_file('test_linkedin.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify LinkedIn URL was extracted
        lead = Lead.objects.first()
        self.assertEqual(lead.linkedin_url, 'https://linkedin.com/in/testuser')
        self.assertIsNone(lead.xing_url)
    
    def test_import_xing_url(self):
        """Test XING URL extraction"""
        csv_data = [
            {
                'name': 'XING User',
                'email': 'xing@example.com',
                'social_profile_url': 'https://xing.com/profile/testuser',
                'score': '75'
            }
        ]
        
        csv_path = self._create_csv_file('test_xing.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify XING URL was extracted
        lead = Lead.objects.first()
        self.assertEqual(lead.xing_url, 'https://xing.com/profile/testuser')
        self.assertIsNone(lead.linkedin_url)
    
    def test_import_invalid_score(self):
        """Test handling of invalid score values"""
        csv_data = [
            {
                'name': 'Invalid Score',
                'email': 'invalid@example.com',
                'score': 'not_a_number'
            }
        ]
        
        csv_path = self._create_csv_file('test_invalid_score.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify lead was created with default score
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 50)
    
    def test_import_nonexistent_file(self):
        """Test error handling for non-existent file"""
        from django.core.management.base import CommandError
        
        with self.assertRaises(CommandError) as context:
            call_command('import_scraper_csv', '/nonexistent/file.csv')
        
        self.assertIn('nicht gefunden', str(context.exception))
    
    def test_import_update_partial_fields(self):
        """Test that update only fills missing fields"""
        # Create existing lead with some fields
        Lead.objects.create(
            name='Existing',
            email='test@example.com',
            quality_score=50,
            company='Old Company'
        )
        
        csv_data = [
            {
                'name': 'Updated',
                'email': 'test@example.com',
                'score': '80',
                'company_name': 'New Company',
                'rolle': 'New Role',
                'region': 'New Region'
            }
        ]
        
        csv_path = self._create_csv_file('test_partial.csv', csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', csv_path, stdout=out)
        
        # Verify company was NOT updated (already had value)
        # but role and location were added
        lead = Lead.objects.first()
        self.assertEqual(lead.quality_score, 80)
        self.assertEqual(lead.company, 'Old Company')  # Not updated
        self.assertEqual(lead.role, 'New Role')  # Added
        self.assertEqual(lead.location, 'New Region')  # Added
    
    def test_import_latin1_encoding(self):
        """Test Latin-1 encoding fallback"""
        csv_data = [
            {
                'name': 'Müller Größe',
                'email': 'mueller@example.com',
                'score': '75'
            }
        ]
        
        # Create CSV file with Latin-1 encoding
        filepath = self.temp_path / 'test_latin1.csv'
        with open(filepath, 'w', encoding='latin-1', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)
        
        # Run the command
        out = io.StringIO()
        call_command('import_scraper_csv', str(filepath), stdout=out)
        
        # Verify lead was created
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.email, 'mueller@example.com')
        
        # Check output mentions Latin-1
        output = out.getvalue()
        self.assertIn('Latin-1', output)


# ==========================
# Landing Page Tests
# ==========================

class LandingPageTest(TestCase):
    """Tests for landing page"""
    
    def test_landing_page_loads(self):
        """Test that landing page loads successfully"""
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TELIS Recruitment')
        self.assertContains(response, 'VERDIENE BIS ZU €7000/MONAT')
        self.assertContains(response, 'JETZT STARTEN')


class OptInAPITest(TestCase):
    """Tests for opt-in API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.url = '/api/opt-in/'
    
    def test_opt_in_creates_lead(self):
        """Test that opt-in creates a new lead"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'telefon': '0123456789'
        }
        
        response = self.client.post(
            self.url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('lead_id', data)
        
        # Verify lead was created
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.name, 'Test User')
        self.assertEqual(lead.email, 'test@example.com')
        self.assertEqual(lead.telefon, '0123456789')
        self.assertEqual(lead.source, Lead.Source.LANDING_PAGE)
        self.assertEqual(lead.status, Lead.Status.NEW)
        self.assertEqual(lead.quality_score, 70)
        self.assertEqual(lead.interest_level, 3)
    
    def test_opt_in_without_phone(self):
        """Test that opt-in works without phone number"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
        }
        
        response = self.client.post(
            self.url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Verify lead was created without phone
        lead = Lead.objects.first()
        self.assertIsNone(lead.telefon)
    
    def test_opt_in_duplicate_email(self):
        """Test that duplicate email updates existing lead"""
        # Create existing lead
        existing = Lead.objects.create(
            name='Existing User',
            email='test@example.com',
            source=Lead.Source.SCRAPER,
            quality_score=50,
            interest_level=1
        )
        
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'telefon': '0123456789'
        }
        
        response = self.client.post(
            self.url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Willkommen zurück!')
        
        # Verify no duplicate was created
        self.assertEqual(Lead.objects.count(), 1)
        
        # Verify lead was updated
        existing.refresh_from_db()
        self.assertEqual(existing.interest_level, 3)
        self.assertIn('Re-Opt-In', existing.source_detail)
    
    def test_opt_in_missing_name(self):
        """Test that opt-in requires name"""
        data = {
            'email': 'test@example.com',
        }
        
        response = self.client.post(
            self.url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Name', data['error'])
    
    def test_opt_in_missing_email(self):
        """Test that opt-in requires email"""
        data = {
            'name': 'Test User',
        }
        
        response = self.client.post(
            self.url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('E-Mail', data['error'])
    
    def test_opt_in_invalid_json(self):
        """Test that opt-in handles invalid JSON"""
        response = self.client.post(
            self.url, 
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


# ==========================
# Brevo Integration Tests
# ==========================

class BrevoIntegrationTest(TestCase):
    """Tests for Brevo email integration"""
    
    def test_brevo_module_imports_without_sdk(self):
        """Test that Brevo module imports gracefully without SDK installed"""
        from leads.services import brevo
        
        # Module should import successfully
        self.assertIsNotNone(brevo)
        
        # Should have BREVO_AVAILABLE flag
        self.assertIsInstance(brevo.BREVO_AVAILABLE, bool)
    
    def test_brevo_graceful_degradation(self):
        """Test that Brevo functions return False/None when SDK not available"""
        from leads.services import brevo
        
        # Mock BREVO_AVAILABLE to False
        original_available = brevo.BREVO_AVAILABLE
        try:
            brevo.BREVO_AVAILABLE = False
            
            # get_brevo_config should return None
            config = brevo.get_brevo_config()
            self.assertIsNone(config)
            
            # create_or_update_contact should return False
            result = brevo.create_or_update_contact('test@example.com', {'VORNAME': 'Test'})
            self.assertFalse(result)
            
            # send_transactional_email should return None
            message_id = brevo.send_transactional_email('test@example.com', 'Test', 1)
            self.assertIsNone(message_id)
            
        finally:
            brevo.BREVO_AVAILABLE = original_available
    
    def test_signal_does_not_break_without_brevo(self):
        """Test that lead creation works even when Brevo is not configured"""
        from django.conf import settings
        
        # Temporarily remove Brevo API key
        original_api_key = getattr(settings, 'BREVO_API_KEY', None)
        try:
            settings.BREVO_API_KEY = None
            
            # Create a landing page lead
            lead = Lead.objects.create(
                name='Signal Test User',
                email='signaltest@example.com',
                source=Lead.Source.LANDING_PAGE,
                quality_score=70,
                interest_level=3
            )
            
            # Lead should be created successfully
            self.assertIsNotNone(lead.id)
            self.assertEqual(lead.email, 'signaltest@example.com')
            
        finally:
            settings.BREVO_API_KEY = original_api_key


class BrevoWebhookTest(TestCase):
    """Tests for Brevo webhook endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.url = '/api/webhooks/brevo/'
        self.lead = Lead.objects.create(
            name='Webhook Test Lead',
            email='webhook@example.com',
            source=Lead.Source.LANDING_PAGE
        )
    
    def test_webhook_email_opened(self):
        """Test webhook for email opened event"""
        data = {
            'event': 'opened',
            'email': 'webhook@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['event'], 'opened')
        
        # Verify lead was updated
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.email_opens, 1)
    
    def test_webhook_email_clicked(self):
        """Test webhook for email clicked event"""
        data = {
            'event': 'click',
            'email': 'webhook@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify lead was updated
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.email_clicks, 1)
    
    def test_webhook_hard_bounce(self):
        """Test webhook for hard bounce event"""
        data = {
            'event': 'hard_bounce',
            'email': 'webhook@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify lead status was updated
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.INVALID)
        self.assertIn('Hard Bounce', self.lead.notes)
    
    def test_webhook_unsubscribed(self):
        """Test webhook for unsubscribe event"""
        self.lead.interest_level = 5
        self.lead.save()
        
        data = {
            'event': 'unsubscribed',
            'email': 'webhook@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify lead interest was set to 0
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.interest_level, 0)
        self.assertIn('Abgemeldet', self.lead.notes)
    
    def test_webhook_missing_email(self):
        """Test webhook with missing email"""
        data = {
            'event': 'opened'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertIn('error', result)
    
    def test_webhook_lead_not_found(self):
        """Test webhook for non-existent lead"""
        data = {
            'event': 'opened',
            'email': 'nonexistent@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'ignored')
        self.assertEqual(result['reason'], 'lead_not_found')
    
    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON"""
        response = self.client.post(
            self.url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertIn('error', result)


class BrevoWebhookSecurityTest(TestCase):
    """Tests for Brevo webhook HMAC signature verification"""
    
    def setUp(self):
        """Set up test data"""
        self.url = '/api/webhooks/brevo/'
        self.lead = Lead.objects.create(
            name='Security Test Lead',
            email='security@example.com',
            source=Lead.Source.LANDING_PAGE
        )
        self.webhook_secret = 'test-webhook-secret-12345'
    
    def _generate_signature(self, body, secret):
        """Helper to generate HMAC signature"""
        import hmac
        import hashlib
        return hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
    
    def test_webhook_with_valid_signature(self):
        """Test webhook accepts valid HMAC signature"""
        from django.conf import settings
        original_secret = getattr(settings, 'BREVO_WEBHOOK_SECRET', None)
        
        try:
            settings.BREVO_WEBHOOK_SECRET = self.webhook_secret
            
            data = {
                'event': 'opened',
                'email': 'security@example.com'
            }
            body = json.dumps(data).encode()
            signature = self._generate_signature(body, self.webhook_secret)
            
            response = self.client.post(
                self.url,
                data=body,
                content_type='application/json',
                HTTP_X_SIB_SIGNATURE=signature
            )
            
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertEqual(result['status'], 'ok')
            
        finally:
            if original_secret is None:
                delattr(settings, 'BREVO_WEBHOOK_SECRET')
            else:
                settings.BREVO_WEBHOOK_SECRET = original_secret
    
    def test_webhook_with_invalid_signature(self):
        """Test webhook rejects invalid HMAC signature"""
        from django.conf import settings
        original_secret = getattr(settings, 'BREVO_WEBHOOK_SECRET', None)
        
        try:
            settings.BREVO_WEBHOOK_SECRET = self.webhook_secret
            
            data = {
                'event': 'opened',
                'email': 'security@example.com'
            }
            
            response = self.client.post(
                self.url,
                data=json.dumps(data),
                content_type='application/json',
                HTTP_X_SIB_SIGNATURE='invalid-signature-12345'
            )
            
            self.assertEqual(response.status_code, 401)
            result = response.json()
            self.assertEqual(result['status'], 'error')
            self.assertIn('signature', result['message'].lower())
            
        finally:
            if original_secret is None:
                delattr(settings, 'BREVO_WEBHOOK_SECRET')
            else:
                settings.BREVO_WEBHOOK_SECRET = original_secret
    
    def test_webhook_without_signature_when_secret_configured(self):
        """Test webhook rejects requests without signature when secret is configured"""
        from django.conf import settings
        original_secret = getattr(settings, 'BREVO_WEBHOOK_SECRET', None)
        
        try:
            settings.BREVO_WEBHOOK_SECRET = self.webhook_secret
            
            data = {
                'event': 'opened',
                'email': 'security@example.com'
            }
            
            response = self.client.post(
                self.url,
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 401)
            result = response.json()
            self.assertEqual(result['status'], 'error')
            self.assertIn('signature', result['message'].lower())
            
        finally:
            if original_secret is None:
                delattr(settings, 'BREVO_WEBHOOK_SECRET')
            else:
                settings.BREVO_WEBHOOK_SECRET = original_secret
    
    def test_webhook_without_secret_configured_allows_requests(self):
        """Test webhook allows requests without signature when secret not configured (graceful degradation)"""
        from django.conf import settings
        original_secret = getattr(settings, 'BREVO_WEBHOOK_SECRET', None)
        
        try:
            # Ensure secret is not set
            if hasattr(settings, 'BREVO_WEBHOOK_SECRET'):
                delattr(settings, 'BREVO_WEBHOOK_SECRET')
            
            data = {
                'event': 'opened',
                'email': 'security@example.com'
            }
            
            response = self.client.post(
                self.url,
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Should succeed but with warning logged
            self.assertEqual(response.status_code, 200)
            
        finally:
            if original_secret:
                settings.BREVO_WEBHOOK_SECRET = original_secret


class TriggerSyncSecurityTest(APITestCase):
    """Tests for trigger_sync path traversal protection"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('trigger-sync')
        
        # Create a temporary test database
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.test_db_path = self.temp_path / 'test_scraper.db'
        
        # Create test database
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE leads(
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                score INT
            )
        """)
        cursor.execute("""
            INSERT INTO leads (id, name, email, score)
            VALUES (1, 'Test Lead', 'test@example.com', 75)
        """)
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Reset global cache (thread-safe)
        from leads import views
        with views._allowed_db_paths_lock:
            views.ALLOWED_DB_PATHS = None
    
    def test_trigger_sync_rejects_path_traversal_attempt(self):
        """Test that path traversal attempts are rejected"""
        response = self.client.post(
            self.url,
            {'db_path': '../../../etc/passwd'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Unauthorized', response.data['error'])
    
    def test_trigger_sync_rejects_absolute_unauthorized_path(self):
        """Test that absolute unauthorized paths are rejected"""
        response = self.client.post(
            self.url,
            {'db_path': '/etc/passwd'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Unauthorized', response.data['error'])
    
    def test_trigger_sync_rejects_non_db_file(self):
        """Test that non-.db files are rejected"""
        response = self.client.post(
            self.url,
            {'db_path': str(self.temp_path / 'test.txt')},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('extension', response.data['error'].lower())
    
    def test_trigger_sync_does_not_expose_full_path_in_errors(self):
        """Test that error messages don't expose full file paths"""
        response = self.client.post(
            self.url,
            {'db_path': '/nonexistent/path/database.db'},
            format='json'
        )
        
        # Should return error without exposing full path
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        error_msg = response.data['error']
        # Error message should not contain full path
        self.assertNotIn('/nonexistent/path/', error_msg)
    
    def test_trigger_sync_allows_whitelisted_path(self):
        """Test that whitelisted paths are allowed"""
        from django.conf import settings
        original_paths = getattr(settings, 'ALLOWED_SCRAPER_DB_PATHS', None)
        
        try:
            # Add test path to whitelist
            settings.ALLOWED_SCRAPER_DB_PATHS = [str(self.test_db_path)]
            
            # Reset cache to pick up new settings (thread-safe)
            from leads import views
            with views._allowed_db_paths_lock:
                views.ALLOWED_DB_PATHS = None
            
            response = self.client.post(
                self.url,
                {'db_path': str(self.test_db_path)},
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            
        finally:
            if original_paths is None:
                if hasattr(settings, 'ALLOWED_SCRAPER_DB_PATHS'):
                    delattr(settings, 'ALLOWED_SCRAPER_DB_PATHS')
            else:
                settings.ALLOWED_SCRAPER_DB_PATHS = original_paths
    
    def test_trigger_sync_uses_default_path_when_not_specified(self):
        """Test that default path is used when db_path is not specified"""
        response = self.client.post(
            self.url,
            {},
            format='json'
        )
        
        # May return 404 if default doesn't exist, but shouldn't be a security error
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        if response.status_code == status.HTTP_404_NOT_FOUND:
            self.assertEqual(response.data['error'], 'Database not found')


# ===============================
# CRM Phase 1: Authentication and Permission Tests
# ===============================

class AuthenticationTest(TestCase):
    """Tests for authentication system"""
    
    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anmelden')
        self.assertContains(response, 'TELIS')
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/crm/'))
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/login/', {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        # Should stay on login page - either 200 or redirect back to login with error
        # Django LoginView returns 200 with form errors
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 200:
            # Check for error indication in the response
            content = response.content.decode()
            # Either our custom error message or Django's default form errors
            self.assertTrue('Ungültige' in content or 'error' in content.lower() or 'form' in content.lower())
    
    def test_logout_redirects_to_login(self):
        """Test that logout redirects to login page"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/logout/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/')
    
    def test_crm_requires_login(self):
        """Test that CRM pages require login"""
        response = self.client.get('/crm/')
        
        # Should redirect to login with next parameter
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertIn('next=/crm/', response.url)
    
    def test_login_redirect_to_next_parameter(self):
        """Test that login redirects to 'next' parameter"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        response = self.client.post('/login/?next=/crm/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/crm/'))


class UserGroupsAndPermissionsTest(TestCase):
    """Tests for user groups and permissions"""
    
    def setUp(self):
        """Set up test groups using management command"""
        call_command('setup_groups')
    
    def test_setup_groups_command_creates_groups(self):
        """Test that setup_groups command creates all required groups"""
        from django.contrib.auth.models import Group
        
        groups = Group.objects.all()
        group_names = [g.name for g in groups]
        
        self.assertIn('Admin', group_names)
        self.assertIn('Manager', group_names)
        self.assertIn('Telefonist', group_names)
    
    def test_setup_groups_command_is_idempotent(self):
        """Test that running setup_groups multiple times doesn't create duplicates"""
        from django.contrib.auth.models import Group
        
        # Run command again
        call_command('setup_groups')
        
        # Should still only have 3 groups
        groups = Group.objects.all()
        self.assertEqual(groups.count(), 3)
    
    def test_admin_group_has_all_permissions(self):
        """Test that Admin group has all necessary permissions"""
        from django.contrib.auth.models import Group
        
        admin_group = Group.objects.get(name='Admin')
        
        # Should have permissions on Lead, CallLog, EmailLog, and User models
        permissions = admin_group.permissions.all()
        self.assertGreater(permissions.count(), 0)
        
        # Check for some key permissions
        permission_codenames = [p.codename for p in permissions]
        self.assertIn('view_lead', permission_codenames)
        self.assertIn('change_lead', permission_codenames)
        self.assertIn('delete_lead', permission_codenames)
    
    def test_manager_group_permissions(self):
        """Test that Manager group has appropriate permissions"""
        from django.contrib.auth.models import Group
        
        manager_group = Group.objects.get(name='Manager')
        permissions = manager_group.permissions.all()
        
        permission_codenames = [p.codename for p in permissions]
        
        # Manager should be able to view and change leads
        self.assertIn('view_lead', permission_codenames)
        self.assertIn('change_lead', permission_codenames)
        
        # Manager should NOT be able to delete leads
        self.assertNotIn('delete_lead', permission_codenames)
    
    def test_telefonist_group_permissions(self):
        """Test that Telefonist group has limited permissions"""
        from django.contrib.auth.models import Group
        
        telefonist_group = Group.objects.get(name='Telefonist')
        permissions = telefonist_group.permissions.all()
        
        permission_codenames = [p.codename for p in permissions]
        
        # Telefonist should be able to view leads and add call logs
        self.assertIn('view_lead', permission_codenames)
        self.assertIn('add_calllog', permission_codenames)
        
        # Telefonist should NOT be able to change or delete leads
        self.assertNotIn('change_lead', permission_codenames)
        self.assertNotIn('delete_lead', permission_codenames)


class CRMDashboardTest(TestCase):
    """Tests for CRM dashboard views"""
    
    def setUp(self):
        """Set up test user and groups"""
        call_command('setup_groups')
        
        from django.contrib.auth.models import Group
        
        # Create test users with different roles
        self.admin_user = User.objects.create_user(username='admin', password='admin123')
        admin_group = Group.objects.get(name='Admin')
        self.admin_user.groups.add(admin_group)
        
        self.manager_user = User.objects.create_user(username='manager', password='manager123')
        manager_group = Group.objects.get(name='Manager')
        self.manager_user.groups.add(manager_group)
        
        self.telefonist_user = User.objects.create_user(username='telefonist', password='telefonist123')
        telefonist_group = Group.objects.get(name='Telefonist')
        self.telefonist_user.groups.add(telefonist_group)
        
        # Create some test leads
        Lead.objects.create(
            name='Test Lead 1',
            email='lead1@example.com',
            quality_score=85,
            interest_level=4,
            assigned_to=self.telefonist_user
        )
        Lead.objects.create(
            name='Test Lead 2',
            email='lead2@example.com',
            quality_score=90,
            interest_level=5
        )
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get('/crm/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
    
    def test_admin_can_access_dashboard(self):
        """Test that admin user can access dashboard"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Willkommen')
        self.assertContains(response, 'Admin')
    
    def test_manager_can_access_dashboard(self):
        """Test that manager user can access dashboard"""
        self.client.login(username='manager', password='manager123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Willkommen')
        self.assertContains(response, 'Manager')
    
    def test_telefonist_can_access_dashboard(self):
        """Test that telefonist user can access dashboard"""
        self.client.login(username='telefonist', password='telefonist123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Willkommen')
        self.assertContains(response, 'Telefonist')
    
    def test_dashboard_shows_correct_stats_for_admin(self):
        """Test that admin sees all leads in dashboard stats"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        
        # Admin should see all leads
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['hot_leads'], 2)  # Both leads have high score and interest
    
    def test_dashboard_shows_correct_stats_for_telefonist(self):
        """Test that telefonist only sees assigned leads in dashboard stats"""
        self.client.login(username='telefonist', password='telefonist123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        
        # Telefonist should only see assigned leads
        stats = response.context['stats']
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['hot_leads'], 1)
    
    def test_dashboard_displays_user_role(self):
        """Test that dashboard displays user's role correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        user_role = response.context['user_role']
        self.assertEqual(user_role, 'Admin')
    
    def test_sidebar_shows_admin_sections_for_admin(self):
        """Test that admin users see admin-only sections in sidebar"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        # Admin should see settings and user management
        self.assertContains(response, 'Einstellungen')
        self.assertContains(response, 'Benutzer')
    
    def test_sidebar_hides_admin_sections_for_telefonist(self):
        """Test that telefonist users don't see admin sections in sidebar"""
        self.client.login(username='telefonist', password='telefonist123')
        response = self.client.get('/crm/')
        
        self.assertEqual(response.status_code, 200)
        # Check for the admin section header - should not be present
        content = response.content.decode()
        # Admin sections should either not exist or be hidden
        # Since we conditionally render them based on user role, they won't be in the HTML
        self.assertNotIn('Administration', content)


class DashboardAPITest(APITestCase):
    """Tests for Dashboard API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create user groups
        from django.contrib.auth.models import Group
        admin_group = Group.objects.create(name='Admin')
        manager_group = Group.objects.create(name='Manager')
        telefonist_group = Group.objects.create(name='Telefonist')
        
        # Create users
        self.admin = User.objects.create_user(username='admin', password='admin123')
        self.admin.groups.add(admin_group)
        
        self.manager = User.objects.create_user(username='manager', password='manager123')
        self.manager.groups.add(manager_group)
        
        self.telefonist = User.objects.create_user(username='telefonist', password='telefonist123')
        self.telefonist.groups.add(telefonist_group)
        
        # Create test leads
        for i in range(10):
            Lead.objects.create(
                name=f'Lead {i}',
                email=f'lead{i}@example.com',
                telefon=f'012345678{i}',
                status=Lead.Status.NEW if i < 5 else Lead.Status.CONTACTED,
                source=Lead.Source.SCRAPER if i < 7 else Lead.Source.LANDING_PAGE,
                quality_score=50 + (i * 5),
                assigned_to=self.telefonist if i < 5 else self.admin
            )
        
        # Create some call logs
        lead = Lead.objects.first()
        CallLog.objects.create(
            lead=lead,
            outcome=CallLog.Outcome.CONNECTED,
            duration_seconds=120,
            called_by=self.telefonist
        )
    
    def test_dashboard_stats_requires_authentication(self):
        """Test that dashboard stats endpoint requires authentication"""
        url = '/crm/api/dashboard-stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_dashboard_stats_for_admin(self):
        """Test dashboard stats endpoint for admin user"""
        self.client.force_authenticate(user=self.admin)
        url = '/crm/api/dashboard-stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('leads_total', response.data)
        self.assertIn('leads_today', response.data)
        self.assertIn('calls_today', response.data)
        self.assertIn('conversion_rate', response.data)
        self.assertIn('hot_leads', response.data)
        self.assertIn('trend_7_days', response.data)
        self.assertIn('status_distribution', response.data)
        self.assertIn('source_distribution', response.data)
        
        # Admin sees all leads
        self.assertEqual(response.data['leads_total'], 10)
    
    def test_dashboard_stats_for_telefonist(self):
        """Test dashboard stats endpoint for telefonist user (filtered)"""
        self.client.force_authenticate(user=self.telefonist)
        url = '/crm/api/dashboard-stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Telefonist only sees assigned leads
        self.assertEqual(response.data['leads_total'], 5)
    
    def test_activity_feed_requires_authentication(self):
        """Test that activity feed endpoint requires authentication"""
        url = '/crm/api/activity-feed/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_activity_feed_returns_recent_activities(self):
        """Test activity feed returns recent activities"""
        self.client.force_authenticate(user=self.admin)
        url = '/crm/api/activity-feed/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Should have at least one activity (call log created in setUp)
        if len(response.data) > 0:
            activity = response.data[0]
            self.assertIn('type', activity)
            self.assertIn('icon', activity)
            self.assertIn('message', activity)
            self.assertIn('timestamp', activity)
            self.assertIn('time_ago', activity)
    
    def test_team_performance_requires_authentication(self):
        """Test that team performance endpoint requires authentication"""
        url = '/crm/api/team-performance/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_team_performance_for_admin(self):
        """Test team performance endpoint for admin user"""
        self.client.force_authenticate(user=self.admin)
        url = '/crm/api/team-performance/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Should have telefonist in the list
        if len(response.data) > 0:
            perf = response.data[0]
            self.assertIn('user_id', perf)
            self.assertIn('username', perf)
            self.assertIn('calls_today', perf)
            self.assertIn('conversions_week', perf)
    
    def test_team_performance_forbidden_for_telefonist(self):
        """Test team performance endpoint is forbidden for telefonist"""
        self.client.force_authenticate(user=self.telefonist)
        url = '/crm/api/team-performance/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_team_performance_allowed_for_manager(self):
        """Test team performance endpoint is allowed for manager"""
        self.client.force_authenticate(user=self.manager)
        url = '/crm/api/team-performance/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LeadManagementViewTest(TestCase):
    """Tests for Lead Management Views"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Group
        admin_group = Group.objects.create(name='Admin')
        
        self.admin = User.objects.create_user(username='admin', password='admin123')
        self.admin.groups.add(admin_group)
        
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com',
            telefon='0123456789',
            status=Lead.Status.NEW,
            quality_score=75
        )
    
    def test_crm_leads_view_requires_login(self):
        """Test that leads view requires login"""
        response = self.client.get('/crm/leads/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_crm_leads_view_for_authenticated_user(self):
        """Test that authenticated users can access leads view"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/crm/leads/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crm/leads.html')
    
    def test_crm_lead_detail_requires_login(self):
        """Test that lead detail view requires login"""
        response = self.client.get(f'/crm/leads/{self.lead.id}/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_crm_lead_detail_for_authenticated_user(self):
        """Test that authenticated users can access lead detail"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(f'/crm/leads/{self.lead.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('lead', response.context)
        self.assertEqual(response.context['lead'], self.lead)
