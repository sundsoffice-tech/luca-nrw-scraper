"""Public URLs for landing pages"""
from django.urls import path
from . import views

app_name = 'pages_public'

urlpatterns = [
    # Public landing page
    path('<slug:slug>/', views.public_page, name='page-public'),
    
    # Form submission endpoint
    path('<slug:slug>/submit/', views.form_submit, name='form-submit'),
]
