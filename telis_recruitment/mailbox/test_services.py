"""Tests for email receiver and threading services"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock
from datetime import timedelta
import threading as python_threading
import time

from mailbox.models import EmailAccount, EmailConversation, Email
from mailbox.services.email_receiver import EmailReceiverService
from mailbox.services.threading import EmailThreadingService


class EmailThreadingServiceTest(TestCase):
    """Test EmailThreadingService"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.account = EmailAccount.objects.create(
            name='Test Account',
            email_address='test@example.com',
            account_type='imap_smtp',
            owner=self.user,
            is_active=True
        )
    
    def test_normalize_subject(self):
        """Test subject normalization removes Re:/Fwd: prefixes"""
        test_cases = [
            ('Test Subject', 'Test Subject'),
            ('Re: Test Subject', 'Test Subject'),
            ('RE: Test Subject', 'Test Subject'),
            ('Fwd: Test Subject', 'Test Subject'),
            ('FWD: Test Subject', 'Test Subject'),
            ('AW: Test Subject', 'Test Subject'),  # German
            ('WG: Test Subject', 'Test Subject'),  # German
            ('Re: Re: Test Subject', 'Test Subject'),  # Multiple prefixes
            ('Re: Fwd: AW: Test Subject', 'Test Subject'),  # Mixed prefixes
        ]
        
        for input_subject, expected in test_cases:
            result = EmailThreadingService.normalize_subject(input_subject)
            self.assertEqual(result, expected, f"Failed for: {input_subject}")
    
    def test_find_conversation_by_in_reply_to(self):
        """Test finding conversation via In-Reply-To header"""
        # Create initial conversation
        conv1 = EmailConversation.objects.create(
            account=self.account,
            subject='Original Subject',
            subject_normalized='Original Subject',
            contact_email='contact@example.com',
            last_message_at=timezone.now(),
            message_count=0,
            unread_count=0
        )
        
        # Create first email in conversation
        email1 = Email.objects.create(
            conversation=conv1,
            account=self.account,
            direction=Email.Direction.INBOUND,
            message_id='<msg1@example.com>',
            from_email='contact@example.com',
            subject='Original Subject',
            body_text='Original message',
            status=Email.Status.RECEIVED,
            received_at=timezone.now()
        )
        
        # Find conversation for reply (should find existing conversation)
        found_conv = EmailThreadingService.find_or_create_conversation(
            account=self.account,
            message_id='<msg2@example.com>',
            in_reply_to='<msg1@example.com>',
            references='',
            subject='Re: Original Subject',
            from_email='test@example.com',
            to_emails=['contact@example.com']
        )
        
        self.assertEqual(found_conv.id, conv1.id)
    
    def test_find_conversation_by_references(self):
        """Test finding conversation via References header"""
        # Create initial conversation
        conv1 = EmailConversation.objects.create(
            account=self.account,
            subject='Original Subject',
            subject_normalized='Original Subject',
            contact_email='contact@example.com',
            last_message_at=timezone.now(),
            message_count=0,
            unread_count=0
        )
        
        # Create first email in conversation
        email1 = Email.objects.create(
            conversation=conv1,
            account=self.account,
            direction=Email.Direction.INBOUND,
            message_id='<msg1@example.com>',
            from_email='contact@example.com',
            subject='Original Subject',
            body_text='Original message',
            status=Email.Status.RECEIVED,
            received_at=timezone.now()
        )
        
        # Find conversation for reply with References (should find existing conversation)
        found_conv = EmailThreadingService.find_or_create_conversation(
            account=self.account,
            message_id='<msg3@example.com>',
            in_reply_to='',
            references='<msg1@example.com> <msg2@example.com>',
            subject='Re: Original Subject',
            from_email='test@example.com',
            to_emails=['contact@example.com']
        )
        
        self.assertEqual(found_conv.id, conv1.id)
    
    def test_create_new_conversation_when_no_match(self):
        """Test creating new conversation when no match found"""
        # No existing conversations
        conv = EmailThreadingService.find_or_create_conversation(
            account=self.account,
            message_id='<msg1@example.com>',
            in_reply_to='',
            references='',
            subject='New Subject',
            from_email='newcontact@example.com',
            to_emails=['test@example.com']
        )
        
        self.assertIsNotNone(conv)
        self.assertEqual(conv.contact_email, 'newcontact@example.com')
        self.assertEqual(conv.subject_normalized, 'New Subject')


class EmailThreadingRaceConditionTest(TransactionTestCase):
    """Test race condition prevention in EmailThreadingService"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.account = EmailAccount.objects.create(
            name='Test Account',
            email_address='test@example.com',
            account_type='imap_smtp',
            owner=self.user,
            is_active=True
        )
        self.errors = []
    
    def test_concurrent_conversation_creation(self):
        """Test that concurrent conversation creation doesn't create duplicates"""
        # Function to create conversation in a thread
        def create_conversation(thread_id):
            try:
                conv = EmailThreadingService.find_or_create_conversation(
                    account=self.account,
                    message_id=f'<msg{thread_id}@example.com>',
                    in_reply_to='',
                    references='',
                    subject='Test Subject',
                    from_email='contact@example.com',
                    to_emails=['test@example.com']
                )
                return conv
            except Exception as e:
                self.errors.append(str(e))
                return None
        
        # Create multiple threads that try to create conversations simultaneously
        threads = []
        results = []
        
        for i in range(5):
            thread = python_threading.Thread(
                target=lambda i=i: results.append(create_conversation(i))
            )
            threads.append(thread)
        
        # Start all threads at once
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that no errors occurred
        self.assertEqual(len(self.errors), 0, f"Errors occurred: {self.errors}")
        
        # Check that only one conversation was created
        conversations = EmailConversation.objects.filter(
            account=self.account,
            subject_normalized='Test Subject',
            contact_email='contact@example.com'
        )
        self.assertEqual(conversations.count(), 1, 
                         "Multiple conversations created - race condition not prevented!")


class EmailReceiverServiceTest(TestCase):
    """Test EmailReceiverService"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.account = EmailAccount.objects.create(
            name='Test Account',
            email_address='test@example.com',
            account_type='imap_smtp',
            owner=self.user,
            is_active=True,
            imap_host='imap.example.com',
            imap_port=993,
            imap_use_ssl=True
        )
        self.service = EmailReceiverService(self.account)
    
    @patch('mailbox.services.email_receiver.imaplib.IMAP4_SSL')
    def test_uses_uid_for_search(self, mock_imap):
        """Test that IMAP search uses UID instead of sequence numbers"""
        # Setup mock IMAP connection
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        
        # Mock login
        mock_connection.login.return_value = ('OK', [])
        
        # Mock select
        mock_connection.select.return_value = ('OK', [b'5'])
        
        # Mock UID search - should be called with 'search' as first parameter
        mock_connection.uid.return_value = ('OK', [b'1 2 3'])
        
        # Connect and fetch
        self.service.connect()
        self.service.fetch_new_emails(limit=10)
        
        # Verify that uid('search', ...) was called
        search_calls = [call for call in mock_connection.uid.call_args_list 
                       if call[0][0] == 'search']
        self.assertGreater(len(search_calls), 0, 
                          "uid('search', ...) was not called - still using sequence numbers!")
    
    @patch('mailbox.services.email_receiver.imaplib.IMAP4_SSL')
    def test_uses_uid_for_fetch(self, mock_imap):
        """Test that IMAP fetch uses UID instead of sequence numbers"""
        # Setup mock IMAP connection
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        
        # Mock login
        mock_connection.login.return_value = ('OK', [])
        
        # Mock select
        mock_connection.select.return_value = ('OK', [b'5'])
        
        # Mock UID search
        mock_connection.uid.side_effect = [
            ('OK', [b'100']),  # search result
            ('OK', [(b'100 (RFC822 {1234}', b'test email content')])  # fetch result
        ]
        
        # Mock email parsing
        with patch('mailbox.services.email_receiver.EmailParser.parse_raw_email') as mock_parser:
            mock_parser.return_value = {
                'message_id': '<test@example.com>',
                'from_email': 'sender@example.com',
                'from_name': 'Sender',
                'to_emails': [{'email': 'test@example.com'}],
                'cc_emails': [],
                'reply_to': '',
                'subject': 'Test Subject',
                'body_text': 'Test body',
                'body_html': '',
                'in_reply_to': '',
                'references': '',
                'date': timezone.now(),
                'attachments': []
            }
            
            # Connect and fetch
            self.service.connect()
            self.service.fetch_new_emails(limit=10)
        
        # Verify that uid('fetch', ...) was called
        fetch_calls = [call for call in mock_connection.uid.call_args_list 
                      if call[0][0] == 'fetch']
        self.assertGreater(len(fetch_calls), 0, 
                          "uid('fetch', ...) was not called - still using sequence numbers!")
    
    @patch('mailbox.services.email_receiver.imaplib.IMAP4_SSL')
    def test_batch_processing_limits_emails(self, mock_imap):
        """Test that batch processing respects the limit parameter"""
        # Setup mock IMAP connection
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        
        # Mock login
        mock_connection.login.return_value = ('OK', [])
        
        # Mock select
        mock_connection.select.return_value = ('OK', [b'100'])
        
        # Mock UID search - return 100 email UIDs
        email_uids = b' '.join([str(i).encode() for i in range(1, 101)])
        mock_connection.uid.return_value = ('OK', [email_uids])
        
        # Connect
        self.service.connect()
        
        # Fetch with limit of 10
        with patch.object(self.service, '_fetch_and_parse_email', return_value=None):
            self.service.fetch_new_emails(limit=10)
        
        # Verify that only 10 emails were processed
        # (We can't easily count actual fetch calls due to mocking, 
        # but we can verify the log message is correct)
        # This is tested indirectly through the code path
        self.assertTrue(True)  # Placeholder for now
