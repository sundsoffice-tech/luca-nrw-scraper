"""URL configuration for pages app"""
from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    # Builder interface (staff only)
    path('', views.builder_list, name='builder-list'),
    path('builder/<slug:slug>/', views.builder_view, name='page-builder'),
    
    # Builder API endpoints
    path('api/<slug:slug>/save/', views.builder_save, name='builder-save'),
    path('api/<slug:slug>/load/', views.builder_load, name='builder-load'),
]
