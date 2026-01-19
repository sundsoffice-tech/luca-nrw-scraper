"""
Test navigation improvements between CRM and Admin interfaces.
Tests the changes made to templates/crm/base.html and templates/admin/base_site.html
"""
import os
from pathlib import Path


def test_crm_base_template_has_admin_link():
    """Test that CRM base template has Admin Center link for staff users"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    assert template_path.exists(), f"Template not found: {template_path}"
    
    content = template_path.read_text()
    
    # Check that admin center link is present
    assert 'Admin Center' in content, "Admin Center link text not found"
    assert "{% url 'admin:index' %}" in content, "Admin URL reference not found"
    assert '{% if user.is_staff %}' in content, "Staff user check not found"
    
    # Check for the admin link with proper icon
    assert '⚙️' in content, "Settings/Admin icon not found"
    
    print("✅ CRM base template has Admin Center link (staff-only)")


def test_crm_base_template_logo_is_clickable():
    """Test that TELIS logo in sidebar is clickable and links to dashboard"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Check that logo is wrapped in a link
    assert '<a href="{% url \'crm-dashboard\' %}" class="flex items-center space-x-3">' in content, \
        "Logo should be wrapped in a clickable link to dashboard"
    
    # Verify the logo structure is within the link
    logo_section = content[content.find('<!-- Logo -->'):content.find('<!-- Navigation -->')]
    assert 'TELIS' in logo_section, "TELIS logo text should be in the link"
    assert '🎯' in logo_section, "Logo emoji should be in the link"
    
    print("✅ TELIS logo is clickable and links to dashboard")


def test_crm_base_template_has_breadcrumbs_with_home():
    """Test that breadcrumbs section has Home link"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Check for breadcrumbs section with Home link
    assert '<!-- Breadcrumbs -->' in content, "Breadcrumbs section not found"
    assert '<a href="{% url \'crm-dashboard\' %}" class="text-gray-400 hover:text-primary transition duration-150">Home</a>' in content, \
        "Home breadcrumb link not found or incorrect"
    
    print("✅ Breadcrumbs have Home link to dashboard")


def test_admin_base_site_template_exists():
    """Test that custom admin template exists"""
    template_path = Path(__file__).parent / 'templates' / 'admin' / 'base_site.html'
    assert template_path.exists(), f"Admin template not found: {template_path}"
    
    content = template_path.read_text()
    
    # Check it extends Django admin base
    assert '{% extends "admin/base.html" %}' in content, "Template should extend admin/base.html"
    
    print("✅ Custom admin template exists and extends base admin template")


def test_admin_base_site_has_back_to_crm_button():
    """Test that admin template has Back to CRM button"""
    template_path = Path(__file__).parent / 'templates' / 'admin' / 'base_site.html'
    content = template_path.read_text()
    
    # Check for back to CRM button
    assert 'Zurück zum CRM' in content, "Back to CRM button text not found"
    assert "{% url 'crm-dashboard' %}" in content, "CRM dashboard URL not found"
    assert '🏠' in content, "Home icon for back button not found"
    
    # Check for LUCA Command Center branding
    assert 'LUCA Command Center' in content, "Admin branding not found"
    
    print("✅ Admin template has Back to CRM button")


def test_admin_link_opens_in_new_tab():
    """Test that Admin Center link opens in new tab"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Find the admin center link section
    admin_link_start = content.find('<!-- Admin Center Link')
    admin_link_end = content.find('{% endif %}', admin_link_start) + 11
    admin_link_section = content[admin_link_start:admin_link_end]
    
    # Check that link has target="_blank"
    assert 'target="_blank"' in admin_link_section, "Admin link should open in new tab"
    
    print("✅ Admin Center link opens in new tab")


def test_mobile_sidebar_toggle_exists():
    """Test that mobile menu button exists"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Check for mobile menu button
    assert '<!-- Mobile menu button -->' in content, "Mobile menu button not found"
    assert 'toggleSidebar()' in content, "Toggle sidebar function not found"
    assert 'lg:hidden' in content, "Mobile-specific hiding class not found"
    
    print("✅ Mobile sidebar toggle exists")


if __name__ == '__main__':
    print("Testing Navigation Improvements...\n")
    
    try:
        test_crm_base_template_has_admin_link()
        test_crm_base_template_logo_is_clickable()
        test_crm_base_template_has_breadcrumbs_with_home()
        test_admin_base_site_template_exists()
        test_admin_base_site_has_back_to_crm_button()
        test_admin_link_opens_in_new_tab()
        test_mobile_sidebar_toggle_exists()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
