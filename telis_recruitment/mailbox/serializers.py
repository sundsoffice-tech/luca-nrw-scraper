"""
Serializers for Mailbox app
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    EmailAccount,
    EmailConversation,
    Email,
    EmailAttachment,
    EmailLabel,
    EmailSignature,
    QuickReply
)


class EmailAccountSerializer(serializers.ModelSerializer):
    """Serializer for EmailAccount"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    shared_with_usernames = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailAccount
        fields = [
            'id', 'name', 'email_address', 'account_type',
            'imap_host', 'imap_port', 'imap_username', 'imap_use_ssl',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_use_tls',
            'is_active', 'is_default', 'sync_enabled', 'sync_interval_minutes',
            'last_sync_at', 'last_sync_error',
            'owner', 'owner_username', 'shared_with', 'shared_with_usernames',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync_at', 'last_sync_error', 'created_at', 'updated_at']
        # Don't expose encrypted passwords in API
        extra_kwargs = {
            'imap_password_encrypted': {'write_only': True},
            'smtp_password_encrypted': {'write_only': True},
            'brevo_api_key_encrypted': {'write_only': True},
        }
    
    def get_shared_with_usernames(self, obj):
        return [user.username for user in obj.shared_with.all()]


class EmailConversationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for conversation lists"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    labels = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailConversation
        fields = [
            'id', 'subject', 'contact_email', 'contact_name',
            'account', 'account_name', 'lead', 'lead_name',
            'status', 'assigned_to', 'assigned_to_username',
            'is_starred', 'is_archived', 'is_read',
            'message_count', 'unread_count',
            'last_message_at', 'labels',
            'created_at'
        ]
        read_only_fields = ['id', 'message_count', 'unread_count', 'last_message_at', 'created_at']
    
    def get_labels(self, obj):
        return [{'id': label.id, 'name': label.name, 'color': label.color} for label in obj.labels.all()]


class EmailConversationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for conversation details"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    labels = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailConversation
        fields = [
            'id', 'subject', 'subject_normalized', 'contact_email', 'contact_name',
            'account', 'account_name', 'lead', 'lead_name',
            'status', 'assigned_to', 'assigned_to_username',
            'is_starred', 'is_archived', 'is_read',
            'message_count', 'unread_count',
            'last_message_at', 'last_inbound_at', 'last_outbound_at',
            'labels', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'subject_normalized', 'message_count', 'unread_count',
            'last_message_at', 'last_inbound_at', 'last_outbound_at',
            'created_at', 'updated_at'
        ]
    
    def get_labels(self, obj):
        return [{'id': label.id, 'name': label.name, 'color': label.color} for label in obj.labels.all()]


class EmailAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for EmailAttachment"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailAttachment
        fields = [
            'id', 'filename', 'content_type', 'size',
            'content_id', 'is_inline', 'is_scanned', 'is_safe',
            'file_url', 'created_at'
        ]
        read_only_fields = ['id', 'size', 'is_scanned', 'is_safe', 'created_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class EmailListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for email lists"""
    conversation_subject = serializers.CharField(source='conversation.subject', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    template_name = serializers.CharField(source='template_used.name', read_only=True)
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Email
        fields = [
            'id', 'conversation', 'conversation_subject',
            'account', 'account_name',
            'direction', 'message_id',
            'from_email', 'from_name', 'subject', 'snippet',
            'status', 'is_read', 'attachment_count',
            'sent_at', 'received_at', 'opened_at', 'opened_count',
            'template_used', 'template_name',
            'created_at'
        ]
        read_only_fields = ['id', 'message_id', 'status', 'created_at']
    
    def get_attachment_count(self, obj):
        return obj.attachments.count() if hasattr(obj, 'attachments') else 0


class EmailDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for email details"""
    conversation_subject = serializers.CharField(source='conversation.subject', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    template_name = serializers.CharField(source='template_used.name', read_only=True)
    attachments = EmailAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Email
        fields = [
            'id', 'conversation', 'conversation_subject',
            'account', 'account_name',
            'direction', 'message_id', 'in_reply_to', 'references',
            'from_email', 'from_name',
            'to_emails', 'cc_emails', 'bcc_emails', 'reply_to_email',
            'subject', 'body_text', 'body_html', 'snippet',
            'template_used', 'template_name',
            'status', 'status_detail', 'brevo_message_id',
            'sent_at', 'delivered_at', 'opened_at', 'opened_count',
            'clicked_at', 'clicked_links',
            'received_at', 'is_read', 'read_at',
            'imap_uid', 'imap_folder', 'scheduled_for',
            'attachments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'message_id', 'status', 'status_detail',
            'brevo_message_id', 'sent_at', 'delivered_at',
            'opened_at', 'opened_count', 'clicked_at', 'clicked_links',
            'received_at', 'read_at', 'imap_uid', 'imap_folder',
            'created_at', 'updated_at'
        ]


class EmailLabelSerializer(serializers.ModelSerializer):
    """Serializer for EmailLabel"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    conversation_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailLabel
        fields = [
            'id', 'name', 'color', 'is_system',
            'owner', 'owner_username', 'conversation_count',
            'created_at'
        ]
        read_only_fields = ['id', 'is_system', 'created_at']
    
    def get_conversation_count(self, obj):
        return obj.conversations.count()


class EmailSignatureSerializer(serializers.ModelSerializer):
    """Serializer for EmailSignature"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = EmailSignature
        fields = [
            'id', 'user', 'user_username', 'name',
            'content_html', 'content_text', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuickReplySerializer(serializers.ModelSerializer):
    """Serializer for QuickReply"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = QuickReply
        fields = [
            'id', 'name', 'shortcut', 'subject',
            'content_html', 'content_text',
            'is_shared', 'owner', 'owner_username',
            'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


# Serializers for creating/sending emails

class EmailComposeSerializer(serializers.Serializer):
    """Serializer for composing/sending emails"""
    account_id = serializers.IntegerField()
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1
    )
    cc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    bcc_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    subject = serializers.CharField(max_length=500)
    body_html = serializers.CharField(allow_blank=True, required=False)
    body_text = serializers.CharField(allow_blank=True, required=False)
    template_id = serializers.IntegerField(required=False, allow_null=True)
    signature_id = serializers.IntegerField(required=False, allow_null=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    in_reply_to = serializers.CharField(required=False, allow_blank=True)
    scheduled_for = serializers.DateTimeField(required=False, allow_null=True)
    attachment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )


class EmailReplySerializer(serializers.Serializer):
    """Serializer for replying to emails"""
    body_html = serializers.CharField(allow_blank=True, required=False)
    body_text = serializers.CharField(allow_blank=True, required=False)
    include_quoted = serializers.BooleanField(default=True)
    signature_id = serializers.IntegerField(required=False, allow_null=True)
    attachment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
