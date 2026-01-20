"""
LUCA NRW Scraper - Django ORM Adapter
======================================
Drop-in replacement for database.py using Django ORM instead of SQLite.

This module provides the same interface as the SQLite-based database.py,
but uses the Django ORM to interact with the Lead model in the CRM.
"""

import logging
import os
import json
from typing import Dict, Optional, Tuple

# Django setup - must happen before any Django imports
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis_recruitment.telis.settings')

import django
try:
    django.setup()
except Exception as exc:
    logging.warning("Django setup failed: %s", exc)

# Now we can import Django models and utilities
from django.db import transaction as django_transaction
from telis_recruitment.leads.models import Lead
from telis_recruitment.leads.field_mapping import (
    SCRAPER_TO_DJANGO_MAPPING,
    JSON_ARRAY_FIELDS,
    INTEGER_FIELDS,
    BOOLEAN_FIELDS,
)

logger = logging.getLogger(__name__)


def _normalize_email(value: Optional[str]) -> Optional[str]:
    """Normalize emails for matching by trimming and lower-casing."""
    if not value:
        return None
    return value.strip().lower()


def _normalize_phone(value: Optional[str]) -> Optional[str]:
    """Keep only digits when normalizing phone numbers for lookup."""
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or None


def _map_scraper_data_to_django(data: Dict) -> Dict:
    """
    Map scraper data fields to Django Lead model fields.
    
    Args:
        data: Dictionary with scraper field names
        
    Returns:
        Dictionary with Django model field names
    """
    mapped_data = {}
    
    for scraper_field, value in data.items():
        # Skip None values and empty strings
        if value is None or value == '':
            continue
            
        # Get Django field name from mapping
        django_field = SCRAPER_TO_DJANGO_MAPPING.get(scraper_field, scraper_field)
        
        # Handle JSON fields (tags, skills, qualifications)
        if scraper_field in JSON_ARRAY_FIELDS:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    # If it's a string that's not valid JSON, convert to array
                    value = [v.strip() for v in value.split(',') if v.strip()]
        
        # Handle integer fields
        elif scraper_field in INTEGER_FIELDS:
            try:
                value = int(value)
            except (ValueError, TypeError):
                continue
        
        # Handle boolean fields
        elif scraper_field in BOOLEAN_FIELDS:
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'ja')
            else:
                value = bool(value)
        
        mapped_data[django_field] = value
    
    return mapped_data


def _map_django_to_scraper(lead: Lead) -> Dict:
    """
    Convert Django Lead model instance to scraper-compatible dictionary.
    
    Args:
        lead: Django Lead model instance
        
    Returns:
        Dictionary with scraper field names
    """
    data = {
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'telefon': lead.telefon,
        'phone_type': lead.phone_type,
        'whatsapp_link': lead.whatsapp_link,
        'rolle': lead.role,
        'company_name': lead.company,
        'region': lead.location,
        'quelle': lead.source_url,
        'score': lead.quality_score,
        'confidence_score': lead.confidence_score,
        'data_quality': lead.data_quality,
        'lead_type': lead.lead_type,
        'ai_category': lead.ai_category,
        'ai_summary': lead.ai_summary,
        'opening_line': lead.opening_line,
        'tags': lead.tags,
        'skills': lead.skills,
        'availability': lead.availability,
        'candidate_status': lead.candidate_status,
        'mobility': lead.mobility,
        'experience_years': lead.experience_years,
        'salary_hint': lead.salary_hint,
        'commission_hint': lead.commission_hint,
        'company_size': lead.company_size,
        'hiring_volume': lead.hiring_volume,
        'industry': lead.industry,
        'private_address': lead.private_address,
        'profile_url': lead.profile_url,
        'cv_url': lead.cv_url,
        'contact_preference': lead.contact_preference,
        'recency_indicator': lead.recency_indicator,
        'last_updated': lead.last_updated,
        'profile_text': lead.profile_text,
        'industries_experience': lead.industries_experience,
        'source_type': lead.source_type,
        'last_activity': lead.last_activity,
        'name_validated': lead.name_validated,
        'ssl_insecure': lead.ssl_insecure,
        'crm_status': lead.status,
    }
    
    # Remove None values
    return {k: v for k, v in data.items() if v is not None}


def upsert_lead(data: Dict) -> Tuple[int, bool]:
    """
    Insert or update a lead using Django ORM.
    
    Deduplication logic:
    1. First check by email (if provided and not empty)
    2. Then check by phone (if provided and not empty)
    3. If found, update existing lead
    4. Otherwise, create new lead
    
    Args:
        data: Dictionary with lead data (scraper field names)
        
    Returns:
        Tuple of (lead_id, created) where created is True if new lead was created
    """
    with django_transaction.atomic():
        # Extract and normalize search fields
        email = data.get('email')
        telefon = data.get('telefon')
        
        normalized_email = _normalize_email(email)
        normalized_phone = _normalize_phone(telefon)
        
        # Try to find existing lead
        existing_lead = None
        
        # Priority 1: Search by email
        if normalized_email:
            try:
                existing_lead = Lead.objects.filter(
                    email__iexact=normalized_email
                ).first()
            except Exception as exc:
                logger.debug("Error searching by email: %s", exc)
        
        # Priority 2: Search by phone if not found by email
        # Note: We use a custom lookup that checks if normalized phone digits
        # are contained in the stored phone number to handle different formats
        # (e.g., +49123456789, 0049123456789, 0123456789)
        if not existing_lead and normalized_phone:
            try:
                # Query all leads and filter in Python for normalized phone match
                # This is more flexible than DB regex but may be less efficient for very large datasets
                for lead in Lead.objects.exclude(telefon__isnull=True).exclude(telefon=''):
                    stored_normalized = _normalize_phone(lead.telefon)
                    if stored_normalized and stored_normalized == normalized_phone:
                        existing_lead = lead
                        break
            except Exception as exc:
                logger.debug("Error searching by phone: %s", exc)
        
        # Map data to Django fields
        mapped_data = _map_scraper_data_to_django(data)
        
        # Ensure source is set to scraper
        if 'source' not in mapped_data:
            mapped_data['source'] = Lead.Source.SCRAPER
        
        if existing_lead:
            # Update existing lead
            for field, value in mapped_data.items():
                setattr(existing_lead, field, value)
            existing_lead.save()
            return (existing_lead.id, False)
        else:
            # Create new lead
            new_lead = Lead.objects.create(**mapped_data)
            return (new_lead.id, True)


def get_lead_count() -> int:
    """
    Get total count of leads from Django ORM.
    
    Returns:
        Total number of leads
    """
    return Lead.objects.count()


def lead_exists(email: Optional[str] = None, telefon: Optional[str] = None) -> bool:
    """
    Check if a lead exists by email or phone.
    
    Args:
        email: Email address to search for
        telefon: Phone number to search for
        
    Returns:
        True if lead exists, False otherwise
    """
    if not email and not telefon:
        return False
    
    normalized_email = _normalize_email(email)
    normalized_phone = _normalize_phone(telefon)
    
    # Check by email first
    if normalized_email:
        if Lead.objects.filter(email__iexact=normalized_email).exists():
            return True
    
    # Check by phone
    if normalized_phone:
        # Query all leads and filter in Python for normalized phone match
        for lead in Lead.objects.exclude(telefon__isnull=True).exclude(telefon=''):
            stored_normalized = _normalize_phone(lead.telefon)
            if stored_normalized and stored_normalized == normalized_phone:
                return True
    
    return False


def get_lead_by_id(lead_id: int) -> Optional[Dict]:
    """
    Get a lead by its ID.
    
    Args:
        lead_id: Lead ID to retrieve
        
    Returns:
        Dictionary with lead data (scraper field names) or None if not found
    """
    try:
        lead = Lead.objects.get(id=lead_id)
        return _map_django_to_scraper(lead)
    except Lead.DoesNotExist:
        return None


def update_lead(lead_id: int, data: Dict) -> bool:
    """
    Update an existing lead.
    
    Args:
        lead_id: Lead ID to update
        data: Dictionary with lead data to update (scraper field names)
        
    Returns:
        True if lead was updated, False if lead not found
    """
    try:
        with django_transaction.atomic():
            lead = Lead.objects.get(id=lead_id)
            
            # Map data to Django fields
            mapped_data = _map_scraper_data_to_django(data)
            
            # Update fields
            for field, value in mapped_data.items():
                setattr(lead, field, value)
            
            lead.save()
            return True
    except Lead.DoesNotExist:
        return False


# Export public API
__all__ = [
    'upsert_lead',
    'get_lead_count',
    'lead_exists',
    'get_lead_by_id',
    'update_lead',
]
