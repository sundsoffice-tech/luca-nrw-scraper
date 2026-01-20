from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    AIProvider, AIModel, AIConfig, PromptTemplate, AIUsageLog,
    DorkPerformance, SourcePerformance, PatternSuccess, TelefonbuchCache
)


class AIModelInline(TabularInline):
    """Inline editing of AI Models within Provider"""
    model = AIModel
    extra = 0
    fields = [
        'name', 'display_name', 'default_temperature', 'default_top_p', 
        'default_max_tokens', 'cost_per_1k_tokens_prompt', 
        'cost_per_1k_tokens_completion', 'active'
    ]


@admin.register(AIProvider)
class AIProviderAdmin(ModelAdmin):
    list_display = [
        'name', 'active_badge', 'base_url', 
        'cost_per_1k_tokens_prompt', 'cost_per_1k_tokens_completion',
        'model_count', 'updated_at'
    ]
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'base_url']
    ordering = ['name']
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('name', 'base_url', 'active')
        }),
        ('Default Costs', {
            'fields': ('cost_per_1k_tokens_prompt', 'cost_per_1k_tokens_completion'),
            'description': 'Default costs can be overridden per model'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AIModelInline]
    
    @admin.display(description='Status')
    def active_badge(self, obj):
        if obj.active:
            return format_html(
                '<span style="background-color: #22c55e; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 500;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">Inactive</span>'
        )
    
    @admin.display(description='Models')
    def model_count(self, obj):
        return obj.models.count()


@admin.register(AIModel)
class AIModelAdmin(ModelAdmin):
    list_display = [
        'display_name', 'provider', 'name', 'active_badge',
        'default_temperature', 'default_max_tokens',
        'effective_prompt_cost', 'effective_completion_cost'
    ]
    list_filter = ['active', 'provider', 'created_at']
    search_fields = ['name', 'display_name', 'provider__name']
    ordering = ['provider', 'name']
    
    fieldsets = (
        ('Model Information', {
            'fields': ('provider', 'name', 'display_name', 'active')
        }),
        ('Default Parameters', {
            'fields': ('default_temperature', 'default_top_p', 'default_max_tokens')
        }),
        ('Cost Overrides', {
            'fields': ('cost_per_1k_tokens_prompt', 'cost_per_1k_tokens_completion'),
            'description': 'Override provider default costs (leave blank to use provider defaults)'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @admin.display(description='Status')
    def active_badge(self, obj):
        if obj.active:
            return format_html(
                '<span style="background-color: #22c55e; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 500;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">Inactive</span>'
        )
    
    @admin.display(description='Prompt Cost (EUR/1K)')
    def effective_prompt_cost(self, obj):
        return f"€{obj.get_prompt_cost():.6f}"
    
    @admin.display(description='Completion Cost (EUR/1K)')
    def effective_completion_cost(self, obj):
        return f"€{obj.get_completion_cost():.6f}"


@admin.register(AIConfig)
class AIConfigAdmin(ModelAdmin):
    list_display = [
        'config_name', 'is_active', 'default_provider', 'default_model',
        'temperature', 'daily_budget', 'monthly_budget', 'updated_at'
    ]
    list_filter = ['is_active', 'created_at']
    ordering = ['-is_active', '-created_at']
    
    fieldsets = (
        ('Status', {
            'fields': ('is_active',),
            'description': 'Only one configuration can be active at a time'
        }),
        ('Default Provider & Model', {
            'fields': ('default_provider', 'default_model')
        }),
        ('Model Parameters', {
            'fields': ('temperature', 'top_p', 'max_tokens', 'learning_rate'),
            'description': 'AI model behavior settings',
        }),
        ('Budget Management', {
            'fields': ('daily_budget', 'monthly_budget'),
            'description': 'Cost control settings',
        }),
        ('Quality & Performance', {
            'fields': ('confidence_threshold', 'retry_limit', 'timeout_seconds'),
            'description': 'Performance tuning',
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def config_name(self, obj):
        return str(obj)
    config_name.short_description = 'Configuration'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion if it's the only config or the active one"""
        if obj and obj.is_active:
            # Allow deletion only if there are other configs
            return AIConfig.objects.count() > 1
        return True
    
    def save_model(self, request, obj, form, change):
        """Enforce singleton behavior for active config"""
        super().save_model(request, obj, form, change)
        if obj.is_active:
            # Ensure only this config is active
            AIConfig.objects.filter(is_active=True).exclude(pk=obj.pk).update(is_active=False)


@admin.register(PromptTemplate)
class PromptTemplateAdmin(ModelAdmin):
    list_display = [
        'title', 'slug', 'category', 'is_active', 
        'content_preview', 'updated_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'slug', 'description', 'content']
    ordering = ['category', 'title']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Template Information', {
            'fields': ('title', 'slug', 'category', 'is_active')
        }),
        ('Content', {
            'fields': ('content', 'description'),
            'description': 'Use {placeholder} syntax for variables (e.g., {name}, {company}, {location})'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @admin.display(description='Content Preview')
    def content_preview(self, obj):
        preview = obj.content[:100]
        if len(obj.content) > 100:
            preview += '...'
        return preview


@admin.register(AIUsageLog)
class AIUsageLogAdmin(ModelAdmin):
    list_display = [
        'created_at', 'success_badge', 'provider', 'model',
        'prompt_slug', 'tokens_prompt', 'tokens_completion',
        'cost', 'latency_ms'
    ]
    list_filter = [
        'success', 'provider', 'model', 'prompt_slug',
        ('created_at', admin.DateFieldListFilter)
    ]
    search_fields = ['provider', 'model', 'prompt_slug', 'request_id', 'error_message']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Request Information', {
            'fields': ('provider', 'model', 'prompt_slug', 'request_id')
        }),
        ('Token Usage', {
            'fields': ('tokens_prompt', 'tokens_completion')
        }),
        ('Performance & Cost', {
            'fields': ('cost', 'latency_ms', 'success', 'error_message')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'provider', 'model', 'prompt_slug', 'tokens_prompt', 'tokens_completion',
        'cost', 'latency_ms', 'success', 'error_message', 'request_id',
        'metadata', 'created_at'
    ]
    
    def has_add_permission(self, request):
        """Logs are created programmatically, not manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup purposes"""
        return True
    
    @admin.display(description='Status')
    def success_badge(self, obj):
        if obj.success:
            return format_html(
                '<span style="background-color: #22c55e; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 500;">✓ Success</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">✗ Failed</span>'
        )
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to the changelist"""
        extra_context = extra_context or {}
        
        # Calculate today's stats
        today = timezone.now().date()
        today_logs = AIUsageLog.objects.filter(created_at__date=today)
        
        extra_context['today_total_cost'] = today_logs.aggregate(
            total=Sum('cost')
        )['total'] or 0
        
        extra_context['today_total_requests'] = today_logs.count()
        extra_context['today_success_rate'] = (
            today_logs.filter(success=True).count() / today_logs.count() * 100
            if today_logs.count() > 0 else 0
        )
        
        # Calculate this month's stats
        first_day_of_month = today.replace(day=1)
        month_logs = AIUsageLog.objects.filter(created_at__date__gte=first_day_of_month)
        
        extra_context['month_total_cost'] = month_logs.aggregate(
            total=Sum('cost')
        )['total'] or 0
        
        extra_context['month_total_requests'] = month_logs.count()
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(DorkPerformance)
class DorkPerformanceAdmin(ModelAdmin):
    list_display = [
        'query_preview', 'pool_badge', 'times_used', 'phone_leads',
        'leads_found', 'success_rate_percent', 'last_used'
    ]
    list_filter = ['pool', ('last_used', admin.DateFieldListFilter)]
    search_fields = ['query', 'query_hash']
    ordering = ['-success_rate', '-phone_leads']
    date_hierarchy = 'last_used'
    
    fieldsets = (
        ('Query Information', {
            'fields': ('query', 'query_hash', 'pool')
        }),
        ('Performance Metrics', {
            'fields': ('times_used', 'leads_found', 'phone_leads', 'success_rate')
        }),
        ('Timestamps', {
            'fields': ('last_used', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['query_hash', 'created_at', 'updated_at']
    
    @admin.display(description='Query')
    def query_preview(self, obj):
        preview = obj.query[:80]
        if len(obj.query) > 80:
            preview += '...'
        return preview
    
    @admin.display(description='Pool')
    def pool_badge(self, obj):
        if obj.pool == 'core':
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 500;">Core</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">Explore</span>'
        )
    
    @admin.display(description='Success Rate')
    def success_rate_percent(self, obj):
        return f"{obj.success_rate * 100:.1f}%"


@admin.register(SourcePerformance)
class SourcePerformanceAdmin(ModelAdmin):
    list_display = [
        'domain', 'status_badge', 'leads_with_phone', 'leads_found',
        'avg_quality_percent', 'total_visits', 'last_visit'
    ]
    list_filter = ['is_blocked', ('last_visit', admin.DateFieldListFilter)]
    search_fields = ['domain', 'blocked_reason']
    ordering = ['-avg_quality', '-leads_with_phone']
    date_hierarchy = 'last_visit'
    
    fieldsets = (
        ('Source Information', {
            'fields': ('domain', 'is_blocked', 'blocked_reason')
        }),
        ('Performance Metrics', {
            'fields': ('leads_found', 'leads_with_phone', 'avg_quality', 'total_visits')
        }),
        ('Timestamps', {
            'fields': ('last_visit', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_blocked:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 500;">🚫 Blocked</span>'
            )
        return format_html(
            '<span style="background-color: #22c55e; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">✓ Active</span>'
        )
    
    @admin.display(description='Quality')
    def avg_quality_percent(self, obj):
        return f"{obj.avg_quality * 100:.1f}%"


@admin.register(PatternSuccess)
class PatternSuccessAdmin(ModelAdmin):
    list_display = [
        'pattern_type', 'pattern_preview', 'occurrences',
        'confidence_percent', 'last_success'
    ]
    list_filter = ['pattern_type', ('last_success', admin.DateFieldListFilter)]
    search_fields = ['pattern_value', 'pattern_hash']
    ordering = ['-confidence', '-occurrences']
    date_hierarchy = 'last_success'
    
    fieldsets = (
        ('Pattern Information', {
            'fields': ('pattern_type', 'pattern_value', 'pattern_hash')
        }),
        ('Performance Metrics', {
            'fields': ('occurrences', 'confidence')
        }),
        ('Metadata', {
            'fields': ('metadata', 'last_success'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['pattern_hash', 'created_at', 'updated_at']
    
    @admin.display(description='Pattern')
    def pattern_preview(self, obj):
        preview = obj.pattern_value[:60]
        if len(obj.pattern_value) > 60:
            preview += '...'
        return preview
    
    @admin.display(description='Confidence')
    def confidence_percent(self, obj):
        return f"{obj.confidence * 100:.1f}%"


@admin.register(TelefonbuchCache)
class TelefonbuchCacheAdmin(ModelAdmin):
    list_display = [
        'query_preview', 'hits', 'expires_at', 'is_expired_badge',
        'created_at'
    ]
    list_filter = [
        ('expires_at', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter)
    ]
    search_fields = ['query_text', 'query_hash']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Query Information', {
            'fields': ('query_text', 'query_hash')
        }),
        ('Cache Data', {
            'fields': ('results_json', 'hits')
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['query_hash', 'created_at', 'updated_at']
    
    @admin.display(description='Query')
    def query_preview(self, obj):
        preview = obj.query_text[:60]
        if len(obj.query_text) > 60:
            preview += '...'
        return preview
    
    @admin.display(description='Expired')
    def is_expired_badge(self, obj):
        if obj.is_expired:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 500;">Expired</span>'
            )
        return format_html(
            '<span style="background-color: #22c55e; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">Valid</span>'
        )
    
    def has_add_permission(self, request):
        """Cache entries are created programmatically"""
        return False
    
    actions = ['cleanup_expired']
    
    @admin.action(description='Clean up expired entries')
    def cleanup_expired(self, request, queryset):
        """Delete expired cache entries"""
        from django.utils import timezone
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f"Deleted {count} expired cache entries.")
