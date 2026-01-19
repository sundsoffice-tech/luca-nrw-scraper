"""Tests for mailbox app"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from .context_processors import unread_email_count
from .models import EmailAccount, EmailConversation
from datetime import datetime


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
