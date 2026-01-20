"""
Test navigation improvements between CRM and Admin interfaces.
Tests the changes made to templates/crm/base.html and templates/admin/base_site.html
"""
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
    
    # Find the admin center link section - search for the if statement
    admin_link_start = content.find('{% if user.is_staff %}', content.find('Support'))
    if admin_link_start == -1:
        raise AssertionError("Could not find admin center section")
    
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


def test_navigation_has_aria_labels():
    """Test that navigation elements have proper ARIA labels"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Check for ARIA attributes on navigation
    assert 'role="navigation"' in content, "Navigation role not found"
    assert 'aria-label="Hauptnavigation"' in content, "Main navigation aria-label not found"
    
    # Check for aria-current on active links
    assert 'aria-current="page"' in content, "aria-current not found on active links"
    
    # Check for aria-hidden on decorative icons
    assert 'aria-hidden="true"' in content, "aria-hidden not found on decorative icons"
    
    print("✅ Navigation has proper ARIA labels")


def test_collapsible_section_is_accessible():
    """Test that collapsible email section has proper accessibility attributes"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Find email section - search for the button and the section div
    email_button_start = content.find('<!-- Email Module Section')
    email_section_marker = 'id="email-section"'
    email_section_div_start = content.find(email_section_marker, email_button_start)
    # Find the next closing div after all the email links
    email_logs_link = content.find('Logs</span>', email_section_div_start)
    email_section_end = content.find('</div>', email_logs_link)
    email_section = content[email_button_start:email_section_end]
    
    # Check for button element instead of div
    assert '<button type="button"' in email_section, "Email section header should be a button"
    
    # Check for ARIA attributes
    assert 'aria-expanded=' in email_section, "Email section should have aria-expanded"
    assert 'aria-controls="email-section"' in email_section, "Email section should have aria-controls"
    
    # Check for keyboard handler
    assert 'onkeydown="handleEmailSectionKeydown(event)"' in email_section, "Email section should have keyboard handler"
    
    print("✅ Collapsible section is accessible")


def test_mobile_menu_has_accessibility():
    """Test that mobile menu button has proper accessibility"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Find mobile menu button
    mobile_button_start = content.find('<!-- Mobile menu button -->')
    mobile_button_end = content.find('</button>', mobile_button_start) + 9
    mobile_button = content[mobile_button_start:mobile_button_end]
    
    # Check for ARIA attributes
    assert 'aria-label=' in mobile_button, "Mobile button should have aria-label"
    assert 'aria-expanded=' in mobile_button, "Mobile button should have aria-expanded"
    assert 'aria-controls="sidebar"' in mobile_button, "Mobile button should have aria-controls"
    
    print("✅ Mobile menu button has proper accessibility")


def test_external_links_have_security():
    """Test that external links have rel='noopener noreferrer'"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Count external links (those with target="_blank")
    import re
    external_links = re.findall(r'<a[^>]*target="_blank"[^>]*>', content)
    noopener_links = [link for link in external_links if 'rel="noopener noreferrer"' in link]
    
    # All external links should have noopener noreferrer
    assert len(external_links) == len(noopener_links), \
        f"All {len(external_links)} external links should have rel='noopener noreferrer', but only {len(noopener_links)} do"
    
    print("✅ External links have security attributes")


def test_toast_container_has_aria_live():
    """Test that toast notification container has aria-live region"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Find toast container
    toast_container_start = content.find('id="toast-container"')
    toast_container_end = content.find('</div>', toast_container_start)
    toast_container = content[toast_container_start:toast_container_end]
    
    # Check for ARIA live region
    assert 'role="region"' in toast_container, "Toast container should have region role"
    assert 'aria-live="polite"' in toast_container, "Toast container should have aria-live"
    
    print("✅ Toast container has aria-live region")


def test_keyboard_navigation_handlers():
    """Test that keyboard navigation handlers are present"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Check for keyboard event handlers
    assert 'handleEmailSectionKeydown' in content, "Email section keyboard handler not found"
    assert "event.key === 'Escape'" in content, "Escape key handler not found"
    assert "event.key === 'Enter'" in content, "Enter key handler not found"
    assert "event.key === ' '" in content, "Space key handler not found"
    
    print("✅ Keyboard navigation handlers are present")


def test_mobile_sidebar_closes_on_link_click():
    """Test that mobile sidebar closes when navigation links are clicked"""
    template_path = Path(__file__).parent / 'templates' / 'crm' / 'base.html'
    content = template_path.read_text()
    
    # Check for closeMobileSidebar function
    assert 'closeMobileSidebar()' in content, "closeMobileSidebar function not found"
    assert 'function closeMobileSidebar()' in content, "closeMobileSidebar function definition not found"
    
    # Check that navigation links call it
    assert 'onclick="closeMobileSidebar()"' in content, "Navigation links should call closeMobileSidebar"
    
    print("✅ Mobile sidebar closes on link click")


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
        test_navigation_has_aria_labels()
        test_collapsible_section_is_accessible()
        test_mobile_menu_has_accessibility()
        test_external_links_have_security()
        test_toast_container_has_aria_live()
        test_keyboard_navigation_handlers()
        test_mobile_sidebar_closes_on_link_click()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
