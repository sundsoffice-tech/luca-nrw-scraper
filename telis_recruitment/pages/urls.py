"""URL configuration for pages app"""
from django.urls import path
from . import views, views_upload, views_editor

app_name = 'pages'

urlpatterns = [
    # Builder interface (staff only)
    path('', views.builder_list, name='builder-list'),
    path('builder/<slug:slug>/', views.builder_view, name='page-builder'),
    
    # Quick Create Interface
    path('quick-create/', views.quick_create, name='quick-create'),
    
    # Project Management
    path('projects/', views.project_list, name='project-list'),
    path('projects/<slug:slug>/', views.project_detail, name='project-detail'),
    path('projects/<slug:slug>/delete/', views.project_delete, name='project-delete'),
    path('upload-project/', views.upload_project, name='upload-project'),
    
    # Project Settings (NEW)
    path('projects/<slug:slug>/settings/', views.project_settings_view, name='project-settings'),
    
    # Project Navigation (NEW)
    path('projects/<slug:slug>/navigation/', views.project_navigation_view, name='project-navigation'),
    path('projects/<slug:slug>/navigation/save/', views.save_navigation, name='save-navigation'),
    
    # Project Build & Export (NEW)
    path('projects/<slug:slug>/build-page/', views.project_build_view, name='project-build-page'),
    path('projects/<slug:slug>/build/', views.build_project, name='project-build'),
    path('projects/<slug:slug>/export/', views.export_project, name='project-export'),
    
    # Project Deployments (NEW)
    path('projects/<slug:slug>/deployments/', views.project_deployments, name='project-deployments'),
    
    # Builder API endpoints
    path('api/<slug:slug>/save/', views.builder_save, name='builder-save'),
    path('api/<slug:slug>/load/', views.builder_load, name='builder-load'),
    path('api/<slug:slug>/publish/', views.publish_page, name='publish-page'),
    
    # Asset Manager
    path('api/assets/upload/', views.upload_asset, name='upload-asset'),
    path('api/assets/', views.list_assets, name='list-assets'),
    path('assets/<int:asset_id>/delete/', views.delete_asset, name='delete_asset'),
    
    # Brand Settings
    path('brand/', views.brand_settings_view, name='brand-settings'),
    path('brand-settings/css/', views.get_brand_css, name='brand_css'),
    
    # Templates
    path('templates/', views.template_list, name='template-list'),
    path('templates/select/', views.select_template, name='select_template'),
    path('templates/<int:template_id>/apply/', views.apply_template, name='apply_template'),
    path('templates/<int:template_id>/config/', views.template_config, name='template-config'),
    path('templates/category/<str:category>/', views.templates_by_category, name='templates-by-category'),
    
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
    
    # Website Editor (Staff Only)
    path('editor/<slug:slug>/', views_editor.website_editor, name='website-editor'),
    path('api/<slug:slug>/editor/file/', views_editor.get_file_content, name='editor-get-file'),
    path('api/<slug:slug>/editor/file/save/', views_editor.save_file_content, name='editor-save-file'),
    path('api/<slug:slug>/editor/file/create/', views_editor.create_file, name='editor-create-file'),
    path('api/<slug:slug>/editor/file/rename/', views_editor.rename_file, name='editor-rename-file'),
    path('api/<slug:slug>/editor/file/move/', views_editor.move_file, name='editor-move-file'),
    path('api/<slug:slug>/editor/file/duplicate/', views_editor.duplicate_file, name='editor-duplicate-file'),
    path('api/<slug:slug>/editor/folder/create/', views_editor.create_folder, name='editor-create-folder'),
    path('api/<slug:slug>/editor/folder/delete/', views_editor.delete_folder, name='editor-delete-folder'),
    path('api/<slug:slug>/editor/search/', views_editor.search_files, name='editor-search'),
    path('api/<slug:slug>/editor/versions/', views_editor.file_versions, name='editor-versions'),
    path('api/<slug:slug>/editor/restore/', views_editor.restore_version, name='editor-restore'),
    path('api/<slug:slug>/export/', views_editor.export_project, name='export-project'),
    path('api/<slug:slug>/import/', views_editor.import_project, name='import-project'),
]
