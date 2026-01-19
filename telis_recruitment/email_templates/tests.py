"""Tests for Email Templates"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import EmailTemplate, EmailTemplateVersion, EmailSendLog
from .services.renderer import (
    render_template, 
    render_email_template, 
    extract_variables_from_template,
    get_sample_variables
)
from leads.models import Lead


class EmailTemplateModelTest(TestCase):
    """Tests for EmailTemplate model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.template = EmailTemplate.objects.create(
            slug='test-template',
            name='Test Template',
            category='custom',
            subject='Hello {name}!',
            html_content='<p>Welcome {name} from {company}</p>',
            text_content='Welcome {name} from {company}',
            available_variables=['name', 'company'],
            created_by=self.user
        )
    
    def test_template_creation(self):
        """Test that a template can be created"""
        self.assertEqual(self.template.slug, 'test-template')
        self.assertEqual(self.template.name, 'Test Template')
        self.assertEqual(self.template.category, 'custom')
        self.assertTrue(self.template.is_active)
        self.assertEqual(self.template.send_count, 0)
    
    def test_template_str(self):
        """Test the string representation of a template"""
        expected = f"{self.template.name} ({self.template.get_category_display()})"
        self.assertEqual(str(self.template), expected)
    
    def test_template_defaults(self):
        """Test default values"""
        self.assertFalse(self.template.ai_generated)
        self.assertEqual(self.template.send_count, 0)
        self.assertIsNone(self.template.last_sent_at)
        self.assertTrue(self.template.is_active)


class EmailTemplateVersionModelTest(TestCase):
    """Tests for EmailTemplateVersion model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.template = EmailTemplate.objects.create(
            slug='test-template',
            name='Test Template',
            category='custom',
            subject='Original',
            html_content='<p>Original</p>',
            created_by=self.user
        )
        self.version = EmailTemplateVersion.objects.create(
            template=self.template,
            version=1,
            subject='Version 1',
            html_content='<p>Version 1</p>',
            created_by=self.user,
            note='Initial version'
        )
    
    def test_version_creation(self):
        """Test that a version can be created"""
        self.assertEqual(self.version.version, 1)
        self.assertEqual(self.version.subject, 'Version 1')
        self.assertEqual(self.version.note, 'Initial version')
    
    def test_version_str(self):
        """Test the string representation of a version"""
        expected = f"{self.template.name} v{self.version.version}"
        self.assertEqual(str(self.version), expected)


class EmailSendLogModelTest(TestCase):
    """Tests for EmailSendLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.template = EmailTemplate.objects.create(
            slug='test-template',
            name='Test Template',
            category='custom',
            subject='Hello',
            html_content='<p>Content</p>',
            created_by=self.user
        )
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com'
        )
        self.log = EmailSendLog.objects.create(
            template=self.template,
            lead=self.lead,
            to_email='test@example.com',
            subject_rendered='Hello Test Lead',
            status='sent'
        )
    
    def test_log_creation(self):
        """Test that a log can be created"""
        self.assertEqual(self.log.to_email, 'test@example.com')
        self.assertEqual(self.log.status, 'sent')
    
    def test_log_str(self):
        """Test the string representation of a log"""
        expected = f"{self.log.to_email} - {self.log.get_status_display()}"
        self.assertEqual(str(self.log), expected)


class RendererServiceTest(TestCase):
    """Tests for renderer service"""
    
    def test_render_template(self):
        """Test basic template rendering"""
        template_str = "Hello {name}!"
        variables = {'name': 'Max'}
        result = render_template(template_str, variables)
        self.assertEqual(result, "Hello Max!")
    
    def test_render_template_missing_variable(self):
        """Test rendering with missing variable"""
        template_str = "Hello {name}!"
        variables = {}
        result = render_template(template_str, variables)
        # Should return original template if variable missing
        self.assertEqual(result, "Hello {name}!")
    
    def test_extract_variables(self):
        """Test variable extraction"""
        template_str = "Hello {name} from {company}!"
        variables = extract_variables_from_template(template_str)
        self.assertIn('name', variables)
        self.assertIn('company', variables)
        self.assertEqual(len(variables), 2)
    
    def test_render_email_template(self):
        """Test full email template rendering"""
        user = User.objects.create_user(username='testuser', password='testpass')
        template = EmailTemplate.objects.create(
            slug='test',
            name='Test',
            category='custom',
            subject='Hello {name}!',
            html_content='<p>Welcome {name}</p>',
            text_content='Welcome {name}',
            created_by=user
        )
        
        variables = {'name': 'Max'}
        result = render_email_template(template, variables)
        
        self.assertEqual(result['subject'], 'Hello Max!')
        self.assertEqual(result['html_content'], '<p>Welcome Max</p>')
        self.assertEqual(result['text_content'], 'Welcome Max')
    
    def test_get_sample_variables(self):
        """Test sample variables"""
        samples = get_sample_variables()
        self.assertIn('name', samples)
        self.assertIn('email', samples)
        self.assertIn('company', samples)


class EmailTemplateAPITest(APITestCase):
    """Tests for EmailTemplate API"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.template = EmailTemplate.objects.create(
            slug='test-template',
            name='Test Template',
            category='custom',
            subject='Hello {name}!',
            html_content='<p>Welcome {name}</p>',
            text_content='Welcome {name}',
            available_variables=['name'],
            created_by=self.user
        )
    
    def test_list_templates(self):
        """Test listing templates"""
        url = '/api/email-templates/templates/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # At least our test template should be present (plus default templates from migration)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_retrieve_template(self):
        """Test retrieving a single template"""
        url = f'/api/email-templates/templates/{self.template.slug}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], 'test-template')
    
    def test_preview_template(self):
        """Test template preview"""
        url = f'/api/email-templates/templates/{self.template.slug}/preview/'
        data = {'variables': {'name': 'Max'}}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['rendered']['subject'], 'Hello Max!')
    
    def test_authentication_required(self):
        """Test that authentication is required"""
        self.client.force_authenticate(user=None)
        url = '/api/email-templates/templates/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
