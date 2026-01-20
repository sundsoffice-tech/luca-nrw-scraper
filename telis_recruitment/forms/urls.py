"""URL patterns for form builder"""
from django.urls import path
from . import views

app_name = 'forms'

urlpatterns = [
    # Form management
    path('', views.form_list, name='list'),
    path('create/', views.form_create, name='create'),
    path('<slug:slug>/', views.form_detail, name='detail'),
    path('<slug:slug>/edit/', views.form_edit, name='edit'),
    path('<slug:slug>/delete/', views.form_delete, name='delete'),
    
    # Form builder
    path('<slug:slug>/builder/', views.form_builder, name='builder'),
    
    # Form preview
    path('<slug:slug>/preview/', views.form_preview, name='preview'),
    
    # Form submissions
    path('<slug:slug>/submissions/', views.form_submissions, name='submissions'),
    path('<slug:slug>/submissions/<int:submission_id>/', views.submission_detail, name='submission-detail'),
    
    # API endpoints
    path('api/<slug:slug>/fields/', views.api_get_fields, name='api-get-fields'),
    path('api/<slug:slug>/fields/save/', views.api_save_fields, name='api-save-fields'),
    path('api/<slug:slug>/submit/', views.api_submit_form, name='api-submit'),
]
