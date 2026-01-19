from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ReportSchedule, ReportHistory


@login_required
def reports_dashboard(request):
    """Haupt-Reports-Seite"""
    return render(request, 'reports/dashboard.html', {
        'schedules': ReportSchedule.objects.filter(is_active=True),
        'recent_reports': ReportHistory.objects.all()[:10],
    })
