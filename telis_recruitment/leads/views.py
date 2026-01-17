import csv
import io
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.db import models, transaction
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Lead, CallLog, EmailLog
from .serializers import LeadSerializer, LeadListSerializer, CallLogSerializer, EmailLogSerializer

logger = logging.getLogger(__name__)


# Constants
DEFAULT_QUALITY_SCORE = 50
MAX_ERROR_REPORTS = 10


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer
    
    def get_queryset(self):
        queryset = Lead.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by lead_type
        lead_type = self.request.query_params.get('lead_type')
        if lead_type:
            queryset = queryset.filter(lead_type=lead_type)
        
        # Filter by minimum score
        min_score = self.request.query_params.get('min_score')
        if min_score:
            try:
                min_score_int = int(min_score)
                queryset = queryset.filter(quality_score__gte=min_score_int)
            except (ValueError, TypeError):
                # Invalid min_score value, ignore the filter
                pass
        
        # Filter by has phone
        has_phone = self.request.query_params.get('has_phone')
        if has_phone == 'true':
            queryset = queryset.exclude(telefon__isnull=True).exclude(telefon='')
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(telefon__icontains=search) |
                models.Q(company__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Dashboard-Statistiken"""
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        total = Lead.objects.count()
        today_count = Lead.objects.filter(created_at__date=today).count()
        
        by_status = dict(Lead.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        by_source = dict(Lead.objects.values('source').annotate(count=Count('id')).values_list('source', 'count'))
        
        avg_score = Lead.objects.aggregate(avg=Avg('quality_score'))['avg'] or 0
        
        # Hot leads count
        hot_leads = Lead.objects.filter(quality_score__gte=80, interest_level__gte=3).count()
        
        # Conversion funnel
        funnel = {
            'new': by_status.get('NEW', 0),
            'contacted': by_status.get('CONTACTED', 0) + by_status.get('VOICEMAIL', 0),
            'interested': by_status.get('INTERESTED', 0),
            'interview': by_status.get('INTERVIEW', 0),
            'hired': by_status.get('HIRED', 0),
        }
        
        return Response({
            'total': total,
            'today': today_count,
            'hot_leads': hot_leads,
            'by_status': by_status,
            'by_source': by_source,
            'avg_score': round(avg_score, 1),
            'funnel': funnel,
        })
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def log_call(self, request, pk=None):
        """Anruf protokollieren"""
        lead = self.get_object()
        
        # For anonymous users, set called_by to None
        called_by_id = request.user.id if request.user.is_authenticated else None
        
        serializer = CallLogSerializer(data={
            'lead': lead.id,
            'outcome': request.data.get('outcome'),
            'duration_seconds': request.data.get('duration_seconds', 0),
            'interest_level': request.data.get('interest_level', 0),
            'notes': request.data.get('notes', ''),
            'called_by': called_by_id,
        })
        
        if serializer.is_valid():
            serializer.save()
            # Refresh lead to get updated data
            lead.refresh_from_db()
            return Response({
                'call_log': serializer.data,
                'lead': LeadSerializer(lead).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def next_to_call(self, request):
        """Nächster Lead zum Anrufen (für Telefon-Dashboard)"""
        lead = Lead.objects.filter(
            status__in=[Lead.Status.NEW, Lead.Status.VOICEMAIL, Lead.Status.CONTACTED],
        ).exclude(
            telefon__isnull=True
        ).exclude(
            telefon=''
        ).order_by('-quality_score', 'call_count', '-created_at').first()
        
        if lead:
            return Response(LeadSerializer(lead).data)
        return Response({'message': 'Keine Leads zum Anrufen verfügbar'}, status=status.HTTP_404_NOT_FOUND)


class CallLogViewSet(viewsets.ModelViewSet):
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CallLog.objects.all()
        lead_id = self.request.query_params.get('lead')
        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)
        return queryset


class EmailLogViewSet(viewsets.ModelViewSet):
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EmailLog.objects.all()
        lead_id = self.request.query_params.get('lead')
        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)
        return queryset


@csrf_exempt
@require_POST
def import_csv(request):
    """
    CSV-Import Endpoint für Scraper-Daten.
    Erwartet: POST mit file-Upload
    Note: CSRF exempt for automated scraper access. Consider adding API key authentication.
    """
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded_file))
        
        imported = 0
        updated = 0
        skipped = 0
        errors = []
        
        with transaction.atomic():
            for i, row in enumerate(reader, 1):
                try:
                    email = (row.get('email') or '').strip() or None
                    telefon = (row.get('telefon') or '').strip() or None
                    
                    if not email and not telefon:
                        skipped += 1
                        continue
                    
                    # Deduplizierung
                    existing = None
                    if email:
                        existing = Lead.objects.filter(email=email).first()
                    if not existing and telefon:
                        existing = Lead.objects.filter(telefon=telefon).first()
                    
                    # Parse and validate score
                    try:
                        score_value = row.get('score', DEFAULT_QUALITY_SCORE)
                        new_score = int(score_value) if score_value else DEFAULT_QUALITY_SCORE
                        new_score = max(0, min(100, new_score))  # Clamp to 0-100 range
                    except (ValueError, TypeError):
                        new_score = DEFAULT_QUALITY_SCORE  # Default score if invalid
                    
                    if existing:
                        if new_score > existing.quality_score:
                            existing.quality_score = new_score
                            existing.save()
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        lead_type = row.get('lead_type', '')
                        if lead_type not in dict(Lead.LeadType.choices):
                            lead_type = Lead.LeadType.UNKNOWN
                        
                        Lead.objects.create(
                            name=row.get('name', 'Unbekannt')[:255],
                            email=email,
                            telefon=telefon,
                            source=Lead.Source.SCRAPER,
                            source_url=(row.get('quelle') or '')[:200] or None,
                            quality_score=new_score,
                            lead_type=lead_type,
                            company=(row.get('company_name') or row.get('firma') or '')[:255] or None,
                            role=(row.get('rolle') or row.get('position') or '')[:255] or None,
                            location=(row.get('region') or row.get('standort') or '')[:255] or None,
                        )
                        imported += 1
                except Exception as e:
                    errors.append(f'Zeile {i}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'imported': imported,
            'updated': updated,
            'skipped': skipped,
            'errors': errors[:MAX_ERROR_REPORTS],
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def api_health(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'service': 'telis-recruitment-api'
    })


def landing_page(request):
    """Landing Page View"""
    return render(request, 'landing/index.html')


def phone_dashboard(request):
    """Telefon Dashboard View"""
    return render(request, 'phone/dashboard.html')


@csrf_exempt
@require_POST
def opt_in(request):
    """
    Opt-In API Endpoint für Landing Page.
    Erstellt einen neuen Lead mit Source: landing_page
    """
    try:
        data = json.loads(request.body)
        
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        telefon = (data.get('telefon') or '').strip() or None
        
        if not name:
            return JsonResponse({'error': 'Name ist erforderlich'}, status=400)
        if not email:
            return JsonResponse({'error': 'E-Mail ist erforderlich'}, status=400)
        
        # Check for duplicates
        existing = Lead.objects.filter(email=email).first()
        if existing:
            # Update interest if already exists
            if existing.source != Lead.Source.LANDING_PAGE:
                existing.source_detail = f'Re-Opt-In von {existing.source}'
            existing.interest_level = max(existing.interest_level, 3)
            existing.save()
            return JsonResponse({
                'success': True,
                'message': 'Willkommen zurück!',
                'lead_id': existing.id
            })
        
        # Create new lead
        lead = Lead.objects.create(
            name=name[:255],
            email=email,
            telefon=telefon,
            source=Lead.Source.LANDING_PAGE,
            status=Lead.Status.NEW,
            quality_score=70,  # Landing page leads start with higher score
            interest_level=3,  # They opted in, so medium-high interest
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Danke! Wir melden uns bald.',
            'lead_id': lead.id
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Ungültige Anfrage'}, status=400)
    except Exception as e:
        # Log the full exception for debugging
        logger.error(f'Opt-in error: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Ein Fehler ist aufgetreten. Bitte versuche es später erneut.'}, status=500)


@csrf_exempt
@require_POST
def brevo_webhook(request):
    """
    Webhook-Endpoint für Brevo Email-Events (opens, clicks, etc.)
    
    Brevo sendet Events wie:
    - opened: Email wurde geöffnet
    - click: Link wurde geklickt
    - hard_bounce: Email unzustellbar
    - unsubscribed: Abgemeldet
    """
    try:
        data = json.loads(request.body)
        
        event = data.get('event')
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email fehlt'}, status=400)
        
        # Lead finden
        lead = Lead.objects.filter(email=email).first()
        if not lead:
            logger.warning(f"Brevo Webhook: Lead nicht gefunden für {email}")
            return JsonResponse({'status': 'ignored', 'reason': 'lead_not_found'})
        
        # Event verarbeiten
        if event == 'opened':
            lead.email_opens += 1
            lead.save(update_fields=['email_opens'])
            logger.info(f"Brevo: Email geöffnet von {email}")
            
        elif event == 'click':
            lead.email_clicks += 1
            lead.save(update_fields=['email_clicks'])
            logger.info(f"Brevo: Link geklickt von {email}")
            
        elif event == 'hard_bounce':
            lead.status = Lead.Status.INVALID
            lead.notes = (lead.notes or '') + f"\n[Brevo] Hard Bounce: Email unzustellbar"
            lead.save(update_fields=['status', 'notes'])
            logger.warning(f"Brevo: Hard Bounce für {email}")
            
        elif event == 'unsubscribed':
            lead.interest_level = 0
            lead.notes = (lead.notes or '') + f"\n[Brevo] Abgemeldet"
            lead.save(update_fields=['interest_level', 'notes'])
            logger.info(f"Brevo: Abmeldung von {email}")
        
        return JsonResponse({'status': 'ok', 'event': event})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Brevo Webhook Fehler: {e}")
        return JsonResponse({'error': str(e)}, status=500)
