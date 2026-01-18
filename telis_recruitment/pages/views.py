"""Views for pages app - builder and public page rendering"""
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db import transaction

from .models import LandingPage, PageVersion, PageComponent, PageSubmission
from leads.models import Lead
from leads.services.brevo import sync_lead_to_brevo

logger = logging.getLogger(__name__)


@staff_member_required
def builder_list(request):
    """List all landing pages in the builder interface"""
    pages = LandingPage.objects.all()
    return render(request, 'pages/builder_list.html', {
        'pages': pages
    })


@staff_member_required
def builder_view(request, slug):
    """GrapesJS builder interface for editing landing pages"""
    page = get_object_or_404(LandingPage, slug=slug)
    components = PageComponent.objects.filter(is_active=True)
    
    return render(request, 'pages/builder.html', {
        'page': page,
        'components': components,
    })


@staff_member_required
@require_POST
def builder_save(request, slug):
    """Save landing page content from builder"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        
        # Update page content
        page.html_json = data.get('html_json', {})
        page.html = data.get('html', '')
        page.css = data.get('css', '')
        page.updated_by = request.user
        page.save()
        
        # Create version entry
        last_version = PageVersion.objects.filter(landing_page=page).first()
        new_version_num = (last_version.version + 1) if last_version else 1
        
        PageVersion.objects.create(
            landing_page=page,
            version=new_version_num,
            html_json=page.html_json,
            html=page.html,
            css=page.css,
            created_by=request.user,
            note=data.get('note', 'Auto-save')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Page saved successfully',
            'version': new_version_num
        })
    except Exception as e:
        logger.error(f"Error saving page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["GET"])
def builder_load(request, slug):
    """Load landing page content for builder"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    return JsonResponse({
        'html_json': page.html_json,
        'html': page.html,
        'css': page.css,
    })


def public_page(request, slug):
    """Public rendering of a landing page"""
    page = get_object_or_404(LandingPage, slug=slug, status='published')
    
    # Build SEO meta tags
    seo_title = page.seo_title or page.title
    seo_description = page.seo_description or ''
    seo_image = page.seo_image or ''
    
    return render(request, 'pages/public_page.html', {
        'page': page,
        'seo_title': seo_title,
        'seo_description': seo_description,
        'seo_image': seo_image,
    })


@csrf_exempt
@require_POST
def form_submit(request, slug):
    """Handle form submission from landing page"""
    page = get_object_or_404(LandingPage, slug=slug, status='published')
    
    try:
        # Parse form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = dict(request.POST)
        
        # Extract UTM parameters
        utm_source = request.GET.get('utm_source', '')
        utm_medium = request.GET.get('utm_medium', '')
        utm_campaign = request.GET.get('utm_campaign', '')
        utm_term = request.GET.get('utm_term', '')
        utm_content = request.GET.get('utm_content', '')
        
        # Get client info
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')
        
        # Create or find lead
        lead = None
        email = data.get('email', '')
        name = data.get('name', '')
        phone = data.get('phone', '') or data.get('telefon', '')
        
        if email:
            # Try to find existing lead by email
            lead = Lead.objects.filter(email=email).first()
            
            if not lead and name:
                # Create new lead
                with transaction.atomic():
                    lead = Lead.objects.create(
                        name=name,
                        email=email,
                        telefon=phone,
                        source=Lead.Source.LANDING_PAGE,
                        source_url=request.build_absolute_uri(page.get_absolute_url()),
                        source_detail=f"Landing Page: {page.title}",
                        status=Lead.Status.NEW,
                    )
                    logger.info(f"Created new lead from page submission: {lead.email}")
        
        # Create submission record
        submission = PageSubmission.objects.create(
            landing_page=page,
            lead=lead,
            data=data,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
            client_ip=client_ip,
            user_agent=user_agent,
            referrer=referrer,
        )
        
        # Sync to Brevo if lead exists
        if lead and lead.email:
            # TODO: Use existing Brevo integration with page-specific list
            try:
                sync_lead_to_brevo(lead)
                logger.info(f"Synced lead to Brevo: {lead.email}")
            except Exception as e:
                logger.error(f"Failed to sync lead to Brevo: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Form submitted successfully',
            'submission_id': submission.id
        })
        
    except Exception as e:
        logger.error(f"Error processing form submission for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to process form submission'
        }, status=400)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
