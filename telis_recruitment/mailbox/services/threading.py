"""
Email threading service for grouping related emails into conversations.
"""
import re
from typing import Optional, List
from django.utils import timezone
from mailbox.models import EmailConversation, EmailAccount
import logging

logger = logging.getLogger(__name__)


class EmailThreadingService:
    """Service for Email-Threading (Konversationen)"""
    
    @staticmethod
    def normalize_subject(subject: str) -> str:
        """
        Entferne Re:/Fwd:/AW:/WG: vom Subject für Threading.
        
        Args:
            subject: Original email subject
            
        Returns:
            Normalized subject without reply/forward prefixes
        """
        if not subject:
            return ""
        
        # Remove common reply/forward prefixes (case-insensitive)
        patterns = [
            r'^Re:\s*',
            r'^RE:\s*',
            r'^Fwd:\s*',
            r'^FWD:\s*',
            r'^AW:\s*',  # German "Antwort"
            r'^WG:\s*',  # German "Weiterleitung"
            r'^Aw:\s*',
            r'^Wg:\s*',
        ]
        
        normalized = subject
        changed = True
        
        # Keep removing prefixes until none are found
        while changed:
            changed = False
            for pattern in patterns:
                new_normalized = re.sub(pattern, '', normalized, count=1)
                if new_normalized != normalized:
                    normalized = new_normalized
                    changed = True
        
        return normalized.strip()
    
    @staticmethod
    def find_or_create_conversation(
        account: EmailAccount,
        message_id: str,
        in_reply_to: str,
        references: str,
        subject: str,
        from_email: str,
        to_emails: List[str],
    ) -> EmailConversation:
        """
        Finde existierende Konversation oder erstelle neue.
        
        Threading-Logik:
        1. Suche nach In-Reply-To Message-ID
        2. Suche nach References Message-IDs
        3. Suche nach normalisiertem Subject + gleicher Kontakt
        4. Erstelle neue Konversation
        
        Args:
            account: EmailAccount instance
            message_id: Message-ID of the current email
            in_reply_to: In-Reply-To header value
            references: References header value (space-separated message IDs)
            subject: Email subject
            from_email: Sender email address
            to_emails: List of recipient email addresses
            
        Returns:
            EmailConversation instance (existing or newly created)
        """
        from mailbox.models import Email  # Import here to avoid circular import
        
        # 1. Try to find conversation by In-Reply-To
        if in_reply_to:
            try:
                parent_email = Email.objects.filter(message_id=in_reply_to).first()
                if parent_email:
                    logger.info(f"Found conversation via In-Reply-To: {parent_email.conversation_id}")
                    return parent_email.conversation
            except Exception as e:
                logger.warning(f"Error finding conversation by In-Reply-To: {e}")
        
        # 2. Try to find conversation by References
        if references:
            reference_ids = references.strip().split()
            if reference_ids:
                try:
                    # Try the most recent reference first (usually the last one)
                    for ref_id in reversed(reference_ids):
                        parent_email = Email.objects.filter(message_id=ref_id).first()
                        if parent_email:
                            logger.info(f"Found conversation via References: {parent_email.conversation_id}")
                            return parent_email.conversation
                except Exception as e:
                    logger.warning(f"Error finding conversation by References: {e}")
        
        # 3. Try to find conversation by normalized subject + contact email
        normalized_subject = EmailThreadingService.normalize_subject(subject)
        
        # Determine the contact email (the "other" party in the conversation)
        # If email is from us (account), contact is first recipient
        # If email is to us, contact is sender
        contact_email = from_email
        if from_email.lower() == account.email_address.lower():
            # Outbound email - contact is recipient
            if to_emails:
                contact_email = to_emails[0]
        
        if normalized_subject and contact_email:
            try:
                # Look for conversation with same normalized subject and contact within last 30 days
                thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
                conversation = EmailConversation.objects.filter(
                    account=account,
                    subject_normalized__iexact=normalized_subject,
                    contact_email__iexact=contact_email,
                    last_message_at__gte=thirty_days_ago
                ).first()
                
                if conversation:
                    logger.info(f"Found conversation via subject+contact: {conversation.id}")
                    return conversation
            except Exception as e:
                logger.warning(f"Error finding conversation by subject: {e}")
        
        # 4. Create new conversation
        logger.info(f"Creating new conversation for subject: {subject}")
        
        # Extract contact name from from_email if available
        contact_name = ""
        # You could parse "Name <email@example.com>" format here if needed
        
        conversation = EmailConversation.objects.create(
            account=account,
            subject=subject,
            subject_normalized=normalized_subject,
            contact_email=contact_email,
            contact_name=contact_name,
            last_message_at=timezone.now(),
            message_count=0,
            unread_count=0
        )
        
        logger.info(f"Created new conversation {conversation.id}")
        return conversation
    
    @staticmethod
    def auto_link_lead(conversation: EmailConversation) -> Optional['Lead']:
        """
        Verknüpfe Konversation automatisch mit Lead basierend auf Email-Adresse.
        
        Args:
            conversation: EmailConversation instance
            
        Returns:
            Lead instance if found and linked, None otherwise
        """
        from leads.models import Lead  # Import here to avoid circular import
        
        if conversation.lead:
            # Already linked
            return conversation.lead
        
        try:
            # Try to find lead by email address
            lead = Lead.objects.filter(email__iexact=conversation.contact_email).first()
            
            if lead:
                conversation.lead = lead
                conversation.save(update_fields=['lead'])
                logger.info(f"Auto-linked conversation {conversation.id} to lead {lead.id}")
                return lead
        except Exception as e:
            logger.warning(f"Error auto-linking lead: {e}")
        
        return None
    
    @staticmethod
    def update_conversation_stats(conversation: EmailConversation) -> None:
        """
        Update conversation statistics (message count, unread count, timestamps).
        
        Args:
            conversation: EmailConversation instance to update
        """
        from mailbox.models import Email  # Import here to avoid circular import
        
        try:
            messages = Email.objects.filter(conversation=conversation)
            
            # Update counts
            conversation.message_count = messages.count()
            conversation.unread_count = messages.filter(is_read=False, direction='inbound').count()
            
            # Update timestamps
            last_message = messages.order_by('-created_at').first()
            if last_message:
                conversation.last_message_at = last_message.created_at
            
            last_inbound = messages.filter(direction='inbound').order_by('-created_at').first()
            if last_inbound:
                conversation.last_inbound_at = last_inbound.created_at
            
            last_outbound = messages.filter(direction='outbound').order_by('-created_at').first()
            if last_outbound:
                conversation.last_outbound_at = last_outbound.created_at
            
            # Update read status - conversation is read if all inbound messages are read
            conversation.is_read = (conversation.unread_count == 0)
            
            conversation.save()
            logger.debug(f"Updated stats for conversation {conversation.id}")
            
        except Exception as e:
            logger.error(f"Error updating conversation stats: {e}")
