"""
API views for the leads application.
"""

import json
import csv
import io
import logging
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django_ratelimit.decorators import ratelimit

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Lead, CallLog, EmailLog
from .serializers import LeadSerializer, LeadListSerializer, CallLogSerializer, EmailLogSerializer
from telis.config import API_RATE_LIMIT_OPT_IN, API_RATE_LIMIT_IMPORT

logger = logging.getLogger(__name__)


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Lead instances.
    """
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    
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
                name__icontains=search
            ) | queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                telefon__icontains=search
            ) | queryset.filter(
                company__icontains=search
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
    
    Returns:
        JSON response with status and service name
    """
    return Response({
        'status': 'ok',
        'service': 'telis-recruitment-api'
    })


@csrf_exempt
@require_POST
@ratelimit(key='ip', rate=API_RATE_LIMIT_OPT_IN, method='POST')
def opt_in(request):
    """
    Opt-In API Endpoint for Landing Page.
    
    Creates a new lead with source: landing_page.
    Rate limited to prevent spam/abuse.
    """
    # Check if rate limit was hit
    if getattr(request, 'limited', False):
        return JsonResponse({
            'error': 'Too many requests. Please try again in a few minutes.'
        }, status=429)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Name is required'
            }, status=400)
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email is required'
            }, status=400)
        
        # Check for existing lead
        existing_lead = Lead.objects.filter(email=email).first()
        
        if existing_lead:
            # Update existing lead
            existing_lead.name = name
            if data.get('telefon'):
                existing_lead.telefon = data.get('telefon')
            existing_lead.interest_level = min(5, existing_lead.interest_level + 1)
            existing_lead.save()
            
            return JsonResponse({
                'success': True,
                'lead_id': existing_lead.id,
                'message': 'Lead updated successfully',
                'status': 'updated'
            }, status=200)
        else:
            # Create new lead
            lead = Lead.objects.create(
                name=name,
                email=email,
                telefon=data.get('telefon', '').strip() or None,
                source=Lead.Source.LANDING_PAGE,
                status=Lead.Status.NEW,
                quality_score=70,
                interest_level=3
            )
            
            return JsonResponse({
                'success': True,
                'lead_id': lead.id,
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate=API_RATE_LIMIT_IMPORT, method='POST')
def import_csv(request):
    """
    CSV Import API Endpoint.
    
    Imports leads from a CSV file.
    Supports deduplication and updates.
    Rate limited to prevent abuse.
    """
    # Check if rate limit was hit
    if getattr(request, 'limited', False):
        return Response({
            'success': False,
            'error': 'Too many requests. Please try again in a few minutes.'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    if 'file' not in request.FILES:
        return Response({
            'success': False,
            'error': 'No file provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    
    # Validate file size (max 10MB by default)
    max_size = getattr(settings, 'MAX_CSV_UPLOAD_SIZE', 10 * 1024 * 1024)
    if csv_file.size > max_size:
        return Response({
            'success': False,
            'error': f'File too large. Maximum size is {max_size / 1024 / 1024}MB'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        
        # Detect delimiter
        sample = decoded_file[:1024]
        if ';' in sample and ',' not in sample:
            delimiter = ';'
        else:
            delimiter = ','
        
        reader = csv.DictReader(io_string, delimiter=delimiter)
        
        imported = 0
        updated = 0
        skipped = 0
        errors = []
        
        with transaction.atomic():
            for row in reader:
                try:
                    result = _process_csv_row(row)
                    if result == 'imported':
                        imported += 1
                    elif result == 'updated':
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors.append(str(e))
        
        return Response({
            'success': True,
            'imported': imported,
            'updated': updated,
            'skipped': skipped,
            'errors': errors if errors else None
        })
        
    except UnicodeDecodeError:
        # Try with latin-1 encoding
        try:
            csv_file.seek(0)
            decoded_file = csv_file.read().decode('latin-1')
            io_string = io.StringIO(decoded_file)
            
            # Detect delimiter
            sample = decoded_file[:1024]
            if ';' in sample and ',' not in sample:
                delimiter = ';'
            else:
                delimiter = ','
            
            reader = csv.DictReader(io_string, delimiter=delimiter)
            
            imported = 0
            updated = 0
            skipped = 0
            errors = []
            
            with transaction.atomic():
                for row in reader:
                    try:
                        result = _process_csv_row(row)
                        if result == 'imported':
                            imported += 1
                        elif result == 'updated':
                            updated += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        errors.append(str(e))
            
            return Response({
                'success': True,
                'imported': imported,
                'updated': updated,
                'skipped': skipped,
                'errors': errors if errors else None
            })
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            return Response({
                'success': False,
                'error': f'Error reading file: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error in import_csv: {str(e)}")
        return Response({
            'success': False,
            'error': f'Error processing CSV: {str(e)}'
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


@csrf_exempt
@require_POST
def brevo_webhook(request):
    """
    Webhook endpoint for Brevo email events.
    
    Handles: opened, click, hard_bounce, unsubscribed events.
    """
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
            'status': 'ok',
            'event': event,
            'lead_id': lead.id
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
    """
    db_path = request.data.get('db_path')
    force = request.data.get('force', False)
    
    # Use default path if not provided
    if not db_path:
        scraper_path = Path(settings.BASE_DIR).parent
        db_path = scraper_path / 'scraper.db'
    else:
        db_path = Path(db_path)
    
    if not db_path.exists():
        return Response({
            'success': False,
            'error': f'Database not found: {db_path}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        import sqlite3
        
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
            'message': f'Sync completed from {db_path}'
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_sync: {str(e)}")
        return Response({
            'success': False,
            'error': f'Error syncing database: {str(e)}'
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
