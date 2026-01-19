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

from .models import LandingPage, PageVersion, PageComponent, PageSubmission, PageAsset
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
            # Convert POST data to dict, preserving multi-value fields
            data = {}
            for key in request.POST.keys():
                values = request.POST.getlist(key)
                data[key] = values if len(values) > 1 else values[0]
        
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
            try:
                # Use page-specific Brevo list if configured
                if page.brevo_list_id:
                    # Import here to avoid circular imports
                    from leads.services.brevo import create_or_update_contact
                    
                    # Prepare contact attributes
                    name_parts = (lead.name or "").split(" ", 1)
                    attributes = {
                        "VORNAME": name_parts[0] if name_parts else "",
                        "NACHNAME": name_parts[1] if len(name_parts) > 1 else "",
                        "TELEFON": lead.telefon or "",
                    }
                    
                    create_or_update_contact(
                        email=lead.email,
                        attributes=attributes,
                        list_ids=[page.brevo_list_id]
                    )
                    logger.info(f"Synced lead to Brevo list {page.brevo_list_id}: {lead.email}")
                else:
                    # Use default sync
                    sync_lead_to_brevo(lead)
                    logger.info(f"Synced lead to Brevo (default lists): {lead.email}")
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


# ============================================================================
# Asset Manager Views
# ============================================================================

@staff_member_required
@require_POST
def upload_asset(request):
    """Upload an asset to the asset manager"""
    try:
        from PIL import Image
        import os
        
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
        if uploaded_file.content_type not in allowed_types:
            return JsonResponse({'success': False, 'error': 'Invalid file type. Only images are allowed.'}, status=400)
        
        # Validate file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File too large. Maximum size is 10MB.'}, status=400)
        
        # Get additional params
        folder = request.POST.get('folder', '')
        alt_text = request.POST.get('alt_text', '')
        
        # Sanitize filename
        original_filename = uploaded_file.name
        safe_filename = os.path.basename(original_filename)  # Remove path components
        
        # Get file size
        file_size = uploaded_file.size
        
        # Try to get image dimensions
        width, height = None, None
        try:
            img = Image.open(uploaded_file)
            width, height = img.size
            uploaded_file.seek(0)  # Reset file pointer
        except Exception:
            pass  # Not an image or couldn't read dimensions
        
        # Create asset
        asset = PageAsset.objects.create(
            file=uploaded_file,
            filename=safe_filename,
            file_size=file_size,
            width=width,
            height=height,
            alt_text=alt_text,
            folder=folder,
            uploaded_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'asset': {
                'id': asset.id,
                'url': asset.file.url,
                'filename': asset.filename,
                'file_size': asset.file_size,
                'width': asset.width,
                'height': asset.height,
                'alt_text': asset.alt_text,
                'folder': asset.folder,
            }
        })
    except Exception as e:
        logger.error(f"Error uploading asset: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to upload asset. Please try again.'}, status=400)


@staff_member_required
@require_http_methods(["GET"])
def list_assets(request):
    """List all assets for GrapesJS Asset Manager"""
    folder = request.GET.get('folder', '')
    
    assets = PageAsset.objects.all()
    if folder:
        assets = assets.filter(folder=folder)
    
    # Format for GrapesJS Asset Manager
    asset_list = []
    for asset in assets:
        asset_list.append({
            'id': asset.id,
            'src': asset.file.url,
            'name': asset.filename,
            'type': 'image',  # Can be extended for other types
            'height': asset.height,
            'width': asset.width,
            'folder': asset.folder,
            'alt': asset.alt_text,
        })
    
    return JsonResponse({'data': asset_list})


@staff_member_required
@require_POST
def delete_asset(request, asset_id):
    """Delete an asset"""
    try:
        asset = PageAsset.objects.get(id=asset_id)
        
        # Delete the file
        if asset.file:
            asset.file.delete()
        
        asset.delete()
        
        return JsonResponse({'success': True, 'message': 'Asset deleted successfully'})
    except PageAsset.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Asset not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting asset {asset_id}: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to delete asset. Please try again.'}, status=400)


# ============================================================================
# Brand Settings Views
# ============================================================================

@staff_member_required
def brand_settings(request):
    """View and edit brand settings"""
    from .models import BrandSettings
    
    # Get or create brand settings
    settings_obj, created = BrandSettings.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        try:
            # Update color settings
            settings_obj.primary_color = request.POST.get('primary_color', settings_obj.primary_color)
            settings_obj.secondary_color = request.POST.get('secondary_color', settings_obj.secondary_color)
            settings_obj.accent_color = request.POST.get('accent_color', settings_obj.accent_color)
            settings_obj.text_color = request.POST.get('text_color', settings_obj.text_color)
            settings_obj.background_color = request.POST.get('background_color', settings_obj.background_color)
            
            # Update typography
            settings_obj.heading_font = request.POST.get('heading_font', settings_obj.heading_font)
            settings_obj.body_font = request.POST.get('body_font', settings_obj.body_font)
            settings_obj.base_font_size = request.POST.get('base_font_size', settings_obj.base_font_size)
            
            # Update social media
            settings_obj.facebook_url = request.POST.get('facebook_url', '')
            settings_obj.instagram_url = request.POST.get('instagram_url', '')
            settings_obj.linkedin_url = request.POST.get('linkedin_url', '')
            settings_obj.twitter_url = request.POST.get('twitter_url', '')
            settings_obj.youtube_url = request.POST.get('youtube_url', '')
            
            # Update contact
            settings_obj.company_name = request.POST.get('company_name', '')
            settings_obj.email = request.POST.get('email', '')
            settings_obj.phone = request.POST.get('phone', '')
            settings_obj.address = request.POST.get('address', '')
            
            # Update legal URLs
            settings_obj.privacy_url = request.POST.get('privacy_url', '')
            settings_obj.imprint_url = request.POST.get('imprint_url', '')
            settings_obj.terms_url = request.POST.get('terms_url', '')
            
            # Handle file uploads
            if 'logo' in request.FILES:
                settings_obj.logo = request.FILES['logo']
            if 'logo_dark' in request.FILES:
                settings_obj.logo_dark = request.FILES['logo_dark']
            if 'favicon' in request.FILES:
                settings_obj.favicon = request.FILES['favicon']
            
            settings_obj.save()
            
            return JsonResponse({'success': True, 'message': 'Brand settings saved successfully'})
        except Exception as e:
            logger.error(f"Error saving brand settings: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to apply template. Please try again.'}, status=400)
    
    return render(request, 'pages/brand_settings.html', {
        'settings': settings_obj
    })


@staff_member_required
@require_http_methods(["GET"])
def get_brand_css(request):
    """Get brand settings as CSS variables"""
    from .models import BrandSettings
    
    settings_obj = BrandSettings.objects.first()
    if settings_obj:
        css = settings_obj.generate_css_variables()
        return HttpResponse(css, content_type='text/css')
    
    return HttpResponse('', content_type='text/css')


# ============================================================================
# Template Views
# ============================================================================

@staff_member_required
def select_template(request):
    """Template selection page"""
    from .models import PageTemplate
    
    templates = PageTemplate.objects.filter(is_active=True)
    
    # Group by category
    templates_by_category = {}
    for template in templates:
        category = template.get_category_display()
        if category not in templates_by_category:
            templates_by_category[category] = []
        templates_by_category[category].append(template)
    
    return render(request, 'pages/select_template.html', {
        'templates_by_category': templates_by_category
    })


@staff_member_required
@require_POST
def apply_template(request, template_id):
    """Apply a template to a new or existing page"""
    from .models import PageTemplate
    
    try:
        template = PageTemplate.objects.get(id=template_id)
        
        # Get target page slug
        slug = request.POST.get('slug')
        if not slug:
            return JsonResponse({'success': False, 'error': 'Slug is required'}, status=400)
        
        # Check if page exists
        try:
            page = LandingPage.objects.get(slug=slug)
        except LandingPage.DoesNotExist:
            # Create new page
            title = request.POST.get('title', template.name)
            page = LandingPage.objects.create(
                slug=slug,
                title=title,
                status='draft',
                created_by=request.user
            )
        
        # Apply template content
        page.html = template.html_content
        page.css = template.css_content
        page.html_json = template.gjs_data
        page.updated_by = request.user
        page.save()
        
        # Increment usage count
        template.usage_count += 1
        template.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Template applied successfully',
            'page_url': page.get_builder_url()
        })
    except PageTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Template not found'}, status=404)
    except Exception as e:
        logger.error(f"Error applying template {template_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

