from django.conf import settings
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    ScraperConfig, ScraperRun, ScraperLog, ErrorLog,
    SearchRegion, SearchDork, PortalSource, BlacklistEntry,
    UrlSeen, QueryDone
)


# Unregister ScraperConfig if it's already registered (prevents AlreadyRegistered error)
if admin.site.is_registered(ScraperConfig):
    admin.site.unregister(ScraperConfig)


@admin.register(ScraperConfig)
class ScraperConfigAdmin(ModelAdmin):
    """Admin interface for ScraperConfig"""
    
    list_display = ['id', 'industry', 'mode', 'qpi', 'smart', 'force', 'once', 'dry_run', 'config_version', 'updated_at', 'updated_by']
    list_filter = ['industry', 'mode', 'smart', 'force', 'once', 'dry_run']
    readonly_fields = ['config_version', 'updated_at', 'updated_by']
    
    BASE_FIELDSETS = (
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
            'fields': ('config_version', 'updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    fieldsets = BASE_FIELDSETS
    SECURITY_FIELDSET = (
        'Sicherheit',
        {
            'fields': ('allow_insecure_ssl',),
            'classes': ('collapse',),
            'description': 'Unsichere SSL-Verbindungen nur im Debug-Modus ändern.',
        }
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.BASE_FIELDSETS)
        if settings.DEBUG:
            fieldsets.append(self.SECURITY_FIELDSET)
        return tuple(fieldsets)
    
    def save_model(self, request, obj, form, change):
        """Set updated_by to current user and notify about automatic restart"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
        # Add message about automatic restart if scraper is running
        from .process_manager import get_manager
        from django.contrib import messages
        
        try:
            manager = get_manager()
            if manager.is_running():
                messages.info(
                    request,
                    'Konfiguration gespeichert. Der laufende Scraper wird automatisch '
                    'neu gestartet, um die Änderungen zu übernehmen (innerhalb von ~10 Sekunden).'
                )
            else:
                messages.success(
                    request,
                    'Konfiguration gespeichert. Die Änderungen werden beim nächsten Start angewendet.'
                )
        except Exception as e:
            # Don't fail if we can't check status
            pass
    
    def has_add_permission(self, request):
        """Only allow one config instance"""
        return not ScraperConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton config"""
        return False


@admin.register(ScraperRun)
class ScraperRunAdmin(ModelAdmin):
    """Admin interface for ScraperRun"""
    
    list_display = ['id', 'status', 'started_at', 'finished_at', 'duration_display', 'leads_found', 'leads_accepted', 'block_rate', 'api_cost', 'pid', 'started_by']
    list_filter = ['status', 'started_at', 'started_by', 'circuit_breaker_triggered']
    search_fields = ['id', 'pid', 'logs']
    readonly_fields = ['started_at', 'finished_at', 'duration_display', 'params_snapshot', 'logs', 'success_rate', 'lead_acceptance_rate']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Status', {
            'fields': ('status', 'started_at', 'finished_at', 'duration_display')
        }),
        ('Prozess', {
            'fields': ('pid', 'started_by')
        }),
        ('Ergebnisse', {
            'fields': ('leads_found', 'leads_accepted', 'leads_rejected', 'api_cost')
        }),
        ('Links/URLs', {
            'fields': ('links_checked', 'links_successful', 'links_failed', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('Performance-Metriken', {
            'fields': ('avg_request_time_ms', 'block_rate', 'timeout_rate', 'error_rate'),
            'classes': ('collapse',)
        }),
        ('Circuit Breaker', {
            'fields': ('circuit_breaker_triggered', 'circuit_breaker_count'),
            'classes': ('collapse',)
        }),
        ('Portal-Statistiken', {
            'fields': ('portal_stats',),
            'classes': ('collapse',)
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
    
    list_display = ['id', 'run', 'level', 'portal', 'message_preview', 'created_at']
    list_filter = ['level', 'portal', 'created_at', 'run']
    search_fields = ['message', 'portal']
    readonly_fields = ['run', 'level', 'portal', 'message', 'created_at']
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        """Show first 100 chars of message"""
        return obj.message[:100] + ('...' if len(obj.message) > 100 else '')
    message_preview.short_description = "Nachricht"
    
    def has_add_permission(self, request):
        """Logs are created automatically"""
        return False


@admin.register(ErrorLog)
class ErrorLogAdmin(ModelAdmin):
    """Admin interface for ErrorLog"""
    
    list_display = ['id', 'run', 'error_type', 'severity', 'portal', 'count', 'message_preview', 'last_occurrence']
    list_filter = ['error_type', 'severity', 'portal', 'created_at']
    search_fields = ['message', 'portal', 'url']
    readonly_fields = ['run', 'created_at', 'last_occurrence', 'details']
    date_hierarchy = 'last_occurrence'
    
    fieldsets = (
        ('Klassifizierung', {
            'fields': ('error_type', 'severity', 'portal')
        }),
        ('Details', {
            'fields': ('message', 'url', 'count')
        }),
        ('Metadaten', {
            'fields': ('run', 'created_at', 'last_occurrence'),
            'classes': ('collapse',)
        }),
        ('Technische Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        """Show first 80 chars of message"""
        return obj.message[:80] + ('...' if len(obj.message) > 80 else '')
    message_preview.short_description = "Fehlermeldung"
    
    def has_add_permission(self, request):
        """Errors are created automatically"""
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
    
    list_display = ['query_short', 'category', 'is_active', 'priority', 'times_used', 'leads_found', 'leads_with_phone', 'success_rate', 'last_synced_at']
    list_filter = ['category', 'is_active', 'ai_generated']
    list_editable = ['is_active', 'priority']
    search_fields = ['query', 'description']
    
    fieldsets = (
        ('Such-Query', {
            'fields': ('query', 'category', 'description', 'is_active', 'priority')
        }),
        ('Performance-Tracking', {
            'fields': ('times_used', 'leads_found', 'leads_with_phone', 'total_search_results', 'success_rate', 'last_used'),
            'classes': ('collapse',)
        }),
        ('KI-Lern-Daten', {
            'fields': ('extraction_patterns', 'top_domains', 'phone_patterns', 'last_synced_at'),
            'classes': ('collapse',),
            'description': 'Automatisch gelernte Muster aus dem AI-System'
        }),
        ('KI-Generierung', {
            'fields': ('ai_generated', 'ai_prompt'),
            'classes': ('collapse',)
        }),
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = [
        'times_used', 
        'leads_found', 
        'leads_with_phone', 
        'total_search_results', 
        'success_rate', 
        'last_used', 
        'extraction_patterns', 
        'top_domains', 
        'phone_patterns', 
        'last_synced_at',
        'created_at', 
        'updated_at',
    ]
    
    def query_short(self, obj):
        return obj.query[:60] + '...' if len(obj.query) > 60 else obj.query
    query_short.short_description = 'Query'


@admin.register(PortalSource)
class PortalSourceAdmin(ModelAdmin):
    """Admin interface for PortalSource"""
    
    list_display = ['display_name', 'name', 'is_active', 'rate_limit_seconds', 'difficulty', 'circuit_breaker_tripped', 'consecutive_errors']
    list_filter = ['is_active', 'difficulty', 'requires_login', 'circuit_breaker_enabled', 'circuit_breaker_tripped']
    list_editable = ['is_active', 'rate_limit_seconds']
    search_fields = ['name', 'display_name']
    
    fieldsets = (
        ('Basis', {
            'fields': ('name', 'display_name', 'base_url', 'is_active')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_seconds', 'max_results')
        }),
        ('Technisch', {
            'fields': ('requires_login', 'difficulty', 'urls')
        }),
        ('Circuit Breaker', {
            'fields': ('circuit_breaker_enabled', 'circuit_breaker_threshold', 'circuit_breaker_cooldown', 
                      'circuit_breaker_tripped', 'circuit_breaker_reset_at', 'consecutive_errors'),
            'classes': ('collapse',)
        }),
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BlacklistEntry)
class BlacklistEntryAdmin(ModelAdmin):
    """Admin interface for BlacklistEntry"""
    
    list_display = ['value', 'entry_type', 'reason', 'is_active']
    list_filter = ['entry_type', 'is_active']
    list_editable = ['is_active']
    search_fields = ['value', 'reason']


@admin.register(UrlSeen)
class UrlSeenAdmin(ModelAdmin):
    """Admin interface for UrlSeen"""
    
    list_display = ['url_preview', 'first_run', 'created_at']
    list_filter = ['created_at', 'first_run']
    search_fields = ['url']
    readonly_fields = ['url', 'first_run', 'created_at']
    date_hierarchy = 'created_at'
    
    def url_preview(self, obj):
        """Show first 80 chars of URL"""
        return obj.url[:80] + ('...' if len(obj.url) > 80 else '')
    url_preview.short_description = "URL"
    
    def has_add_permission(self, request):
        """URLs are tracked automatically"""
        return False


@admin.register(QueryDone)
class QueryDoneAdmin(ModelAdmin):
    """Admin interface for QueryDone"""
    
    list_display = ['query_preview', 'last_run', 'created_at', 'last_executed_at']
    list_filter = ['created_at', 'last_executed_at', 'last_run']
    search_fields = ['query']
    readonly_fields = ['query', 'last_run', 'created_at', 'last_executed_at']
    date_hierarchy = 'last_executed_at'
    
    def query_preview(self, obj):
        """Show first 100 chars of query"""
        return obj.query[:100] + ('...' if len(obj.query) > 100 else '')
    query_preview.short_description = "Query"
    
    def has_add_permission(self, request):
        """Queries are tracked automatically"""
        return False
