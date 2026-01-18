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
    
    # API endpoints
    path('api/scraper/status/', views.api_scraper_status, name='api-status'),
    path('api/scraper/start/', views.api_scraper_start, name='api-start'),
    path('api/scraper/stop/', views.api_scraper_stop, name='api-stop'),
    path('api/scraper/logs/stream/', views.api_scraper_logs_stream, name='api-logs-stream'),
    path('api/scraper/config/', views.api_scraper_config, name='api-config'),
    path('api/scraper/config/update/', views.api_scraper_config_update, name='api-config-update'),
    path('api/scraper/runs/', views.api_scraper_runs, name='api-runs'),
]
