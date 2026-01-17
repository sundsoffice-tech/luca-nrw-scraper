"""
Brevo (Sendinblue) API Integration für Email-Marketing
"""
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Brevo API Client
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
    BREVO_AVAILABLE = True
except ImportError:
    BREVO_AVAILABLE = False
    logger.warning("sib-api-v3-sdk nicht installiert. Brevo-Integration deaktiviert.")


def get_brevo_config():
    """Gibt Brevo API Configuration zurück"""
    if not BREVO_AVAILABLE:
        return None
    
    api_key = getattr(settings, 'BREVO_API_KEY', None)
    if not api_key:
        logger.warning("BREVO_API_KEY nicht konfiguriert")
        return None
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key
    return configuration


def create_or_update_contact(email: str, attributes: Dict[str, Any], list_ids: list = None) -> bool:
    """
    Erstellt oder aktualisiert einen Kontakt in Brevo.
    
    Args:
        email: E-Mail-Adresse des Kontakts
        attributes: Dict mit Kontakt-Attributen (VORNAME, NACHNAME, TELEFON, etc.)
        list_ids: Liste von Brevo List-IDs für den Kontakt
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    config = get_brevo_config()
    if not config:
        return False
    
    try:
        api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(config))
        
        # Kontakt erstellen oder updaten
        create_contact = sib_api_v3_sdk.CreateContact(
            email=email,
            attributes=attributes,
            list_ids=list_ids or [],
            update_enabled=True  # Update wenn bereits existiert
        )
        
        api_instance.create_contact(create_contact)
        logger.info(f"Brevo: Kontakt erstellt/aktualisiert: {email}")
        return True
        
    except ApiException as e:
        if e.status == 400 and 'duplicate' in str(e.body).lower():
            # Kontakt existiert bereits, versuche Update
            try:
                update_contact = sib_api_v3_sdk.UpdateContact(
                    attributes=attributes,
                    list_ids=list_ids or []
                )
                api_instance.update_contact(email, update_contact)
                logger.info(f"Brevo: Kontakt aktualisiert: {email}")
                return True
            except ApiException as update_error:
                logger.error(f"Brevo Update-Fehler für {email}: {update_error}")
                return False
        else:
            logger.error(f"Brevo API-Fehler für {email}: {e}")
            return False
    except Exception as e:
        logger.error(f"Brevo Fehler für {email}: {e}")
        return False


def send_transactional_email(
    to_email: str,
    to_name: str,
    template_id: int,
    params: Dict[str, Any] = None
) -> Optional[str]:
    """
    Sendet eine transaktionale Email über Brevo Template.
    
    Args:
        to_email: Empfänger E-Mail
        to_name: Empfänger Name
        template_id: Brevo Template ID
        params: Template-Parameter (z.B. {"VORNAME": "Max"})
    
    Returns:
        Message-ID bei Erfolg, None bei Fehler
    """
    config = get_brevo_config()
    if not config:
        return None
    
    try:
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email, "name": to_name}],
            template_id=template_id,
            params=params or {}
        )
        
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Brevo: Email gesendet an {to_email}, Message-ID: {response.message_id}")
        return response.message_id
        
    except ApiException as e:
        logger.error(f"Brevo Email-Fehler für {to_email}: {e}")
        return None
    except Exception as e:
        logger.error(f"Brevo Email-Fehler für {to_email}: {e}")
        return None


def send_welcome_email(lead) -> Optional[str]:
    """
    Sendet Welcome-Email an neuen Landing Page Lead.
    
    Args:
        lead: Lead Model-Instanz
    
    Returns:
        Message-ID bei Erfolg, None bei Fehler
    """
    if not lead.email:
        return None
    
    # Template ID aus Settings oder Default
    template_id = getattr(settings, 'BREVO_WELCOME_TEMPLATE_ID', None)
    if not template_id:
        logger.warning("BREVO_WELCOME_TEMPLATE_ID nicht konfiguriert")
        return None
    
    # Name aufteilen
    name_parts = (lead.name or "").split(" ", 1)
    vorname = name_parts[0] if name_parts else ""
    nachname = name_parts[1] if len(name_parts) > 1 else ""
    
    params = {
        "VORNAME": vorname,
        "NACHNAME": nachname,
        "NAME": lead.name or "",
    }
    
    return send_transactional_email(
        to_email=lead.email,
        to_name=lead.name or "",
        template_id=template_id,
        params=params
    )


def sync_lead_to_brevo(lead) -> bool:
    """
    Synchronisiert einen Lead zu Brevo (Kontakt erstellen + Liste hinzufügen).
    
    Args:
        lead: Lead Model-Instanz
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not lead.email:
        return False
    
    # Name aufteilen
    name_parts = (lead.name or "").split(" ", 1)
    vorname = name_parts[0] if name_parts else ""
    nachname = name_parts[1] if len(name_parts) > 1 else ""
    
    attributes = {
        "VORNAME": vorname,
        "NACHNAME": nachname,
        "TELEFON": lead.telefon or "",
        "FIRMA": lead.company or "",
        "QUELLE": lead.source or "",
        "QUALITY_SCORE": lead.quality_score,
    }
    
    # List IDs aus Settings
    list_ids = []
    default_list_id = getattr(settings, 'BREVO_DEFAULT_LIST_ID', None)
    if default_list_id:
        list_ids.append(default_list_id)
    
    # Landing Page Leads in separate Liste
    if lead.source == 'landing_page':
        landing_list_id = getattr(settings, 'BREVO_LANDING_PAGE_LIST_ID', None)
        if landing_list_id:
            list_ids.append(landing_list_id)
    
    return create_or_update_contact(lead.email, attributes, list_ids)
