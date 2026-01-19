from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import ReportSchedule, ReportHistory


class ReportHistoryInline(TabularInline):
    """Inline for ReportHistory"""
    model = ReportHistory
    extra = 0
    can_delete = False
    readonly_fields = ['report_type', 'generated_at', 'generated_by', 'period_start', 'period_end', 'file_format', 'file_path']
    fields = ['report_type', 'generated_at', 'generated_by', 'period_start', 'period_end', 'file_format']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReportSchedule)
class ReportScheduleAdmin(ModelAdmin):
    """Admin interface for ReportSchedule"""
    
    list_display = ['name', 'report_type', 'frequency', 'is_active', 'last_run', 'next_run']
    list_filter = ['report_type', 'frequency', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name', 'recipients']
    readonly_fields = ['created_at', 'updated_at', 'last_run']
    
    fieldsets = (
        ('Basis-Einstellungen', {
            'fields': ('name', 'report_type', 'frequency', 'is_active'),
        }),
        ('Empfänger', {
            'fields': ('recipients',),
        }),
        ('Zeitplanung', {
            'fields': ('last_run', 'next_run'),
        }),
        ('Metadaten', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [ReportHistoryInline]
    
    actions = ['activate_schedules', 'deactivate_schedules']
    
    def activate_schedules(self, request, queryset):
        """Aktiviere ausgewählte Report-Zeitpläne"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} Report-Zeitplan(e) wurden aktiviert.')
    activate_schedules.short_description = "Ausgewählte Zeitpläne aktivieren"
    
    def deactivate_schedules(self, request, queryset):
        """Deaktiviere ausgewählte Report-Zeitpläne"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} Report-Zeitplan(e) wurden deaktiviert.')
    deactivate_schedules.short_description = "Ausgewählte Zeitpläne deaktivieren"
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user on creation"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReportHistory)
class ReportHistoryAdmin(ModelAdmin):
    """Admin interface for ReportHistory (read-only)"""
    
    list_display = ['report_type', 'generated_at', 'generated_by', 'period_start', 'period_end', 'file_format']
    list_filter = ['report_type', 'file_format', 'generated_at']
    search_fields = ['report_type', 'file_path']
    readonly_fields = ['schedule', 'report_type', 'generated_at', 'generated_by', 'period_start', 'period_end', 'data', 'file_path', 'file_format']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report-Informationen', {
            'fields': ('schedule', 'report_type', 'generated_at', 'generated_by'),
        }),
        ('Zeitraum', {
            'fields': ('period_start', 'period_end'),
        }),
        ('Datei', {
            'fields': ('file_path', 'file_format'),
        }),
        ('Report-Daten', {
            'fields': ('data',),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        """Reports are generated automatically"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of old reports"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Reports are read-only"""
        return False
