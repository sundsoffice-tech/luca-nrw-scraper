"""
Analytics Service
KPI-Summary und Trend-Daten für Dashboard
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate
from django.utils import timezone


class AnalyticsService:
    """Liefert KPIs und Trends für das Dashboard"""
    
    def get_kpi_summary(self, days: int = 30) -> Dict[str, Any]:
        """Holt KPI-Summary für Dashboard"""
        from leads.models import Lead
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        prev_start = start_date - timedelta(days=days)
        
        # Aktuelle Periode
        current = Lead.objects.filter(created_at__range=[start_date, end_date])
        previous = Lead.objects.filter(created_at__range=[prev_start, start_date])
        
        current_total = current.count()
        previous_total = previous.count()
        
        current_with_phone = current.exclude(telefon__isnull=True).exclude(telefon='').count()
        previous_with_phone = previous.exclude(telefon__isnull=True).exclude(telefon='').count()
        
        # Änderungen berechnen
        total_change = self._calc_change(current_total, previous_total)
        phone_change = self._calc_change(current_with_phone, previous_with_phone)
        
        # Phone Rate
        phone_rate = round(current_with_phone / max(current_total, 1) * 100, 1)
        prev_phone_rate = round(previous_with_phone / max(previous_total, 1) * 100, 1)
        
        return {
            'total_leads': current_total,
            'total_leads_change': total_change,
            'with_phone': current_with_phone,
            'with_phone_change': phone_change,
            'phone_rate': phone_rate,
            'phone_rate_change': round(phone_rate - prev_phone_rate, 1),
            'period_days': days,
        }
    
    def get_trend_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Holt Trend-Daten für Charts"""
        from leads.models import Lead
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        trend = Lead.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Count('id'),
            with_phone=Count('id', filter=Q(telefon__isnull=False) & ~Q(telefon=''))
        ).order_by('date')
        
        return [
            {
                'date': str(t['date']),
                'total': t['total'],
                'with_phone': t['with_phone'],
            }
            for t in trend
        ]
    
    def _calc_change(self, current: int, previous: int) -> float:
        """Berechnet prozentuale Änderung"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)
