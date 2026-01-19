"""
URL routing for TELIS CRM application.
All CRM URLs are protected and require authentication.
"""

from django.urls import path
from . import views
from . import views_export
from . import views_support

urlpatterns = [
    # Main views
    path('', views.crm_dashboard, name='crm-dashboard'),
    path('leads/', views.crm_leads, name='crm-leads'),
    path('leads/<int:pk>/', views.crm_lead_detail, name='crm-lead-detail'),
    
    # Support tools
    path('support/bundle/', views_support.support_bundle_view, name='support-bundle'),
    path('support/health/', views_support.system_health_view, name='system-health'),
    
    # Scraper control (Admin only) - DISABLED - now handled by scraper_control app
    # path('scraper/', views_scraper.scraper_page, name='crm-scraper'),
    
    # API for Dashboard
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('api/activity-feed/', views.activity_feed, name='activity-feed'),
    path('api/team-performance/', views.team_performance, name='team-performance'),
    
    # Scraper API (Admin only) - DISABLED - now handled by scraper_control app
    # path('api/scraper/start/', views_scraper.scraper_start, name='scraper-start'),
    # path('api/scraper/stop/', views_scraper.scraper_stop, name='scraper-stop'),
    # path('api/scraper/status/', views_scraper.scraper_status, name='scraper-status'),
    # path('api/scraper/logs/', views_scraper.scraper_logs, name='scraper-logs'),
    # path('api/scraper/config/', views_scraper.scraper_config, name='scraper-config'),
    # path('api/scraper/config/update/', views_scraper.scraper_config_update, name='scraper-config-update'),
    # path('api/scraper/runs/', views_scraper.scraper_runs, name='scraper-runs'),
    
    # Export API
    path('api/export/csv/', views_export.export_leads_csv, name='export-csv'),
    path('api/export/excel/', views_export.export_leads_excel, name='export-excel'),
    
    # Saved Filters API
    path('api/saved-filters/', views.saved_filters, name='saved-filters'),
    path('api/saved-filters/<int:filter_id>/', views.saved_filter_detail, name='saved-filter-detail'),
    
    # Future: Add more CRM routes here
    # path('phone/', views.crm_phone, name='crm-phone'),
    # path('emails/', views.crm_emails, name='crm-emails'),
    # path('reports/', views.crm_reports, name='crm-reports'),
]
