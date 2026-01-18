"""URL Configuration for Email Templates"""
from django.urls import path
from . import views

app_name = 'email_templates'

# Web Interface URLs (for /crm/email-templates/)
urlpatterns = [
    path('', views.template_list, name='template-list'),
    path('<slug:slug>/edit/', views.template_editor, name='template-editor'),
    path('<slug:slug>/preview/', views.template_preview, name='template-preview'),
]
