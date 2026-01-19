from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    EmailAccount, 
    EmailConversation, 
    Email, 
    EmailAttachment,
    EmailLabel,
    EmailSignature,
    QuickReply
)


@admin.register(EmailAccount)
class EmailAccountAdmin(ModelAdmin):
    list_display = ['name', 'email_address', 'account_type', 'is_active', 'is_default', 'owner', 'last_sync_at']
    list_filter = ['account_type', 'is_active', 'is_default', 'sync_enabled']
    search_fields = ['name', 'email_address', 'owner__username']
    readonly_fields = ['created_at', 'updated_at', 'last_sync_at']
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('name', 'email_address', 'account_type', 'owner')
        }),
        ('IMAP-Einstellungen', {
            'fields': ('imap_host', 'imap_port', 'imap_username', 'imap_password_encrypted', 'imap_use_ssl'),
            'classes': ('collapse',)
        }),
        ('SMTP-Einstellungen', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password_encrypted', 'smtp_use_tls'),
            'classes': ('collapse',)
        }),
        ('Brevo-Einstellungen', {
            'fields': ('brevo_api_key_encrypted',),
            'classes': ('collapse',)
        }),
        ('Synchronisation', {
            'fields': ('sync_enabled', 'sync_interval_minutes', 'last_sync_at', 'last_sync_error')
        }),
        ('Status & Zugriffsrechte', {
            'fields': ('is_active', 'is_default', 'shared_with')
        }),
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['shared_with']


@admin.register(EmailConversation)
class EmailConversationAdmin(ModelAdmin):
    list_display = ['subject', 'contact_email', 'status', 'account', 'lead', 'assigned_to', 'message_count', 'unread_count', 'is_starred', 'last_message_at']
    list_filter = ['status', 'is_starred', 'is_archived', 'is_read', 'account']
    search_fields = ['subject', 'contact_email', 'contact_name']
    readonly_fields = ['created_at', 'updated_at', 'message_count', 'unread_count', 'last_message_at']
    raw_id_fields = ['lead', 'assigned_to', 'account']
    
    fieldsets = (
        ('Konversation', {
            'fields': ('subject', 'subject_normalized', 'contact_email', 'contact_name', 'account')
        }),
        ('Zuordnung', {
            'fields': ('lead', 'assigned_to')
        }),
        ('Status', {
            'fields': ('status', 'is_starred', 'is_archived', 'is_read')
        }),
        ('Statistiken', {
            'fields': ('message_count', 'unread_count', 'last_message_at', 'last_inbound_at', 'last_outbound_at')
        }),
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Email)
class EmailAdmin(ModelAdmin):
    list_display = ['subject', 'from_email', 'direction', 'status', 'conversation', 'account', 'is_read', 'created_at']
    list_filter = ['direction', 'status', 'is_read', 'account']
    search_fields = ['subject', 'from_email', 'from_name', 'body_text', 'message_id']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'received_at', 'read_at']
    raw_id_fields = ['conversation', 'account', 'template_used']
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('conversation', 'account', 'direction', 'message_id', 'in_reply_to', 'references')
        }),
        ('Absender/Empfänger', {
            'fields': ('from_email', 'from_name', 'to_emails', 'cc_emails', 'bcc_emails', 'reply_to_email')
        }),
        ('Inhalt', {
            'fields': ('subject', 'body_text', 'body_html', 'snippet', 'template_used')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'status_detail', 'brevo_message_id')
        }),
        ('Zeitstempel (Ausgehend)', {
            'fields': ('sent_at', 'delivered_at', 'opened_at', 'opened_count', 'clicked_at', 'clicked_links'),
            'classes': ('collapse',)
        }),
        ('Zeitstempel (Eingehend)', {
            'fields': ('received_at', 'is_read', 'read_at'),
            'classes': ('collapse',)
        }),
        ('IMAP', {
            'fields': ('imap_uid', 'imap_folder'),
            'classes': ('collapse',)
        }),
        ('Planung', {
            'fields': ('scheduled_for',),
            'classes': ('collapse',)
        }),
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(ModelAdmin):
    list_display = ['filename', 'email', 'content_type', 'size', 'is_inline', 'is_safe', 'created_at']
    list_filter = ['is_inline', 'is_scanned', 'is_safe', 'content_type']
    search_fields = ['filename', 'content_id']
    readonly_fields = ['created_at', 'size']
    raw_id_fields = ['email']
    
    fieldsets = (
        ('Datei', {
            'fields': ('email', 'file', 'filename', 'content_type', 'size')
        }),
        ('Inline-Bild', {
            'fields': ('content_id', 'is_inline')
        }),
        ('Sicherheit', {
            'fields': ('is_scanned', 'is_safe')
        }),
        ('Zeitstempel', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailLabel)
class EmailLabelAdmin(ModelAdmin):
    list_display = ['name', 'color', 'is_system', 'owner', 'created_at']
    list_filter = ['is_system']
    search_fields = ['name']
    readonly_fields = ['created_at']
    raw_id_fields = ['owner']
    filter_horizontal = ['conversations']
    
    fieldsets = (
        ('Label', {
            'fields': ('name', 'color', 'is_system', 'owner')
        }),
        ('Konversationen', {
            'fields': ('conversations',)
        }),
        ('Zeitstempel', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailSignature)
class EmailSignatureAdmin(ModelAdmin):
    list_display = ['name', 'user', 'is_default', 'created_at']
    list_filter = ['is_default', 'user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Signatur', {
            'fields': ('user', 'name', 'is_default')
        }),
        ('Inhalt', {
            'fields': ('content_html', 'content_text')
        }),
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuickReply)
class QuickReplyAdmin(ModelAdmin):
    list_display = ['name', 'shortcut', 'is_shared', 'owner', 'usage_count', 'created_at']
    list_filter = ['is_shared']
    search_fields = ['name', 'shortcut', 'subject']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    raw_id_fields = ['owner']
    
    fieldsets = (
        ('Schnellantwort', {
            'fields': ('name', 'shortcut', 'is_shared', 'owner')
        }),
        ('Inhalt', {
            'fields': ('subject', 'content_html', 'content_text')
        }),
        ('Statistiken', {
            'fields': ('usage_count',)
        }),
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
