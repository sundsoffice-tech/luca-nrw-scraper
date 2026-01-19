"""Admin configuration for Email Templates"""
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import (
    EmailTemplate, EmailTemplateVersion, EmailSendLog,
    EmailFlow, FlowStep, FlowExecution, FlowStepExecution
)


class EmailTemplateVersionInline(admin.TabularInline):
    """Inline für Template-Versionen"""
    model = EmailTemplateVersion
    extra = 0
    fields = ['version', 'subject', 'created_by', 'created_at', 'note']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EmailTemplate)
class EmailTemplateAdmin(ModelAdmin):
    """Admin für EmailTemplate mit Unfold-Styling"""
    list_display = [
        'name', 'category', 'is_active', 'send_count', 
        'ai_generated_badge', 'last_sent_at', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'ai_generated', 'sync_to_brevo']
    search_fields = ['name', 'slug', 'subject']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['send_count', 'last_sent_at', 'created_at', 'updated_at']
    inlines = [EmailTemplateVersionInline]
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('slug', 'name', 'category', 'is_active')
        }),
        ('Email-Inhalt', {
            'fields': ('subject', 'html_content', 'text_content', 'available_variables')
        }),
        ('KI-Generierung', {
            'fields': ('ai_generated', 'ai_prompt_used'),
            'classes': ('collapse',)
        }),
        ('Brevo-Integration', {
            'fields': ('sync_to_brevo', 'brevo_template_id'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('send_count', 'last_sent_at', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_templates', 'deactivate_templates', 'duplicate_template']
    
    def ai_generated_badge(self, obj):
        """Badge für KI-generierte Templates"""
        if obj.ai_generated:
            return format_html('<span style="color: #06b6d4;">🤖 KI</span>')
        return '-'
    ai_generated_badge.short_description = 'KI'
    
    @admin.action(description='Ausgewählte Templates aktivieren')
    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} Template(s) aktiviert.')
    
    @admin.action(description='Ausgewählte Templates deaktivieren')
    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} Template(s) deaktiviert.')
    
    @admin.action(description='Template duplizieren')
    def duplicate_template(self, request, queryset):
        for template in queryset:
            template.pk = None
            template.slug = f"{template.slug}-copy"
            template.name = f"{template.name} (Kopie)"
            template.send_count = 0
            template.last_sent_at = None
            template.save()
        self.message_user(request, f'{queryset.count()} Template(s) dupliziert.')


@admin.register(EmailTemplateVersion)
class EmailTemplateVersionAdmin(ModelAdmin):
    """Admin für EmailTemplateVersion"""
    list_display = ['template', 'version', 'subject', 'created_by', 'created_at']
    list_filter = ['template', 'created_at']
    search_fields = ['template__name', 'subject', 'note']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Version-Info', {
            'fields': ('template', 'version', 'note')
        }),
        ('Inhalt', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Metadaten', {
            'fields': ('created_by', 'created_at')
        }),
    )


@admin.register(EmailSendLog)
class EmailSendLogAdmin(ModelAdmin):
    """Admin für EmailSendLog"""
    list_display = [
        'to_email', 'subject_rendered', 'status_badge', 
        'template', 'lead', 'sent_at'
    ]
    list_filter = ['status', 'sent_at']
    search_fields = ['to_email', 'subject_rendered', 'brevo_message_id']
    readonly_fields = ['sent_at', 'opened_at', 'clicked_at']
    
    fieldsets = (
        ('Email-Info', {
            'fields': ('to_email', 'subject_rendered', 'status')
        }),
        ('Verknüpfungen', {
            'fields': ('template', 'lead')
        }),
        ('Brevo-Tracking', {
            'fields': ('brevo_message_id',)
        }),
        ('Zeitstempel', {
            'fields': ('sent_at', 'opened_at', 'clicked_at')
        }),
    )
    
    def status_badge(self, obj):
        """Farbige Status-Badges"""
        colors = {
            'sent': '#gray',
            'delivered': '#06b6d4',
            'opened': '#10b981',
            'clicked': '#3b82f6',
            'bounced': '#f59e0b',
            'failed': '#ef4444',
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


class FlowStepInline(admin.TabularInline):
    """Inline für Flow-Steps"""
    model = FlowStep
    extra = 1
    fields = ['order', 'name', 'action_type', 'email_template', 'is_active']
    ordering = ['order']


@admin.register(EmailFlow)
class EmailFlowAdmin(ModelAdmin):
    """Admin für EmailFlow mit Unfold-Styling"""
    list_display = [
        'name', 'trigger_type_display', 'is_active_badge', 'execution_count', 
        'last_executed_at', 'created_at'
    ]
    list_filter = ['is_active', 'trigger_type', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['execution_count', 'last_executed_at', 'created_at', 'updated_at']
    inlines = [FlowStepInline]
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('slug', 'name', 'description', 'is_active')
        }),
        ('Trigger-Konfiguration', {
            'fields': ('trigger_type', 'trigger_config')
        }),
        ('Statistiken', {
            'fields': ('execution_count', 'last_executed_at'),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_flows', 'deactivate_flows', 'duplicate_flow']
    
    def trigger_type_display(self, obj):
        """Zeige Trigger-Typ mit Icon"""
        icons = {
            'lead_created': '➕',
            'lead_status_changed': '🔄',
            'lead_score_reached': '⭐',
            'tag_added': '🏷️',
            'time_based': '⏰',
            'form_submitted': '📝',
            'email_opened': '📧',
            'email_clicked': '🖱️',
            'manual': '👆',
        }
        icon = icons.get(obj.trigger_type, '📋')
        return format_html(f'{icon} {obj.get_trigger_type_display()}')
    trigger_type_display.short_description = 'Trigger'
    
    def is_active_badge(self, obj):
        """Badge für aktive/inaktive Flows"""
        if obj.is_active:
            return format_html('<span style="color: #10b981;">✓ Aktiv</span>')
        return format_html('<span style="color: #6b7280;">○ Inaktiv</span>')
    is_active_badge.short_description = 'Status'
    
    @admin.action(description='Ausgewählte Flows aktivieren')
    def activate_flows(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} Flow(s) aktiviert.')
    
    @admin.action(description='Ausgewählte Flows deaktivieren')
    def deactivate_flows(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} Flow(s) deaktiviert.')
    
    @admin.action(description='Flow duplizieren')
    def duplicate_flow(self, request, queryset):
        from django.utils.text import slugify
        import time
        
        for flow in queryset:
            # Speichere Steps
            steps = list(flow.steps.all())
            # Dupliziere Flow
            flow.pk = None
            # Generate unique slug
            base_slug = f"{flow.slug}-copy"
            slug = base_slug
            counter = 1
            while EmailFlow.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            flow.slug = slug
            flow.name = f"{flow.name} (Kopie)"
            flow.execution_count = 0
            flow.last_executed_at = None
            flow.is_active = False
            flow.save()
            # Dupliziere Steps
            for step in steps:
                step.pk = None
                step.flow = flow
                step.save()
        self.message_user(request, f'{queryset.count()} Flow(s) dupliziert.')


@admin.register(FlowStep)
class FlowStepAdmin(ModelAdmin):
    """Admin für FlowStep"""
    list_display = ['flow', 'order', 'action_type', 'name', 'email_template', 'is_active']
    list_filter = ['action_type', 'is_active', 'flow']
    search_fields = ['name', 'flow__name']
    readonly_fields = []
    
    fieldsets = (
        ('Zuordnung', {
            'fields': ('flow', 'order')
        }),
        ('Aktion', {
            'fields': ('action_type', 'name', 'action_config')
        }),
        ('Email-Template', {
            'fields': ('email_template',),
            'description': 'Nur für action_type="send_email"'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


class FlowStepExecutionInline(admin.TabularInline):
    """Inline für Step-Executions"""
    model = FlowStepExecution
    extra = 0
    fields = ['step', 'status', 'started_at', 'completed_at']
    readonly_fields = ['step', 'status', 'started_at', 'completed_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FlowExecution)
class FlowExecutionAdmin(ModelAdmin):
    """Admin für FlowExecution"""
    list_display = [
        'flow', 'lead', 'status_badge', 'current_step', 
        'started_at', 'completed_at'
    ]
    list_filter = ['status', 'flow', 'started_at']
    search_fields = ['flow__name', 'lead__name', 'lead__email']
    readonly_fields = ['started_at', 'completed_at']
    inlines = [FlowStepExecutionInline]
    
    fieldsets = (
        ('Ausführung', {
            'fields': ('flow', 'lead', 'status', 'current_step')
        }),
        ('Zeitplan', {
            'fields': ('started_at', 'completed_at', 'next_execution_at')
        }),
        ('Fehler & Log', {
            'fields': ('error_message', 'execution_log'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Farbige Status-Badges"""
        colors = {
            'pending': '#6b7280',
            'running': '#06b6d4',
            'waiting': '#f59e0b',
            'completed': '#10b981',
            'paused': '#8b5cf6',
            'failed': '#ef4444',
            'cancelled': '#6b7280',
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(FlowStepExecution)
class FlowStepExecutionAdmin(ModelAdmin):
    """Admin für FlowStepExecution"""
    list_display = [
        'execution', 'step', 'status_badge', 
        'started_at', 'completed_at'
    ]
    list_filter = ['status', 'step__action_type', 'started_at']
    search_fields = ['execution__flow__name', 'step__name']
    readonly_fields = ['started_at', 'completed_at']
    
    fieldsets = (
        ('Zuordnung', {
            'fields': ('execution', 'step', 'status')
        }),
        ('Zeitstempel', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Ergebnis', {
            'fields': ('result_data', 'error_message'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Farbige Status-Badges"""
        colors = {
            'pending': '#6b7280',
            'running': '#06b6d4',
            'completed': '#10b981',
            'failed': '#ef4444',
            'skipped': '#f59e0b',
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
