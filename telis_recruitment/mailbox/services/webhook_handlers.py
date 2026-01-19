"""
Webhook handlers for Brevo events.
"""
import logging
from typing import Dict, Optional, Any
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from mailbox.models import Email, EmailAccount

logger = logging.getLogger(__name__)


class BrevoWebhookHandler:
    """Handler für Brevo Webhooks"""
    
    @staticmethod
    def handle_event(event_data: Dict[str, Any]) -> bool:
        """
        Verarbeite Brevo Webhook Event.
        
        Events:
        - delivered: Email zugestellt
        - opened: Email geöffnet (+ opened_count)
        - click: Link geklickt (+ clicked_links)
        - soft_bounce: Temporärer Fehler
        - hard_bounce: Permanenter Fehler
        - spam: Als Spam markiert
        - unsubscribed: Abgemeldet
        - inbound: Eingehende Email (Inbound Parsing)
        
        Args:
            event_data: Webhook event data from Brevo
            
        Returns:
            True if event was handled successfully, False otherwise
        """
        event_type = event_data.get('event')
        
        if not event_type:
            logger.warning("No event type in webhook data")
            return False
        
        logger.info(f"Processing Brevo webhook event: {event_type}")
        
        # Route to appropriate handler
        handlers = {
            'delivered': BrevoWebhookHandler._handle_delivered,
            'opened': BrevoWebhookHandler._handle_opened,
            'click': BrevoWebhookHandler._handle_click,
            'soft_bounce': BrevoWebhookHandler._handle_soft_bounce,
            'hard_bounce': BrevoWebhookHandler._handle_hard_bounce,
            'spam': BrevoWebhookHandler._handle_spam,
            'unsubscribed': BrevoWebhookHandler._handle_unsubscribed,
            'inbound': BrevoWebhookHandler._handle_inbound_email,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return handler(event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return False
    
    @staticmethod
    def _find_email_by_message_id(message_id: str) -> Optional[Email]:
        """
        Find email by Brevo message ID.
        
        Args:
            message_id: Brevo message ID
            
        Returns:
            Email instance or None
        """
        try:
            return Email.objects.get(brevo_message_id=message_id)
        except Email.DoesNotExist:
            logger.warning(f"Email not found for message_id: {message_id}")
            return None
        except Email.MultipleObjectsReturned:
            logger.warning(f"Multiple emails found for message_id: {message_id}")
            return Email.objects.filter(brevo_message_id=message_id).first()
    
    @staticmethod
    def _handle_delivered(event_data: Dict[str, Any]) -> bool:
        """Handle delivered event."""
        message_id = event_data.get('message-id')
        if not message_id:
            return False
        
        email = BrevoWebhookHandler._find_email_by_message_id(message_id)
        if not email:
            return False
        
        email.status = Email.Status.DELIVERED
        email.delivered_at = timezone.now()
        
        # Extract timestamp from event if available
        if 'ts_event' in event_data:
            try:
                email.delivered_at = parse_datetime(event_data['ts_event']) or timezone.now()
            except:
                pass
        
        email.save(update_fields=['status', 'delivered_at'])
        logger.info(f"Email {email.id} marked as delivered")
        return True
    
    @staticmethod
    def _handle_opened(event_data: Dict[str, Any]) -> bool:
        """Handle opened event."""
        message_id = event_data.get('message-id')
        if not message_id:
            return False
        
        email = BrevoWebhookHandler._find_email_by_message_id(message_id)
        if not email:
            return False
        
        # Update status and increment open count
        email.status = Email.Status.OPENED
        email.opened_count += 1
        
        # Set opened_at on first open
        if not email.opened_at:
            email.opened_at = timezone.now()
            
            # Extract timestamp from event if available
            if 'ts_event' in event_data:
                try:
                    email.opened_at = parse_datetime(event_data['ts_event']) or timezone.now()
                except:
                    pass
        
        email.save(update_fields=['status', 'opened_at', 'opened_count'])
        logger.info(f"Email {email.id} opened (count: {email.opened_count})")
        return True
    
    @staticmethod
    def _handle_click(event_data: Dict[str, Any]) -> bool:
        """Handle click event."""
        message_id = event_data.get('message-id')
        if not message_id:
            return False
        
        email = BrevoWebhookHandler._find_email_by_message_id(message_id)
        if not email:
            return False
        
        # Update status
        email.status = Email.Status.CLICKED
        
        # Set clicked_at on first click
        if not email.clicked_at:
            email.clicked_at = timezone.now()
            
            # Extract timestamp from event if available
            if 'ts_event' in event_data:
                try:
                    email.clicked_at = parse_datetime(event_data['ts_event']) or timezone.now()
                except:
                    pass
        
        # Add clicked link to list
        url = event_data.get('link', '')
        if url:
            click_data = {
                'url': url,
                'clicked_at': timezone.now().isoformat()
            }
            
            # Extract timestamp from event if available
            if 'ts_event' in event_data:
                try:
                    dt = parse_datetime(event_data['ts_event'])
                    if dt:
                        click_data['clicked_at'] = dt.isoformat()
                except:
                    pass
            
            email.clicked_links.append(click_data)
        
        email.save(update_fields=['status', 'clicked_at', 'clicked_links'])
        logger.info(f"Email {email.id} link clicked: {url}")
        return True
    
    @staticmethod
    def _handle_soft_bounce(event_data: Dict[str, Any]) -> bool:
        """Handle soft bounce event (temporary failure)."""
        message_id = event_data.get('message-id')
        if not message_id:
            return False
        
        email = BrevoWebhookHandler._find_email_by_message_id(message_id)
        if not email:
            return False
        
        # Don't change status to bounced for soft bounces (might be retried)
        # Just log the error details
        error = event_data.get('error', 'Soft bounce')
        email.status_detail = f"Soft bounce: {error}"
        email.save(update_fields=['status_detail'])
        
        logger.warning(f"Email {email.id} soft bounced: {error}")
        return True
    
    @staticmethod
    def _handle_hard_bounce(event_data: Dict[str, Any]) -> bool:
        """Handle hard bounce event (permanent failure)."""
        message_id = event_data.get('message-id')
        if not message_id:
            return False
        
        email = BrevoWebhookHandler._find_email_by_message_id(message_id)
        if not email:
            return False
        
        email.status = Email.Status.BOUNCED
        error = event_data.get('error', 'Hard bounce')
        email.status_detail = f"Hard bounce: {error}"
        email.save(update_fields=['status', 'status_detail'])
        
        logger.error(f"Email {email.id} hard bounced: {error}")
        return True
    
    @staticmethod
    def _handle_spam(event_data: Dict[str, Any]) -> bool:
        """Handle spam complaint event."""
        message_id = event_data.get('message-id')
        if not message_id:
            return False
        
        email = BrevoWebhookHandler._find_email_by_message_id(message_id)
        if not email:
            return False
        
        email.status_detail = "Marked as spam by recipient"
        email.save(update_fields=['status_detail'])
        
        logger.warning(f"Email {email.id} marked as spam")
        return True
    
    @staticmethod
    def _handle_unsubscribed(event_data: Dict[str, Any]) -> bool:
        """Handle unsubscribe event."""
        email_address = event_data.get('email')
        
        if email_address:
            logger.info(f"User unsubscribed: {email_address}")
            # You could add logic here to update lead preferences
        
        return True
    
    @staticmethod
    def _handle_inbound_email(event_data: Dict[str, Any]) -> bool:
        """
        Handle inbound email from Brevo Inbound Parsing.
        
        This would create a new Email record from incoming email data.
        Note: This requires Brevo Inbound Email Parsing to be configured.
        
        Args:
            event_data: Inbound email data from Brevo
            
        Returns:
            True if email was processed successfully
        """
        logger.info("Received inbound email via Brevo")
        
        # TODO: Implement inbound email parsing
        # This would involve:
        # 1. Parse email data from event_data
        # 2. Find appropriate EmailAccount
        # 3. Create Email record
        # 4. Find/create conversation
        # 5. Link to lead if applicable
        
        logger.warning("Inbound email handling not yet implemented")
        return False
