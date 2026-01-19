"""URL Configuration for Email Templates"""
from django.urls import path
from . import views

app_name = 'email_templates'

# Web Interface URLs (for /crm/email-templates/)
urlpatterns = [
    # Templates
    path('', views.template_list, name='template-list'),
    path('templates/<slug:slug>/edit/', views.template_editor, name='template-editor'),
    path('templates/<slug:slug>/preview/', views.template_preview, name='template-preview'),
    
    # Send Logs
    path('logs/', views.send_logs, name='send-logs'),
    
    # Brevo Settings
    path('settings/brevo/', views.brevo_settings, name='brevo-settings'),
    
    # Flows
    path('flows/', views.flow_list, name='flow-list'),
    path('flows/new/', views.flow_builder, name='flow-builder-new'),
    path('flows/<slug:slug>/', views.flow_detail, name='flow-detail'),
    path('flows/<slug:slug>/edit/', views.flow_builder, name='flow-builder-edit'),
]
