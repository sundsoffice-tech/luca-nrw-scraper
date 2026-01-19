from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.http import HttpResponse
import csv
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from .models import Lead, CallLog, EmailLog, SyncStatus
# Note: ScraperRun is registered in scraper_control.admin, not here


class CallLogInline(admin.TabularInline):
    """Inline-Ansicht für Anrufe im Lead-Detail"""
    model = CallLog
    extra = 0
    readonly_fields = ['called_at', 'called_by']
    fields = ['outcome', 'duration_seconds', 'interest_level', 'notes', 'called_at', 'called_by']


class EmailLogInline(admin.TabularInline):
    """Inline-Ansicht für Emails im Lead-Detail"""
    model = EmailLog
    extra = 0
    readonly_fields = ['sent_at', 'opened_at', 'clicked_at']
    fields = ['email_type', 'subject', 'sent_at', 'opened_at', 'clicked_at']


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = [
        'name', 
        'status_badge', 
        'source_badge',
        'quality_bar',
        'telefon', 
        'email',
        'lead_type',
        'call_count',
        'interest_badge',
        'created_at'
    ]
    list_filter = [
        'status', 
        'source', 
        'lead_type',
        'interest_level',
        ('created_at', RangeDateFilter),
        'assigned_to',
    ]
    list_filter_submit = True  # Add apply button to filters
    search_fields = ['name', 'email', 'telefon', 'company', 'notes']
    ordering = ['-quality_score', '-created_at']
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Kontakt', {
            'fields': ('name', 'email', 'telefon', 'company', 'role', 'location')
        }),
        ('Status & Qualität', {
            'fields': ('status', 'quality_score', 'lead_type', 'interest_level', 'assigned_to')
        }),
        ('Quelle', {
            'fields': ('source', 'source_url', 'source_detail'),
            'classes': ('collapse',)
        }),
        ('Social Profiles', {
            'fields': ('linkedin_url', 'xing_url'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('call_count', 'last_called_at', 'next_followup_at', 
                      'email_sent_count', 'email_opens', 'email_clicks', 'last_email_at'),
            'classes': ('collapse',)
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['call_count', 'last_called_at', 'email_sent_count', 'email_opens', 'email_clicks', 'last_email_at', 'created_at', 'updated_at']
    inlines = [CallLogInline, EmailLogInline]
    
    actions = ['mark_as_contacted', 'mark_as_interested', 'mark_as_not_interested', 'export_selected_csv']
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'NEW': '#ef4444',
            'CONTACTED': '#eab308', 
            'VOICEMAIL': '#f97316',
            'INTERESTED': '#22c55e',
            'INTERVIEW': '#3b82f6',
            'HIRED': '#a855f7',
            'NOT_INTERESTED': '#6b7280',
            'INVALID': '#1f2937',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, obj.get_status_display()
        )
    
    @admin.display(description='Quelle')
    def source_badge(self, obj):
        icons = {
            'scraper': '🤖',
            'landing_page': '🌐',
            'manual': '✍️',
            'referral': '👥',
        }
        icon = icons.get(obj.source, '❓')
        return format_html('{} {}', icon, obj.get_source_display())
    
    @admin.display(description='Score')
    def quality_bar(self, obj):
        score = obj.quality_score
        if score >= 80:
            color = '#22c55e'
        elif score >= 60:
            color = '#eab308'
        elif score >= 40:
            color = '#f97316'
        else:
            color = '#ef4444'
        
        return format_html(
            '<div style="width: 60px; background: #e5e7eb; border-radius: 4px; overflow: hidden; display: inline-block; vertical-align: middle;">'
            '<div style="width: {}%; height: 14px; background: {};"></div>'
            '</div>'
            '<span style="font-size: 11px; margin-left: 6px; font-weight: 500;">{}</span>',
            score, color, score
        )
    
    @admin.display(description='Interesse')
    def interest_badge(self, obj):
        if obj.interest_level == 0:
            return format_html('<span style="color: #9ca3af;">-</span>')
        stars = '⭐' * obj.interest_level
        return format_html('<span title="{}/5">{}</span>', obj.interest_level, stars)
    
    @admin.action(description='✅ Als "Kontaktiert" markieren')
    def mark_as_contacted(self, request, queryset):
        updated = queryset.update(status=Lead.Status.CONTACTED)
        self.message_user(request, f'{updated} Lead(s) als kontaktiert markiert.')
    
    @admin.action(description='🟢 Als "Interessiert" markieren')
    def mark_as_interested(self, request, queryset):
        updated = queryset.update(status=Lead.Status.INTERESTED)
        self.message_user(request, f'{updated} Lead(s) als interessiert markiert.')
    
    @admin.action(description='⛔ Als "Kein Interesse" markieren')
    def mark_as_not_interested(self, request, queryset):
        updated = queryset.update(status=Lead.Status.NOT_INTERESTED)
        self.message_user(request, f'{updated} Lead(s) als nicht interessiert markiert.')
    
    @admin.action(description='📥 Als CSV exportieren')
    def export_selected_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
        # Add UTF-8 BOM (Byte Order Mark) for proper Unicode character display in Excel
        response.write('\ufeff'.encode('utf-8'))
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Telefon', 'Status', 'Score', 'Quelle', 'Lead-Typ', 'Firma', 'Interesse', 'Anrufe', 'Erstellt'])
        
        for lead in queryset:
            writer.writerow([
                lead.name,
                lead.email or '',
                lead.telefon or '',
                lead.get_status_display(),
                lead.quality_score,
                lead.get_source_display(),
                lead.get_lead_type_display(),
                lead.company or '',
                lead.interest_level,
                lead.call_count,
                lead.created_at.strftime('%d.%m.%Y %H:%M')
            ])
        
        return response


@admin.register(CallLog)
class CallLogAdmin(ModelAdmin):
    list_display = ['lead', 'outcome_badge', 'duration_display', 'interest_display', 'called_by', 'called_at']
    list_filter = ['outcome', 'called_at', 'called_by', 'interest_level']
    search_fields = ['lead__name', 'notes']
    date_hierarchy = 'called_at'
    
    @admin.display(description='Ergebnis')
    def outcome_badge(self, obj):
        colors = {
            'CONNECTED': '#22c55e',
            'VOICEMAIL': '#f97316',
            'BUSY': '#eab308',
            'NO_ANSWER': '#6b7280',
            'WRONG_NUMBER': '#ef4444',
            'CALLBACK_REQUESTED': '#3b82f6',
        }
        color = colors.get(obj.outcome, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_outcome_display()
        )
    
    @admin.display(description='Dauer')
    def duration_display(self, obj):
        if obj.duration_seconds == 0:
            return '-'
        minutes = obj.duration_seconds // 60
        seconds = obj.duration_seconds % 60
        return f'{minutes}:{seconds:02d}'
    
    @admin.display(description='Interesse')
    def interest_display(self, obj):
        if obj.interest_level == 0:
            return '-'
        return '⭐' * obj.interest_level


@admin.register(EmailLog)
class EmailLogAdmin(ModelAdmin):
    list_display = ['lead', 'email_type_badge', 'subject', 'sent_at', 'opened_badge', 'clicked_badge']
    list_filter = ['email_type', 'sent_at']
    search_fields = ['lead__name', 'subject']
    date_hierarchy = 'sent_at'
    
    @admin.display(description='Typ')
    def email_type_badge(self, obj):
        icons = {
            'WELCOME': '👋',
            'FOLLOWUP_1': '📧',
            'FOLLOWUP_2': '📧',
            'FOLLOWUP_3': '📧',
            'INTERVIEW_INVITE': '📅',
            'CUSTOM': '✉️',
        }
        icon = icons.get(obj.email_type, '📧')
        return format_html('{} {}', icon, obj.get_email_type_display())
    
    @admin.display(description='Geöffnet')
    def opened_badge(self, obj):
        if obj.opened_at:
            return format_html('<span style="color: #22c55e;">✓ {}</span>', obj.opened_at.strftime('%d.%m. %H:%M'))
        return format_html('<span style="color: #9ca3af;">-</span>')
    
    @admin.display(description='Geklickt')
    def clicked_badge(self, obj):
        if obj.clicked_at:
            return format_html('<span style="color: #22c55e;">✓ {}</span>', obj.clicked_at.strftime('%d.%m. %H:%M'))
        return format_html('<span style="color: #9ca3af;">-</span>')


@admin.register(SyncStatus)
class SyncStatusAdmin(ModelAdmin):
    """Admin for SyncStatus - shows sync history and statistics"""
    
    list_display = [
        'source',
        'last_sync_badge',
        'last_lead_id',
        'total_imported',
        'total_updated',
        'total_skipped'
    ]
    
    readonly_fields = [
        'source',
        'last_sync_at',
        'last_lead_id',
        'leads_imported',
        'leads_updated',
        'leads_skipped'
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion"""
        return False
    
    @admin.display(description='Letzter Sync')
    def last_sync_badge(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.last_sync_at
        
        # Color based on freshness
        if diff < timedelta(hours=1):
            color = '#22c55e'  # Green - recent
            icon = '🟢'
        elif diff < timedelta(hours=6):
            color = '#eab308'  # Yellow - somewhat recent
            icon = '🟡'
        else:
            color = '#ef4444'  # Red - old
            icon = '🔴'
        
        return format_html(
            '{} <span style="color: {}; font-weight: 500;">{}</span>',
            icon,
            color,
            obj.last_sync_at.strftime('%d.%m.%Y %H:%M:%S')
        )
    
    @admin.display(description='Importiert')
    def total_imported(self, obj):
        return format_html(
            '<span style="color: #22c55e; font-weight: 500;">🆕 {}</span>',
            obj.leads_imported
        )
    
    @admin.display(description='Aktualisiert')
    def total_updated(self, obj):
        return format_html(
            '<span style="color: #3b82f6; font-weight: 500;">🔄 {}</span>',
            obj.leads_updated
        )
    
    @admin.display(description='Übersprungen')
    def total_skipped(self, obj):
        return format_html(
            '<span style="color: #6b7280;">⏭️  {}</span>',
            obj.leads_skipped
        )


# Admin Site Customization
admin.site.site_header = '🎯 TELIS Recruitment'
admin.site.site_title = 'TELIS Admin'
admin.site.index_title = 'Lead Management Dashboard'
