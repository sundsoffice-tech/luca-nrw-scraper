"""Tests for pages app"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import LandingPage, PageVersion, PageComponent, PageSubmission, UploadedFile
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
    
    def test_asset_urls_resolve(self):
        """Test that asset management URLs resolve correctly in builder template"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:page-builder', kwargs={'slug': 'test'}))
        self.assertEqual(response.status_code, 200)
        # Verify upload-asset and list-assets URLs are present in the rendered template
        self.assertContains(response, reverse('pages:upload-asset'))
        self.assertContains(response, reverse('pages:list-assets'))


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


class EditorViewTest(TestCase):
    """Test code editor views"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass',
            is_staff=True
        )
        self.page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            status='draft',
            is_uploaded_site=True,
            created_by=self.staff_user
        )
    
    def test_editor_requires_staff(self):
        """Test editor view requires staff access"""
        response = self.client.get(reverse('pages:website-editor', kwargs={'slug': 'test'}))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_editor_view_loads(self):
        """Test editor view loads correctly"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:website-editor', kwargs={'slug': 'test'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'monaco-editor')


class FileVersionTest(TestCase):
    """Test FileVersion model"""
    
    def setUp(self):
        from .models import FileVersion
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.page = LandingPage.objects.create(
            slug='test',
            title='Test Page',
            is_uploaded_site=True,
            created_by=self.user
        )
        self.uploaded_file = UploadedFile.objects.create(
            landing_page=self.page,
            original_filename='test.html',
            relative_path='test.html',
            file_type='text/html',
            file_size=100
        )
    
    def test_file_version_creation(self):
        """Test creating a file version"""
        from .models import FileVersion
        version = FileVersion.objects.create(
            uploaded_file=self.uploaded_file,
            content='<html>Test</html>',
            version=1,
            created_by=self.user,
            note='Initial version'
        )
        self.assertEqual(version.version, 1)
        self.assertEqual(version.note, 'Initial version')


class ProjectTemplateTest(TestCase):
    """Test ProjectTemplate model"""
    
    def test_project_template_creation(self):
        """Test creating a project template"""
        from .models import ProjectTemplate
        template = ProjectTemplate.objects.create(
            name='Test Template',
            slug='test-template',
            category='basic',
            description='A test template',
            files_data={'index.html': '<html></html>'},
            is_active=True
        )
        self.assertEqual(template.slug, 'test-template')
        self.assertTrue(template.is_active)
        self.assertEqual(template.usage_count, 0)
    
    def test_increment_usage(self):
        """Test incrementing template usage count"""
        from .models import ProjectTemplate
        template = ProjectTemplate.objects.create(
            name='Test Template',
            slug='test-template',
            category='basic',
            files_data={}
        )
        initial_count = template.usage_count
        template.increment_usage()
        template.refresh_from_db()
        self.assertEqual(template.usage_count, initial_count + 1)


class ResponsiveEditingTest(TestCase):
    """Test responsive editing functionality"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass',
            is_staff=True
        )
        self.page = LandingPage.objects.create(
            slug='responsive-test',
            title='Responsive Test Page',
            status='draft',
            created_by=self.staff_user
        )
    
    def test_builder_includes_responsive_sections(self):
        """Test that builder includes responsive editing sections"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:page-builder', kwargs={'slug': 'responsive-test'}))
        self.assertEqual(response.status_code, 200)
        
        # Check for responsive sections in the builder
        self.assertContains(response, 'Responsive Typography')
        self.assertContains(response, 'Responsive Spacing')
        self.assertContains(response, 'Responsive Visibility')
    
    def test_builder_includes_device_indicator(self):
        """Test that builder includes device mode indicator"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:page-builder', kwargs={'slug': 'responsive-test'}))
        self.assertEqual(response.status_code, 200)
        
        # Check for device indicator
        self.assertContains(response, 'device-mode-indicator')
        self.assertContains(response, 'Editing: Desktop View')
    
    def test_builder_has_device_buttons(self):
        """Test that builder has device switching buttons"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:page-builder', kwargs={'slug': 'responsive-test'}))
        self.assertEqual(response.status_code, 200)
        
        # Check for device buttons
        self.assertContains(response, 'btn-desktop')
        self.assertContains(response, 'btn-tablet')
        self.assertContains(response, 'btn-mobile')
        self.assertContains(response, 'setDevice')
    
    def test_responsive_properties_configuration(self):
        """Test that responsive properties are properly configured"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:page-builder', kwargs={'slug': 'responsive-test'}))
        self.assertEqual(response.status_code, 200)
        
        # Check for font-size properties for different devices
        self.assertContains(response, 'Font Size (Desktop)')
        self.assertContains(response, 'Font Size (Tablet)')
        self.assertContains(response, 'Font Size (Mobile)')
        
        # Check for spacing properties
        self.assertContains(response, 'Margin (Tablet)')
        self.assertContains(response, 'Margin (Mobile)')
        self.assertContains(response, 'Padding (Tablet)')
        self.assertContains(response, 'Padding (Mobile)')
        
        # Check for visibility properties
        self.assertContains(response, 'Display (Desktop)')
        self.assertContains(response, 'Display (Tablet)')
        self.assertContains(response, 'Display (Mobile)')
    
    def test_media_query_configuration(self):
        """Test that media query configuration is present"""
        self.client.login(username='staffuser', password='staffpass')
        response = self.client.get(reverse('pages:page-builder', kwargs={'slug': 'responsive-test'}))
        self.assertEqual(response.status_code, 200)
        
        # Check for mediaCondition configuration
        self.assertContains(response, "mediaCondition: 'max-width'")
        
        # Check for device configuration with IDs
        self.assertContains(response, "id: 'desktop'")
        self.assertContains(response, "id: 'tablet'")
        self.assertContains(response, "id: 'mobile'")
    
    def test_save_page_with_responsive_css(self):
        """Test saving a page with responsive CSS"""
        import json
        self.client.login(username='staffuser', password='staffpass')
        
        # Sample CSS with media queries
        responsive_css = """
        .hero { font-size: 48px; }
        @media (max-width: 992px) {
            .hero { font-size: 36px; }
        }
        @media (max-width: 480px) {
            .hero { font-size: 24px; }
        }
        """
        
        data = {
            'html': '<div class="hero">Test</div>',
            'css': responsive_css,
            'html_json': {'type': 'div', 'classes': ['hero'], 'content': 'Test'},
            'note': 'Test with responsive CSS'
        }
        
        response = self.client.post(
            reverse('pages:builder-save', kwargs={'slug': 'responsive-test'}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify the CSS was saved
        self.page.refresh_from_db()
        self.assertIn('@media', self.page.css)
        self.assertIn('max-width: 992px', self.page.css)
        self.assertIn('max-width: 480px', self.page.css)

