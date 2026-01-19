from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import UserPreferences, SystemSettings


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
