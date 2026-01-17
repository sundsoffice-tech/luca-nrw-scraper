import csv
import io
import json
import logging
from io import StringIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.db import models, transaction
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Lead, CallLog, EmailLog, SyncStatus
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
    def append_note(lead, note_text):
        """Helper function to append notes to lead"""
        if lead.notes:
            lead.notes = f"{lead.notes}\n{note_text}"
        else:
            lead.notes = note_text
    
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
            append_note(lead, "[Brevo] Hard Bounce: Email unzustellbar")
            lead.save(update_fields=['status', 'notes'])
            logger.warning(f"Brevo: Hard Bounce für {email}")
            
        elif event == 'unsubscribed':
            lead.interest_level = 0
            append_note(lead, "[Brevo] Abgemeldet")
            lead.save(update_fields=['interest_level', 'notes'])
            logger.info(f"Brevo: Abmeldung von {email}")
        
        return JsonResponse({'status': 'ok', 'event': event})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Brevo Webhook Fehler: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_sync(request):
    """
    Triggert einen manuellen Sync vom Scraper.
    
    Optional parameters:
    - force: Boolean - Force reimport all leads (default: false)
    - db_path: String - Custom path to scraper.db (optional)
    """
    try:
        force = request.data.get('force', False)
        db_path = request.data.get('db_path', None)
        
        # Build command arguments
        args = []
        if db_path:
            args.extend(['--db', db_path])
        if force:
            args.append('--force')
        
        # Call the management command
        out = StringIO()
        
        call_command('import_scraper_db', *args, stdout=out)
        
        output = out.getvalue()
        
        # Get updated sync status
        try:
            sync_status = SyncStatus.objects.get(source='scraper_db')
            sync_data = {
                'last_sync_at': sync_status.last_sync_at.isoformat(),
                'last_lead_id': sync_status.last_lead_id,
                'total_imported': sync_status.leads_imported,
                'total_updated': sync_status.leads_updated,
                'total_skipped': sync_status.leads_skipped,
            }
        except SyncStatus.DoesNotExist:
            sync_data = None
        
        return Response({
            'success': True,
            'message': 'Sync erfolgreich abgeschlossen',
            'output': output,
            'sync_status': sync_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Sync error: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# CRM Views
# ===============================

def get_user_role(user):
    """Helper function to get user's role name"""
    if not user.is_authenticated:
        return None
    
    # Check for superuser
    if user.is_superuser:
        return 'Admin'
    
    # Get first group (primary role)
    group = user.groups.first()
    if group:
        return group.name
    
    return 'Benutzer'


def get_dashboard_stats(user):
    """Get dashboard statistics for the user"""
    from django.db.models import Count, Avg
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Base queryset (filter by assigned_to for Telefonisten)
    user_role = get_user_role(user)
    if user_role == 'Telefonist':
        leads_queryset = Lead.objects.filter(assigned_to=user)
        # Filter calls to only those made by this user
        calls_queryset = CallLog.objects.filter(called_by=user, called_at__date=today)
    else:
        leads_queryset = Lead.objects.all()
        calls_queryset = CallLog.objects.filter(called_at__date=today)
    
    total = leads_queryset.count()
    today_count = leads_queryset.filter(created_at__date=today).count()
    
    # Hot leads count
    hot_leads = leads_queryset.filter(quality_score__gte=80, interest_level__gte=3).count()
    
    # Call stats
    calls_today = calls_queryset.count()
    
    return {
        'total': total,
        'today': today_count,
        'hot_leads': hot_leads,
        'calls_today': calls_today,
    }


@login_required
def crm_dashboard(request):
    """
    Main CRM dashboard for logged-in users.
    Shows overview statistics and quick actions.
    """
    context = {
        'user_role': get_user_role(request.user),
        'stats': get_dashboard_stats(request.user),
    }
    return render(request, 'crm/dashboard.html', context)


@login_required
def crm_leads(request):
    """
    Lead management view with filtering and bulk actions.
    """
    context = {
        'user_role': get_user_role(request.user),
    }
    return render(request, 'crm/leads.html', context)


@login_required
def crm_lead_detail(request, pk):
    """
    Lead detail view (slide-over panel).
    """
    from django.shortcuts import get_object_or_404
    lead = get_object_or_404(Lead, pk=pk)
    
    # Check permissions for Telefonist
    user_role = get_user_role(request.user)
    if user_role == 'Telefonist' and lead.assigned_to != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Sie haben keine Berechtigung, diesen Lead zu sehen.")
    
    context = {
        'lead': lead,
        'user_role': user_role,
    }
    return render(request, 'crm/lead_detail.html', context)


# ===============================
# Dashboard API Endpoints
# ===============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Real-time KPIs for dashboard.
    Returns comprehensive statistics including trends and distributions.
    """
    from django.db.models import Count, Avg, Q
    from django.utils import timezone
    from datetime import timedelta
    
    user = request.user
    user_role = get_user_role(user)
    
    # Base queryset (filter by assigned_to for Telefonisten)
    if user_role == 'Telefonist':
        leads_queryset = Lead.objects.filter(assigned_to=user)
        calls_queryset = CallLog.objects.filter(called_by=user)
    else:
        leads_queryset = Lead.objects.all()
        calls_queryset = CallLog.objects.all()
    
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)
    
    # Basic stats
    total_leads = leads_queryset.count()
    leads_today = leads_queryset.filter(created_at__date=today).count()
    calls_today = calls_queryset.filter(called_at__date=today).count()
    hot_leads = leads_queryset.filter(quality_score__gte=80).count()
    
    # Conversion rate (leads that reached INTERVIEW or HIRED status)
    converted_leads = leads_queryset.filter(
        status__in=[Lead.Status.INTERVIEW, Lead.Status.HIRED]
    ).count()
    conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0
    
    # Previous week conversion for comparison
    prev_week_leads = leads_queryset.filter(
        created_at__gte=last_week_start, 
        created_at__lt=week_ago
    ).count()
    prev_week_converted = leads_queryset.filter(
        status__in=[Lead.Status.INTERVIEW, Lead.Status.HIRED],
        created_at__gte=last_week_start,
        created_at__lt=week_ago
    ).count()
    prev_conversion_rate = round((prev_week_converted / prev_week_leads * 100), 1) if prev_week_leads > 0 else 0
    conversion_change = round(conversion_rate - prev_conversion_rate, 1)
    
    # 7-day trend data
    trend_7_days = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        new_leads = leads_queryset.filter(created_at__date=date).count()
        conversions = leads_queryset.filter(
            status__in=[Lead.Status.INTERVIEW, Lead.Status.HIRED],
            updated_at__date=date
        ).count()
        trend_7_days.append({
            'date': date.strftime('%Y-%m-%d'),
            'label': date.strftime('%d.%m'),
            'new_leads': new_leads,
            'conversions': conversions
        })
    
    # Status distribution
    status_dist = leads_queryset.values('status').annotate(count=Count('id')).order_by('-count')
    status_distribution = {
        item['status']: {
            'count': item['count'],
            'label': dict(Lead.Status.choices).get(item['status'], item['status'])
        }
        for item in status_dist
    }
    
    # Source distribution
    source_dist = leads_queryset.values('source').annotate(count=Count('id')).order_by('-count')
    source_distribution = {
        item['source']: {
            'count': item['count'],
            'label': dict(Lead.Source.choices).get(item['source'], item['source']),
            'percentage': round((item['count'] / total_leads * 100), 1) if total_leads > 0 else 0
        }
        for item in source_dist
    }
    
    # Average calls per day (last 7 days)
    avg_calls = calls_queryset.filter(called_at__gte=week_ago).count() / 7
    
    return Response({
        'leads_total': total_leads,
        'leads_today': leads_today,
        'calls_today': calls_today,
        'conversion_rate': conversion_rate,
        'conversion_change': conversion_change,
        'hot_leads': hot_leads,
        'avg_calls_per_day': round(avg_calls, 1),
        'trend_7_days': trend_7_days,
        'status_distribution': status_distribution,
        'source_distribution': source_distribution,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_feed(request):
    """
    Recent activities for dashboard feed.
    Shows latest calls, status changes, and new leads.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    user = request.user
    user_role = get_user_role(user)
    
    # Filter by user for Telefonisten
    if user_role == 'Telefonist':
        call_logs = CallLog.objects.filter(called_by=user)
        leads_queryset = Lead.objects.filter(assigned_to=user)
    else:
        call_logs = CallLog.objects.all()
        leads_queryset = Lead.objects.all()
    
    activities = []
    now = timezone.now()
    
    # Recent calls (last 20)
    recent_calls = call_logs.select_related('lead', 'called_by').order_by('-called_at')[:20]
    for call in recent_calls:
        time_diff = now - call.called_at
        activities.append({
            'type': 'call',
            'icon': '📞',
            'message': f"{call.called_by.get_full_name() or call.called_by.username} hat {call.lead.name} angerufen",
            'detail': call.get_outcome_display(),
            'timestamp': call.called_at.isoformat(),
            'time_ago': _format_time_ago(time_diff),
            'lead_id': call.lead.id,
        })
    
    # Recent status changes (infer from updated leads with status != NEW)
    recent_status_changes = leads_queryset.exclude(
        status=Lead.Status.NEW
    ).order_by('-updated_at')[:10]
    for lead in recent_status_changes:
        time_diff = now - lead.updated_at
        activities.append({
            'type': 'status_change',
            'icon': '✅',
            'message': f'Lead "{lead.name}" → {lead.get_status_display()}',
            'detail': f'Score: {lead.quality_score}',
            'timestamp': lead.updated_at.isoformat(),
            'time_ago': _format_time_ago(time_diff),
            'lead_id': lead.id,
        })
    
    # New leads (last 10)
    new_leads = leads_queryset.order_by('-created_at')[:10]
    for lead in new_leads:
        time_diff = now - lead.created_at
        if time_diff.total_seconds() < 86400:  # Only show if less than 24h old
            activities.append({
                'type': 'new_lead',
                'icon': '🆕',
                'message': f'Neuer Lead: {lead.name}',
                'detail': f'Quelle: {lead.get_source_display()}',
                'timestamp': lead.created_at.isoformat(),
                'time_ago': _format_time_ago(time_diff),
                'lead_id': lead.id,
            })
    
    # Sort all activities by timestamp (most recent first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Return top 20
    return Response(activities[:20])


def _format_time_ago(time_diff):
    """Helper to format timedelta as human-readable string"""
    seconds = int(time_diff.total_seconds())
    if seconds < 60:
        return "gerade eben"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"vor {minutes} Minute{'n' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"vor {hours} Stunde{'n' if hours != 1 else ''}"
    else:
        days = seconds // 86400
        return f"vor {days} Tag{'en' if days != 1 else ''}"


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team_performance(request):
    """
    Team performance statistics for Manager/Admin.
    Shows per-user call and conversion stats.
    """
    from django.db.models import Count, Avg, Q
    from django.utils import timezone
    from django.contrib.auth.models import User
    from datetime import timedelta
    
    user_role = get_user_role(request.user)
    
    # Only Manager and Admin can access this
    if user_role not in ['Admin', 'Manager']:
        return Response(
            {'error': 'Keine Berechtigung'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    now = timezone.now()
    today = now.date()
    week_start = now - timedelta(days=7)
    
    # Get all users with Telefonist role
    telefonist_group = User.objects.filter(groups__name='Telefonist')
    
    performance_data = []
    
    for user in telefonist_group:
        # Calls today
        calls_today = CallLog.objects.filter(
            called_by=user,
            called_at__date=today
        ).count()
        
        # Conversions this week (leads moved to INTERVIEW or HIRED)
        conversions_week = Lead.objects.filter(
            assigned_to=user,
            status__in=[Lead.Status.INTERVIEW, Lead.Status.HIRED],
            updated_at__gte=week_start
        ).count()
        
        # Average call duration
        avg_duration = CallLog.objects.filter(
            called_by=user,
            called_at__gte=week_start
        ).aggregate(avg=Avg('duration_seconds'))['avg'] or 0
        
        # Total assigned leads
        assigned_leads = Lead.objects.filter(assigned_to=user).count()
        
        performance_data.append({
            'user_id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'calls_today': calls_today,
            'conversions_week': conversions_week,
            'avg_duration_seconds': round(avg_duration),
            'avg_duration_formatted': f"{int(avg_duration // 60)}:{int(avg_duration % 60):02d}",
            'assigned_leads': assigned_leads,
        })
    
    # Sort by calls today (descending)
    performance_data.sort(key=lambda x: x['calls_today'], reverse=True)
    
    return Response(performance_data)
