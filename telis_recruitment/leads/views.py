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
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django_ratelimit.decorators import ratelimit

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Lead, CallLog, EmailLog
from .serializers import LeadSerializer, LeadListSerializer, CallLogSerializer, EmailLogSerializer
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


# Template views for public pages
from django.shortcuts import render


def landing_page(request):
    """
    Landing page view.
    
    Public page for lead opt-in.
    """
    return render(request, 'leads/landing_page.html')


def phone_dashboard(request):
    """
    Phone dashboard view.
    
    Public page for phone number verification/lookup.
    """
    return render(request, 'leads/phone_dashboard.html')
