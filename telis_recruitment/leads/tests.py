from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import io
import csv
import tempfile
from pathlib import Path
from .models import Lead, CallLog, EmailLog


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

