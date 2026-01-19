"""
Email receiver service for fetching emails via IMAP.
"""
import imaplib
from typing import List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.files.base import ContentFile
import logging

from mailbox.models import Email, EmailAccount, EmailConversation, EmailAttachment
from mailbox.services.encryption import decrypt_password
from mailbox.services.parser import EmailParser
from mailbox.services.threading import EmailThreadingService

logger = logging.getLogger(__name__)


class EmailReceiverService:
    """Service zum Empfangen von Emails via IMAP"""
    
    def __init__(self, account: EmailAccount):
        """
        Initialize email receiver service.
        
        Args:
            account: EmailAccount instance to use for receiving
        """
        self.account = account
        self.connection = None
    
    def connect(self) -> bool:
        """
        Verbinde zum IMAP-Server.
        
        Returns:
            True on success, False on failure
        """
        try:
            # Disconnect if already connected
            if self.connection:
                try:
                    self.connection.logout()
                except:
                    pass
            
            # Decrypt credentials
            password = decrypt_password(self.account.imap_password_encrypted) if self.account.imap_password_encrypted else ""
            
            # Connect to IMAP server
            if self.account.imap_use_ssl:
                self.connection = imaplib.IMAP4_SSL(
                    self.account.imap_host,
                    self.account.imap_port
                )
            else:
                self.connection = imaplib.IMAP4(
                    self.account.imap_host,
                    self.account.imap_port
                )
            
            # Login
            username = self.account.imap_username or self.account.email_address
            self.connection.login(username, password)
            
            logger.info(f"Connected to IMAP server: {self.account.imap_host}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to IMAP: {e}")
            self.account.last_sync_error = str(e)
            self.account.save(update_fields=['last_sync_error'])
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass
            self.connection = None
    
    def fetch_new_emails(self, folder: str = 'INBOX', limit: int = 50) -> List[Email]:
        """
        Hole neue Emails vom Server.
        
        - Prüft last_sync_at
        - Parsed Email-Header und Body
        - Erstellt Email-Records
        - Threading via In-Reply-To/References
        
        Args:
            folder: IMAP folder to fetch from
            limit: Maximum number of emails to fetch
            
        Returns:
            List of created Email instances
        """
        if not self.connection:
            if not self.connect():
                return []
        
        created_emails = []
        
        try:
            # Select folder
            self.connection.select(folder, readonly=False)
            
            # Determine search criteria based on last sync
            if self.account.last_sync_at:
                # Fetch emails since last sync
                since_date = self.account.last_sync_at.strftime('%d-%b-%Y')
                search_criteria = f'(SINCE {since_date})'
            else:
                # First sync - fetch recent emails
                since_date = (timezone.now() - timedelta(days=30)).strftime('%d-%b-%Y')
                search_criteria = f'(SINCE {since_date})'
            
            # Search for emails
            typ, data = self.connection.search(None, search_criteria)
            
            if typ != 'OK':
                logger.error(f"IMAP search failed: {typ}")
                return created_emails
            
            # Get email IDs
            email_ids = data[0].split()
            
            # Limit number of emails
            if len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Get most recent
            
            logger.info(f"Found {len(email_ids)} emails to fetch")
            
            # Fetch each email
            for email_id in email_ids:
                try:
                    email = self._fetch_and_parse_email(email_id, folder)
                    if email:
                        created_emails.append(email)
                except Exception as e:
                    logger.error(f"Error fetching email {email_id}: {e}")
                    continue
            
            # Update last sync time
            self.account.last_sync_at = timezone.now()
            self.account.last_sync_error = ""
            self.account.save(update_fields=['last_sync_at', 'last_sync_error'])
            
            logger.info(f"Fetched {len(created_emails)} new emails")
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            self.account.last_sync_error = str(e)
            self.account.save(update_fields=['last_sync_error'])
        
        return created_emails
    
    def _fetch_and_parse_email(self, email_id: bytes, folder: str) -> Optional[Email]:
        """
        Fetch and parse a single email.
        
        Args:
            email_id: IMAP email ID
            folder: IMAP folder name
            
        Returns:
            Created Email instance or None
        """
        try:
            # Fetch email data
            typ, data = self.connection.fetch(email_id, '(RFC822)')
            
            if typ != 'OK':
                logger.error(f"Failed to fetch email {email_id}")
                return None
            
            # Parse email
            raw_email = data[0][1]
            parsed = EmailParser.parse_raw_email(raw_email)
            
            # Check if email already exists
            message_id = parsed['message_id']
            if Email.objects.filter(message_id=message_id).exists():
                logger.debug(f"Email {message_id} already exists, skipping")
                return None
            
            # Extract recipient emails for threading
            to_emails_list = [e['email'] for e in parsed['to_emails']]
            
            # Find or create conversation
            conversation = EmailThreadingService.find_or_create_conversation(
                account=self.account,
                message_id=message_id,
                in_reply_to=parsed['in_reply_to'],
                references=parsed['references'],
                subject=parsed['subject'],
                from_email=parsed['from_email'],
                to_emails=to_emails_list,
            )
            
            # Create email record
            email = Email.objects.create(
                conversation=conversation,
                account=self.account,
                direction=Email.Direction.INBOUND,
                message_id=message_id,
                in_reply_to=parsed['in_reply_to'],
                references=parsed['references'],
                from_email=parsed['from_email'],
                from_name=parsed['from_name'],
                to_emails=parsed['to_emails'],
                cc_emails=parsed['cc_emails'],
                reply_to_email=parsed['reply_to'],
                subject=parsed['subject'],
                body_text=parsed['body_text'],
                body_html=parsed['body_html'],
                snippet=EmailParser.generate_snippet(parsed['body_text'] or parsed['body_html']),
                status=Email.Status.RECEIVED,
                received_at=parsed['date'] if parsed['date'] else timezone.now(),
                is_read=False,
                imap_uid=email_id.decode(),
                imap_folder=folder,
            )
            
            # Save attachments
            for att_data in parsed['attachments']:
                try:
                    attachment = EmailAttachment.objects.create(
                        email=email,
                        filename=att_data['filename'],
                        content_type=att_data['content_type'],
                        size=att_data['size'],
                        content_id=att_data['content_id'],
                        is_inline=att_data['is_inline'],
                    )
                    
                    # Save file content
                    attachment.file.save(
                        att_data['filename'],
                        ContentFile(att_data['content']),
                        save=True
                    )
                    
                    logger.debug(f"Saved attachment: {att_data['filename']}")
                except Exception as e:
                    logger.warning(f"Error saving attachment: {e}")
            
            # Update conversation stats
            EmailThreadingService.update_conversation_stats(conversation)
            
            # Try to auto-link to lead
            EmailThreadingService.auto_link_lead(conversation)
            
            logger.info(f"Created email {email.id} in conversation {conversation.id}")
            return email
            
        except Exception as e:
            logger.error(f"Error parsing email {email_id}: {e}")
            return None
    
    def sync_all_folders(self) -> int:
        """
        Synchronisiere alle IMAP-Ordner.
        
        Returns:
            Total number of emails fetched
        """
        if not self.connection:
            if not self.connect():
                return 0
        
        total_fetched = 0
        
        try:
            # List all folders
            typ, folders = self.connection.list()
            
            if typ != 'OK':
                logger.error("Failed to list folders")
                return 0
            
            # Fetch emails from each folder
            for folder_data in folders:
                try:
                    # Parse folder name
                    # Format: b'(\\HasNoChildren) "/" "INBOX"'
                    folder_name = folder_data.decode().split('"')[-2]
                    
                    logger.info(f"Syncing folder: {folder_name}")
                    
                    emails = self.fetch_new_emails(folder=folder_name, limit=20)
                    total_fetched += len(emails)
                    
                except Exception as e:
                    logger.warning(f"Error syncing folder: {e}")
                    continue
            
            logger.info(f"Total emails fetched: {total_fetched}")
            
        except Exception as e:
            logger.error(f"Error syncing folders: {e}")
        
        return total_fetched
