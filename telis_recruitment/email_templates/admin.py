"""Admin configuration for Email Templates"""
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import EmailTemplate, EmailTemplateVersion, EmailSendLog


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
