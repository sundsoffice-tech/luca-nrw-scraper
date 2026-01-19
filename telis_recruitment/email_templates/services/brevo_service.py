"""Brevo Email Service - Email-Versand via Brevo API"""
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Custom exception for Brevo API when SDK is not available
class BrevoApiException(Exception):
    """Custom exception for Brevo API errors"""
    pass


# Check if Brevo SDK is available
BREVO_AVAILABLE = False
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
    BREVO_AVAILABLE = True
except ImportError:
    # Use custom exception when SDK is not installed
    sib_api_v3_sdk = None
    ApiException = BrevoApiException
    logger.warning("Brevo SDK not available. Install with: pip install sib-api-v3-sdk")


class BrevoEmailService:
    """Service for sending emails via Brevo"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Brevo service
        
        Args:
            api_key: Brevo API key. If not provided, will try to get from environment
        """
        self.api_key = api_key or os.getenv('BREVO_API_KEY')
        self.configured = bool(self.api_key and BREVO_AVAILABLE)
        
        if self.configured:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.api_key
            self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
        else:
            self.api_instance = None
            if not BREVO_AVAILABLE:
                logger.warning("Brevo SDK not installed")
            elif not self.api_key:
                logger.warning("Brevo API key not configured")
    
    def is_configured(self) -> bool:
        """Check if Brevo is properly configured"""
        return self.configured
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[list] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a transactional email via Brevo
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            sender_email: Sender email (default from env)
            sender_name: Sender name (default from env)
            reply_to: Reply-to email address
            tags: List of tags for tracking
            params: Additional parameters for template variables
        
        Returns:
            dict: Response from Brevo API with message_id
        
        Raises:
            Exception: If email sending fails
        """
        if not self.is_configured():
            raise Exception("Brevo service is not configured")
        
        # Default sender from environment
        if not sender_email:
            sender_email = os.getenv('BREVO_SENDER_EMAIL', 'noreply@example.com')
        if not sender_name:
            sender_name = os.getenv('BREVO_SENDER_NAME', 'TELIS Recruitment')
        
        # Prepare email
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={"email": sender_email, "name": sender_name},
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=tags or []
        )
        
        if reply_to:
            send_smtp_email.reply_to = {"email": reply_to}
        
        if params:
            send_smtp_email.params = params
        
        try:
            # Send email
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            
            logger.info(f"Email sent successfully to {to_email}, message_id: {api_response.message_id}")
            
            return {
                'success': True,
                'message_id': api_response.message_id,
                'to': to_email
            }
        except ApiException as e:
            logger.error(f"Brevo API exception: {e}")
            raise Exception(f"Failed to send email: {e}")
    
    def send_template_email(
        self,
        template_id: int,
        to_email: str,
        params: Dict[str, Any],
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send an email using a Brevo template
        
        Args:
            template_id: Brevo template ID
            to_email: Recipient email address
            params: Template parameters/variables
            sender_email: Sender email (default from env)
            sender_name: Sender name (default from env)
            tags: List of tags for tracking
        
        Returns:
            dict: Response from Brevo API
        """
        if not self.is_configured():
            raise Exception("Brevo service is not configured")
        
        # Default sender from environment
        if not sender_email:
            sender_email = os.getenv('BREVO_SENDER_EMAIL', 'noreply@example.com')
        if not sender_name:
            sender_name = os.getenv('BREVO_SENDER_NAME', 'TELIS Recruitment')
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={"email": sender_email, "name": sender_name},
            template_id=template_id,
            params=params,
            tags=tags or []
        )
        
        try:
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            
            logger.info(f"Template email sent to {to_email}, message_id: {api_response.message_id}")
            
            return {
                'success': True,
                'message_id': api_response.message_id,
                'to': to_email
            }
        except ApiException as e:
            logger.error(f"Brevo API exception: {e}")
            raise Exception(f"Failed to send template email: {e}")
    
    def get_email_events(self, message_id: str) -> Dict[str, Any]:
        """
        Get events for a specific email message
        
        Args:
            message_id: Brevo message ID
        
        Returns:
            dict: Email events (opens, clicks, etc.)
        """
        if not self.is_configured():
            raise Exception("Brevo service is not configured")
        
        try:
            # This would use the email events API
            # api_response = self.api_instance.get_email_event_report(message_id)
            # For now, return placeholder
            return {
                'message_id': message_id,
                'events': []
            }
        except ApiException as e:
            logger.error(f"Failed to get email events: {e}")
            return {'error': str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Brevo API connection
        
        Returns:
            dict: Connection status
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Brevo service not configured'
            }
        
        try:
            # Test by getting account info
            account_api = sib_api_v3_sdk.AccountApi(
                sib_api_v3_sdk.ApiClient(
                    sib_api_v3_sdk.Configuration()
                )
            )
            account_api.api_client.configuration.api_key['api-key'] = self.api_key
            
            account_info = account_api.get_account()
            
            return {
                'success': True,
                'email': account_info.email,
                'company_name': account_info.company_name
            }
        except ApiException as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def send_email_via_brevo(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    tags: Optional[list] = None
) -> Dict[str, Any]:
    """
    Convenience function to send email via Brevo
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML content
        text_content: Plain text content
        tags: Email tags for tracking
    
    Returns:
        dict: Send result
    """
    service = BrevoEmailService()
    
    if not service.is_configured():
        logger.warning("Brevo not configured, email not sent")
        return {
            'success': False,
            'error': 'Brevo service not configured',
            'simulated': True
        }
    
    return service.send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        tags=tags
    )


def send_template_via_brevo(
    template_id: int,
    to_email: str,
    params: Dict[str, Any],
    tags: Optional[list] = None
) -> Dict[str, Any]:
    """
    Convenience function to send template email via Brevo
    
    Args:
        template_id: Brevo template ID
        to_email: Recipient email
        params: Template variables
        tags: Email tags for tracking
    
    Returns:
        dict: Send result
    """
    service = BrevoEmailService()
    
    if not service.is_configured():
        logger.warning("Brevo not configured, email not sent")
        return {
            'success': False,
            'error': 'Brevo service not configured',
            'simulated': True
        }
    
    return service.send_template_email(
        template_id=template_id,
        to_email=to_email,
        params=params,
        tags=tags
    )
