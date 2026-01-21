"""Tests for fallback static file handler"""
from django.test import TestCase, Client
from django.urls import reverse


class FallbackStaticHandlerTest(TestCase):
    """Test fallback static file handler"""
    
    def setUp(self):
        self.client = Client()
    
    def test_fallback_static_css(self):
        """Test fallback handler returns valid CSS response"""
        response = self.client.get('/src/main.css')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/css')
        self.assertIn('File not found - placeholder', response.content.decode())
    
    def test_fallback_static_js(self):
        """Test fallback handler returns valid JS response"""
        response = self.client.get('/dist/bundle.js')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/javascript')
        self.assertIn('File not found - placeholder', response.content.decode())
    
    def test_fallback_static_map(self):
        """Test fallback handler returns valid source map response"""
        response = self.client.get('/src/main.css.map')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.content.decode(), '{}')
    
    def test_fallback_static_unknown_type(self):
        """Test fallback handler for unknown file type"""
        response = self.client.get('/assets/image.png')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertEqual(response.content.decode(), '')
    
    def test_fallback_static_nested_path(self):
        """Test fallback handler with nested paths"""
        response = self.client.get('/src/components/header.css')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/css')
    
    def test_fallback_static_all_routes(self):
        """Test all configured fallback routes"""
        routes = [
            ('/src/test.css', 'text/css'),
            ('/dist/test.js', 'application/javascript'),
            ('/assets/test.css', 'text/css'),
            ('/css/test.css', 'text/css'),
            ('/js/test.js', 'application/javascript'),
        ]
        
        for path, content_type in routes:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], content_type)


class AssetValidationTest(TestCase):
    """Test asset validation utility"""
    
    def test_validate_asset_references_finds_suspicious_paths(self):
        """Test that validation detects suspicious asset paths"""
        from pages.utils import validate_asset_references
        
        html = '''
        <html>
            <head>
                <link rel="stylesheet" href="/src/main.css">
                <script src="/dist/bundle.js"></script>
            </head>
        </html>
        '''
        
        warnings = validate_asset_references(html)
        self.assertEqual(len(warnings), 2)
        self.assertIn('/src/main.css', warnings[0])
        self.assertIn('/dist/bundle.js', warnings[1])
    
    def test_validate_asset_references_ignores_external(self):
        """Test that validation ignores external URLs"""
        from pages.utils import validate_asset_references
        
        html = '''
        <html>
            <head>
                <link rel="stylesheet" href="https://cdn.example.com/style.css">
                <script src="https://cdn.example.com/script.js"></script>
            </head>
        </html>
        '''
        
        warnings = validate_asset_references(html)
        self.assertEqual(len(warnings), 0)
    
    def test_validate_asset_references_ignores_relative(self):
        """Test that validation ignores normal relative paths"""
        from pages.utils import validate_asset_references
        
        html = '''
        <html>
            <head>
                <link rel="stylesheet" href="/static/style.css">
                <script src="/media/script.js"></script>
            </head>
        </html>
        '''
        
        warnings = validate_asset_references(html)
        self.assertEqual(len(warnings), 0)
    
    def test_validate_asset_references_empty_html(self):
        """Test validation with empty HTML"""
        from pages.utils import validate_asset_references
        
        warnings = validate_asset_references('')
        self.assertEqual(len(warnings), 0)
    
    def test_validate_asset_references_no_assets(self):
        """Test validation with HTML but no asset references"""
        from pages.utils import validate_asset_references
        
        html = '<html><body><h1>Test</h1></body></html>'
        warnings = validate_asset_references(html)
        self.assertEqual(len(warnings), 0)
