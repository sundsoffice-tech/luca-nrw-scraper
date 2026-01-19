from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.reports_dashboard, name='dashboard'),
    
    # API Endpoints
    path('api/kpis/', views.api_kpis, name='api_kpis'),
    path('api/trend/', views.api_trend, name='api_trend'),
    path('api/report/<str:report_type>/', views.api_report, name='api_report'),
    
    # Export
    path('export/<str:report_type>/<str:file_format>/', views.export_report, name='export'),
]
