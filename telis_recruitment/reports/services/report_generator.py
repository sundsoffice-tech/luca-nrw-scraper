"""
Report Generator Service
Generiert verschiedene Report-Typen aus Django Models
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate
from django.utils import timezone


class ReportGenerator:
    """Generiert Reports aus der Datenbank mit Filter-Unterstützung"""
    
    def __init__(
        self, 
        start_date: datetime = None, 
        end_date: datetime = None,
        filters: dict = None
    ):
        self.end_date = end_date or timezone.now()
        self.start_date = start_date or (self.end_date - timedelta(days=30))
        self.filters = filters or {}
    
    def _apply_lead_filters(self, queryset):
        """Wendet Filter auf Lead-Queryset an"""
        # Status Filter
        if self.filters.get('status'):
            statuses = self.filters['status']
            if isinstance(statuses, str):
                statuses = [statuses]
            queryset = queryset.filter(status__in=statuses)
        
        # Region Filter (location field in Lead model)
        if self.filters.get('region'):
            regions = self.filters['region']
            if isinstance(regions, str):
                regions = [regions]
            queryset = queryset.filter(location__in=regions)
        
        # Quelle/Source Filter
        if self.filters.get('source'):
            sources = self.filters['source']
            if isinstance(sources, str):
                sources = [sources]
            queryset = queryset.filter(source__in=sources)
        
        # Min Score Filter
        if self.filters.get('min_score'):
            queryset = queryset.filter(quality_score__gte=int(self.filters['min_score']))
        
        # Max Score Filter
        if self.filters.get('max_score'):
            queryset = queryset.filter(quality_score__lte=int(self.filters['max_score']))
        
        # Mit Telefon Filter
        if self.filters.get('with_phone'):
            queryset = queryset.exclude(telefon__isnull=True).exclude(telefon='')
        
        # Mit Email Filter
        if self.filters.get('with_email'):
            queryset = queryset.exclude(email__isnull=True).exclude(email='')
        
        return queryset
    
    def _apply_scraper_filters(self, queryset):
        """Wendet Filter auf ScraperRun-Queryset an"""
        # Industry Filter (from params_snapshot)
        if self.filters.get('industry'):
            industries = self.filters['industry']
            if isinstance(industries, str):
                industries = [industries]
            queryset = queryset.filter(params_snapshot__industry__in=industries)
        
        # Status Filter (für Runs)
        if self.filters.get('run_status'):
            statuses = self.filters['run_status']
            if isinstance(statuses, str):
                statuses = [statuses]
            queryset = queryset.filter(status__in=statuses)
        
        # Mode Filter (from params_snapshot)
        if self.filters.get('mode'):
            modes = self.filters['mode']
            if isinstance(modes, str):
                modes = [modes]
            queryset = queryset.filter(params_snapshot__mode__in=modes)
        
        return queryset
    
    def generate_lead_report(self) -> Dict[str, Any]:
        """Lead-Übersicht Report MIT Filtern"""
        from leads.models import Lead
        
        leads = Lead.objects.filter(
            created_at__range=[self.start_date, self.end_date]
        )
        
        # Filter anwenden
        leads = self._apply_lead_filters(leads)
        
        total = leads.count()
        with_phone = leads.exclude(telefon__isnull=True).exclude(telefon='').count()
        with_email = leads.exclude(email__isnull=True).exclude(email='').count()
        
        # Status-Verteilung
        status_distribution = list(leads.values('status').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        # Quellen-Verteilung (Top 10)
        source_distribution = list(leads.values('source').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        
        # Regionen-Verteilung
        region_distribution = list(leads.values('location').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        
        # Täglicher Trend
        daily_trend = list(leads.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date'))
        
        return {
            'report_type': 'lead_overview',
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
            },
            'summary': {
                'total_leads': total,
                'with_phone': with_phone,
                'with_email': with_email,
                'phone_rate': round(with_phone / max(total, 1) * 100, 1),
                'email_rate': round(with_email / max(total, 1) * 100, 1),
            },
            'status_distribution': status_distribution,
            'source_distribution': source_distribution,
            'region_distribution': region_distribution,
            'daily_trend': [
                {'date': str(d['date']), 'count': d['count']} 
                for d in daily_trend
            ],
        }
    
    def generate_scraper_report(self) -> Dict[str, Any]:
        """Scraper-Performance Report MIT Filtern"""
        from scraper_control.models import ScraperRun
        
        runs = ScraperRun.objects.filter(
            started_at__range=[self.start_date, self.end_date]
        )
        
        # Filter anwenden
        runs = self._apply_scraper_filters(runs)
        
        total_runs = runs.count()
        completed = runs.filter(status='completed').count()
        failed = runs.filter(status='failed').count()
        
        # Aggregierte Stats
        stats = runs.aggregate(
            total_leads=Sum('leads_found'),
            avg_leads=Avg('leads_found')
        )
        
        # Berechne durchschnittliche Dauer
        avg_duration = 0
        run_count = 0
        for run in runs:
            if run.duration:
                avg_duration += run.duration.total_seconds()
                run_count += 1
        
        if run_count > 0:
            avg_duration = avg_duration / run_count
        
        # Runs nach Industry (aus params_snapshot)
        industry_stats = []
        industry_data = {}
        for run in runs:
            industry = run.params_snapshot.get('industry', 'unknown') if run.params_snapshot else 'unknown'
            if industry not in industry_data:
                industry_data[industry] = {'count': 0, 'leads': 0}
            industry_data[industry]['count'] += 1
            industry_data[industry]['leads'] += run.leads_found or 0
        
        for industry, data in industry_data.items():
            industry_stats.append({
                'industry': industry,
                'count': data['count'],
                'leads': data['leads']
            })
        
        industry_stats.sort(key=lambda x: x['leads'], reverse=True)
        
        return {
            'report_type': 'scraper_performance',
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
            },
            'summary': {
                'total_runs': total_runs,
                'completed': completed,
                'failed': failed,
                'success_rate': round(completed / max(total_runs, 1) * 100, 1),
                'total_leads_found': stats['total_leads'] or 0,
                'avg_leads_per_run': round(stats['avg_leads'] or 0, 1),
                'avg_duration_seconds': round(avg_duration, 1),
            },
            'industry_stats': industry_stats,
        }
    
    def generate_cost_report(self) -> Dict[str, Any]:
        """Kosten-Analyse Report"""
        try:
            from ai_config.models import AIUsageLog, AIConfig
            
            usage = AIUsageLog.objects.filter(
                created_at__range=[self.start_date, self.end_date]
            )
            
            total_cost = usage.aggregate(total=Sum('cost'))['total'] or 0
            total_tokens_prompt = usage.aggregate(total=Sum('tokens_prompt'))['total'] or 0
            total_tokens_completion = usage.aggregate(total=Sum('tokens_completion'))['total'] or 0
            
            # Kosten nach Provider
            by_provider = list(usage.values('provider').annotate(
                cost=Sum('cost'),
                requests=Count('id')
            ).order_by('-cost'))
            
            # Kosten nach Model
            by_model = list(usage.values('model').annotate(
                cost=Sum('cost'),
                requests=Count('id')
            ).order_by('-cost'))
            
            # Budget Status
            config = AIConfig.objects.filter(is_active=True).first()
            daily_budget = float(config.daily_budget) if config else 5.0
            monthly_budget = float(config.monthly_budget) if config else 150.0
            
            return {
                'report_type': 'cost_analysis',
                'period': {
                    'start': self.start_date.isoformat(),
                    'end': self.end_date.isoformat(),
                },
                'summary': {
                    'total_cost': float(total_cost),
                    'total_tokens_prompt': total_tokens_prompt,
                    'total_tokens_completion': total_tokens_completion,
                    'total_requests': usage.count(),
                    'daily_budget': daily_budget,
                    'monthly_budget': monthly_budget,
                },
                'by_provider': [
                    {'provider': p['provider'], 'cost': float(p['cost']), 'requests': p['requests']}
                    for p in by_provider
                ],
                'by_model': [
                    {'model': m['model'], 'cost': float(m['cost']), 'requests': m['requests']}
                    for m in by_model
                ],
            }
        except ImportError:
            return {
                'report_type': 'cost_analysis',
                'error': 'AI-Kostenanalyse ist nicht aktiviert. Bitte aktivieren Sie das ai_config Modul.',
                'period': {
                    'start': self.start_date.isoformat(),
                    'end': self.end_date.isoformat(),
                },
                'summary': {},
            }
    
    def generate_source_report(self) -> Dict[str, Any]:
        """Quellen-Analyse Report"""
        from leads.models import Lead
        
        leads = Lead.objects.filter(
            created_at__range=[self.start_date, self.end_date]
        )
        
        # Top Quellen mit Details
        sources = leads.values('source').annotate(
            total=Count('id'),
            with_phone=Count('id', filter=Q(telefon__isnull=False) & ~Q(telefon='')),
            avg_score=Avg('quality_score')
        ).order_by('-total')[:20]
        
        source_data = []
        for s in sources:
            phone_rate = round(s['with_phone'] / max(s['total'], 1) * 100, 1)
            source_data.append({
                'source': s['source'] or 'Unbekannt',
                'total': s['total'],
                'with_phone': s['with_phone'],
                'phone_rate': phone_rate,
                'avg_score': round(s['avg_score'] or 0, 1),
            })
        
        return {
            'report_type': 'source_analysis',
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
            },
            'sources': source_data,
        }
    
    def generate_conversion_report(self) -> Dict[str, Any]:
        """Conversion-Funnel Report"""
        from leads.models import Lead
        
        leads = Lead.objects.filter(
            created_at__range=[self.start_date, self.end_date]
        )
        
        total = leads.count()
        contacted = leads.filter(status__in=['CONTACTED', 'VOICEMAIL', 'INTERESTED', 'INTERVIEW', 'HIRED']).count()
        interested = leads.filter(status__in=['INTERESTED', 'INTERVIEW', 'HIRED']).count()
        interview = leads.filter(status__in=['INTERVIEW', 'HIRED']).count()
        hired = leads.filter(status='HIRED').count()
        
        funnel = [
            {'stage': 'Leads', 'count': total, 'rate': 100},
            {'stage': 'Kontaktiert', 'count': contacted, 'rate': round(contacted / max(total, 1) * 100, 1)},
            {'stage': 'Interessiert', 'count': interested, 'rate': round(interested / max(total, 1) * 100, 1)},
            {'stage': 'Interview', 'count': interview, 'rate': round(interview / max(total, 1) * 100, 1)},
            {'stage': 'Eingestellt', 'count': hired, 'rate': round(hired / max(total, 1) * 100, 1)},
        ]
        
        return {
            'report_type': 'conversion_funnel',
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
            },
            'funnel': funnel,
        }
    
    def generate_report(self, report_type: str) -> Dict[str, Any]:
        """Generiert Report nach Typ"""
        generators = {
            'lead_overview': self.generate_lead_report,
            'scraper_performance': self.generate_scraper_report,
            'cost_analysis': self.generate_cost_report,
            'source_analysis': self.generate_source_report,
            'conversion_funnel': self.generate_conversion_report,
        }
        
        generator = generators.get(report_type)
        if not generator:
            raise ValueError(f"Unbekannter Report-Typ: {report_type}")
        
        return generator()
