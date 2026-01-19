"""
Reports Views
Dashboard und API Endpoints
"""
import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.utils import timezone

from .services.report_generator import ReportGenerator
from .services.analytics import AnalyticsService
from .services.export import ReportExporter


def _parse_filters(request) -> dict:
    """Extrahiert Filter-Parameter aus Request"""
    filters = {}
    
    # Lead Filter
    if request.GET.get('status'):
        filters['status'] = request.GET.getlist('status') or request.GET.get('status').split(',')
    
    if request.GET.get('region'):
        filters['region'] = request.GET.getlist('region') or request.GET.get('region').split(',')
    
    if request.GET.get('source'):
        filters['source'] = request.GET.getlist('source') or request.GET.get('source').split(',')
    
    if request.GET.get('min_score'):
        filters['min_score'] = request.GET.get('min_score')
    
    if request.GET.get('max_score'):
        filters['max_score'] = request.GET.get('max_score')
    
    if request.GET.get('with_phone') in ['true', '1', 'True']:
        filters['with_phone'] = True
    
    if request.GET.get('with_email') in ['true', '1', 'True']:
        filters['with_email'] = True
    
    # Scraper Filter
    if request.GET.get('industry'):
        filters['industry'] = request.GET.getlist('industry') or request.GET.get('industry').split(',')
    
    if request.GET.get('run_status'):
        filters['run_status'] = request.GET.getlist('run_status') or request.GET.get('run_status').split(',')
    
    if request.GET.get('mode'):
        filters['mode'] = request.GET.getlist('mode') or request.GET.get('mode').split(',')
    
    return filters


@login_required
def reports_dashboard(request):
    """Haupt-Reports-Dashboard"""
    try:
        from .models import ReportSchedule, ReportHistory
        schedules = ReportSchedule.objects.filter(is_active=True)[:5]
        recent_reports = ReportHistory.objects.all()[:10]
    except (ImportError, AttributeError) as e:
        # Handle missing models or database errors gracefully
        schedules = []
        recent_reports = []
    
    return render(request, 'reports/dashboard.html', {
        'schedules': schedules,
        'recent_reports': recent_reports,
    })


@login_required
@require_GET
def api_kpis(request):
    """API: KPI Summary"""
    days = int(request.GET.get('days', 30))
    analytics = AnalyticsService()
    kpis = analytics.get_kpi_summary(days=days)
    return JsonResponse(kpis)


@login_required
@require_GET
def api_trend(request):
    """API: Trend-Daten"""
    days = int(request.GET.get('days', 30))
    analytics = AnalyticsService()
    trend = analytics.get_trend_data(days=days)
    return JsonResponse({'trend': trend})


@login_required
@require_GET
def api_report(request, report_type):
    """API: Report-Daten generieren MIT Filtern"""
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Custom Datum Support
    if request.GET.get('start_date'):
        try:
            start_date = datetime.fromisoformat(request.GET.get('start_date'))
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.fromisoformat(request.GET.get('end_date'))
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
        except ValueError:
            pass
    
    # Filter parsen
    filters = _parse_filters(request)
    
    generator = ReportGenerator(
        start_date=start_date, 
        end_date=end_date,
        filters=filters
    )
    
    try:
        report = generator.generate_report(report_type)
        # Filter-Info zum Response hinzufügen
        report['applied_filters'] = filters
        return JsonResponse(report)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def export_report(request, report_type, file_format):
    """Export Report als PDF/Excel/CSV MIT Filtern"""
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Custom Datum Support
    if request.GET.get('start_date'):
        try:
            start_date = datetime.fromisoformat(request.GET.get('start_date'))
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.fromisoformat(request.GET.get('end_date'))
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
        except ValueError:
            pass
    
    # Filter parsen
    filters = _parse_filters(request)
    
    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        filters=filters
    )
    exporter = ReportExporter()
    
    try:
        report = generator.generate_report(report_type)
    except ValueError as e:
        return HttpResponse(f"Fehler: {e}", status=400)
    
    title = f"{report_type.replace('_', ' ').title()} Report"
    filename = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if file_format == 'pdf':
        content = exporter.export_pdf(report, title)
        response = HttpResponse(content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    elif file_format == 'xlsx':
        content = exporter.export_excel(report, title)
        response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    elif file_format == 'csv':
        content = exporter.export_csv(report)
        response = HttpResponse(content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    else:
        return HttpResponse("Unbekanntes Format", status=400)
    
    return response


@login_required
@require_GET
def api_filter_options(request):
    """API: Verfügbare Filter-Optionen"""
    from leads.models import Lead
    
    # Status-Optionen aus Model
    status_choices = [
        {'value': choice[0], 'label': choice[1]} 
        for choice in Lead.Status.choices
    ]
    
    # Regionen aus DB
    regions = list(Lead.objects.values_list('location', flat=True).distinct().order_by('location'))
    regions = [r for r in regions if r]  # Leere entfernen
    
    # Quellen aus DB
    sources = list(Lead.objects.values_list('source', flat=True).distinct().order_by('source'))
    sources = [s for s in sources if s][:50]  # Top 50
    
    # Industries
    try:
        from scraper_control.models import ScraperConfig
        industries = [
            {'value': choice[0], 'label': choice[1]}
            for choice in ScraperConfig.INDUSTRY_CHOICES
        ]
    except:
        industries = []
    
    return JsonResponse({
        'status': status_choices,
        'regions': regions,
        'sources': sources,
        'industries': industries,
        'score_range': {'min': 0, 'max': 100},
    })
