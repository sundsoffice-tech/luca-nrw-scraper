"""
Test to verify that the scraper URL fix works correctly.
This test ensures that the scraper_control:dashboard URL can be resolved correctly.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.template import Context, Template


class ScraperURLFixTest(TestCase):
    """Test that the scraper URL is correctly resolved"""
    
    def setUp(self):
        """Set up test user and client"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        
        # Create Admin group and add user to it
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        self.admin_user.groups.add(admin_group)
        
        self.client = Client()
    
    def test_scraper_control_url_exists(self):
        """Test that the scraper_control:dashboard URL can be resolved"""
        # This should not raise NoReverseMatch
        url = reverse('scraper_control:dashboard')
        
        # The URL should be /crm/scraper/
        self.assertEqual(url, '/crm/scraper/')
    
    def test_template_url_tag_resolves(self):
        """Test that the {% url 'scraper_control:dashboard' %} tag resolves correctly in a template"""
        # Create a simple template with the URL tag
        template_string = "{% url 'scraper_control:dashboard' %}"
        template = Template(template_string)
        
        # Render the template
        rendered = template.render(Context({}))
        
        # Should render to /crm/scraper/
        self.assertEqual(rendered, '/crm/scraper/')
    
    def test_old_crm_scraper_url_does_not_exist(self):
        """Test that the old 'crm-scraper' URL name no longer exists"""
        from django.urls.exceptions import NoReverseMatch
        
        # Attempting to reverse the old URL should raise NoReverseMatch
        with self.assertRaises(NoReverseMatch):
            reverse('crm-scraper')

