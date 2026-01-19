"""Tests for Email Templates"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    EmailTemplate, EmailTemplateVersion, EmailSendLog,
    EmailFlow, FlowStep, FlowExecution, FlowStepExecution
)
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


class EmailFlowModelTest(TestCase):
    """Tests for EmailFlow model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.flow = EmailFlow.objects.create(
            slug='welcome-flow',
            name='Welcome Flow',
            description='Welcome new leads',
            trigger_type='lead_created',
            trigger_config={'immediate': True},
            created_by=self.user
        )
    
    def test_flow_creation(self):
        """Test that a flow can be created"""
        self.assertEqual(self.flow.slug, 'welcome-flow')
        self.assertEqual(self.flow.name, 'Welcome Flow')
        self.assertEqual(self.flow.trigger_type, 'lead_created')
        self.assertFalse(self.flow.is_active)  # Default is False
        self.assertEqual(self.flow.execution_count, 0)
    
    def test_flow_str(self):
        """Test the string representation of a flow"""
        self.assertEqual(str(self.flow), 'Welcome Flow')
    
    def test_flow_defaults(self):
        """Test default values"""
        self.assertFalse(self.flow.is_active)
        self.assertEqual(self.flow.execution_count, 0)
        self.assertIsNone(self.flow.last_executed_at)


class FlowStepModelTest(TestCase):
    """Tests for FlowStep model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.flow = EmailFlow.objects.create(
            slug='test-flow',
            name='Test Flow',
            trigger_type='lead_created',
            created_by=self.user
        )
        self.template = EmailTemplate.objects.create(
            slug='test-template',
            name='Test Template',
            category='custom',
            subject='Test',
            html_content='<p>Test</p>',
            created_by=self.user
        )
        self.step = FlowStep.objects.create(
            flow=self.flow,
            order=0,
            name='Send Welcome Email',
            action_type='send_email',
            email_template=self.template,
            action_config={}
        )
    
    def test_step_creation(self):
        """Test that a step can be created"""
        self.assertEqual(self.step.order, 0)
        self.assertEqual(self.step.action_type, 'send_email')
        self.assertEqual(self.step.name, 'Send Welcome Email')
        self.assertTrue(self.step.is_active)
    
    def test_step_str(self):
        """Test the string representation of a step"""
        expected = f"{self.flow.name} - Step {self.step.order}: {self.step.get_action_type_display()}"
        self.assertEqual(str(self.step), expected)
    
    def test_step_ordering(self):
        """Test that steps are ordered correctly"""
        step2 = FlowStep.objects.create(
            flow=self.flow,
            order=1,
            action_type='wait',
            action_config={'duration': '1 day'}
        )
        steps = list(self.flow.steps.all())
        self.assertEqual(steps[0], self.step)
        self.assertEqual(steps[1], step2)


class FlowExecutionModelTest(TestCase):
    """Tests for FlowExecution model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.flow = EmailFlow.objects.create(
            slug='test-flow',
            name='Test Flow',
            trigger_type='lead_created',
            created_by=self.user
        )
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com'
        )
        self.execution = FlowExecution.objects.create(
            flow=self.flow,
            lead=self.lead,
            status='pending'
        )
    
    def test_execution_creation(self):
        """Test that an execution can be created"""
        self.assertEqual(self.execution.status, 'pending')
        self.assertEqual(self.execution.flow, self.flow)
        self.assertEqual(self.execution.lead, self.lead)
        self.assertIsNone(self.execution.current_step)
    
    def test_execution_str(self):
        """Test the string representation of an execution"""
        expected = f"{self.flow.name} - {self.lead.name} ({self.execution.get_status_display()})"
        self.assertEqual(str(self.execution), expected)


class FlowStepExecutionModelTest(TestCase):
    """Tests for FlowStepExecution model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.flow = EmailFlow.objects.create(
            slug='test-flow',
            name='Test Flow',
            trigger_type='lead_created',
            created_by=self.user
        )
        self.lead = Lead.objects.create(
            name='Test Lead',
            email='test@example.com'
        )
        self.step = FlowStep.objects.create(
            flow=self.flow,
            order=0,
            action_type='send_email',
            action_config={}
        )
        self.execution = FlowExecution.objects.create(
            flow=self.flow,
            lead=self.lead
        )
        self.step_execution = FlowStepExecution.objects.create(
            execution=self.execution,
            step=self.step,
            status='completed',
            result_data={'email_sent': True}
        )
    
    def test_step_execution_creation(self):
        """Test that a step execution can be created"""
        self.assertEqual(self.step_execution.status, 'completed')
        self.assertEqual(self.step_execution.result_data, {'email_sent': True})


class EmailFlowAPITest(APITestCase):
    """Tests for EmailFlow API"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.template = EmailTemplate.objects.create(
            slug='test-template',
            name='Test Template',
            category='custom',
            subject='Test',
            html_content='<p>Test</p>',
            created_by=self.user
        )
        
        self.flow = EmailFlow.objects.create(
            slug='test-flow',
            name='Test Flow',
            description='Test flow description',
            trigger_type='lead_created',
            trigger_config={},
            created_by=self.user
        )
        
        FlowStep.objects.create(
            flow=self.flow,
            order=0,
            action_type='send_email',
            email_template=self.template,
            action_config={}
        )
    
    def test_list_flows(self):
        """Test listing flows"""
        url = '/api/email-templates/flows/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_flow(self):
        """Test retrieving a single flow"""
        url = f'/api/email-templates/flows/{self.flow.slug}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], 'test-flow')
        self.assertEqual(len(response.data['steps']), 1)
    
    def test_create_flow(self):
        """Test creating a new flow"""
        url = '/api/email-templates/flows/'
        data = {
            'name': 'New Flow',
            'slug': 'new-flow',
            'description': 'New test flow',
            'trigger_type': 'lead_created',
            'trigger_config': {},
            'is_active': False,
            'steps': [
                {
                    'order': 0,
                    'action_type': 'send_email',
                    'email_template': self.template.id,
                    'action_config': {},
                    'is_active': True
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Flow')
        
        # Verify flow was created with steps
        flow = EmailFlow.objects.get(slug='new-flow')
        self.assertEqual(flow.steps.count(), 1)
    
    def test_activate_flow(self):
        """Test activating a flow"""
        url = f'/api/email-templates/flows/{self.flow.slug}/activate/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'activated')
        
        # Verify flow is active
        self.flow.refresh_from_db()
        self.assertTrue(self.flow.is_active)
    
    def test_deactivate_flow(self):
        """Test deactivating a flow"""
        self.flow.is_active = True
        self.flow.save()
        
        url = f'/api/email-templates/flows/{self.flow.slug}/deactivate/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'deactivated')
        
        # Verify flow is inactive
        self.flow.refresh_from_db()
        self.assertFalse(self.flow.is_active)
    
    def test_duplicate_flow(self):
        """Test duplicating a flow"""
        url = f'/api/email-templates/flows/{self.flow.slug}/duplicate/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'duplicated')
        
        # Verify duplicate was created
        self.assertEqual(EmailFlow.objects.count(), 2)
        duplicate = EmailFlow.objects.get(slug='test-flow-copy')
        self.assertEqual(duplicate.name, 'Test Flow (Kopie)')
        self.assertFalse(duplicate.is_active)
        self.assertEqual(duplicate.steps.count(), 1)
    
    def test_flow_statistics(self):
        """Test flow statistics endpoint"""
        url = f'/api/email-templates/flows/{self.flow.slug}/statistics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_executions', response.data)
        self.assertIn('status_counts', response.data)
        self.assertIn('steps_count', response.data)
    
    def test_authentication_required_for_flows(self):
        """Test that authentication is required"""
        self.client.force_authenticate(user=None)
        url = '/api/email-templates/flows/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
