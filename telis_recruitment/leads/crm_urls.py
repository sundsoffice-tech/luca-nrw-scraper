"""
URL routing for TELIS CRM application.
All CRM URLs are protected and require authentication.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Main views
    path('', views.crm_dashboard, name='crm-dashboard'),
    path('leads/', views.crm_leads, name='crm-leads'),
    path('leads/<int:pk>/', views.crm_lead_detail, name='crm-lead-detail'),
    
    # API for Dashboard
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('api/activity-feed/', views.activity_feed, name='activity-feed'),
    path('api/team-performance/', views.team_performance, name='team-performance'),
    
    # Future: Add more CRM routes here
    # path('phone/', views.crm_phone, name='crm-phone'),
    # path('emails/', views.crm_emails, name='crm-emails'),
    # path('reports/', views.crm_reports, name='crm-reports'),
]
