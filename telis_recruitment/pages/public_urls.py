"""Public URLs for landing pages"""
from django.urls import path
from . import views, views_upload

app_name = 'pages_public'

urlpatterns = [
    # Public landing page
    path('<slug:slug>/', views.public_page, name='page-public'),
    
    # Form submission endpoint
    path('<slug:slug>/submit/', views.form_submit, name='form-submit'),
    
    # Static file serving for uploaded sites
    path('<slug:slug>/static/<path:file_path>', views_upload.serve_uploaded_file, name='serve-static'),
]
