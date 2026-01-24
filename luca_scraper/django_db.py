"""
LUCA NRW Scraper - Django ORM Adapter
======================================
Drop-in replacement for database.py using Django ORM instead of SQLite.

This module provides the same interface as the SQLite-based database.py,
but uses the Django ORM to interact with the Lead model in the CRM.
"""

from __future__ import annotations

import logging
import os
import json
import time
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Tuple

# Allow Django ORM calls from async contexts (scraper runs inside asyncio)
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

# Django setup - must happen before any Django imports
# Use the same settings module as manage.py (telis.settings), ensuring repo root is on sys.path.
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')

# Ensure repo root is on sys.path so 'telis', 'leads', and 'scraper_control' packages resolve
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
project_root = repo_root / "telis_recruitment"
if project_root.exists() and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# Also add parent directory to ensure scraper_control can be found
parent_dir = Path(__file__).resolve().parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import django
try:
    django.setup()
except Exception as exc:
    logging.warning("Django setup failed: %s", exc)

logger = logging.getLogger(__name__)

# Cache for lazy-loaded Django imports to avoid repeated imports
_django_imports_cache = None

# Lazy import helpers - import Django models only when needed
def _get_django_imports():
    """
    Lazily import Django models and utilities to avoid import errors.
    
    This function caches the imports on first call to avoid repeated import overhead.
    
    Returns:
        Dictionary containing Django models and utility functions
        
    Raises:
        ImportError: If Django models or utilities cannot be imported
        django.core.exceptions.AppRegistryNotReady: If Django is not properly initialized
        
    Note:
        Callers should ensure Django is initialized before calling this function.
        This is typically done by calling django.setup() at the module or application entry point.
    """
    global _django_imports_cache
    
    # Return cached imports if available
    if _django_imports_cache is not None:
        return _django_imports_cache
    
    # Import Django models and utilities
    from django.db import IntegrityError, transaction as django_transaction
    from django.apps import apps
    
    if TYPE_CHECKING:
        # For Pylance/mypy (static analysis)
        from telis_recruitment.leads.utils.normalization import normalize_email, normalize_phone
        from telis_recruitment.leads.field_mapping import (
            SCRAPER_TO_DJANGO_MAPPING,
            JSON_ARRAY_FIELDS,
            INTEGER_FIELDS,
            BOOLEAN_FIELDS,
        )
    else:
        # At runtime (Django resolves paths)
        from leads.utils.normalization import normalize_email, normalize_phone
        from leads.field_mapping import (
            SCRAPER_TO_DJANGO_MAPPING,
            JSON_ARRAY_FIELDS,
            INTEGER_FIELDS,
            BOOLEAN_FIELDS,
        )

    Lead = apps.get_model('leads', 'Lead')
    if Lead is None:
        raise LookupError("Lead model could not be found via Django apps registry")
    
    # Cache the imports for future calls
    _django_imports_cache = {
        'IntegrityError': IntegrityError,
        'django_transaction': django_transaction,
        'Lead': Lead,
        'normalize_email': normalize_email,
        'normalize_phone': normalize_phone,
        'SCRAPER_TO_DJANGO_MAPPING': SCRAPER_TO_DJANGO_MAPPING,
        'JSON_ARRAY_FIELDS': JSON_ARRAY_FIELDS,
        'INTEGER_FIELDS': INTEGER_FIELDS,
        'BOOLEAN_FIELDS': BOOLEAN_FIELDS,
    }
    
    return _django_imports_cache

# Transient error keywords that indicate retryable database errors
TRANSIENT_ERROR_KEYWORDS = [
    'database is locked',
    'connection',
    'timeout',
    'deadlock',
    'temporary',
    'locked',
    'busy'
]

def _map_scraper_data_to_django(data: Dict) -> Dict:
    """
    Map scraper data fields to Django Lead model fields.
    
    Args:
        data: Dictionary with scraper field names
        
    Returns:
        Dictionary with Django model field names
    """
    # Lazy import Django constants
    imports = _get_django_imports()
    SCRAPER_TO_DJANGO_MAPPING = imports['SCRAPER_TO_DJANGO_MAPPING']
    JSON_ARRAY_FIELDS = imports['JSON_ARRAY_FIELDS']
    INTEGER_FIELDS = imports['INTEGER_FIELDS']
    BOOLEAN_FIELDS = imports['BOOLEAN_FIELDS']
    
    mapped_data = {}
    unmapped_fields = []
    
    for scraper_field, value in data.items():
        # Skip None values and empty strings
        if value is None or value == '':
            continue
            
        # Get Django field name from mapping
        django_field = SCRAPER_TO_DJANGO_MAPPING.get(scraper_field)
        
        if django_field is None:
            # Field not in mapping - log it for visibility
            unmapped_fields.append(scraper_field)
            continue
        
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
    
    # Log unmapped fields for debugging and monitoring
    if unmapped_fields:
        logger.info(
            "Scraper fields not in SCRAPER_TO_DJANGO_MAPPING (skipped): %s. "
            "Consider adding to field_mapping.py if these should be imported.",
            unmapped_fields
        )
    
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
        'crm_status': lead.status,  # Map Django status to scraper crm_status
    }
    
    # Remove None values
    return {k: v for k, v in data.items() if v is not None}


def upsert_lead(data: Dict, max_retries: int = 3, retry_delay: float = 0.1) -> Tuple[int, bool]:
    """
    Insert or update a lead using Django ORM with optimized queries and retry logic.
    
    This implementation avoids N+1 queries by using a combination of:
    - Django's get_or_create/update for single-query upserts
    - Atomic transactions to ensure data consistency
    - Retry logic with exponential backoff for transient errors
    
    Deduplication logic:
    1. Try to get existing lead by email (case-insensitive)
    2. If not found by email, try by phone (normalized)
    3. If found, update; otherwise create
    
    Args:
        data: Dictionary with lead data (scraper field names)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 0.1)
        
    Returns:
        Tuple of (lead_id, created) where created is True if new lead was created
        
    Raises:
        Exception: If all retry attempts fail
    """
    # Lazy import Django modules
    imports = _get_django_imports()
    Lead = imports['Lead']
    normalize_email = imports['normalize_email']
    normalize_phone = imports['normalize_phone']
    django_transaction = imports['django_transaction']
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # Extract and normalize search fields
            email = data.get('email')
            telefon = data.get('telefon')
            
            normalized_email = normalize_email(email)
            normalized_phone = normalize_phone(telefon)
            
            # Map data to Django fields
            mapped_data = _map_scraper_data_to_django(data)
            
            # Ensure source is set to scraper
            if 'source' not in mapped_data:
                mapped_data['source'] = Lead.Source.SCRAPER
            
            with django_transaction.atomic():
                # Priority 1: Try to find by email
                existing_lead = None
                
                if normalized_email:
                    try:
                        existing_lead = Lead.objects.filter(email_normalized=normalized_email).first()
                    except Exception as exc:
                        logger.debug("Error searching by normalized email: %s", exc)
                
                # Priority 2: If not found by email, search by normalized phone
                if not existing_lead and normalized_phone:
                    try:
                        existing_lead = Lead.objects.filter(normalized_phone=normalized_phone).first()
                    except Exception as exc:
                        logger.debug("Error searching by normalized phone: %s", exc)
                
                # Update or create based on whether we found a lead
                if existing_lead:
                    # Update existing lead
                    for field, value in mapped_data.items():
                        setattr(existing_lead, field, value)
                    try:
                        existing_lead.save()
                        logger.debug(f"Successfully updated lead {existing_lead.id}")
                        return (existing_lead.id, False)
                    except Exception as exc:
                        # Handle potential constraint violations
                        logger.warning("Failed to update lead %d: %s", existing_lead.id, exc)
                        raise
                else:
                    # Create new lead
                    try:
                        new_lead = Lead.objects.create(**mapped_data)
                        logger.debug(f"Successfully created lead {new_lead.id}")
                        return (new_lead.id, True)
                    except Exception as exc:
                        # If create fails due to race condition, try to find and update
                        logger.debug("Create failed, attempting to find existing lead: %s", exc)
                        if normalized_email:
                            existing_lead = Lead.objects.filter(email_normalized=normalized_email).first()
                            if existing_lead:
                                for field, value in mapped_data.items():
                                    setattr(existing_lead, field, value)
                                existing_lead.save()
                                logger.debug(f"Recovered and updated lead {existing_lead.id} after race condition")
                                return (existing_lead.id, False)
                        # Re-raise if we couldn't recover
                        raise
        
        except Exception as exc:
            last_exception = exc
            # Check if this is a transient error that we should retry
            error_str = str(exc).lower()
            is_transient = any(keyword in error_str for keyword in TRANSIENT_ERROR_KEYWORDS)
            
            if is_transient and attempt < max_retries - 1:
                # Calculate exponential backoff delay
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    f"Transient error on attempt {attempt + 1}/{max_retries} for lead save: {exc}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)
            else:
                # Either not a transient error or we're out of retries
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to save lead after {max_retries} attempts. Last error: {exc}"
                    )
                raise




def get_lead_count() -> int:
    """
    Get total count of leads from Django ORM.
    
    Returns:
        Total number of leads
    """
    imports = _get_django_imports()
    Lead = imports['Lead']
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
    
    imports = _get_django_imports()
    Lead = imports['Lead']
    normalize_email = imports['normalize_email']
    normalize_phone = imports['normalize_phone']
    
    normalized_email = normalize_email(email)
    normalized_phone = normalize_phone(telefon)
    
    # Check by email first
    if normalized_email and Lead.objects.filter(email_normalized=normalized_email).exists():
        return True

    # Check by normalized phone column
    if normalized_phone and Lead.objects.filter(normalized_phone=normalized_phone).exists():
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
    imports = _get_django_imports()
    Lead = imports['Lead']
    
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
    imports = _get_django_imports()
    Lead = imports['Lead']
    django_transaction = imports['django_transaction']
    
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


def is_url_seen(url: str) -> bool:
    """
    Check if a URL has been seen before.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL has been seen, False otherwise
    """
    from scraper_control.models import UrlSeen
    return UrlSeen.objects.filter(url=url).exists()


def mark_url_seen(url: str, run_id: Optional[int] = None) -> None:
    """
    Mark a URL as seen.
    
    Args:
        url: URL to mark as seen
        run_id: Optional scraper run ID
    """
    from scraper_control.models import UrlSeen, ScraperRun
    
    defaults = {}

    if run_id:
        if ScraperRun.objects.filter(id=run_id).exists():
            defaults['first_run_id'] = run_id
        else:
            logger.warning(f"ScraperRun with id {run_id} not found")

    UrlSeen.objects.get_or_create(url=url, defaults=defaults)


def is_query_done(query: str, ttl_hours: int = 48) -> bool:
    """
    Check if a query has been executed before within TTL window.
    
    Args:
        query: Search query to check
        ttl_hours: Time-to-live in hours (default: 48)
        
    Returns:
        True if query has been executed recently, False otherwise
    """
    from scraper_control.models import QueryDone
    from django.utils import timezone
    from datetime import timedelta
    
    # Calculate cutoff time
    cutoff = timezone.now() - timedelta(hours=ttl_hours)
    
    # Check if query exists and was executed within TTL window
    return QueryDone.objects.filter(
        query=query,
        last_executed_at__gte=cutoff
    ).exists()


def mark_query_done(query: str, run_id: Optional[int] = None) -> None:
    """
    Mark a query as executed with current timestamp.
    
    Args:
        query: Search query to mark as done
        run_id: Optional scraper run ID
    """
    from scraper_control.models import QueryDone
    from django.utils import timezone
    
    # Update or create with current timestamp
    # Note: last_executed_at has auto_now=True, so it updates automatically
    defaults = {}
    if run_id:
        defaults['last_run_id'] = run_id
    
    QueryDone.objects.update_or_create(
        query=query,
        defaults=defaults
    )


def cleanup_expired_queries(ttl_hours: int = 48) -> int:
    """
    Delete expired query cache entries.
    
    Args:
        ttl_hours: Time-to-live in hours
        
    Returns:
        Number of deleted entries
    """
    from scraper_control.models import QueryDone
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(hours=ttl_hours)
    
    # Delete old queries
    deleted, _ = QueryDone.objects.filter(
        last_executed_at__lt=cutoff
    ).delete()
    
    logger.info(f"Cleaned up {deleted} expired query cache entries (older than {ttl_hours}h)")
    return deleted


def cleanup_expired_urls(ttl_hours: int = 168) -> int:
    """
    Delete expired URL seen cache entries.
    
    Args:
        ttl_hours: Time-to-live in hours (default: 7 days = 168 hours)
        
    Returns:
        Number of deleted entries
    """
    from scraper_control.models import UrlSeen
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(hours=ttl_hours)
    
    # Delete old URLs
    deleted, _ = UrlSeen.objects.filter(
        created_at__lt=cutoff
    ).delete()
    
    logger.info(f"Cleaned up {deleted} expired URL cache entries (older than {ttl_hours}h)")
    return deleted


def start_scraper_run() -> int:
    """
    Start a new scraper run.
    
    Returns:
        ID of the created scraper run
    """
    from scraper_control.models import ScraperRun
    
    run = ScraperRun.objects.create(
        status='running',
        links_checked=0,
        leads_found=0
    )
    return run.id


def finish_scraper_run(
    run_id: int,
    links_checked: Optional[int] = None,
    leads_new: Optional[int] = None,
    status: str = "completed",
    metrics: Optional[Dict] = None
) -> None:
    """
    Finish a scraper run and update its metrics.
    
    Args:
        run_id: ID of the scraper run to finish
        links_checked: Number of links checked
        leads_new: Number of new leads found
        status: Status of the run (completed, failed, stopped, etc.)
        metrics: Optional dictionary of additional metrics
    """
    from scraper_control.models import ScraperRun
    from django.utils import timezone
    
    try:
        run = ScraperRun.objects.get(id=run_id)
        
        # Update basic fields
        run.finished_at = timezone.now()
        run.status = status
        
        if links_checked is not None:
            run.links_checked = links_checked
        
        if leads_new is not None:
            run.leads_found = leads_new
        
        # Update metrics if provided
        if metrics:
            # Map metrics to ScraperRun fields
            if 'links_successful' in metrics:
                run.links_successful = metrics['links_successful']
            if 'links_failed' in metrics:
                run.links_failed = metrics['links_failed']
            if 'leads_accepted' in metrics:
                run.leads_accepted = metrics['leads_accepted']
            if 'leads_rejected' in metrics:
                run.leads_rejected = metrics['leads_rejected']
            if 'avg_request_time_ms' in metrics:
                run.avg_request_time_ms = metrics['avg_request_time_ms']
            if 'block_rate' in metrics:
                run.block_rate = metrics['block_rate']
            if 'timeout_rate' in metrics:
                run.timeout_rate = metrics['timeout_rate']
            if 'error_rate' in metrics:
                run.error_rate = metrics['error_rate']
            if 'circuit_breaker_triggered' in metrics:
                run.circuit_breaker_triggered = metrics['circuit_breaker_triggered']
            if 'circuit_breaker_count' in metrics:
                run.circuit_breaker_count = metrics['circuit_breaker_count']
            if 'portal_stats' in metrics:
                run.portal_stats = metrics['portal_stats']
        
        run.save()
        
    except ScraperRun.DoesNotExist:
        logger.error(f"ScraperRun with id {run_id} not found")


# Export public API
__all__ = [
    'upsert_lead',
    'get_lead_count',
    'lead_exists',
    'get_lead_by_id',
    'update_lead',
    'is_url_seen',
    'mark_url_seen',
    'is_query_done',
    'mark_query_done',
    'cleanup_expired_queries',
    'cleanup_expired_urls',
    'start_scraper_run',
    'finish_scraper_run',
]
