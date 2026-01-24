"""
Central field mapping for Lead data synchronization.

This module provides canonical field name mappings between:
- scraper.db (SQLite)
- Django Lead model
- Various data sources

Usage:
    from leads.field_mapping import SCRAPER_TO_DJANGO_MAPPING, get_canonical_field
    
    django_field = SCRAPER_TO_DJANGO_MAPPING.get(scraper_field, scraper_field)
"""

# Canonical field schema - maps various field name variations to canonical names
FIELD_SCHEMA = {
    'phone': ['telefon', 'phone', 'telefonnummer', 'phone_number'],
    'role': ['rolle', 'role', 'role_guess', 'position'],
    'location': ['region', 'location', 'location_specific', 'standort', 'city'],
    'company': ['company_name', 'company', 'firma'],
    'score': ['score', 'quality_score'],
    'source': ['quelle', 'source_url', 'source'],
    'email': ['email', 'e_mail', 'mail'],
    'name': ['name', 'full_name', 'contact_name'],
    'ai_category': ['ai_category', 'ai_label', 'ai_kategorie'],
    'ai_summary': ['ai_summary', 'ai_zusammenfassung', 'ai_insight', 'ai_note'],
    'skills': ['skills', 'skillset', 'kompetenzen', 'skill_tags'],
    'qualifications': ['qualifications', 'qualification', 'qualifikationen', 'education', 'certifications'],
}

# Scraper DB â†’ Django Model field mapping
# Maps scraper.db column names to Django Lead model field names
SCRAPER_TO_DJANGO_MAPPING = {
    # Core fields
    'name': 'name',
    'email': 'email',
    'telefon': 'telefon',
    
    # Role and company
    'rolle': 'role',
    'role_guess': 'role',
    'company_name': 'company',
    'firma': 'company',
    'firma_groesse': 'company_size',
    
    # Location
    'region': 'location',
    'location_specific': 'location',
    'location': 'location',
    
    # Source
    'quelle': 'source_url',
    'source_url': 'source_url',
    
    # Quality and scoring
    'score': 'quality_score',
    'quality_score': 'quality_score',
    'confidence_score': 'confidence_score',
    'data_quality': 'data_quality',
    
    # Lead classification
    'lead_type': 'lead_type',
    
    # Phone details
    'phone_type': 'phone_type',
    'whatsapp_link': 'whatsapp_link',
    
    # AI fields
    'ai_category': 'ai_category',
    'ai_summary': 'ai_summary',
    'opening_line': 'opening_line',
    
    # Arrays/Lists (stored as JSON)
    'tags': 'tags',
    'skills': 'skills',
    'qualifications': 'qualifications',
    
    # Candidate-specific
    'availability': 'availability',
    'candidate_status': 'candidate_status',
    'current_status': 'candidate_status',  # alias
    'mobility': 'mobility',
    'experience_years': 'experience_years',
    
    # Company details
    'salary_hint': 'salary_hint',
    'commission_hint': 'commission_hint',
    'company_size': 'company_size',
    'hiring_volume': 'hiring_volume',
    'industry': 'industry',
    'industries': 'industry',  # alias
    
    # Contact details
    'private_address': 'private_address',
    'profile_url': 'profile_url',
    'social_profile_url': 'profile_url',  # alias to profile_url
    'cv_url': 'cv_url',
    'contact_preference': 'contact_preference',
    
    # Social profiles
    'linkedin_url': 'linkedin_url',
    'xing_url': 'xing_url',
    
    # Metadata
    'recency_indicator': 'recency_indicator',
    'last_updated': 'last_updated',
    
    # Additional scraper fields
    'profile_text': 'profile_text',
    'industries_experience': 'industries_experience',
    'source_type': 'source_type',
    'last_activity': 'last_activity',
    'name_validated': 'name_validated',
    'ssl_insecure': 'ssl_insecure',
    
    # CRM synchronization
    'crm_status': 'status',  # Maps scraper's crm_status to Django's status field
}

# Django Model â†’ Scraper DB reverse mapping
# Note: When multiple scraper fields map to the same Django field,
# only the first occurrence is preserved in the reverse mapping.
# This is by design as the mapping is primarily used for scraper â†’ Django direction.
DJANGO_TO_SCRAPER_MAPPING = {}
for scraper_field, django_field in SCRAPER_TO_DJANGO_MAPPING.items():
    # Only set if not already set (preserves first mapping)
    if django_field not in DJANGO_TO_SCRAPER_MAPPING:
        DJANGO_TO_SCRAPER_MAPPING[django_field] = scraper_field

# Fields that should be treated as JSON arrays
JSON_ARRAY_FIELDS = ['tags', 'skills', 'qualifications']

# Fields that should be treated as JSON objects
JSON_OBJECT_FIELDS = []

# Fields that are integers
INTEGER_FIELDS = [
    'score', 'quality_score', 'confidence_score', 'data_quality',
    'experience_years', 'hiring_volume'
]

# Fields that are booleans
BOOLEAN_FIELDS = ['name_validated']

# Fields that should be URLs
URL_FIELDS = [
    'source_url', 'profile_url', 'cv_url', 'linkedin_url', 'xing_url', 'quelle'
]


def get_canonical_field(field_name):
    """
    Get the canonical field name for a given field variation.
    
    Args:
        field_name: Field name to look up
        
    Returns:
        Canonical field name or the original if not found
    """
    field_lower = field_name.lower()
    
    for canonical, variations in FIELD_SCHEMA.items():
        if field_lower in [v.lower() for v in variations]:
            return canonical
    
    return field_name


def map_scraper_to_django(scraper_field):
    """
    Map a scraper.db field name to Django Lead model field name.
    
    Args:
        scraper_field: Field name from scraper.db
        
    Returns:
        Django model field name or None if not mapped
    """
    return SCRAPER_TO_DJANGO_MAPPING.get(scraper_field)


def map_django_to_scraper(django_field):
    """
    Map a Django Lead model field name to scraper.db field name.
    
    Args:
        django_field: Field name from Django model
        
    Returns:
        scraper.db field name or None if not mapped
    """
    # Return first occurrence (primary mapping)
    for scraper_field, mapped_django in SCRAPER_TO_DJANGO_MAPPING.items():
        if mapped_django == django_field:
            return scraper_field
    return None


def is_json_field(field_name):
    """Check if a field should be treated as JSON."""
    return field_name in JSON_ARRAY_FIELDS or field_name in JSON_OBJECT_FIELDS


def is_integer_field(field_name):
    """Check if a field should be treated as an integer."""
    return field_name in INTEGER_FIELDS


def is_boolean_field(field_name):
    """Check if a field should be treated as a boolean."""
    return field_name in BOOLEAN_FIELDS


def is_url_field(field_name):
    """Check if a field should be treated as a URL."""
    return field_name in URL_FIELDS

