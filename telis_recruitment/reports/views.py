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
    """API: Report-Daten generieren"""
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    generator = ReportGenerator(start_date=start_date, end_date=end_date)
    
    try:
        report = generator.generate_report(report_type)
        return JsonResponse(report)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def export_report(request, report_type, file_format):
    """Export Report als PDF/Excel/CSV"""
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    generator = ReportGenerator(start_date=start_date, end_date=end_date)
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
