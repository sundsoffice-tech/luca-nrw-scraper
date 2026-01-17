from rest_framework import serializers
from .models import Lead, CallLog, EmailLog


class CallLogSerializer(serializers.ModelSerializer):
    outcome_display = serializers.CharField(source='get_outcome_display', read_only=True)
    
    class Meta:
        model = CallLog
        fields = '__all__'
        read_only_fields = ['called_at']


class EmailLogSerializer(serializers.ModelSerializer):
    email_type_display = serializers.CharField(source='get_email_type_display', read_only=True)
    
    class Meta:
        model = EmailLog
        fields = '__all__'
        read_only_fields = ['sent_at']


class LeadSerializer(serializers.ModelSerializer):
    call_logs = CallLogSerializer(many=True, read_only=True)
    email_logs = EmailLogSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    lead_type_display = serializers.CharField(source='get_lead_type_display', read_only=True)
    has_contact_info = serializers.BooleanField(read_only=True)
    is_hot_lead = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'call_count', 'last_called_at', 
                          'email_sent_count', 'email_opens', 'email_clicks', 'last_email_at']


class LeadListSerializer(serializers.ModelSerializer):
    """Kompakte Version für Listen"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = Lead
        fields = ['id', 'name', 'email', 'telefon', 'status', 'status_display', 
                 'quality_score', 'source', 'source_display', 'lead_type',
                 'call_count', 'interest_level', 'created_at']
