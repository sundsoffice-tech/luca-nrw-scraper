from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import UserPreferences, SystemSettings, PageView, AnalyticsEvent


@admin.register(UserPreferences)
class UserPreferencesAdmin(ModelAdmin):
    list_display = ['user', 'theme', 'language', 'email_notifications', 'updated_at']
    list_filter = ['theme', 'language', 'email_notifications']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemSettings)
class SystemSettingsAdmin(ModelAdmin):
    fieldsets = (
        ('Allgemein', {
            'fields': ('site_name', 'site_url', 'admin_email')
        }),
        ('Module', {
            'fields': ('enable_email_module', 'enable_scraper', 'enable_ai_features', 'enable_landing_pages')
        }),
        ('Analytics & Tracking', {
            'fields': ('enable_analytics', 'google_analytics_id', 'meta_pixel_id', 'custom_tracking_code'),
            'description': 'Konfigurieren Sie Tracking-Codes für externe Analytics-Dienste'
        }),
        ('Wartung', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
        ('Sicherheit', {
            'fields': ('session_timeout_minutes', 'max_login_attempts')
        }),
        ('Metadaten', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Only one instance allowed (singleton)
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of singleton
        return False


@admin.register(PageView)
class PageViewAdmin(ModelAdmin):
    list_display = ['path', 'page_title', 'user', 'timestamp', 'method', 'ip_address']
    list_filter = ['method', 'timestamp', 'user']
    search_fields = ['path', 'page_title', 'user__username', 'ip_address']
    readonly_fields = ['user', 'session_key', 'path', 'page_title', 'method', 'referrer', 
                       'user_agent', 'ip_address', 'timestamp', 'load_time']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Page views are created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Page views should not be modified
        return False


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(ModelAdmin):
    list_display = ['category', 'action', 'label', 'user', 'timestamp', 'page_path']
    list_filter = ['category', 'action', 'timestamp', 'user']
    search_fields = ['action', 'label', 'page_path', 'user__username']
    readonly_fields = ['user', 'session_key', 'category', 'action', 'label', 'value',
                       'page_path', 'metadata', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Analytics events are created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Analytics events should not be modified
        return False
