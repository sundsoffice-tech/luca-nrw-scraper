"""Tests for pages app"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import LandingPage, PageVersion, PageComponent, PageSubmission
from leads.models import Lead


class LandingPageModelTest(TestCase):
    """Test LandingPage model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_landing_page_creation(self):
        """Test creating a landing page"""
        page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            status='draft',
            created_by=self.user
        )
        self.assertEqual(page.slug, 'test')
        self.assertEqual(page.status, 'draft')
        self.assertIsNone(page.published_at)
    
    def test_landing_page_publish(self):
        """Test publishing a landing page"""
        page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            status='draft',
            created_by=self.user
        )
        page.status = 'published'
        page.save()
        self.assertIsNotNone(page.published_at)
    
    def test_landing_page_urls(self):
        """Test URL generation"""
        page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            status='published',
            created_by=self.user
        )
        self.assertEqual(page.get_absolute_url(), '/p/test/')
        self.assertEqual(page.get_builder_url(), '/crm/pages/builder/test/')


class PageComponentModelTest(TestCase):
    """Test PageComponent model"""
    
    def test_component_creation(self):
        """Test creating a page component"""
        component = PageComponent.objects.create(
            name='Test Component',
            slug='test-component',
            category='hero',
            html_snippet='<div>Test</div>',
            is_active=True
        )
        self.assertEqual(component.slug, 'test-component')
        self.assertTrue(component.is_active)


class PublicPageViewTest(TestCase):
    """Test public page rendering"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            status='published',
            html='<h1>Test</h1>',
            css='h1 { color: red; }',
            created_by=self.user
        )
    
    def test_public_page_render(self):
        """Test rendering a public page"""
        response = self.client.get(reverse('pages_public:page-public', kwargs={'slug': 'test'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1>Test</h1>')
    
    def test_draft_page_not_accessible(self):
        """Test that draft pages are not accessible"""
        draft_page = LandingPage.objects.create(
            slug='draft',
            title='Draft Page',
            status='draft',
            created_by=self.user
        )
        response = self.client.get(reverse('pages_public:page-public', kwargs={'slug': 'draft'}))
        self.assertEqual(response.status_code, 404)


class BuilderViewTest(TestCase):
    """Test builder views (staff only)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass',
            is_staff=True
        )
        self.page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            status='draft',
            created_by=self.staff_user
        )
    
    def test_builder_requires_staff(self):
        """Test builder views require staff access"""
        # Not logged in
        response = self.client.get(reverse('pages:builder-list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Regular user
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('pages:builder-list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Staff user
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:builder-list'))
        self.assertEqual(response.status_code, 200)
    
    def test_builder_view_loads(self):
        """Test builder view loads correctly"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:page-builder', kwargs={'slug': 'test'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'grapesjs')


class FormSubmissionTest(TestCase):
    """Test form submission"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            status='published',
            created_by=self.user
        )
    
    def test_form_submission(self):
        """Test submitting a form"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+49123456789'
        }
        response = self.client.post(
            reverse('pages_public:form-submit', kwargs={'slug': 'test'}),
            data=data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check submission was created
        submission = PageSubmission.objects.first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.landing_page, self.page)
        self.assertEqual(submission.data['email'], 'test@example.com')
    
    def test_form_submission_creates_lead(self):
        """Test form submission creates a lead"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+49123456789'
        }
        response = self.client.post(
            reverse('pages_public:form-submit', kwargs={'slug': 'test'}),
            data=data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check lead was created
        lead = Lead.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, 'Test User')
        self.assertEqual(lead.source, Lead.Source.LANDING_PAGE)
