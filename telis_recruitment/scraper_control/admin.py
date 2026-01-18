from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ScraperConfig, ScraperRun, ScraperLog


@admin.register(ScraperConfig)
class ScraperConfigAdmin(ModelAdmin):
    """Admin interface for ScraperConfig"""
    
    list_display = ['id', 'industry', 'mode', 'qpi', 'smart', 'force', 'once', 'dry_run', 'updated_at', 'updated_by']
    list_filter = ['industry', 'mode', 'smart', 'force', 'once', 'dry_run']
    readonly_fields = ['updated_at', 'updated_by']
    
    fieldsets = (
        ('Grundeinstellungen', {
            'fields': ('industry', 'mode', 'qpi', 'daterestrict'),
            'description': 'Basis-Scraper-Einstellungen',
        }),
        ('Flags', {
            'fields': ('smart', 'force', 'once', 'dry_run'),
            'description': 'Erweiterte Optionen und Flags',
        }),
        ('Metadaten', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set updated_by to current user"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        """Only allow one config instance"""
        return not ScraperConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton config"""
        return False


@admin.register(ScraperRun)
class ScraperRunAdmin(ModelAdmin):
    """Admin interface for ScraperRun"""
    
    list_display = ['id', 'status', 'started_at', 'finished_at', 'duration_display', 'leads_found', 'api_cost', 'pid', 'started_by']
    list_filter = ['status', 'started_at', 'started_by']
    search_fields = ['id', 'pid', 'logs']
    readonly_fields = ['started_at', 'finished_at', 'duration_display', 'params_snapshot', 'logs']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Status', {
            'fields': ('status', 'started_at', 'finished_at', 'duration_display')
        }),
        ('Prozess', {
            'fields': ('pid', 'started_by')
        }),
        ('Ergebnisse', {
            'fields': ('leads_found', 'api_cost')
        }),
        ('Parameter', {
            'fields': ('params_snapshot',),
            'classes': ('collapse',)
        }),
        ('Logs', {
            'fields': ('logs',),
            'classes': ('collapse',)
        }),
    )
    
    def duration_display(self, obj):
        """Display duration in a readable format"""
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "-"
    duration_display.short_description = "Dauer"
    
    def has_add_permission(self, request):
        """Runs are created automatically"""
        return False


@admin.register(ScraperLog)
class ScraperLogAdmin(ModelAdmin):
    """Admin interface for ScraperLog"""
    
    list_display = ['id', 'run', 'level', 'message_preview', 'created_at']
    list_filter = ['level', 'created_at', 'run']
    search_fields = ['message']
    readonly_fields = ['run', 'level', 'message', 'created_at']
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        """Show first 100 chars of message"""
        return obj.message[:100] + ('...' if len(obj.message) > 100 else '')
    message_preview.short_description = "Nachricht"
    
    def has_add_permission(self, request):
        """Logs are created automatically"""
        return False
