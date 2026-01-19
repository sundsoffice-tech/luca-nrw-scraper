"""Serializers for Email Templates"""
from rest_framework import serializers
from .models import (
    EmailTemplate, EmailTemplateVersion, EmailSendLog,
    EmailFlow, FlowStep, FlowExecution, FlowStepExecution
)


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


class FlowStepSerializer(serializers.ModelSerializer):
    """Serializer für FlowStep"""
    email_template_name = serializers.CharField(source='email_template.name', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = FlowStep
        fields = [
            'id', 'order', 'name', 'action_type', 'action_type_display',
            'action_config', 'email_template', 'email_template_name', 'is_active'
        ]


class EmailFlowSerializer(serializers.ModelSerializer):
    """Serializer für EmailFlow"""
    steps = FlowStepSerializer(many=True, read_only=True)
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = EmailFlow
        fields = [
            'id', 'name', 'slug', 'description', 'is_active', 'trigger_type', 
            'trigger_type_display', 'trigger_config', 'steps', 'execution_count', 
            'last_executed_at', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'execution_count', 'last_executed_at', 'created_at', 'updated_at']


class EmailFlowCreateSerializer(serializers.ModelSerializer):
    """Serializer für EmailFlow-Erstellung mit nested Steps"""
    steps = FlowStepSerializer(many=True)
    
    class Meta:
        model = EmailFlow
        fields = ['name', 'slug', 'description', 'trigger_type', 'trigger_config', 'is_active', 'steps']
    
    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        flow = EmailFlow.objects.create(**validated_data)
        for step_data in steps_data:
            FlowStep.objects.create(flow=flow, **step_data)
        return flow
    
    def update(self, instance, validated_data):
        steps_data = validated_data.pop('steps', None)
        
        # Update Flow
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update Steps if provided
        if steps_data is not None:
            # Lösche alte Steps
            instance.steps.all().delete()
            # Erstelle neue Steps
            for step_data in steps_data:
                FlowStep.objects.create(flow=instance, **step_data)
        
        return instance


class FlowStepExecutionSerializer(serializers.ModelSerializer):
    """Serializer für FlowStepExecution"""
    step_name = serializers.CharField(source='step.name', read_only=True)
    step_action_type = serializers.CharField(source='step.get_action_type_display', read_only=True)
    
    class Meta:
        model = FlowStepExecution
        fields = [
            'id', 'step', 'step_name', 'step_action_type', 'status',
            'started_at', 'completed_at', 'result_data', 'error_message'
        ]
        read_only_fields = ['id']


class FlowExecutionSerializer(serializers.ModelSerializer):
    """Serializer für FlowExecution"""
    flow_name = serializers.CharField(source='flow.name', read_only=True)
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    step_executions = FlowStepExecutionSerializer(many=True, read_only=True)
    
    class Meta:
        model = FlowExecution
        fields = [
            'id', 'flow', 'flow_name', 'lead', 'lead_name', 'current_step',
            'status', 'started_at', 'completed_at', 'next_execution_at',
            'error_message', 'execution_log', 'step_executions'
        ]
        read_only_fields = ['id', 'started_at']
