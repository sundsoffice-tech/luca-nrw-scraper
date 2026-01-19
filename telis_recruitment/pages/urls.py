"""URL configuration for pages app"""
from django.urls import path
from . import views, views_upload

app_name = 'pages'

urlpatterns = [
    # Builder interface (staff only)
    path('', views.builder_list, name='builder-list'),
    path('builder/<slug:slug>/', views.builder_view, name='page-builder'),
    
    # Builder API endpoints
    path('api/<slug:slug>/save/', views.builder_save, name='builder-save'),
    path('api/<slug:slug>/load/', views.builder_load, name='builder-load'),
    
    # Asset Manager
    path('api/assets/upload/', views.upload_asset, name='upload-asset'),
    path('api/assets/', views.list_assets, name='list-assets'),
    path('assets/', views.list_assets, name='list_assets'),
    path('assets/upload/', views.upload_asset, name='upload_asset'),
    path('assets/<int:asset_id>/delete/', views.delete_asset, name='delete_asset'),
    
    # Brand Settings
    path('brand/', views.brand_settings, name='brand-settings'),
    path('brand-settings/', views.brand_settings, name='brand_settings'),
    path('brand-settings/css/', views.get_brand_css, name='brand_css'),
    
    # Templates
    path('templates/', views.template_list, name='template-list'),
    path('templates/select/', views.select_template, name='select_template'),
    path('templates/<int:template_id>/apply/', views.apply_template, name='apply_template'),
    
    # Upload Management (Staff Only)
    path('upload/<slug:slug>/', views_upload.upload_manager, name='upload-manager'),
    path('api/<slug:slug>/upload/zip/', views_upload.upload_zip, name='upload-zip'),
    path('api/<slug:slug>/upload/file/', views_upload.upload_file, name='upload-file'),
    path('api/<slug:slug>/upload/delete/', views_upload.delete_file, name='delete-file'),
    path('api/<slug:slug>/upload/list/', views_upload.list_files, name='list-files'),
    path('api/<slug:slug>/upload/stats/', views_upload.get_stats, name='get-stats'),
    path('api/<slug:slug>/upload/entry-point/', views_upload.set_entry_point, name='set-entry-point'),
    
    # Domain Management (Staff Only)
    path('domain/<slug:slug>/', views_upload.domain_settings, name='domain-settings'),
    path('api/<slug:slug>/domain/save/', views_upload.save_domain_settings, name='save-domain'),
    path('api/<slug:slug>/domain/verify/', views_upload.verify_dns, name='verify-dns'),
    path('api/<slug:slug>/domain/nginx/', views_upload.get_nginx_config, name='nginx-config'),
]
