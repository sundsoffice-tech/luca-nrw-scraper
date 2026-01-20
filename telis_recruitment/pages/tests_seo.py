"""Tests for SEO features"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from pages.models import LandingPage
from pages.services.seo_analyzer import SEOAnalyzer
from pages.services.sitemap_generator import generate_sitemap_xml


class SEOAnalyzerTestCase(TestCase):
    """Tests for SEO Analyzer service"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        self.page = LandingPage.objects.create(
            slug='test-page',
            title='Test Page',
            seo_title='Test SEO Title',
            seo_description='This is a test SEO description that should be a good length for testing purposes.',
            html='<h1>Test Heading</h1><p>Content</p><img src="test.jpg" alt="Test image">',
            status='published',
            created_by=self.user
        )
    
    def test_analyze_returns_score(self):
        """Test that analyzer returns a score"""
        analyzer = SEOAnalyzer(self.page)
        result = analyzer.analyze()
        
        self.assertIn('score', result)
        self.assertIn('grade', result)
        self.assertIsInstance(result['score'], (int, float))
        self.assertIn(result['grade'], ['A', 'B', 'C', 'D', 'F'])
    
    def test_analyze_checks_title_length(self):
        """Test title length validation"""
        # Too short title
        self.page.seo_title = 'Short'
        analyzer = SEOAnalyzer(self.page)
        result = analyzer.analyze()
        
        self.assertTrue(any('title' in msg.lower() and 'short' in msg.lower() 
                          for msg in result['warnings']))
        
        # Too long title
        self.page.seo_title = 'A' * 70
        analyzer = SEOAnalyzer(self.page)
        result = analyzer.analyze()
        
        self.assertTrue(any('title' in msg.lower() and 'long' in msg.lower() 
                          for msg in result['warnings']))
    
    def test_analyze_checks_description(self):
        """Test description validation"""
        # Missing description
        self.page.seo_description = ''
        analyzer = SEOAnalyzer(self.page)
        result = analyzer.analyze()
        
        self.assertTrue(any('description' in msg.lower() 
                          for msg in result['issues']))
    
    def test_analyze_checks_headings(self):
        """Test heading structure validation"""
        # No H1
        self.page.html = '<h2>Heading</h2><p>Content</p>'
        analyzer = SEOAnalyzer(self.page)
        result = analyzer.analyze()
        
        self.assertTrue(any('h1' in msg.lower() 
                          for msg in result['issues']))
        
        # Multiple H1s
        self.page.html = '<h1>First</h1><h1>Second</h1>'
        analyzer = SEOAnalyzer(self.page)
        result = analyzer.analyze()
        
        self.assertTrue(any('h1' in msg.lower() and 'multiple' in msg.lower() 
                          for msg in result['warnings']))
    
    def test_analyze_checks_images(self):
        """Test image alt text validation"""
        # Image without alt
        self.page.html = '<img src="test.jpg">'
        analyzer = SEOAnalyzer(self.page)
        result = analyzer.analyze()
        
        self.assertTrue(any('alt' in msg.lower() 
                          for msg in result['warnings']))


class SitemapGeneratorTestCase(TestCase):
    """Tests for Sitemap Generator service"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Create published pages
        self.page1 = LandingPage.objects.create(
            slug='page-one',
            title='Page One',
            status='published',
            sitemap_priority=0.8,
            sitemap_changefreq='daily',
            created_by=self.user
        )
        
        self.page2 = LandingPage.objects.create(
            slug='page-two',
            title='Page Two',
            status='published',
            sitemap_priority=0.5,
            sitemap_changefreq='weekly',
            created_by=self.user
        )
        
        # Create draft page (should not appear in sitemap)
        self.page3 = LandingPage.objects.create(
            slug='page-draft',
            title='Draft Page',
            status='draft',
            created_by=self.user
        )
    
    def test_sitemap_contains_published_pages(self):
        """Test that sitemap includes published pages"""
        pages = LandingPage.objects.filter(status='published')
        xml = generate_sitemap_xml(pages)
        
        self.assertIn('page-one', xml)
        self.assertIn('page-two', xml)
        self.assertNotIn('page-draft', xml)
    
    def test_sitemap_includes_priority(self):
        """Test that sitemap includes priority values"""
        pages = LandingPage.objects.filter(status='published')
        xml = generate_sitemap_xml(pages)
        
        self.assertIn('<priority>0.8</priority>', xml)
        self.assertIn('<priority>0.5</priority>', xml)
    
    def test_sitemap_includes_changefreq(self):
        """Test that sitemap includes change frequency"""
        pages = LandingPage.objects.filter(status='published')
        xml = generate_sitemap_xml(pages)
        
        self.assertIn('<changefreq>daily</changefreq>', xml)
        self.assertIn('<changefreq>weekly</changefreq>', xml)
    
    def test_sitemap_xml_format(self):
        """Test that sitemap is valid XML"""
        pages = LandingPage.objects.filter(status='published')
        xml = generate_sitemap_xml(pages)
        
        self.assertTrue(xml.startswith('<?xml'))
        self.assertIn('<urlset', xml)
        self.assertIn('</urlset>', xml)


class SEOAPITestCase(TestCase):
    """Tests for SEO API endpoints"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.page = LandingPage.objects.create(
            slug='test-api-page',
            title='Test API Page',
            seo_title='API Test Title',
            seo_description='API test description',
            status='published',
            created_by=self.user
        )
    
    def test_analyze_seo_endpoint(self):
        """Test SEO analysis API endpoint"""
        response = self.client.get(f'/crm/pages/api/{self.page.slug}/seo/analyze/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('analysis', data)
        self.assertIn('score', data['analysis'])
        self.assertIn('grade', data['analysis'])
    
    def test_update_seo_endpoint(self):
        """Test SEO update API endpoint"""
        new_data = {
            'seo_title': 'Updated SEO Title',
            'seo_description': 'Updated SEO description for testing purposes',
            'seo_keywords': 'test, seo, keywords',
            'sitemap_priority': 0.7,
            'sitemap_changefreq': 'monthly'
        }
        
        response = self.client.post(
            f'/crm/pages/api/{self.page.slug}/seo/update/',
            data=json.dumps(new_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify changes
        self.page.refresh_from_db()
        self.assertEqual(self.page.seo_title, 'Updated SEO Title')
        self.assertEqual(self.page.seo_keywords, 'test, seo, keywords')
        self.assertEqual(float(self.page.sitemap_priority), 0.7)
    
    def test_update_slug_endpoint(self):
        """Test slug update API endpoint"""
        new_slug_data = {
            'new_slug': 'updated-slug'
        }
        
        response = self.client.post(
            f'/crm/pages/api/{self.page.slug}/slug/update/',
            data=json.dumps(new_slug_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['new_slug'], 'updated-slug')
        
        # Verify changes
        self.page.refresh_from_db()
        self.assertEqual(self.page.slug, 'updated-slug')
    
    def test_update_slug_duplicate(self):
        """Test slug update with duplicate slug"""
        # Create another page
        LandingPage.objects.create(
            slug='existing-slug',
            title='Existing Page',
            status='draft',
            created_by=self.user
        )
        
        # Try to update to existing slug
        response = self.client.post(
            f'/crm/pages/api/{self.page.slug}/slug/update/',
            data=json.dumps({'new_slug': 'existing-slug'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('already exists', data['error'])


class SitemapViewTestCase(TestCase):
    """Tests for sitemap.xml view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        LandingPage.objects.create(
            slug='sitemap-test',
            title='Sitemap Test',
            status='published',
            created_by=self.user
        )
    
    def test_sitemap_xml_accessible(self):
        """Test that sitemap.xml is accessible"""
        response = self.client.get('/sitemap.xml')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
    
    def test_sitemap_contains_pages(self):
        """Test that sitemap contains published pages"""
        response = self.client.get('/sitemap.xml')
        content = response.content.decode('utf-8')
        
        self.assertIn('sitemap-test', content)
        self.assertIn('<loc>', content)
        self.assertIn('<lastmod>', content)
    
    def test_robots_txt_accessible(self):
        """Test that robots.txt is accessible"""
        response = self.client.get('/robots.txt')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
    
    def test_robots_txt_contains_sitemap(self):
        """Test that robots.txt references sitemap"""
        response = self.client.get('/robots.txt')
        content = response.content.decode('utf-8')
        
        self.assertIn('Sitemap:', content)
        self.assertIn('sitemap.xml', content)
