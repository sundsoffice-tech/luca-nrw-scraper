from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ScraperConfig, ScraperRun, ScraperLog, SearchRegion, SearchDork, PortalSource, BlacklistEntry


# Unregister ScraperConfig if it's already registered (prevents AlreadyRegistered error)
if admin.site.is_registered(ScraperConfig):
    admin.site.unregister(ScraperConfig)


@admin.register(ScraperConfig)
class ScraperConfigAdmin(ModelAdmin):
    """Admin interface for ScraperConfig"""
    
    list_display = ['id', 'industry', 'mode', 'qpi', 'smart', 'force', 'once', 'dry_run', 'updated_at', 'updated_by']
    list_filter = ['industry', 'mode', 'smart', 'force', 'once', 'dry_run']
    readonly_fields = ['updated_at', 'updated_by']
    
    fieldsets = (
        ('Basis-Einstellungen', {
            'fields': ('industry', 'mode', 'qpi', 'daterestrict'),
        }),
        ('Flags', {
            'fields': ('smart', 'force', 'once', 'dry_run'),
        }),
        ('HTTP & Performance', {
            'fields': ('http_timeout', 'async_limit', 'pool_size', 'http2_enabled'),
            'classes': ('collapse',)
        }),
        ('Rate Limiting', {
            'fields': ('sleep_between_queries', 'max_google_pages', 'circuit_breaker_penalty', 'retry_max_per_url'),
            'classes': ('collapse',)
        }),
        ('Process Manager - Retry & Circuit Breaker', {
            'fields': ('process_max_retry_attempts', 'process_qpi_reduction_factor', 'process_error_rate_threshold', 
                      'process_circuit_breaker_failures', 'process_retry_backoff_base'),
            'classes': ('collapse',)
        }),
        ('Scoring', {
            'fields': ('min_score', 'max_per_domain', 'default_quality_score', 'confidence_threshold'),
            'classes': ('collapse',)
        }),
        ('Feature Flags', {
            'fields': ('enable_kleinanzeigen', 'enable_telefonbuch', 'enable_perplexity', 'enable_bing', 'parallel_portal_crawl', 'max_concurrent_portals'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('allow_pdf', 'max_content_length'),
            'classes': ('collapse',)
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


@admin.register(SearchRegion)
class SearchRegionAdmin(ModelAdmin):
    """Admin interface for SearchRegion"""
    
    list_display = ['name', 'is_active', 'is_metropolis', 'priority']
    list_filter = ['is_active', 'is_metropolis']
    list_editable = ['is_active', 'is_metropolis', 'priority']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SearchDork)
class SearchDorkAdmin(ModelAdmin):
    """Admin interface for SearchDork"""
    
    list_display = ['query_short', 'category', 'is_active', 'priority', 'times_used', 'leads_found', 'success_rate']
    list_filter = ['category', 'is_active', 'ai_generated']
    list_editable = ['is_active', 'priority']
    search_fields = ['query', 'description']
    
    def query_short(self, obj):
        return obj.query[:60] + '...' if len(obj.query) > 60 else obj.query
    query_short.short_description = 'Query'


@admin.register(PortalSource)
class PortalSourceAdmin(ModelAdmin):
    """Admin interface for PortalSource"""
    
    list_display = ['display_name', 'name', 'is_active', 'rate_limit_seconds', 'difficulty']
    list_filter = ['is_active', 'difficulty', 'requires_login']
    list_editable = ['is_active', 'rate_limit_seconds']
    search_fields = ['name', 'display_name']


@admin.register(BlacklistEntry)
class BlacklistEntryAdmin(ModelAdmin):
    """Admin interface for BlacklistEntry"""
    
    list_display = ['value', 'entry_type', 'reason', 'is_active']
    list_filter = ['entry_type', 'is_active']
    list_editable = ['is_active']
    search_fields = ['value', 'reason']
