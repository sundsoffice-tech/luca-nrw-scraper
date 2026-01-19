"""
API views for the leads application.

Required Environment Variables:
- BREVO_WEBHOOK_SECRET: Secret key for Brevo webhook signature verification
                        Get this from Brevo Dashboard > Settings > Webhooks

Optional Settings:
- ALLOWED_SCRAPER_DB_PATHS: List of additional allowed database paths for sync
"""

import json
import csv
import io
import logging
import hmac
import hashlib
import os
import threading
import sqlite3
import re
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django_ratelimit.decorators import ratelimit
from django.utils import timezone
from django.utils.timesince import timesince

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action

from .models import Lead, CallLog, EmailLog, SavedFilter
from .serializers import LeadSerializer, LeadListSerializer, CallLogSerializer, EmailLogSerializer
from .permissions import IsManager, IsTelefonist
from telis.config import API_RATE_LIMIT_OPT_IN, API_RATE_LIMIT_IMPORT

logger = logging.getLogger(__name__)

# Constants
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 255
MAX_CSV_ERRORS = 100

# Validation patterns
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
"""
Email validation pattern.
Validates standard email format: local@domain.tld
- Local part: alphanumeric, dots, underscores, percent, plus, hyphens
- Domain: alphanumeric, dots, hyphens
- TLD: minimum 2 characters
Note: For production use, consider Django's EmailValidator for better coverage.
"""

PHONE_REGEX = re.compile(r'^[\d\s\-\+\(\)\/]{6,25}$')
"""
Phone number validation pattern.
Accepts various international formats with:
- Digits (0-9)
- Spaces, hyphens, plus signs, parentheses, forward slashes
- Length: 6-25 characters
Examples: +49 123 456789, (123) 456-7890, 0123456789
"""


class LeadPagination(PageNumberPagination):
    """Pagination for Lead list endpoints."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Lead instances.
    """
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LeadPagination
    
    def get_serializer_class(self):
        """Use a more compact serializer for list actions"""
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer
    
    def get_queryset(self):
        """
        Optionally restricts the returned leads by filtering against
        query parameters in the URL.
        """
        queryset = Lead.objects.all().order_by('-created_at')
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by source
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by lead type
        lead_type = self.request.query_params.get('lead_type', None)
        if lead_type:
            queryset = queryset.filter(lead_type=lead_type)
        
        # Filter by minimum quality score
        min_score = self.request.query_params.get('min_score', None)
        if min_score:
            queryset = queryset.filter(quality_score__gte=min_score)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(telefon__icontains=search) |
                Q(company__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def batch_update_status(self, request):
        """Batch update status for multiple leads."""
        lead_ids = request.data.get('lead_ids', [])
        new_status = request.data.get('status')
        
        if not lead_ids or not new_status:
            return Response({
                'success': False,
                'error': 'lead_ids and status are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status not in dict(Lead.Status.choices):
            return Response({
                'success': False,
                'error': 'Invalid status value'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        leads_qs = _get_leads_queryset_for_user(request.user)
        updated_count = leads_qs.filter(id__in=lead_ids).update(status=new_status)
        
        return Response({
            'success': True,
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def batch_add_tags(self, request):
        """Batch add tags to multiple leads."""
        lead_ids = request.data.get('lead_ids', [])
        tags_to_add = request.data.get('tags', [])
        
        if not lead_ids or not tags_to_add:
            return Response({
                'success': False,
                'error': 'lead_ids and tags are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        leads_qs = _get_leads_queryset_for_user(request.user)
        leads = leads_qs.filter(id__in=lead_ids)
        
        updated_count = 0
        for lead in leads:
            current_tags = lead.tags or []
            # Add new tags if not already present
            for tag in tags_to_add:
                if tag not in current_tags:
                    current_tags.append(tag)
            lead.tags = current_tags
            lead.save()
            updated_count += 1
        
        return Response({
            'success': True,
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def batch_assign(self, request):
        """Batch assign leads to a user."""
        lead_ids = request.data.get('lead_ids', [])
        user_id = request.data.get('user_id')
        
        if not lead_ids or not user_id:
            return Response({
                'success': False,
                'error': 'lead_ids and user_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assigned_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        leads_qs = _get_leads_queryset_for_user(request.user)
        updated_count = leads_qs.filter(id__in=lead_ids).update(assigned_to=assigned_user)
        
        return Response({
            'success': True,
            'updated_count': updated_count,
            'assigned_to': assigned_user.get_full_name() or assigned_user.username
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def batch_delete(self, request):
        """Batch delete leads."""
        lead_ids = request.data.get('lead_ids', [])
        
        if not lead_ids:
            return Response({
                'success': False,
                'error': 'lead_ids are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        leads_qs = _get_leads_queryset_for_user(request.user)
        deleted_count, _ = leads_qs.filter(id__in=lead_ids).delete()
        
        return Response({
            'success': True,
            'deleted_count': deleted_count
        })


class CallLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing CallLog instances.
    """
    queryset = CallLog.objects.all().order_by('-called_at')
    serializer_class = CallLogSerializer
    permission_classes = [IsAuthenticated]


class EmailLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing EmailLog instances.
    """
    queryset = EmailLog.objects.all().order_by('-sent_at')
    serializer_class = EmailLogSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
def api_health(request):
    """
    Health check endpoint.
    
    Checks:
    - API availability
    - Database connectivity
    
    Returns:
        JSON response with status and component health
    """
    health_status = {
        'api': 'ok',
        'database': 'unknown'
    }
    overall_status = 'ok'
    
    # Check database connectivity
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['database'] = 'ok'
    except Exception as e:
        health_status['database'] = 'error'
        overall_status = 'degraded'
        logger.error(f"Health check database error: {e}")
    
    # Get version info if available
    version = getattr(settings, 'APP_VERSION', None)
    
    response_data = {
        'success': True,
        'data': {
            'status': overall_status,
            'service': 'telis-recruitment-api',
            'components': health_status
        }
    }
    
    if version:
        response_data['data']['version'] = version
    
    # Return 200 for ok, 503 for degraded
    status_code = 200 if overall_status == 'ok' else 503
    
    return Response(response_data, status=status_code)


@csrf_exempt
@require_POST
@ratelimit(key='ip', rate=API_RATE_LIMIT_OPT_IN, method='POST')
def opt_in(request):
    """
    Opt-In API Endpoint for Landing Page.
    
    Creates a new lead with source: landing_page.
    Rate limited to prevent spam/abuse.
    """
    if getattr(request, 'limited', False):
        return JsonResponse({
            'success': False,
            'error': 'Too many requests. Please try again in a few minutes.'
        }, status=429)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        telefon = data.get('telefon', '').strip() if data.get('telefon') else None
        
        # Name validation
        if not name or len(name) < MIN_NAME_LENGTH:
            return JsonResponse({
                'success': False,
                'error': f'Name must be at least {MIN_NAME_LENGTH} characters'
            }, status=400)
        
        if len(name) > MAX_NAME_LENGTH:
            return JsonResponse({
                'success': False,
                'error': f'Name is too long (max {MAX_NAME_LENGTH} characters)'
            }, status=400)
        
        # Email validation
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email is required'
            }, status=400)
        
        if not EMAIL_REGEX.match(email):
            return JsonResponse({
                'success': False,
                'error': 'Invalid email format'
            }, status=400)
        
        # Phone validation (optional but must be valid if provided)
        if telefon and not PHONE_REGEX.match(telefon):
            return JsonResponse({
                'success': False,
                'error': 'Invalid phone number format'
            }, status=400)
        
        # Check for existing lead
        existing_lead = Lead.objects.filter(email=email).first()
        
        if existing_lead:
            # Update existing lead
            existing_lead.name = name
            if telefon:
                existing_lead.telefon = telefon
            existing_lead.interest_level = min(5, existing_lead.interest_level + 1)
            existing_lead.save()
            
            logger.info(f"Lead updated via opt_in: {existing_lead.id}")
            
            return JsonResponse({
                'success': True,
                'data': {
                    'lead_id': existing_lead.id,
                    'action': 'updated'
                },
                'message': 'Lead updated successfully'
            }, status=200)
        else:
            # Create new lead
            lead = Lead.objects.create(
                name=name,
                email=email,
                telefon=telefon,
                source=Lead.Source.LANDING_PAGE,
                status=Lead.Status.NEW,
                quality_score=70,
                interest_level=3
            )
            
            logger.info(f"Lead created via opt_in: {lead.id}")
            
            return JsonResponse({
                'success': True,
                'data': {
                    'lead_id': lead.id,
                    'action': 'created'
                },
                'message': 'Lead created successfully'
            }, status=201)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in opt_in: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


def _decode_csv_file(csv_file):
    """
    Try to decode CSV file with multiple encodings.
    
    Args:
        csv_file: Uploaded file object
        
    Returns:
        str: Decoded string content
        
    Raises:
        UnicodeDecodeError: If no encoding works
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            csv_file.seek(0)
            content = csv_file.read().decode(encoding)
            logger.debug(f"CSV decoded successfully with {encoding}")
            return content
        except UnicodeDecodeError:
            continue
    
    # If no encoding works, raise a more descriptive error
    raise ValueError(
        f"Could not decode file with any supported encoding. "
        f"Tried: {', '.join(encodings)}. "
        f"Please ensure the file is saved with UTF-8 or Latin-1 encoding."
    )


def _detect_csv_delimiter(content: str) -> str:
    """Detect CSV delimiter from content sample."""
    sample = content[:2048]
    semicolon_count = sample.count(';')
    comma_count = sample.count(',')
    
    # Use semicolon if it appears more often (common in German CSVs)
    return ';' if semicolon_count > comma_count else ','


def _process_csv_content(decoded_content: str) -> dict:
    """
    Process decoded CSV content and import leads.
    
    Args:
        decoded_content: Decoded CSV string
        
    Returns:
        dict: Import statistics with keys: imported, updated, skipped, errors
    """
    io_string = io.StringIO(decoded_content)
    delimiter = _detect_csv_delimiter(decoded_content)
    
    reader = csv.DictReader(io_string, delimiter=delimiter)
    
    imported = 0
    updated = 0
    skipped = 0
    errors = []
    
    with transaction.atomic():
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                result = _process_csv_row(row)
                if result == 'imported':
                    imported += 1
                elif result == 'updated':
                    updated += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                if len(errors) >= MAX_CSV_ERRORS:
                    errors.append(f"... (additional errors truncated, max {MAX_CSV_ERRORS} shown)")
                    break
    
    return {
        'imported': imported,
        'updated': updated,
        'skipped': skipped,
        'errors': errors if errors else None
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate=API_RATE_LIMIT_IMPORT, method='POST')
def import_csv(request):
    """
    CSV Import API Endpoint.
    
    Imports leads from a CSV file.
    Supports multiple encodings (UTF-8, Latin-1, etc.) and delimiters.
    Handles deduplication and updates.
    Rate limited to prevent abuse.
    """
    # Check rate limit
    if getattr(request, 'limited', False):
        return Response({
            'success': False,
            'error': 'Too many requests. Please try again in a few minutes.'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Check file presence
    if 'file' not in request.FILES:
        return Response({
            'success': False,
            'error': 'No file provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    
    # Validate file size (max 10MB by default)
    max_size = getattr(settings, 'MAX_CSV_UPLOAD_SIZE', 10 * 1024 * 1024)
    if csv_file.size > max_size:
        max_size_mb = max_size // 1024 // 1024
        return Response({
            'success': False,
            'error': f'File too large. Maximum size is {max_size_mb}MB'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode file with automatic encoding detection
        decoded_content = _decode_csv_file(csv_file)
        
        # Process CSV content
        result = _process_csv_content(decoded_content)
        
        # Log import results
        logger.info(
            f"CSV import by {request.user}: "
            f"{result['imported']} imported, {result['updated']} updated, "
            f"{result['skipped']} skipped"
        )
        
        return Response({
            'success': True,
            'data': result,
            'message': f"Import completed: {result['imported']} new, {result['updated']} updated"
        })
        
    except (UnicodeDecodeError, ValueError) as e:
        logger.warning(f"CSV decode error for file uploaded by {request.user}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Could not decode file. Please ensure it uses UTF-8 or Latin-1 encoding.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Error in import_csv: {e}")
        return Response({
            'success': False,
            'error': 'Error processing CSV file'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _process_csv_row(row):
    """
    Process a single CSV row for import.
    
    Returns:
        str: 'imported', 'updated', or 'skipped'
    """
    # Field mapping
    email = (row.get('email') or row.get('Email') or row.get('E-Mail') or '').strip() or None
    telefon = (row.get('telefon') or row.get('Telefon') or row.get('phone') or '').strip() or None
    name = (row.get('name') or row.get('Name') or 'Unbekannt').strip()
    
    # Skip if no contact info
    if not email and not telefon:
        return 'skipped'
    
    # Parse score
    try:
        score_raw = row.get('score') or row.get('Score') or row.get('quality_score') or '50'
        score = int(score_raw) if score_raw else 50
        score = max(0, min(100, score))  # Clamp 0-100
    except (ValueError, TypeError):
        score = 50
    
    # Check for existing lead (deduplication)
    existing = None
    if email:
        existing = Lead.objects.filter(email=email).first()
    if not existing and telefon:
        existing = Lead.objects.filter(telefon=telefon).first()
    
    if existing:
        # Update if score is better
        if score > existing.quality_score:
            existing.quality_score = score
            # Update other fields if better data available
            if not existing.company and row.get('company_name'):
                existing.company = row.get('company_name')[:255]
            if not existing.role:
                role = (row.get('rolle') or row.get('position') or row.get('Position') or '')
                if role:
                    existing.role = role[:255]
            if not existing.location:
                location = (row.get('region') or row.get('standort') or row.get('Standort') or '')
                if location:
                    existing.location = location[:255]
            existing.save()
            return 'updated'
        else:
            return 'skipped'
    else:
        # Create new lead
        lead_type_raw = row.get('lead_type') or row.get('Lead-Typ') or ''
        if lead_type_raw in dict(Lead.LeadType.choices):
            lead_type = lead_type_raw
        else:
            lead_type = Lead.LeadType.UNKNOWN
        
        Lead.objects.create(
            name=name[:255],
            email=email,
            telefon=telefon,
            source=Lead.Source.SCRAPER,
            source_url=(row.get('quelle') or row.get('source_url') or '')[:200] or None,
            quality_score=score,
            lead_type=lead_type,
            company=(row.get('company_name') or row.get('firma') or row.get('Firma') or '')[:255] or None,
            role=(row.get('rolle') or row.get('position') or row.get('Position') or '')[:255] or None,
            location=(row.get('region') or row.get('standort') or row.get('Standort') or '')[:255] or None,
            linkedin_url=row.get('social_profile_url') if 'linkedin' in (row.get('social_profile_url') or '').lower() else None,
            xing_url=row.get('social_profile_url') if 'xing' in (row.get('social_profile_url') or '').lower() else None,
        )
        return 'imported'


# Thread-safe cache for allowed database paths
_allowed_db_paths_lock = threading.Lock()
ALLOWED_DB_PATHS = None


def _get_allowed_db_paths():
    """Get list of allowed database paths (whitelist). Thread-safe."""
    global ALLOWED_DB_PATHS
    if ALLOWED_DB_PATHS is None:
        with _allowed_db_paths_lock:
            # Double-check locking pattern
            if ALLOWED_DB_PATHS is None:
                base = Path(settings.BASE_DIR).parent.resolve()
                ALLOWED_DB_PATHS = [
                    base / 'scraper.db',
                ]
                # Add custom paths from settings if defined
                custom_paths = getattr(settings, 'ALLOWED_SCRAPER_DB_PATHS', [])
                for p in custom_paths:
                    ALLOWED_DB_PATHS.append(Path(p).resolve())
    return ALLOWED_DB_PATHS


@csrf_exempt
@require_POST
def brevo_webhook(request):
    """
    Webhook endpoint for Brevo email events.
    Secured with HMAC signature verification.
    
    Handles: opened, click, hard_bounce, unsubscribed events.
    """
    # Verify webhook signature
    signature = request.headers.get('X-Sib-Signature')
    webhook_secret = getattr(settings, 'BREVO_WEBHOOK_SECRET', None)
    
    if webhook_secret:
        if not signature:
            logger.warning("Brevo webhook called without signature")
            return JsonResponse({
                'status': 'error',
                'message': 'Missing signature'
            }, status=401)
        
        expected_signature = hmac.new(
            webhook_secret.encode(),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid Brevo webhook signature received")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid signature'
            }, status=401)
    else:
        # Log warning if secret not configured (allows graceful deployment)
        logger.warning("BREVO_WEBHOOK_SECRET not configured - webhook signature verification disabled!")
    
    try:
        data = json.loads(request.body)
        
        event = data.get('event')
        email = data.get('email')
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Email address required'
            }, status=400)
        
        # Find lead by email
        try:
            lead = Lead.objects.get(email=email)
        except Lead.DoesNotExist:
            return JsonResponse({
                'status': 'ok',
                'message': 'Lead not found, ignoring event'
            })
        
        # Process event
        if event == 'opened':
            lead.email_opens = F('email_opens') + 1
            lead.save(update_fields=['email_opens'])
        
        elif event == 'click':
            lead.email_clicks = F('email_clicks') + 1
            lead.interest_level = min(5, lead.interest_level + 1)
            lead.save(update_fields=['email_clicks', 'interest_level'])
        
        elif event == 'hard_bounce':
            lead.status = Lead.Status.INVALID
            lead.save(update_fields=['status'])
        
        elif event == 'unsubscribed':
            lead.status = Lead.Status.UNSUBSCRIBED
            lead.save(update_fields=['status'])
        
        # Refresh to get actual values (F expressions)
        lead.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'data': {
                'event': event,
                'lead_id': lead.id
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in brevo_webhook: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_sync(request):
    """
    Trigger synchronization from scraper database.
    
    Parameters:
        - db_path: Path to scraper database (optional, uses default if not provided)
        - force: Force update even if score is lower (optional, default: false)
    
    Security: Only whitelisted database paths are allowed.
    """
    db_path_input = request.data.get('db_path')
    force = request.data.get('force', False)
    
    # Determine and validate database path
    if db_path_input:
        # Resolve path (removes ../ and resolves symlinks)
        db_path = Path(db_path_input).resolve()
        
        # Whitelist check
        allowed_paths = _get_allowed_db_paths()
        if db_path not in allowed_paths:
            logger.warning(
                f"Unauthorized db_path attempted: {db_path} by user {request.user}"
            )
            return Response({
                'success': False,
                'error': 'Unauthorized database path'
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        # Use default path
        db_path = Path(settings.BASE_DIR).parent / 'scraper.db'
    
    # Additional validation: must be .db file
    if not str(db_path).endswith('.db'):
        return Response({
            'success': False,
            'error': 'Invalid database file extension'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Don't expose full path in error messages
    if not db_path.exists():
        return Response({
            'success': False,
            'error': 'Database not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if leads table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        if not cursor.fetchone():
            conn.close()
            return Response({
                'success': False,
                'error': 'No leads table found in database'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get leads from scraper database
        cursor.execute("SELECT * FROM leads")
        columns = [description[0] for description in cursor.description]
        
        imported = 0
        updated = 0
        skipped = 0
        
        with transaction.atomic():
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                result = _process_csv_row(row_dict)
                
                if result == 'imported':
                    imported += 1
                elif result == 'updated':
                    updated += 1
                else:
                    skipped += 1
        
        conn.close()
        
        return Response({
            'success': True,
            'imported': imported,
            'updated': updated,
            'skipped': skipped,
            'message': 'Sync completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_sync: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error syncing database'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# CRM helpers and dashboard views
_CONVERTED_STATUSES = {
    Lead.Status.INTERESTED,
    Lead.Status.INTERVIEW,
    Lead.Status.HIRED,
}

_TEAM_PERFORMANCE_GROUPS = ['Admin', 'Manager', 'Telefonist']


def _get_leads_queryset_for_user(user):
    """Return leads that the current user is allowed to see."""
    if not user.is_authenticated:
        return Lead.objects.none()
    if user.is_superuser or user.groups.filter(name__in=['Admin', 'Manager']).exists():
        return Lead.objects.all()
    return Lead.objects.filter(assigned_to=user)


def _get_user_role(user):
    """Simplified role name for CRM templates."""
    if user.is_superuser or user.groups.filter(name='Admin').exists():
        return 'Admin'
    if user.groups.filter(name='Manager').exists():
        return 'Manager'
    if user.groups.filter(name='Telefonist').exists():
        return 'Telefonist'
    return None


def _format_duration(seconds):
    """Format duration seconds into human-friendly string."""
    total_seconds = int(seconds or 0)
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _format_time_ago(timestamp):
    """Return a localized human readable 'time ago' string."""
    if not timestamp:
        return ''
    return f"vor {timesince(timestamp, timezone.now())}"


def _build_dashboard_stats(user):
    """Build data for the dashboard KPIs, charts and tables."""
    leads_qs = _get_leads_queryset_for_user(user)
    total_leads = leads_qs.count()
    today = timezone.localdate()
    week_start_date = today - timedelta(days=6)
    month_start_date = today - timedelta(days=29)
    prev_week_start = today - timedelta(days=13)
    prev_week_end = today - timedelta(days=7)

    leads_today = leads_qs.filter(created_at__date=today).count()
    leads_week = leads_qs.filter(created_at__date__gte=week_start_date).count()
    leads_month = leads_qs.filter(created_at__date__gte=month_start_date).count()
    hot_leads = leads_qs.filter(quality_score__gte=80, interest_level__gte=3).count()

    calls_today = CallLog.objects.filter(
        lead__in=leads_qs,
        called_at__date=today
    ).count()

    calls_last_week = CallLog.objects.filter(
        lead__in=leads_qs,
        called_at__date__gte=week_start_date
    ).count()
    avg_calls_per_day = round(calls_last_week / 7, 1) if calls_last_week else 0

    conversions_current = leads_qs.filter(
        status__in=_CONVERTED_STATUSES,
        created_at__date__gte=week_start_date,
        created_at__date__lte=today
    ).count()
    conversions_previous = leads_qs.filter(
        status__in=_CONVERTED_STATUSES,
        created_at__date__gte=prev_week_start,
        created_at__date__lte=prev_week_end
    ).count()
    conversion_change = conversions_current - conversions_previous
    conversion_rate = round((conversions_current / total_leads) * 100, 1) if total_leads else 0

    trend_7_days = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_leads = leads_qs.filter(created_at__date=day).count()
        day_conversions = leads_qs.filter(
            created_at__date=day,
            status__in=_CONVERTED_STATUSES
        ).count()
        trend_7_days.append({
            'label': day.strftime('%d.%m'),
            'new_leads': day_leads,
            'conversions': day_conversions
        })

    status_rows = leads_qs.values('status').annotate(count=Count('id'))
    status_map = {row['status']: row['count'] for row in status_rows}
    status_distribution = {
        key: {
            'label': label,
            'count': status_map.get(key, 0)
        }
        for key, label in Lead.Status.choices
    }

    source_rows = leads_qs.values('source').annotate(count=Count('id'))
    source_map = {row['source']: row['count'] for row in source_rows}
    source_distribution = {}
    for key, label in Lead.Source.choices:
        count = source_map.get(key, 0)
        percentage = round((count / total_leads) * 100, 1) if total_leads else 0
        source_distribution[key] = {
            'label': label,
            'count': count,
            'percentage': percentage
        }
    
    # Top sources by conversion rate (quality)
    top_sources = []
    for key, label in Lead.Source.choices:
        source_leads = leads_qs.filter(source=key)
        source_count = source_leads.count()
        if source_count > 0:
            converted = source_leads.filter(status__in=_CONVERTED_STATUSES).count()
            conversion_rate_src = round((converted / source_count) * 100, 1)
            avg_quality = source_leads.aggregate(Avg('quality_score'))['quality_score__avg'] or 0
            top_sources.append({
                'source': label,
                'count': source_count,
                'conversion_rate': conversion_rate_src,
                'avg_quality': round(avg_quality, 1)
            })
    top_sources.sort(key=lambda x: x['conversion_rate'], reverse=True)
    
    # Top error reasons (invalid leads with telefon missing or status INVALID)
    error_reasons = []
    no_mobile = leads_qs.filter(Q(telefon__isnull=True) | Q(telefon='')).count()
    invalid_status = leads_qs.filter(status=Lead.Status.INVALID).count()
    no_email = leads_qs.filter(Q(email__isnull=True) | Q(email='')).count()
    
    if no_mobile > 0:
        error_reasons.append({'reason': 'Kein Telefon gefunden', 'count': no_mobile})
    if invalid_status > 0:
        error_reasons.append({'reason': 'Ungültiger Lead', 'count': invalid_status})
    if no_email > 0:
        error_reasons.append({'reason': 'Keine E-Mail gefunden', 'count': no_email})
    
    # Data quality trends (last 7 days)
    quality_trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_leads = leads_qs.filter(created_at__date=day)
        avg_quality = day_leads.aggregate(Avg('quality_score'))['quality_score__avg'] or 0
        quality_trend.append({
            'label': day.strftime('%d.%m'),
            'avg_quality': round(avg_quality, 1)
        })

    return {
        'leads_total': total_leads,
        'leads_today': leads_today,
        'leads_week': leads_week,
        'leads_month': leads_month,
        'calls_today': calls_today,
        'avg_calls_per_day': avg_calls_per_day,
        'conversion_rate': conversion_rate,
        'conversion_change': conversion_change,
        'hot_leads': hot_leads,
        'trend_7_days': trend_7_days,
        'status_distribution': status_distribution,
        'source_distribution': source_distribution,
        'top_sources': top_sources,
        'error_reasons': error_reasons,
        'quality_trend': quality_trend,
    }


def _build_activity_feed(leads_qs, limit=12):
    """Construct a combined activity feed from calls and emails."""
    lead_ids = leads_qs.values_list('id', flat=True)
    calls = CallLog.objects.filter(
        lead_id__in=lead_ids
    ).select_related('lead', 'called_by').order_by('-called_at')[:limit * 2]
    emails = EmailLog.objects.filter(
        lead_id__in=lead_ids
    ).select_related('lead').order_by('-sent_at')[:limit * 2]

    activities = []
    for log in calls:
        actor = log.called_by.get_full_name() if log.called_by else None
        actor = actor or (log.called_by.username if log.called_by else 'Team')
        activities.append({
            'type': 'call',
            'icon': '📞',
            'message': f"Anruf {log.get_outcome_display().lower()} mit {log.lead.name}",
            'detail': f"{actor} • {log.get_outcome_display()}",
            'lead_id': log.lead_id,
            'timestamp': log.called_at.isoformat(),
            '_ts': log.called_at,
            'time_ago': _format_time_ago(log.called_at)
        })

    for log in emails:
        activities.append({
            'type': 'email',
            'icon': '✉️',
            'message': f"E-Mail {log.get_email_type_display().lower()} an {log.lead.name}",
            'detail': log.subject or log.get_email_type_display(),
            'lead_id': log.lead_id,
            'timestamp': log.sent_at.isoformat(),
            '_ts': log.sent_at,
            'time_ago': _format_time_ago(log.sent_at)
        })

    activities.sort(key=lambda entry: entry['_ts'], reverse=True)
    cleaned = []
    for entry in activities[:limit]:
        entry.pop('_ts', None)
        cleaned.append(entry)
    return cleaned


def _build_team_performance():
    """Aggregate team performance metrics for Admin/Managers."""
    week_start = timezone.now() - timedelta(days=6)
    today = timezone.localdate()
    users = User.objects.filter(
        Q(groups__name__in=_TEAM_PERFORMANCE_GROUPS) | Q(is_superuser=True)
    ).distinct()

    performers = []
    for user in users:
        calls_today = CallLog.objects.filter(
            called_by=user,
            called_at__date=today
        ).count()
        conversions_week = Lead.objects.filter(
            assigned_to=user,
            status__in=_CONVERTED_STATUSES,
            updated_at__gte=week_start
        ).count()
        avg_duration = CallLog.objects.filter(
            called_by=user,
            called_at__gte=week_start
        ).aggregate(avg=Avg('duration_seconds'))['avg'] or 0
        performers.append({
            'user_id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'calls_today': calls_today,
            'conversions_week': conversions_week,
            'avg_duration_formatted': _format_duration(avg_duration),
        })

    performers.sort(key=lambda perf: (
        -perf['calls_today'],
        -perf['conversions_week'],
        perf['full_name']
    ))
    return performers


@login_required(login_url='crm-login')
def crm_dashboard(request):
    """
    CRM dashboard template view.
    Loads KPI cards and allows the client-side JS to populate charts.
    """
    stats = _build_dashboard_stats(request.user)
    return render(request, 'crm/dashboard.html', {
        'user_role': _get_user_role(request.user),
        'stats': {
            'total': stats['leads_total'],
            'today': stats['leads_today'],
            'week': stats['leads_week'],
            'month': stats['leads_month'],
            'calls_today': stats['calls_today'],
            'hot_leads': stats['hot_leads'],
            'conversion_rate': stats['conversion_rate'],
            'top_sources': stats['top_sources'][:5],
            'error_reasons': stats['error_reasons'][:5],
            'quality_trend': stats['quality_trend'],
        }
    })


@login_required(login_url='crm-login')
def crm_leads(request):
    """Render the CRM lead management page."""
    return render(request, 'crm/leads.html', {
        'user_role': _get_user_role(request.user)
    })


@login_required(login_url='crm-login')
def crm_lead_detail(request, pk):
    """Render a single lead detail panel for CRM users."""
    leads_qs = _get_leads_queryset_for_user(request.user)
    lead = get_object_or_404(leads_qs, pk=pk)
    return render(request, 'crm/lead_detail.html', {
        'lead': lead,
        'user_role': _get_user_role(request.user)
    })


@api_view(['GET'])
@permission_classes([IsTelefonist])
def dashboard_stats(request):
    """Return the dashboard statistics used by Chart.js + KPI cards."""
    stats = _build_dashboard_stats(request.user)
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsTelefonist])
def activity_feed(request):
    """Return recent activities (calls + emails) for the CRM feed."""
    leads_qs = _get_leads_queryset_for_user(request.user)
    feed = _build_activity_feed(leads_qs)
    return Response(feed, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsManager])
def team_performance(request):
    """Return aggregated team performance metrics (Admin/Manager only)."""
    performers = _build_team_performance()
    return Response(performers, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def saved_filters(request):
    """
    GET: List all saved filters for the user
    POST: Create a new saved filter
    """
    if request.method == 'GET':
        # Get user's own filters + shared filters
        user_filters = SavedFilter.objects.filter(user=request.user)
        shared_filters = SavedFilter.objects.filter(is_shared=True).exclude(user=request.user)
        
        filters_data = []
        for f in user_filters:
            filters_data.append({
                'id': f.id,
                'name': f.name,
                'description': f.description,
                'filter_params': f.filter_params,
                'is_shared': f.is_shared,
                'is_owner': True,
                'created_at': f.created_at.isoformat()
            })
        
        for f in shared_filters:
            filters_data.append({
                'id': f.id,
                'name': f.name,
                'description': f.description,
                'filter_params': f.filter_params,
                'is_shared': True,
                'is_owner': False,
                'owner': f.user.get_full_name() or f.user.username,
                'created_at': f.created_at.isoformat()
            })
        
        return Response(filters_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        name = request.data.get('name')
        description = request.data.get('description', '')
        filter_params = request.data.get('filter_params', {})
        is_shared = request.data.get('is_shared', False)
        
        if not name or not filter_params:
            return Response({
                'success': False,
                'error': 'name and filter_params are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if filter with same name exists
        if SavedFilter.objects.filter(user=request.user, name=name).exists():
            return Response({
                'success': False,
                'error': 'A filter with this name already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        saved_filter = SavedFilter.objects.create(
            user=request.user,
            name=name,
            description=description,
            filter_params=filter_params,
            is_shared=is_shared
        )
        
        return Response({
            'success': True,
            'filter': {
                'id': saved_filter.id,
                'name': saved_filter.name,
                'description': saved_filter.description,
                'filter_params': saved_filter.filter_params,
                'is_shared': saved_filter.is_shared
            }
        }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def saved_filter_detail(request, filter_id):
    """
    PUT: Update a saved filter
    DELETE: Delete a saved filter
    """
    try:
        saved_filter = SavedFilter.objects.get(id=filter_id, user=request.user)
    except SavedFilter.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Filter not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        saved_filter.name = request.data.get('name', saved_filter.name)
        saved_filter.description = request.data.get('description', saved_filter.description)
        saved_filter.filter_params = request.data.get('filter_params', saved_filter.filter_params)
        saved_filter.is_shared = request.data.get('is_shared', saved_filter.is_shared)
        saved_filter.save()
        
        return Response({
            'success': True,
            'filter': {
                'id': saved_filter.id,
                'name': saved_filter.name,
                'description': saved_filter.description,
                'filter_params': saved_filter.filter_params,
                'is_shared': saved_filter.is_shared
            }
        })
    
    elif request.method == 'DELETE':
        saved_filter.delete()
        return Response({
            'success': True,
            'message': 'Filter deleted successfully'
        })


# Template views for public pages


def landing_page(request):
    """
    Landing page view.
    
    Public page for lead opt-in.
    """
    week_start = timezone.now() - timedelta(days=7)
    hired_this_week = Lead.objects.filter(
        status=Lead.Status.HIRED,
        updated_at__gte=week_start
    ).count()

    return render(request, 'leads/landing_page.html', {
        'stats': {
            'hired_this_week': hired_this_week
        }
    })


def phone_dashboard(request):
    """
    Phone dashboard view.
    
    Public page for phone number verification/lookup.
    """
    return render(request, 'leads/phone_dashboard.html')
