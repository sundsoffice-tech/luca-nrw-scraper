"""
URL configuration for scraper_control app.
All URLs are prefixed with /crm/scraper/ in the main urls.py
"""

from django.urls import path
from . import views

app_name = 'scraper_control'

urlpatterns = [
    # Dashboard view
    path('', views.scraper_dashboard, name='dashboard'),
    
    # API endpoints - Scraper control
    path('api/scraper/status/', views.api_scraper_status, name='api-status'),
    path('api/scraper/start/', views.api_scraper_start, name='api-start'),
    path('api/scraper/stop/', views.api_scraper_stop, name='api-stop'),
    path('api/scraper/logs/stream/', views.api_scraper_logs_stream, name='api-logs-stream'),
    path('api/scraper/config/', views.api_scraper_config, name='api-config'),
    path('api/scraper/config/update/', views.api_scraper_config_update, name='api-config-update'),
    path('api/scraper/runs/', views.api_scraper_runs, name='api-runs'),
    
    # API endpoints - Logs and Errors
    path('api/logs/', views.api_logs_filtered, name='api-logs-filtered'),
    path('api/errors/', views.api_errors_filtered, name='api-errors-filtered'),
    
    # API endpoints - Control Center
    path('api/control/rate-limit/', views.api_update_rate_limit, name='api-update-rate-limit'),
    path('api/control/portal/toggle/', views.api_toggle_portal, name='api-toggle-portal'),
    path('api/control/portals/', views.api_portals_status, name='api-portals-status'),
    path('api/control/circuit-breaker/reset/', views.api_reset_circuit_breaker, name='api-reset-circuit-breaker'),
]
