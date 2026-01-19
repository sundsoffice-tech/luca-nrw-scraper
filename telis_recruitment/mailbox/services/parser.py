"""
Email parser service for parsing raw email messages.
"""
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Dict, List, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)


class EmailParser:
    """Service für Email Parsing"""
    
    @staticmethod
    def parse_raw_email(raw_email: bytes) -> Dict[str, Any]:
        """
        Parse rohe Email-Daten in strukturierte Daten.
        
        Args:
            raw_email: Raw email bytes
            
        Returns:
            Dictionary with parsed email data
        """
        try:
            msg = email.message_from_bytes(raw_email)
            
            return {
                'message_id': EmailParser._get_header(msg, 'Message-ID', ''),
                'in_reply_to': EmailParser._get_header(msg, 'In-Reply-To', ''),
                'references': EmailParser._get_header(msg, 'References', ''),
                'subject': EmailParser._decode_header(msg.get('Subject', '')),
                'from_email': EmailParser._parse_email_address(msg.get('From', ''))[0],
                'from_name': EmailParser._parse_email_address(msg.get('From', ''))[1],
                'to_emails': EmailParser._parse_email_list(msg.get('To', '')),
                'cc_emails': EmailParser._parse_email_list(msg.get('Cc', '')),
                'reply_to': EmailParser._parse_email_address(msg.get('Reply-To', ''))[0] if msg.get('Reply-To') else '',
                'date': EmailParser._parse_date(msg.get('Date')),
                'body_text': EmailParser._get_text_body(msg),
                'body_html': EmailParser._get_html_body(msg),
                'attachments': EmailParser._extract_attachments(msg),
            }
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            raise
    
    @staticmethod
    def _decode_header(header_value: str) -> str:
        """
        Decode email header (handles encoded-words).
        
        Args:
            header_value: Raw header value
            
        Returns:
            Decoded header string
        """
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            result = []
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        result.append(part.decode(encoding, errors='replace'))
                    else:
                        result.append(part.decode('utf-8', errors='replace'))
                else:
                    result.append(part)
            
            return ''.join(result)
        except Exception as e:
            logger.warning(f"Error decoding header: {e}")
            return str(header_value)
    
    @staticmethod
    def _get_header(msg: email.message.Message, header_name: str, default: str = '') -> str:
        """
        Get header value from message.
        
        Args:
            msg: Email message object
            header_name: Name of the header
            default: Default value if header not found
            
        Returns:
            Header value
        """
        value = msg.get(header_name)
        if value:
            return EmailParser._decode_header(value)
        return default
    
    @staticmethod
    def _parse_email_address(address_str: str) -> tuple:
        """
        Parse email address string into (email, name) tuple.
        
        Args:
            address_str: Email address string (e.g., "John Doe <john@example.com>")
            
        Returns:
            Tuple of (email, name)
        """
        if not address_str:
            return ('', '')
        
        try:
            name, email_addr = parseaddr(EmailParser._decode_header(address_str))
            return (email_addr, name)
        except Exception as e:
            logger.warning(f"Error parsing email address: {e}")
            return (address_str, '')
    
    @staticmethod
    def _parse_email_list(addresses_str: str) -> List[Dict[str, str]]:
        """
        Parse comma-separated email addresses into list of dicts.
        
        Args:
            addresses_str: Comma-separated email addresses
            
        Returns:
            List of {"email": "...", "name": "..."} dicts
        """
        if not addresses_str:
            return []
        
        try:
            # Split by comma, but not commas within quotes
            addresses = email.utils.getaddresses([EmailParser._decode_header(addresses_str)])
            
            result = []
            for name, email_addr in addresses:
                if email_addr:  # Only add if we have an email address
                    result.append({
                        'email': email_addr,
                        'name': name
                    })
            
            return result
        except Exception as e:
            logger.warning(f"Error parsing email list: {e}")
            return []
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[str]:
        """
        Parse email date header.
        
        Args:
            date_str: Date string from email header
            
        Returns:
            ISO format datetime string or None
        """
        if not date_str:
            return None
        
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except Exception as e:
            logger.warning(f"Error parsing date: {e}")
            return None
    
    @staticmethod
    def _get_text_body(msg: email.message.Message) -> str:
        """
        Extract plain text body from email.
        
        Args:
            msg: Email message object
            
        Returns:
            Plain text body
        """
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break
                    except Exception as e:
                        logger.warning(f"Error decoding text part: {e}")
        else:
            if msg.get_content_type() == 'text/plain':
                try:
                    payload = msg.get_payload(decode=True)
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                except Exception as e:
                    logger.warning(f"Error decoding text body: {e}")
        
        return body
    
    @staticmethod
    def _get_html_body(msg: email.message.Message) -> str:
        """
        Extract HTML body from email.
        
        Args:
            msg: Email message object
            
        Returns:
            HTML body
        """
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/html':
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break
                    except Exception as e:
                        logger.warning(f"Error decoding HTML part: {e}")
        else:
            if msg.get_content_type() == 'text/html':
                try:
                    payload = msg.get_payload(decode=True)
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                except Exception as e:
                    logger.warning(f"Error decoding HTML body: {e}")
        
        return body
    
    @staticmethod
    def _extract_attachments(msg: email.message.Message) -> List[Dict[str, Any]]:
        """
        Extract attachments from email.
        
        Args:
            msg: Email message object
            
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                # Skip non-attachment parts
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                
                filename = part.get_filename()
                if filename:
                    # Decode filename if needed
                    filename = EmailParser._decode_header(filename)
                    
                    try:
                        content = part.get_payload(decode=True)
                        content_type = part.get_content_type()
                        content_id = part.get('Content-ID', '').strip('<>')
                        
                        attachments.append({
                            'filename': filename,
                            'content': content,
                            'content_type': content_type,
                            'content_id': content_id,
                            'size': len(content) if content else 0,
                            'is_inline': 'inline' in part.get('Content-Disposition', '').lower()
                        })
                    except Exception as e:
                        logger.warning(f"Error extracting attachment {filename}: {e}")
        
        return attachments
    
    @staticmethod
    def generate_snippet(text: str, max_length: int = 200) -> str:
        """
        Generate a short snippet from email body for preview.
        
        Args:
            text: Email body text
            max_length: Maximum length of snippet
            
        Returns:
            Snippet string
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate to max_length
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return text
