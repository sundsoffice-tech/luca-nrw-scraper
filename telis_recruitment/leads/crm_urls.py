"""
URL routing for TELIS CRM application.
All CRM URLs are protected and require authentication.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.crm_dashboard, name='crm-dashboard'),
    # Future: Add more CRM routes here
    # path('leads/', views.crm_leads, name='crm-leads'),
    # path('phone/', views.crm_phone, name='crm-phone'),
    # path('emails/', views.crm_emails, name='crm-emails'),
    # path('reports/', views.crm_reports, name='crm-reports'),
]
