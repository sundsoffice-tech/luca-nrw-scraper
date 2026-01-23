"""
CRM Adapter - Direct integration with Django Lead model.
Replaces SQLite storage with direct CRM database writes.
"""

import os
import sys
import logging
from typing import Dict, Tuple, Optional, Any

logger = logging.getLogger(__name__)

# Ensure Django is initialized before importing models
def _ensure_django():
    """
    Ensure Django is properly configured and initialized.
    
    Returns:
        True if Django is available and ready, False otherwise
    """
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')
    
    try:
        import django
        from django.apps import apps
        
        if not apps.ready:
            # Add paths to sys.path for Django project discovery
            from pathlib import Path
            repo_root = Path(__file__).resolve().parent.parent
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            project_root = repo_root / "telis_recruitment"
            if project_root.exists() and str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            django.setup()
        
        return True
    except Exception as e:
        logger.warning(f"Django not available: {e}")
        return False

def upsert_lead_crm(data: Dict[str, Any]) -> Tuple[int, bool]:
    """
    Insert or update a lead directly in Django CRM.
    
    Args:
        data: Lead data with scraper field names
        
    Returns:
        Tuple of (lead_id, created) where created is True if new lead
    """
    if not _ensure_django():
        # Fallback to SQLite if Django unavailable
        logger.info("Django unavailable, falling back to SQLite")
        from .repository import upsert_lead_sqlite
        return upsert_lead_sqlite(data)
    
    try:
        from telis_recruitment.leads.models import Lead
        from telis_recruitment.leads.utils.normalization import normalize_email, normalize_phone
        
        # Extract and normalize search fields
        email = data.get('email')
        telefon = data.get('telefon')
        
        normalized_email = normalize_email(email)
        normalized_phone = normalize_phone(telefon)
        
        # Try to find existing lead
        existing = None
        if normalized_email:
            existing = Lead.objects.filter(email_normalized=normalized_email).first()
        if not existing and normalized_phone:
            existing = Lead.objects.filter(normalized_phone=normalized_phone).first()
        
        if existing:
            # Update existing lead if new data is better
            updated = False
            
            # Update quality score if better
            new_score = data.get('score', 0)
            if isinstance(new_score, (int, float)) and new_score > (existing.quality_score or 0):
                existing.quality_score = int(new_score)
                updated = True
            
            # Update empty fields with new data
            if not existing.company and data.get('company_name'):
                existing.company = str(data['company_name'])[:255]
                updated = True
            
            if not existing.role and data.get('rolle'):
                existing.role = str(data['rolle'])[:255]
                updated = True
            
            if not existing.location and data.get('region'):
                existing.location = str(data['region'])[:255]
                updated = True
            
            # Update source_url if not set
            source_url = data.get('quelle') or data.get('source_url')
            if not existing.source_url and source_url:
                existing.source_url = str(source_url)[:200]
                updated = True
            
            # Update other enrichment fields if they're better/new
            if data.get('ai_category') and not existing.ai_category:
                existing.ai_category = str(data['ai_category'])[:100]
                updated = True
            
            if data.get('ai_summary') and not existing.ai_summary:
                existing.ai_summary = str(data['ai_summary'])
                updated = True
            
            if data.get('opening_line') and not existing.opening_line:
                existing.opening_line = str(data['opening_line'])
                updated = True
            
            if updated:
                existing.save()
                logger.debug(f"Updated existing lead {existing.id} in Django CRM")
            
            return (existing.id, False)
        else:
            # Create new lead
            # Map scraper fields to Django model fields
            lead_data = {
                'name': str(data.get('name') or 'Unknown')[:255],
                'email': email,
                'telefon': telefon,
                'source': Lead.Source.SCRAPER,
                'quality_score': int(data.get('score', 50)),
            }
            
            # Add optional fields
            source_url = data.get('quelle') or data.get('source_url') or ''
            if source_url:
                lead_data['source_url'] = str(source_url)[:200]
            
            # Map lead_type
            lead_type_value = data.get('lead_type')
            lead_data['lead_type'] = _map_lead_type(lead_type_value)
            
            # Map other fields
            if data.get('company_name'):
                lead_data['company'] = str(data['company_name'])[:255]
            elif data.get('firma'):
                lead_data['company'] = str(data['firma'])[:255]
            
            if data.get('rolle'):
                lead_data['role'] = str(data['rolle'])[:255]
            elif data.get('position'):
                lead_data['role'] = str(data['position'])[:255]
            
            if data.get('region'):
                lead_data['location'] = str(data['region'])[:255]
            elif data.get('standort'):
                lead_data['location'] = str(data['standort'])[:255]
            
            # Add phone type
            if data.get('phone_type'):
                lead_data['phone_type'] = str(data['phone_type'])[:20]
            
            # Add WhatsApp link
            if data.get('whatsapp_link'):
                lead_data['whatsapp_link'] = str(data['whatsapp_link'])[:255]
            
            # Add AI enrichment fields
            if data.get('ai_category'):
                lead_data['ai_category'] = str(data['ai_category'])[:100]
            
            if data.get('ai_summary'):
                lead_data['ai_summary'] = str(data['ai_summary'])
            
            if data.get('opening_line'):
                lead_data['opening_line'] = str(data['opening_line'])
            
            # Add quality metrics
            if data.get('confidence_score') is not None:
                lead_data['confidence_score'] = int(data['confidence_score'])
            
            if data.get('data_quality') is not None:
                lead_data['data_quality'] = int(data['data_quality'])
            
            # Add salary/commission hints
            if data.get('salary_hint'):
                lead_data['salary_hint'] = str(data['salary_hint'])[:100]
            
            if data.get('commission_hint'):
                lead_data['commission_hint'] = str(data['commission_hint'])[:100]
            
            # Add company details
            if data.get('company_size'):
                lead_data['company_size'] = str(data['company_size'])[:100]
            
            if data.get('hiring_volume') is not None:
                try:
                    lead_data['hiring_volume'] = int(data['hiring_volume'])
                except (ValueError, TypeError):
                    pass
            
            if data.get('industry'):
                lead_data['industry'] = str(data['industry'])[:255]
            
            # Add candidate-specific fields
            if data.get('availability'):
                lead_data['availability'] = str(data['availability'])[:100]
            
            if data.get('candidate_status'):
                lead_data['candidate_status'] = str(data['candidate_status'])[:100]
            
            if data.get('mobility'):
                lead_data['mobility'] = str(data['mobility'])[:100]
            
            if data.get('experience_years') is not None:
                try:
                    lead_data['experience_years'] = int(data['experience_years'])
                except (ValueError, TypeError):
                    pass
            
            # Add profile/social fields
            if data.get('profile_url'):
                lead_data['profile_url'] = str(data['profile_url'])[:200]
            
            if data.get('cv_url'):
                lead_data['cv_url'] = str(data['cv_url'])[:200]
            
            if data.get('linkedin_url'):
                lead_data['linkedin_url'] = str(data['linkedin_url'])[:200]
            
            if data.get('xing_url'):
                lead_data['xing_url'] = str(data['xing_url'])[:200]
            
            # Add contact preference
            if data.get('contact_preference'):
                lead_data['contact_preference'] = str(data['contact_preference'])[:100]
            
            # Add metadata
            if data.get('recency_indicator'):
                lead_data['recency_indicator'] = str(data['recency_indicator'])[:100]
            
            if data.get('last_updated'):
                lead_data['last_updated'] = str(data['last_updated'])[:100]
            
            if data.get('profile_text'):
                lead_data['profile_text'] = str(data['profile_text'])
            
            if data.get('industries_experience'):
                lead_data['industries_experience'] = str(data['industries_experience'])
            
            if data.get('source_type'):
                lead_data['source_type'] = str(data['source_type'])[:50]
            
            if data.get('last_activity'):
                lead_data['last_activity'] = str(data['last_activity'])[:100]
            
            if data.get('name_validated') is not None:
                lead_data['name_validated'] = bool(data['name_validated'])
            
            if data.get('ssl_insecure'):
                lead_data['ssl_insecure'] = str(data['ssl_insecure'])[:20]
            
            # Handle JSON fields (tags, skills, qualifications)
            if data.get('tags'):
                tags = data['tags']
                if isinstance(tags, str):
                    # Try to parse JSON string
                    try:
                        import json
                        tags = json.loads(tags)
                    except:
                        # If not JSON, split by comma
                        tags = [t.strip() for t in tags.split(',') if t.strip()]
                if isinstance(tags, list):
                    lead_data['tags'] = tags
            
            if data.get('skills'):
                skills = data['skills']
                if isinstance(skills, str):
                    try:
                        import json
                        skills = json.loads(skills)
                    except:
                        skills = [s.strip() for s in skills.split(',') if s.strip()]
                if isinstance(skills, list):
                    lead_data['skills'] = skills
            
            if data.get('qualifications'):
                qualifications = data['qualifications']
                if isinstance(qualifications, str):
                    try:
                        import json
                        qualifications = json.loads(qualifications)
                    except:
                        qualifications = [q.strip() for q in qualifications.split(',') if q.strip()]
                if isinstance(qualifications, list):
                    lead_data['qualifications'] = qualifications
            
            lead = Lead.objects.create(**lead_data)
            logger.info(f"Created new lead {lead.id} in Django CRM")
            return (lead.id, True)
            
    except Exception as e:
        logger.error(f"Failed to save lead to CRM: {e}", exc_info=True)
        # Fallback to SQLite
        logger.info("Falling back to SQLite due to error")
        from .repository import upsert_lead_sqlite
        return upsert_lead_sqlite(data)

def _map_lead_type(lead_type: Optional[str]) -> str:
    """Map scraper lead type to Django Lead.LeadType."""
    if not lead_type:
        return 'unknown'
    
    try:
        from telis_recruitment.leads.models import Lead
        # Check if the lead_type is a valid choice
        valid_choices = dict(Lead.LeadType.choices)
        if lead_type in valid_choices:
            return lead_type
        return Lead.LeadType.UNKNOWN
    except:
        return 'unknown'

def sync_sqlite_to_crm(batch_size: int = 100) -> Dict[str, int]:
    """
    Sync all leads from SQLite to Django CRM.
    Use this to migrate existing data.
    
    Args:
        batch_size: Number of leads to process in each batch
    
    Returns:
        Stats dict with 'synced', 'skipped', 'errors' counts
    """
    if not _ensure_django():
        return {'error': 'Django not available'}
    
    from .connection import db
    
    stats = {'synced': 0, 'skipped': 0, 'errors': 0, 'total': 0}
    
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM leads")
        total = cur.fetchone()[0]
        stats['total'] = total
        
        logger.info(f"Starting sync of {total} leads from SQLite to Django CRM")
        
        # Fetch leads in batches
        offset = 0
        while True:
            cur.execute(f"SELECT * FROM leads LIMIT {batch_size} OFFSET {offset}")
            rows = cur.fetchall()
            
            if not rows:
                break
            
            for row in rows:
                try:
                    # Convert row to dict
                    data = dict(row)
                    
                    # Sync to CRM
                    lead_id, created = upsert_lead_crm(data)
                    
                    if created:
                        stats['synced'] += 1
                    else:
                        stats['skipped'] += 1
                        
                    # Log progress every 100 leads
                    processed = stats['synced'] + stats['skipped'] + stats['errors']
                    if processed % 100 == 0:
                        logger.info(f"Progress: {processed}/{total} leads processed")
                        
                except Exception as e:
                    logger.error(f"Failed to sync lead: {e}")
                    stats['errors'] += 1
            
            offset += batch_size
        
        logger.info(f"Sync complete: {stats['synced']} created, {stats['skipped']} updated, {stats['errors']} errors")
        
    except Exception as e:
        logger.error(f"Failed to sync SQLite to CRM: {e}", exc_info=True)
        stats['error'] = str(e)
    
    return stats


# Export public API
__all__ = [
    'upsert_lead_crm',
    'sync_sqlite_to_crm',
]
