"""URL configuration for app_settings"""
from django.urls import path
from . import views

app_name = 'app_settings'

urlpatterns = [
    path('', views.settings_dashboard, name='dashboard'),
    path('user/', views.user_preferences_view, name='user-preferences'),
    path('system/', views.system_settings_view, name='system-settings'),
    path('integrations/', views.integrations_view, name='integrations'),
]
