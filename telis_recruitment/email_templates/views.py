"""Views for Email Templates"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json

from .models import EmailTemplate, EmailTemplateVersion, EmailSendLog
from .serializers import (
    EmailTemplateSerializer, 
    EmailTemplateVersionSerializer, 
    EmailSendLogSerializer
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
