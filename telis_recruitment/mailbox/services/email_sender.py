"""
Email sender service for sending emails via Brevo or SMTP.
"""
import base64
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime
from django.utils import timezone
from django.conf import settings
import logging

from mailbox.models import Email, EmailAccount, EmailAttachment
from mailbox.services.encryption import decrypt_password, decrypt_api_key

logger = logging.getLogger(__name__)

# Brevo API Client
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
    BREVO_AVAILABLE = True
except ImportError:
    BREVO_AVAILABLE = False
    logger.warning("sib-api-v3-sdk nicht installiert. Brevo-Integration deaktiviert.")


class EmailSenderService:
    """Service zum Senden von Emails via Brevo oder SMTP"""
    
    def __init__(self, account: EmailAccount):
        """
        Initialize email sender service.
        
        Args:
            account: EmailAccount instance to use for sending
        """
        self.account = account
    
    def send_email(
        self,
        email: Email,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> bool:
        """
        Sende eine Email und aktualisiere Email-Record.
        
        Args:
            email: Email instance to send
            attachments: List of EmailAttachment instances
            
        Returns:
            True on success, False on failure
        """
        if not self.account.is_active:
            logger.error(f"Account {self.account.email_address} is not active")
            email.status = Email.Status.FAILED
            email.status_detail = "Account is not active"
            email.save()
            return False
        
        # Update status to sending
        email.status = Email.Status.SENDING
        email.save()
        
        try:
            # Send via appropriate method based on account type
            if self.account.account_type == EmailAccount.AccountType.BREVO:
                success = self._send_via_brevo(email, attachments)
            else:
                success = self._send_via_smtp(email, attachments)
            
            if success:
                email.status = Email.Status.SENT
                email.sent_at = timezone.now()
                logger.info(f"Email sent successfully: {email.id}")
            else:
                email.status = Email.Status.FAILED
                logger.error(f"Email send failed: {email.id}")
            
            email.save()
            return success
            
        except Exception as e:
            logger.error(f"Error sending email {email.id}: {e}")
            email.status = Email.Status.FAILED
            email.status_detail = str(e)
            email.save()
            return False
    
    def _send_via_brevo(self, email: Email, attachments: Optional[List[EmailAttachment]] = None) -> bool:
        """
        Sende via Brevo Transactional API.
        
        Args:
            email: Email instance
            attachments: List of EmailAttachment instances
            
        Returns:
            True on success, False on failure
        """
        if not BREVO_AVAILABLE:
            logger.error("Brevo SDK not available")
            return False
        
        try:
            # Decrypt API key
            api_key = decrypt_api_key(self.account.brevo_api_key_encrypted)
            if not api_key:
                logger.error("Brevo API key not configured")
                return False
            
            # Configure API client
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = api_key
            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
            
            # Prepare email data
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender={"email": email.from_email, "name": email.from_name or ""},
                to=[{"email": e['email'], "name": e.get('name', '')} for e in email.to_emails],
                subject=email.subject,
                html_content=email.body_html or None,
                text_content=email.body_text or None,
            )
            
            # Add CC if present
            if email.cc_emails:
                send_smtp_email.cc = [{"email": e['email'], "name": e.get('name', '')} for e in email.cc_emails]
            
            # Add BCC if present
            if email.bcc_emails:
                send_smtp_email.bcc = [{"email": e['email'], "name": e.get('name', '')} for e in email.bcc_emails]
            
            # Add reply-to if present
            if email.reply_to_email:
                send_smtp_email.reply_to = {"email": email.reply_to_email}
            
            # Add headers for threading
            headers = {}
            if email.in_reply_to:
                headers['In-Reply-To'] = email.in_reply_to
            if email.references:
                headers['References'] = email.references
            if headers:
                send_smtp_email.headers = headers
            
            # Add attachments if present
            if attachments:
                attachment_list = []
                for att in attachments:
                    try:
                        with open(att.file.path, 'rb') as f:
                            content = f.read()
                            attachment_list.append({
                                'name': att.filename,
                                'content': base64.b64encode(content).decode(),
                            })
                    except Exception as e:
                        logger.warning(f"Could not attach file {att.filename}: {e}")
                
                if attachment_list:
                    send_smtp_email.attachment = attachment_list
            
            # Send email
            response = api_instance.send_transac_email(send_smtp_email)
            
            # Store Brevo message ID
            email.brevo_message_id = response.message_id
            
            logger.info(f"Brevo: Email sent, Message-ID: {response.message_id}")
            return True
            
        except ApiException as e:
            logger.error(f"Brevo API error: {e}")
            email.status_detail = f"Brevo API error: {e}"
            return False
        except Exception as e:
            logger.error(f"Error sending via Brevo: {e}")
            email.status_detail = str(e)
            return False
    
    def _send_via_smtp(self, email: Email, attachments: Optional[List[EmailAttachment]] = None) -> bool:
        """
        Sende via SMTP direkt.
        
        Args:
            email: Email instance
            attachments: List of EmailAttachment instances
            
        Returns:
            True on success, False on failure
        """
        try:
            # Decrypt credentials
            username = self.account.smtp_username
            password = decrypt_password(self.account.smtp_password_encrypted) if self.account.smtp_password_encrypted else ""
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email.subject
            msg['From'] = f"{email.from_name} <{email.from_email}>" if email.from_name else email.from_email
            msg['To'] = ', '.join([e['email'] for e in email.to_emails])
            
            if email.cc_emails:
                msg['Cc'] = ', '.join([e['email'] for e in email.cc_emails])
            
            if email.reply_to_email:
                msg['Reply-To'] = email.reply_to_email
            
            # Add Message-ID
            msg['Message-ID'] = email.message_id
            
            # Add threading headers
            if email.in_reply_to:
                msg['In-Reply-To'] = email.in_reply_to
            if email.references:
                msg['References'] = email.references
            
            # Add body parts
            if email.body_text:
                msg.attach(MIMEText(email.body_text, 'plain', 'utf-8'))
            if email.body_html:
                msg.attach(MIMEText(email.body_html, 'html', 'utf-8'))
            
            # Add attachments
            if attachments:
                for att in attachments:
                    try:
                        with open(att.file.path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{att.filename}"',
                            )
                            msg.attach(part)
                    except Exception as e:
                        logger.warning(f"Could not attach file {att.filename}: {e}")
            
            # Connect to SMTP server and send
            server = None
            try:
                if self.account.smtp_use_tls:
                    server = smtplib.SMTP(self.account.smtp_host, self.account.smtp_port)
                    server.starttls()
                else:
                    server = smtplib.SMTP_SSL(self.account.smtp_host, self.account.smtp_port)
                
                if username and password:
                    server.login(username, password)
                
                # Collect all recipients
                all_recipients = [e['email'] for e in email.to_emails]
                if email.cc_emails:
                    all_recipients.extend([e['email'] for e in email.cc_emails])
                if email.bcc_emails:
                    all_recipients.extend([e['email'] for e in email.bcc_emails])
                
                server.sendmail(email.from_email, all_recipients, msg.as_string())
                
                logger.info(f"SMTP: Email sent successfully")
                return True
            finally:
                if server:
                    try:
                        server.quit()
                    except Exception:
                        pass
            
        except Exception as e:
            logger.error(f"Error sending via SMTP: {e}")
            email.status_detail = str(e)
            return False
    
    def send_batch_emails(self, emails: List[Email]) -> Dict[int, bool]:
        """
        Send multiple emails in batch.
        
        Args:
            emails: List of Email instances to send
            
        Returns:
            Dictionary mapping email ID to success status
        """
        results = {}
        
        for email in emails:
            # Get attachments for this email
            attachments = list(email.attachments.all()) if hasattr(email, 'attachments') else []
            
            # Send email
            success = self.send_email(email, attachments)
            results[email.id] = success
        
        return results
