"""Serializers for Email Templates"""
from rest_framework import serializers
from .models import EmailTemplate, EmailTemplateVersion, EmailSendLog


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer für EmailTemplate"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'slug', 'name', 'category',
            'subject', 'html_content', 'text_content',
            'available_variables', 'ai_generated', 'ai_prompt_used',
            'brevo_template_id', 'sync_to_brevo',
            'is_active', 'send_count', 'last_sent_at',
            'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'send_count', 'last_sent_at', 'created_at', 'updated_at']


class EmailTemplateVersionSerializer(serializers.ModelSerializer):
    """Serializer für EmailTemplateVersion"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = EmailTemplateVersion
        fields = [
            'id', 'template', 'version',
            'subject', 'html_content', 'text_content',
            'created_by', 'created_by_username',
            'created_at', 'note'
        ]
        read_only_fields = ['id', 'created_at']


class EmailSendLogSerializer(serializers.ModelSerializer):
    """Serializer für EmailSendLog"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    
    class Meta:
        model = EmailSendLog
        fields = [
            'id', 'template', 'template_name', 'lead', 'lead_name',
            'to_email', 'subject_rendered', 'status',
            'brevo_message_id', 'sent_at', 'opened_at', 'clicked_at'
        ]
        read_only_fields = ['id', 'sent_at']
