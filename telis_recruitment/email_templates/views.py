"""Views for Email Templates"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json

from .models import (
    EmailTemplate, EmailTemplateVersion, EmailSendLog,
    EmailFlow, FlowStep, FlowExecution
)
from .serializers import (
    EmailTemplateSerializer, 
    EmailTemplateVersionSerializer, 
    EmailSendLogSerializer,
    EmailFlowSerializer,
    EmailFlowCreateSerializer,
    FlowExecutionSerializer
)
from .services.renderer import render_email_template, get_sample_variables, get_template_variables
from .services.ai_generator import generate_email_template, improve_email_text, generate_subject_lines


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet für EmailTemplate API"""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    def perform_create(self, serializer):
        """Setze created_by beim Erstellen"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def preview(self, request, slug=None):
        """
        Vorschau mit Test-Daten rendern
        POST /api/email-templates/<slug>/preview/
        Body: {"variables": {"name": "Max", ...}} (optional)
        """
        template = self.get_object()
        
        # Verwende mitgelieferte oder Standard-Variablen
        variables = request.data.get('variables', get_sample_variables())
        
        try:
            rendered = render_email_template(template, variables)
            return Response({
                'success': True,
                'rendered': rendered,
                'variables_used': get_template_variables(template)
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, slug=None):
        """
        Test-Email senden
        POST /api/email-templates/<slug>/send-test/
        Body: {"to_email": "test@example.com", "variables": {...}}
        """
        template = self.get_object()
        
        to_email = request.data.get('to_email')
        if not to_email:
            return Response({
                'success': False,
                'error': 'to_email erforderlich'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        variables = request.data.get('variables', get_sample_variables())
        
        try:
            rendered = render_email_template(template, variables)
            
            # Hier würde der tatsächliche Email-Versand erfolgen (z.B. via Brevo)
            # Für Test-Zwecke loggen wir nur
            EmailSendLog.objects.create(
                template=template,
                to_email=to_email,
                subject_rendered=rendered['subject'],
                status='sent'
            )
            
            # Update Template
            template.send_count += 1
            template.last_sent_at = timezone.now()
            template.save()
            
            return Response({
                'success': True,
                'message': f'Test-Email würde gesendet an {to_email}',
                'rendered': rendered
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def ai_generate(self, request):
        """
        KI-Generierung eines Templates
        POST /api/email-templates/ai-generate/
        Body: {
            "category": "welcome",
            "context": "Neue Leads begrüßen",
            "tone": "professional",
            "language": "de"
        }
        """
        try:
            category = request.data.get('category', 'custom')
            context = request.data.get('context', '')
            tone = request.data.get('tone', 'professional')
            language = request.data.get('language', 'de')
            
            if not context:
                return Response({
                    'success': False,
                    'error': 'context erforderlich'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = generate_email_template(category, context, tone, language)
            
            return Response({
                'success': True,
                'template': result
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def ai_improve(self, request):
        """
        Text-Verbesserung mit KI
        POST /api/email-templates/ai-improve/
        Body: {
            "text": "Zu verbessernder Text",
            "improvement_type": "clarity"
        }
        """
        try:
            text = request.data.get('text', '')
            improvement_type = request.data.get('improvement_type', 'clarity')
            
            if not text:
                return Response({
                    'success': False,
                    'error': 'text erforderlich'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            improved = improve_email_text(text, improvement_type)
            
            return Response({
                'success': True,
                'improved_text': improved
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def ai_subjects(self, request):
        """
        Betreffzeilen generieren
        POST /api/email-templates/ai-subjects/
        Body: {
            "content": "Email-Inhalt",
            "count": 5
        }
        """
        try:
            content = request.data.get('content', '')
            count = request.data.get('count', 5)
            
            if not content:
                return Response({
                    'success': False,
                    'error': 'content erforderlich'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            subjects = generate_subject_lines(content, count)
            
            return Response({
                'success': True,
                'subjects': subjects
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailTemplateVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet für EmailTemplateVersion API (read-only)"""
    queryset = EmailTemplateVersion.objects.all()
    serializer_class = EmailTemplateVersionSerializer
    permission_classes = [IsAuthenticated]


class EmailSendLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet für EmailSendLog API (read-only)"""
    queryset = EmailSendLog.objects.all()
    serializer_class = EmailSendLogSerializer
    permission_classes = [IsAuthenticated]


class EmailFlowViewSet(viewsets.ModelViewSet):
    """ViewSet für EmailFlow API"""
    queryset = EmailFlow.objects.all()
    serializer_class = EmailFlowSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EmailFlowCreateSerializer
        return EmailFlowSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, slug=None):
        """Flow aktivieren"""
        flow = self.get_object()
        flow.is_active = True
        flow.save()
        return Response({
            'status': 'activated',
            'message': f'Flow "{flow.name}" wurde aktiviert.'
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, slug=None):
        """Flow deaktivieren"""
        flow = self.get_object()
        flow.is_active = False
        flow.save()
        return Response({
            'status': 'deactivated',
            'message': f'Flow "{flow.name}" wurde deaktiviert.'
        })
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, slug=None):
        """Flow duplizieren"""
        flow = self.get_object()
        
        # Speichere Steps
        steps = list(flow.steps.all().values(
            'order', 'name', 'action_type', 'action_config', 
            'email_template_id', 'is_active'
        ))
        
        # Dupliziere Flow
        flow.pk = None
        
        # Generate unique slug
        base_slug = f"{slug}-copy"
        new_slug = base_slug
        counter = 1
        while EmailFlow.objects.filter(slug=new_slug).exists():
            new_slug = f"{base_slug}-{counter}"
            counter += 1
        
        flow.slug = new_slug
        flow.name = f"{flow.name} (Kopie)"
        flow.execution_count = 0
        flow.last_executed_at = None
        flow.is_active = False
        flow.created_by = request.user
        flow.save()
        
        # Dupliziere Steps
        for step_data in steps:
            FlowStep.objects.create(flow=flow, **step_data)
        
        serializer = self.get_serializer(flow)
        return Response({
            'status': 'duplicated',
            'message': f'Flow "{flow.name}" wurde dupliziert.',
            'flow': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, slug=None):
        """Flow-Statistiken abrufen"""
        flow = self.get_object()
        
        # Zähle Executions nach Status
        executions = flow.executions.all()
        stats = {
            'total_executions': flow.execution_count,
            'last_executed_at': flow.last_executed_at,
            'status_counts': {
                'pending': executions.filter(status='pending').count(),
                'running': executions.filter(status='running').count(),
                'waiting': executions.filter(status='waiting').count(),
                'completed': executions.filter(status='completed').count(),
                'paused': executions.filter(status='paused').count(),
                'failed': executions.filter(status='failed').count(),
                'cancelled': executions.filter(status='cancelled').count(),
            },
            'steps_count': flow.steps.count(),
            'active_steps_count': flow.steps.filter(is_active=True).count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def executions(self, request, slug=None):
        """Flow-Ausführungen abrufen"""
        flow = self.get_object()
        executions = flow.executions.all()[:20]  # Letzte 20
        serializer = FlowExecutionSerializer(executions, many=True)
        return Response(serializer.data)


# Web Interface Views
@login_required
def template_list(request):
    """Liste aller Templates"""
    templates = EmailTemplate.objects.all()
    return render(request, 'email_templates/template_list.html', {
        'templates': templates
    })


@login_required
def template_editor(request, slug):
    """Template Editor"""
    template = get_object_or_404(EmailTemplate, slug=slug)
    return render(request, 'email_templates/template_editor.html', {
        'template': template,
        'sample_variables': get_sample_variables()
    })


@login_required
def template_preview(request, slug):
    """Template Vorschau"""
    template = get_object_or_404(EmailTemplate, slug=slug)
    
    # Verwende Sample-Variablen oder aus Query-Parameter
    variables = get_sample_variables()
    
    try:
        rendered = render_email_template(template, variables)
        return render(request, 'email_templates/template_preview.html', {
            'template': template,
            'rendered': rendered,
            'variables': variables
        })
    except Exception as e:
        return render(request, 'email_templates/template_preview.html', {
            'template': template,
            'error': str(e)
        })


@login_required
def flow_list(request):
    """Liste aller Flows"""
    flows = EmailFlow.objects.all()
    
    # Filter nach Status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        flows = flows.filter(is_active=True)
    elif status_filter == 'inactive':
        flows = flows.filter(is_active=False)
    
    # Filter nach Trigger-Typ
    trigger_filter = request.GET.get('trigger', '')
    if trigger_filter:
        flows = flows.filter(trigger_type=trigger_filter)
    
    # Für Template-Context
    trigger_types = EmailFlow.TRIGGER_TYPES
    
    return render(request, 'email_templates/flow_list.html', {
        'flows': flows,
        'trigger_types': trigger_types,
        'status_filter': status_filter,
        'trigger_filter': trigger_filter
    })


@login_required
def flow_builder(request, slug=None):
    """Flow-Builder (Neu oder Bearbeiten)"""
    flow = None
    if slug:
        flow = get_object_or_404(EmailFlow, slug=slug)
    
    # Hole verfügbare Templates
    email_templates = EmailTemplate.objects.filter(is_active=True)
    
    # Trigger-Typen
    trigger_types = EmailFlow.TRIGGER_TYPES
    action_types = FlowStep.ACTION_TYPES
    
    return render(request, 'email_templates/flow_builder.html', {
        'flow': flow,
        'email_templates': email_templates,
        'trigger_types': trigger_types,
        'action_types': action_types,
    })


@login_required
def flow_detail(request, slug):
    """Flow-Details"""
    flow = get_object_or_404(EmailFlow, slug=slug)
    
    # Hole letzte Executions
    recent_executions = flow.executions.all()[:10]
    
    return render(request, 'email_templates/flow_detail.html', {
        'flow': flow,
        'recent_executions': recent_executions
    })
