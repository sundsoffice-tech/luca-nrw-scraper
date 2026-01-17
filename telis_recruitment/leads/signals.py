"""
Django Signals für Lead-Events (z.B. Brevo-Sync nach Erstellung)
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Lead

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Lead)
def lead_post_save(sender, instance, created, **kwargs):
    """
    Signal-Handler nach Lead-Erstellung/Update.
    - Bei neuen Landing Page Leads: Sync zu Brevo + Welcome Email
    """
    # Nur bei neuen Leads von Landing Page
    if not created:
        return
    
    if instance.source != Lead.Source.LANDING_PAGE:
        return
    
    if not instance.email:
        return
    
    # Brevo-Integration nur wenn aktiviert
    if not getattr(settings, 'BREVO_API_KEY', None):
        logger.debug("Brevo nicht konfiguriert, überspringe Sync")
        return
    
    try:
        from .services.brevo import sync_lead_to_brevo, send_welcome_email
        
        # Kontakt zu Brevo synchen
        sync_success = sync_lead_to_brevo(instance)
        if sync_success:
            logger.info(f"Lead {instance.id} zu Brevo synchronisiert")
        
        # Welcome Email senden
        message_id = send_welcome_email(instance)
        if message_id:
            logger.info(f"Welcome Email an Lead {instance.id} gesendet: {message_id}")
            # Email-Counter erhöhen
            instance.email_sent_count += 1
            instance.save(update_fields=['email_sent_count'])
            
    except Exception as e:
        logger.error(f"Brevo-Sync Fehler für Lead {instance.id}: {e}")
