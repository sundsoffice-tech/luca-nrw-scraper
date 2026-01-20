"""Sitemap generation for landing pages"""
from django.urls import reverse
from django.utils import timezone
from django.conf import settings


def generate_sitemap_xml(pages, request=None):
    """
    Generate sitemap.xml for published landing pages
    
    Args:
        pages: QuerySet of LandingPage objects
        request: Optional request object to build absolute URLs
        
    Returns:
        XML string for sitemap
    """
    # Get base URL
    if request:
        base_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
    else:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for page in pages:
        xml_lines.append('  <url>')
        
        # Build the URL
        page_url = f"{base_url}/p/{page.slug}/"
        xml_lines.append(f'    <loc>{page_url}</loc>')
        
        # Last modification date
        lastmod = page.updated_at or page.created_at
        if lastmod:
            xml_lines.append(f'    <lastmod>{lastmod.strftime("%Y-%m-%d")}</lastmod>')
        
        # Change frequency
        changefreq = page.sitemap_changefreq or 'weekly'
        xml_lines.append(f'    <changefreq>{changefreq}</changefreq>')
        
        # Priority
        priority = float(page.sitemap_priority) if page.sitemap_priority else 0.5
        xml_lines.append(f'    <priority>{priority:.1f}</priority>')
        
        xml_lines.append('  </url>')
    
    xml_lines.append('</urlset>')
    
    return '\n'.join(xml_lines)


def generate_sitemap_index(request=None):
    """
    Generate a sitemap index if multiple sitemaps exist
    
    Args:
        request: Optional request object to build absolute URLs
        
    Returns:
        XML string for sitemap index
    """
    if request:
        base_url = request.build_absolute_uri('/')[:-1]
    else:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # Main sitemap
    xml_lines.append('  <sitemap>')
    xml_lines.append(f'    <loc>{base_url}/sitemap.xml</loc>')
    xml_lines.append(f'    <lastmod>{timezone.now().strftime("%Y-%m-%d")}</lastmod>')
    xml_lines.append('  </sitemap>')
    
    xml_lines.append('</sitemapindex>')
    
    return '\n'.join(xml_lines)
