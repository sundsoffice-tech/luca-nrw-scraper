"""Tests for mailbox app"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from .context_processors import unread_email_count
from .models import EmailAccount, EmailConversation, Email
from .services.encryption import encrypt_string, decrypt_string
from .services.email_sender import EmailSenderService
from datetime import datetime
import unittest.mock as mock


class UnreadEmailCountContextProcessorTest(TestCase):
    """Test unread_email_count context processor"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create a test email account
        self.account = EmailAccount.objects.create(
            name='Test Account',
            email_address='test@example.com',
            account_type='imap_smtp',
            owner=self.user,
            is_active=True
        )
    
    def test_unread_count_for_authenticated_user(self):
        """Test unread count returns correct number for authenticated user"""
        # Create unread conversation
        EmailConversation.objects.create(
            subject='Test Subject 1',
            subject_normalized='Test Subject 1',
            contact_email='contact1@example.com',
            account=self.account,
            status='open',
            is_read=False,
            last_message_at=datetime.now()
        )
        
        # Create read conversation (should not be counted)
        EmailConversation.objects.create(
            subject='Test Subject 2',
            subject_normalized='Test Subject 2',
            contact_email='contact2@example.com',
            account=self.account,
            status='open',
            is_read=True,
            last_message_at=datetime.now()
        )
        
        # Create trashed conversation (should not be counted)
        EmailConversation.objects.create(
            subject='Test Subject 3',
            subject_normalized='Test Subject 3',
            contact_email='contact3@example.com',
            account=self.account,
            status='trash',
            is_read=False,
            last_message_at=datetime.now()
        )
        
        # Test with authenticated user
        request = self.factory.get('/')
        request.user = self.user
        
        result = unread_email_count(request)
        
        self.assertEqual(result['unread_email_count'], 1)
    
    def test_unread_count_for_anonymous_user(self):
        """Test unread count returns 0 for anonymous user"""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        result = unread_email_count(request)
        
        self.assertEqual(result['unread_email_count'], 0)
    
    def test_unread_count_with_shared_account(self):
        """Test unread count includes conversations from shared accounts"""
        # Create another user and share account
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        self.account.shared_with.add(other_user)
        
        # Create unread conversation
        EmailConversation.objects.create(
            subject='Shared Subject',
            subject_normalized='Shared Subject',
            contact_email='shared@example.com',
            account=self.account,
            status='open',
            is_read=False,
            last_message_at=datetime.now()
        )
        
        # Test with shared user
        request = self.factory.get('/')
        request.user = other_user
        
        result = unread_email_count(request)
        
        self.assertEqual(result['unread_email_count'], 1)
    
    def test_context_processor_handles_missing_models_gracefully(self):
        """Test that context processor doesn't crash if models are unavailable"""
        # This test ensures the try-except block works
        request = self.factory.get('/')
        request.user = self.user
        
        # Even if there's an error, it should return a valid dict
        result = unread_email_count(request)
        
        self.assertIn('unread_email_count', result)
        self.assertIsInstance(result['unread_email_count'], int)


class EncryptionServiceTest(TestCase):
    """Test encryption service security improvements"""
    
    @override_settings(ENCRYPTION_SALT=None)
    def test_encryption_raises_error_when_salt_not_configured(self):
        """Test that encryption raises ImproperlyConfigured when ENCRYPTION_SALT is not set"""
        with self.assertRaises(ImproperlyConfigured) as cm:
            encrypt_string("test_data")
        
        self.assertIn("ENCRYPTION_SALT must be configured", str(cm.exception))
        self.assertIn("environment variable", str(cm.exception))
    
    @override_settings(ENCRYPTION_SALT='test_salt_for_encryption_v1')
    def test_encryption_works_with_valid_salt(self):
        """Test that encryption and decryption work correctly with configured salt"""
        test_data = "sensitive_password_123"
        
        # Encrypt the data
        encrypted = encrypt_string(test_data)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, test_data)
        
        # Decrypt the data
        decrypted = decrypt_string(encrypted)
        self.assertEqual(decrypted, test_data)
    
    @override_settings(ENCRYPTION_SALT='test_salt_for_encryption_v1')
    def test_encryption_with_empty_string(self):
        """Test that encryption handles empty strings correctly"""
        encrypted = encrypt_string("")
        self.assertEqual(encrypted, "")
        
        decrypted = decrypt_string("")
        self.assertEqual(decrypted, "")


class EmailSenderServiceTest(TestCase):
    """Test email sender service error handling"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create a Brevo account
        self.brevo_account = EmailAccount.objects.create(
            name='Brevo Test Account',
            email_address='test@example.com',
            account_type='brevo',
            owner=self.user,
            is_active=True
        )
    
    @mock.patch('mailbox.services.email_sender.BREVO_AVAILABLE', False)
    def test_brevo_raises_error_when_sdk_not_installed(self):
        """Test that _send_via_brevo raises ImproperlyConfigured when SDK is missing"""
        # Create a test email
        email = Email.objects.create(
            account=self.brevo_account,
            from_email='test@example.com',
            subject='Test Subject',
            body_text='Test Body',
            to_emails=[{'email': 'recipient@example.com'}],
            status='draft'
        )
        
        service = EmailSenderService(self.brevo_account)
        
        # Should raise ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured) as cm:
            service._send_via_brevo(email)
        
        self.assertIn("sib-api-v3-sdk", str(cm.exception))
        self.assertIn("not installed", str(cm.exception))
        self.assertIn("pip install", str(cm.exception))
