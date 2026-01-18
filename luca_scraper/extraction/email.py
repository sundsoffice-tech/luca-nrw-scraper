# -*- coding: utf-8 -*-
"""
Email extraction, validation and normalization.

This module provides utilities for cleaning, normalizing, and validating email addresses.
"""

import re
from typing import List, Dict

# Private mail domains (not company emails)
PRIVATE_MAIL_DOMAINS = {
    "gmail.com", "gmx.de", "web.de", "t-online.de", "yahoo.de", 
    "outlook.com", "icloud.com", "hotmail.com", "aol.com", "freenet.de"
}

# Business email providers (not real company emails)
BUSINESS_MAIL_PROVIDERS = {
    "mailbox.org", "protonmail.com", "proton.me", "tutanota.com"
}


def clean_email(email: str) -> str:
    """
    Clean obfuscated email addresses.
    
    Removes common anti-spam text like "remove-this." and ".nospam".
    
    Args:
        email: Raw email address
        
    Returns:
        Cleaned email address
        
    Examples:
        >>> clean_email("test.remove-this.@example.com")
        'test@example.com'
        >>> clean_email("test.nospam@example.com")
        'test@example.com'
    """
    if not email:
        return ""
    return email.replace("remove-this.", "").replace(".nospam", "")


def normalize_email(e: str) -> str:
    """
    Normalize email addresses for deduplication.
    
    - Converts to lowercase
    - Removes dots from Gmail local part (gmail ignores dots)
    - Strips plus addressing (everything after +)
    
    Args:
        e: Email address to normalize
        
    Returns:
        Normalized email address
        
    Examples:
        >>> normalize_email("Test.User+tag@Gmail.com")
        'testuser@gmail.com'
        >>> normalize_email("user@EXAMPLE.COM")
        'user@example.com'
    """
    if not e:
        return ""
    e = clean_email(e.strip().lower())
    local, _, domain = e.partition("@")
    
    # Gmail normalization: ignore dots and plus addressing
    if domain == "gmail.com":
        local = local.split("+", 1)[0].replace(".", "")
    
    return f"{local}@{domain}"


def is_private_email(email: str) -> bool:
    """
    Check if email is from a private (non-business) domain.
    
    Args:
        email: Email address to check
        
    Returns:
        True if private email, False if business email
        
    Examples:
        >>> is_private_email("test@gmail.com")
        True
        >>> is_private_email("test@company.com")
        False
    """
    if not email or "@" not in email:
        return False
    
    domain = email.split("@")[-1].lower()
    return domain in PRIVATE_MAIL_DOMAINS or domain in BUSINESS_MAIL_PROVIDERS


def is_valid_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
        
    Examples:
        >>> is_valid_email("test@example.com")
        True
        >>> is_valid_email("invalid")
        False
    """
    if not email:
        return False
    
    # Basic RFC 5322 pattern (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def email_quality(email: str, page_url: str) -> str:
    """
    Assess email quality (private vs business).
    
    Args:
        email: Email address
        page_url: URL where email was found
        
    Returns:
        "private" for personal emails, "business" for company emails
        
    Examples:
        >>> email_quality("test@gmail.com", "https://example.com")
        'private'
        >>> email_quality("info@company.com", "https://company.com")
        'business'
    """
    if not email or not is_valid_email(email):
        return "unknown"
    
    if is_private_email(email):
        return "private"
    
    return "business"


def extract_emails_from_text(text: str) -> List[str]:
    """
    Extract all email addresses from text.
    
    Args:
        text: Text to search for emails
        
    Returns:
        List of unique email addresses found
        
    Examples:
        >>> extract_emails_from_text("Contact: test@example.com or admin@test.org")
        ['test@example.com', 'admin@test.org']
    """
    if not text:
        return []
    
    # Email pattern
    pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    emails = re.findall(pattern, text)
    
    # Clean and deduplicate
    cleaned = [clean_email(e.lower()) for e in emails]
    return list(dict.fromkeys(cleaned))  # Preserve order, remove duplicates
