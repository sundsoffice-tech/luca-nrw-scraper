from django.test import TestCase
from django.contrib.auth.models import User
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
        
        # Test status_badge
        badge = admin_instance.status_badge(self.lead)
        self.assertIn(self.lead.get_status_display(), badge)
        self.assertIn('#ef4444', badge)  # NEW status color
        
        # Test source_badge
        source = admin_instance.source_badge(self.lead)
        self.assertIn('🤖', source)  # Scraper icon
        
        # Test quality_bar
        quality = admin_instance.quality_bar(self.lead)
        self.assertIn('85', quality)
        self.assertIn('#22c55e', quality)  # Green for score >= 80
        
        # Test interest_badge
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
        
        # Test outcome_badge
        badge = admin_instance.outcome_badge(call_log)
        self.assertIn(call_log.get_outcome_display(), badge)
        self.assertIn('#22c55e', badge)  # CONNECTED color
        
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
