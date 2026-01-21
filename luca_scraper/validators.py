"""
Input validation for URLs, emails, phone numbers, and lead data.

Provides comprehensive validation to prevent security issues and data quality problems.
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urlunparse


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    import json
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    print(f"[{ts}] [{level.upper():7}] {msg}{ctx_str}", flush=True)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class URLValidator:
    """
    Validates and sanitizes URLs for security and correctness.
    
    Features:
    - Scheme whitelist (http, https)
    - Maximum URL length check (2048 chars)
    - Dangerous pattern detection (javascript:, data:, file:)
    - URL sanitization
    """
    
    # Maximum URL length per RFC 2616
    MAX_URL_LENGTH = 2048
    
    # Allowed URL schemes
    ALLOWED_SCHEMES = {'http', 'https'}
    
    # Dangerous URL patterns that should be rejected
    DANGEROUS_PATTERNS = [
        r'javascript:',
        r'data:',
        r'file:',
        r'vbscript:',
        r'about:',
    ]
    
    @classmethod
    def validate(cls, url: str, allow_relative: bool = False) -> bool:
        """
        Validate a URL for security and correctness.
        
        Args:
            url: URL to validate
            allow_relative: Whether to allow relative URLs (default: False)
            
        Returns:
            True if URL is valid
            
        Raises:
            ValidationError: If URL is invalid
            
        Example:
            >>> URLValidator.validate("https://example.com/path")
            True
            >>> URLValidator.validate("javascript:alert(1)")  # Raises ValidationError
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string")
        
        # Check length
        if len(url) > cls.MAX_URL_LENGTH:
            raise ValidationError(
                f"URL exceeds maximum length of {cls.MAX_URL_LENGTH} characters"
            )
        
        # Check for dangerous patterns
        url_lower = url.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, url_lower):
                raise ValidationError(
                    f"URL contains dangerous pattern: {pattern}"
                )
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(f"Failed to parse URL: {e}")
        
        # Check scheme
        if parsed.scheme:
            if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
                raise ValidationError(
                    f"URL scheme '{parsed.scheme}' not allowed. "
                    f"Allowed: {', '.join(cls.ALLOWED_SCHEMES)}"
                )
        elif not allow_relative:
            raise ValidationError("URL must have a scheme (http or https)")
        
        # Validate hostname for absolute URLs
        if not allow_relative and not parsed.netloc:
            raise ValidationError("URL must have a hostname")
        
        return True
    
    @classmethod
    def sanitize(cls, url: str) -> str:
        """
        Sanitize a URL by removing dangerous components.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
            
        Example:
            >>> URLValidator.sanitize("https://example.com/path?query=1#fragment")
            'https://example.com/path?query=1'
        """
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            
            # Remove fragment (everything after #)
            sanitized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                ''  # Remove fragment
            ))
            
            return sanitized.strip()
        except Exception as e:
            log("warn", "Failed to sanitize URL", url=url, error=str(e))
            return url.strip()
    
    @classmethod
    def is_safe(cls, url: str) -> bool:
        """
        Check if URL is safe without raising exceptions.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is safe, False otherwise
            
        Example:
            >>> URLValidator.is_safe("https://example.com")
            True
            >>> URLValidator.is_safe("javascript:alert(1)")
            False
        """
        try:
            cls.validate(url)
            return True
        except ValidationError:
            return False


class DataValidator:
    """
    Validates extracted data like emails, phone numbers, and leads.
    
    Features:
    - Email validation with regex
    - Phone number validation
    - Lead validation (requires email or phone)
    """
    
    # Email regex pattern (basic but effective)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Phone number pattern (international format with optional +, spaces, dashes)
    PHONE_PATTERN = re.compile(
        r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$'
    )
    
    # Minimum phone number length (excluding formatting)
    MIN_PHONE_DIGITS = 7
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid
            
        Raises:
            ValidationError: If email is invalid
            
        Example:
            >>> DataValidator.validate_email("test@example.com")
            True
            >>> DataValidator.validate_email("invalid.email")  # Raises ValidationError
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")
        
        email = email.strip()
        
        # Check length
        if len(email) > 254:  # RFC 5321
            raise ValidationError("Email exceeds maximum length of 254 characters")
        
        # Check pattern
        if not cls.EMAIL_PATTERN.match(email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return True
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        Validate a phone number.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if phone is valid
            
        Raises:
            ValidationError: If phone is invalid
            
        Example:
            >>> DataValidator.validate_phone("+49 123 4567890")
            True
            >>> DataValidator.validate_phone("abc")  # Raises ValidationError
        """
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone must be a non-empty string")
        
        phone = phone.strip()
        
        # Extract digits only
        digits = re.sub(r'\D', '', phone)
        
        # Check minimum length
        if len(digits) < cls.MIN_PHONE_DIGITS:
            raise ValidationError(
                f"Phone number must have at least {cls.MIN_PHONE_DIGITS} digits"
            )
        
        # Check pattern (allows international format)
        if not cls.PHONE_PATTERN.match(phone):
            raise ValidationError(f"Invalid phone format: {phone}")
        
        return True
    
    @classmethod
    def validate_lead(cls, lead_data: Dict[str, Any]) -> bool:
        """
        Validate a lead record.
        
        Requires at least one of: email or phone
        
        Args:
            lead_data: Dictionary containing lead data
            
        Returns:
            True if lead is valid
            
        Raises:
            ValidationError: If lead is invalid
            
        Example:
            >>> DataValidator.validate_lead({"email": "test@example.com"})
            True
            >>> DataValidator.validate_lead({"name": "John"})  # Raises ValidationError
        """
        if not isinstance(lead_data, dict):
            raise ValidationError("Lead data must be a dictionary")
        
        email = lead_data.get('email', '').strip()
        phone = lead_data.get('phone', '').strip()
        
        # At least one contact method is required
        if not email and not phone:
            raise ValidationError(
                "Lead must have at least one contact method (email or phone)"
            )
        
        # Validate email if present
        if email:
            try:
                cls.validate_email(email)
            except ValidationError as e:
                raise ValidationError(f"Invalid email in lead: {e}")
        
        # Validate phone if present
        if phone:
            try:
                cls.validate_phone(phone)
            except ValidationError as e:
                raise ValidationError(f"Invalid phone in lead: {e}")
        
        return True
    
    @classmethod
    def is_valid_email(cls, email: str) -> bool:
        """
        Check if email is valid without raising exceptions.
        
        Args:
            email: Email to check
            
        Returns:
            True if email is valid, False otherwise
        """
        try:
            cls.validate_email(email)
            return True
        except ValidationError:
            return False
    
    @classmethod
    def is_valid_phone(cls, phone: str) -> bool:
        """
        Check if phone is valid without raising exceptions.
        
        Args:
            phone: Phone to check
            
        Returns:
            True if phone is valid, False otherwise
        """
        try:
            cls.validate_phone(phone)
            return True
        except ValidationError:
            return False
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """
        Sanitize an email address.
        
        Args:
            email: Email to sanitize
            
        Returns:
            Sanitized email (lowercase, trimmed)
        """
        if not email:
            return ""
        return email.strip().lower()
    
    @classmethod
    def sanitize_phone(cls, phone: str) -> str:
        """
        Sanitize a phone number by removing non-digit characters except +.
        
        Args:
            phone: Phone to sanitize
            
        Returns:
            Sanitized phone number
        """
        if not phone:
            return ""
        
        # Keep + at the start if present
        phone = phone.strip()
        has_plus = phone.startswith('+')
        
        # Remove all non-digits except the leading +
        digits = re.sub(r'\D', '', phone)
        
        return f"+{digits}" if has_plus else digits
