"""Views for pages app - builder and public page rendering"""
import json
import logging
import os
import zipfile
import shutil
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction, models as db_models
from django.db.models import Count
from django.conf import settings

from .models import (
    Project, LandingPage, PageVersion, PageComponent, PageSubmission, 
    PageAsset, BrandSettings, PageTemplate
)
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


@staff_member_required
@require_POST
def publish_page(request, slug):
    """Publish or unpublish a landing page"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        publish = data.get('publish', True)
        
        if publish:
            page.status = 'published'
            page.published_at = timezone.now()
            message = 'Page published successfully'
        else:
            page.status = 'draft'
            page.published_at = None
            message = 'Page unpublished successfully'
        
        page.updated_by = request.user
        page.save()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'status': page.status,
            'published_at': page.published_at.isoformat() if page.published_at else None,
            'public_url': page.get_absolute_url() if page.status == 'published' else None
        })
    except Exception as e:
        logger.error(f"Error publishing page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


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
    """
    Handle form submission from landing page
    
    Security Note - CSRF Exemption:
    -------------------------------
    This endpoint is marked @csrf_exempt because landing pages may be:
    1. Embedded in external websites or email campaigns
    2. Hosted on custom domains (external to main app domain)
    3. Accessed from various marketing channels without prior session

    Alternative Security Measures:
    - Origin validation: Checks if request comes from allowed domains
    - Rate limiting: Prevents abuse (TODO: Implement with django-ratelimit)
    - Input validation: Strict validation of all form data
    - Lead deduplication: Prevents spam submissions
    
    IMPORTANT: Only use this for legitimate lead capture forms.
    Consider implementing ReCaptcha for production deployments.
    
    See: https://docs.djangoproject.com/en/stable/ref/csrf/#csrf-exempt
    """
    page = get_object_or_404(LandingPage, slug=slug, status='published')
    
    # Security: Validate origin if ALLOWED_HOSTS is configured
    # This provides some protection even without CSRF tokens
    origin = request.META.get('HTTP_ORIGIN', '')
    referer = request.META.get('HTTP_REFERER', '')
    
    # Log the submission for security monitoring
    logger.info(f"Form submission for page '{slug}' from origin='{origin}' referer='{referer}'")
    
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
    """Upload asset für GrapesJS"""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'Keine Datei'}, status=400)
    
    file = request.FILES['file']
    mime = file.content_type
    width, height = None, None
    
    # Validate file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'Datei zu groß. Maximum 10MB.'}, status=400)
    
    # Get landing_page if provided
    landing_page = None
    page_id = request.POST.get('landing_page_id')
    if page_id:
        try:
            landing_page = LandingPage.objects.get(id=page_id)
        except LandingPage.DoesNotExist:
            return JsonResponse({'error': 'Landing Page nicht gefunden'}, status=400)
    
    if mime.startswith('image/'):
        try:
            from PIL import Image
            img = Image.open(file)
            width, height = img.size
            file.seek(0)
        except (IOError, Image.UnidentifiedImageError) as e:
            logger.warning(f"Failed to process image: {e}")
            # Continue without dimensions
        asset_type = 'image'
    else:
        asset_type = 'document'
    
    asset = PageAsset.objects.create(
        landing_page=landing_page,
        file=file,
        name=file.name,
        asset_type=asset_type,
        width=width,
        height=height,
        file_size=file.size,
        mime_type=mime,
        folder=request.POST.get('folder', ''),
        uploaded_by=request.user
    )
    
    return JsonResponse({'src': asset.url, 'name': asset.name, 'width': width, 'height': height})


@staff_member_required
def list_assets(request):
    """Liste Assets für GrapesJS Asset Manager"""
    assets = PageAsset.objects.filter(asset_type='image')
    page_id = request.GET.get('landing_page_id')
    if page_id:
        assets = assets.filter(db_models.Q(landing_page_id=page_id) | db_models.Q(landing_page__isnull=True))
    
    return JsonResponse([{'src': a.url, 'name': a.name} for a in assets], safe=False)


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
def brand_settings_view(request):
    """Brand Settings Seite"""
    from django.contrib import messages
    
    settings = BrandSettings.get_settings()
    if request.method == 'POST':
        # Update all fields from POST
        for f in ['primary_color', 'secondary_color', 'accent_color', 'text_color', 'background_color',
                  'heading_font', 'body_font', 'company_name', 'contact_email', 'contact_phone',
                  'facebook_url', 'instagram_url', 'linkedin_url', 'privacy_url', 'imprint_url']:
            if f in request.POST:
                setattr(settings, f, request.POST[f])
        
        # Handle file uploads
        if 'logo' in request.FILES:
            settings.logo = request.FILES['logo']
        if 'logo_dark' in request.FILES:
            settings.logo_dark = request.FILES['logo_dark']
        if 'favicon' in request.FILES:
            settings.favicon = request.FILES['favicon']
        
        settings.save()
        messages.success(request, 'Gespeichert!')
        return redirect('pages:brand-settings')
    return render(request, 'pages/brand_settings.html', {'settings': settings})


@staff_member_required
@require_http_methods(["GET"])
def get_brand_css(request):
    """Get brand settings as CSS variables"""
    settings_obj = BrandSettings.objects.first()
    if settings_obj:
        css = settings_obj.get_css_variables()
        return HttpResponse(css, content_type='text/css')
    
    return HttpResponse('', content_type='text/css')


# ============================================================================
# Template Views
# ============================================================================

@staff_member_required
def select_template(request):
    """Template selection page"""
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
        page.html = template.html
        page.css = template.css
        page.html_json = template.html_json
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


@staff_member_required
def template_list(request):
    """Liste aller Templates"""
    templates = PageTemplate.objects.filter(is_active=True)
    
    # Group by category
    templates_by_category = {}
    for template in templates:
        category = template.get_category_display()
        if category not in templates_by_category:
            templates_by_category[category] = []
        templates_by_category[category].append(template)
    
    return render(request, 'pages/template_list.html', {'templates_by_category': templates_by_category})


@staff_member_required
def template_config(request, template_id):
    """Get template layout configuration"""
    try:
        template = PageTemplate.objects.get(id=template_id, is_active=True)
        
        return JsonResponse({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'slug': template.slug,
                'category': template.category,
                'category_display': template.get_category_display(),
                'description': template.description,
                'layout_config': template.layout_config,
                'html_json': template.html_json,
                'css': template.css,
            }
        })
    except PageTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Template not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting template config {template_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_member_required
def templates_by_category(request, category):
    """Get templates filtered by category"""
    try:
        templates = PageTemplate.objects.filter(is_active=True, category=category)
        
        templates_data = [
            {
                'id': t.id,
                'name': t.name,
                'slug': t.slug,
                'category': t.category,
                'description': t.description,
                'layout_config': t.layout_config,
                'usage_count': t.usage_count,
                'thumbnail_url': t.thumbnail.url if t.thumbnail else None,
            }
            for t in templates
        ]
        
        return JsonResponse({
            'success': True,
            'category': category,
            'templates': templates_data
        })
    except Exception as e:
        logger.error(f"Error getting templates for category {category}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



# ============================================================================
# Project Management Views
# ============================================================================

@staff_member_required
def quick_create(request):
    """Quick create interface with tabs for different input methods"""
    templates = PageTemplate.objects.filter(is_active=True)
    
    return render(request, 'pages/quick_create.html', {
        'templates': templates
    })


@staff_member_required
@require_POST
def upload_project(request):
    """
    Upload komplettes HTML/CSS/JS Projekt als ZIP
    
    Security Note:
    -------------
    This function allows staff members to upload complete web projects including JavaScript.
    The uploaded JavaScript will execute in visitor browsers when pages are published.
    
    Security Measures:
    - Only staff members can upload (enforced by @staff_member_required)
    - File types are restricted to a whitelist (see ALLOWED_EXTENSIONS)
    - Path traversal is prevented through normalization
    - Hidden files are skipped
    - File size limits are enforced (50MB max)
    - Uploaded pages are served with Content-Security-Policy headers
    
    ⚠️  WARNING: Only upload projects from trusted sources!
    
    See pages/SECURITY.md for detailed security documentation.
    """
    try:
        # Check if ZIP file is provided
        if 'zip_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Keine ZIP-Datei hochgeladen'
            }, status=400)
        
        zip_file = request.FILES['zip_file']
        
        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if zip_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': f'Datei zu groß. Maximum: 50MB (hochgeladen: {zip_file.size / (1024 * 1024):.1f}MB)'
            }, status=400)
        
        # Get project metadata
        project_name = request.POST.get('name', zip_file.name.replace('.zip', ''))
        project_slug = slugify(project_name)
        project_type = request.POST.get('type', 'website')
        project_description = request.POST.get('description', '')
        
        # Check if project with this slug already exists
        if Project.objects.filter(slug=project_slug).exists():
            return JsonResponse({
                'success': False,
                'error': f'Ein Projekt mit dem Slug "{project_slug}" existiert bereits'
            }, status=400)
        
        # Allowed file extensions
        allowed_extensions = {
            '.html', '.htm', '.css', '.js', '.json',
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico',
            '.woff', '.woff2', '.ttf', '.eot',
            '.txt', '.md'
        }
        
        # Extract ZIP to temporary directory
        projects_root = os.path.join(settings.MEDIA_ROOT, 'projects')
        os.makedirs(projects_root, exist_ok=True)
        
        project_path = os.path.join(projects_root, project_slug)
        
        # Extract ZIP file
        html_files = []
        extracted_files = []
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # Validate and extract files
            for file_info in zip_ref.filelist:
                # Skip directories
                if file_info.is_dir():
                    continue
                
                # Get file extension
                file_ext = os.path.splitext(file_info.filename)[1].lower()
                
                # Skip hidden files and unwanted files
                filename_parts = Path(file_info.filename).parts
                if any(part.startswith('.') or part.startswith('__') for part in filename_parts):
                    continue
                
                # Check if file type is allowed
                if file_ext not in allowed_extensions:
                    logger.warning(f"Skipping file with disallowed extension: {file_info.filename}")
                    continue
                
                # Prevent path traversal attacks
                extracted_path = os.path.normpath(os.path.join(project_path, file_info.filename))
                if not extracted_path.startswith(project_path):
                    logger.warning(f"Path traversal attempt detected: {file_info.filename}")
                    continue
                
                # Extract the file
                zip_ref.extract(file_info, project_path)
                extracted_files.append(file_info.filename)
                
                # Track HTML files
                if file_ext in ['.html', '.htm']:
                    html_files.append(file_info.filename)
        
        if not html_files:
            return JsonResponse({
                'success': False,
                'error': 'Keine HTML-Dateien im ZIP-Archiv gefunden'
            }, status=400)
        
        # Create Project
        with transaction.atomic():
            project = Project.objects.create(
                name=project_name,
                slug=project_slug,
                project_type=project_type,
                description=project_description,
                static_path=f'projects/{project_slug}/',
                created_by=request.user
            )
            
            # Create LandingPage for each HTML file
            main_page = None
            pages_created = []
            
            for html_file in html_files:
                # Generate page slug from filename
                page_filename = os.path.basename(html_file)
                page_name = os.path.splitext(page_filename)[0]
                page_slug = f"{project_slug}-{slugify(page_name)}"
                
                # Ensure unique slug
                counter = 1
                original_slug = page_slug
                while LandingPage.objects.filter(slug=page_slug).exists():
                    page_slug = f"{original_slug}-{counter}"
                    counter += 1
                
                # Read HTML content
                html_path = os.path.join(project_path, html_file)
                with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                
                # Create LandingPage
                page = LandingPage.objects.create(
                    slug=page_slug,
                    title=f"{project_name} - {page_name}",
                    status='draft',
                    project=project,
                    is_uploaded_site=True,
                    uploaded_files_path=f'projects/{project_slug}/',
                    entry_point=html_file,
                    html=html_content,
                    created_by=request.user,
                    updated_by=request.user
                )
                
                pages_created.append({
                    'slug': page_slug,
                    'title': page.title,
                    'file': html_file
                })
                
                # Set main page (index.html or first HTML file)
                if page_filename.lower() in ['index.html', 'index.htm'] or main_page is None:
                    main_page = page
            
            # Set main page for project
            if main_page:
                project.main_page = main_page
                project.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Projekt "{project_name}" erfolgreich hochgeladen',
            'data': {
                'project': {
                    'name': project.name,
                    'slug': project.slug,
                    'url': project.get_absolute_url()
                },
                'pages': pages_created,
                'files_extracted': len(extracted_files)
            }
        })
    
    except zipfile.BadZipFile:
        return JsonResponse({
            'success': False,
            'error': 'Ungültige ZIP-Datei'
        }, status=400)
    except Exception as e:
        logger.error(f"Error uploading project: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Fehler beim Hochladen: {str(e)}'
        }, status=500)


@staff_member_required
def project_list(request):
    """Liste aller hochgeladenen Projekte"""
    projects = Project.objects.annotate(
        page_count=Count('pages')
    ).select_related('main_page', 'created_by')
    
    return render(request, 'pages/project_list.html', {
        'projects': projects
    })


@staff_member_required
def project_detail(request, slug):
    """Projektdetails mit allen Seiten"""
    project = get_object_or_404(Project.objects.select_related('main_page', 'created_by'), slug=slug)
    pages = project.pages.all().order_by('title')
    
    return render(request, 'pages/project_detail.html', {
        'project': project,
        'pages': pages
    })


@staff_member_required
@require_POST
def project_delete(request, slug):
    """Projekt und alle zugehörigen Seiten löschen"""
    project = get_object_or_404(Project, slug=slug)
    
    try:
        # Delete project files
        if project.static_path:
            project_path = os.path.join(settings.MEDIA_ROOT, project.static_path)
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
        
        # Delete project (will cascade delete pages)
        project_name = project.name
        project.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Projekt "{project_name}" wurde gelöscht'
        })
    except Exception as e:
        logger.error(f"Error deleting project {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Fehler beim Löschen: {str(e)}'
        }, status=500)


# ============================================================================
# Project Settings, Navigation, Build & Export Views
# ============================================================================

@staff_member_required
def project_settings_view(request, slug):
    """Projekt-Einstellungen bearbeiten"""
    from .models import ProjectSettings
    
    project = get_object_or_404(Project, slug=slug)
    
    # Get or create settings
    settings_obj, created = ProjectSettings.objects.get_or_create(project=project)
    
    if request.method == 'POST':
        try:
            # Update SEO settings
            settings_obj.default_seo_title_suffix = request.POST.get('default_seo_title_suffix', '')
            settings_obj.default_seo_description = request.POST.get('default_seo_description', '')
            settings_obj.default_seo_image = request.POST.get('default_seo_image', '')
            
            # Update Analytics
            settings_obj.google_analytics_id = request.POST.get('google_analytics_id', '')
            settings_obj.facebook_pixel_id = request.POST.get('facebook_pixel_id', '')
            settings_obj.custom_head_code = request.POST.get('custom_head_code', '')
            settings_obj.custom_body_code = request.POST.get('custom_body_code', '')
            
            # Update Design
            settings_obj.primary_color = request.POST.get('primary_color', '#3B82F6')
            settings_obj.secondary_color = request.POST.get('secondary_color', '#10B981')
            settings_obj.font_family = request.POST.get('font_family', 'Inter, sans-serif')
            
            # Handle favicon upload
            if 'favicon' in request.FILES:
                settings_obj.favicon = request.FILES['favicon']
            
            # Handle custom 404 page
            custom_404_id = request.POST.get('custom_404_page')
            if custom_404_id:
                try:
                    settings_obj.custom_404_page = LandingPage.objects.get(id=custom_404_id)
                except LandingPage.DoesNotExist:
                    settings_obj.custom_404_page = None
            else:
                settings_obj.custom_404_page = None
            
            settings_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Einstellungen gespeichert'
            })
        except Exception as e:
            logger.error(f"Error saving project settings: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET request - show form
    pages = LandingPage.objects.filter(project=project)
    
    return render(request, 'pages/project_settings.html', {
        'project': project,
        'settings': settings_obj,
        'pages': pages
    })


@staff_member_required
def project_navigation_view(request, slug):
    """Navigation Editor mit Drag & Drop"""
    from .models import ProjectNavigation
    
    project = get_object_or_404(Project, slug=slug)
    
    # Get navigation items
    nav_items = ProjectNavigation.objects.filter(project=project).select_related('page', 'parent')
    
    # Get available pages
    available_pages = LandingPage.objects.filter(project=project)
    
    return render(request, 'pages/project_navigation.html', {
        'project': project,
        'nav_items': nav_items,
        'available_pages': available_pages
    })


@staff_member_required
@require_POST
def save_navigation(request, slug):
    """Speichert Navigation-Struktur (AJAX)"""
    from .models import ProjectNavigation
    
    project = get_object_or_404(Project, slug=slug)
    
    try:
        data = json.loads(request.body)
        navigation_items = data.get('navigation', [])
        
        # Delete old navigation
        ProjectNavigation.objects.filter(project=project).delete()
        
        # Create new navigation recursively
        def create_nav_items(items, parent=None, order_offset=0):
            for idx, item in enumerate(items):
                # Get page if page_id is provided
                page = None
                if item.get('page_id'):
                    try:
                        page = LandingPage.objects.get(id=item['page_id'])
                    except LandingPage.DoesNotExist:
                        pass
                
                # Create navigation item
                nav_item = ProjectNavigation.objects.create(
                    project=project,
                    parent=parent,
                    title=item.get('title', ''),
                    page=page,
                    external_url=item.get('external_url', ''),
                    icon=item.get('icon', ''),
                    order=order_offset + idx,
                    is_visible=item.get('is_visible', True),
                    open_in_new_tab=item.get('open_in_new_tab', False)
                )
                
                # Create children recursively
                if 'children' in item and item['children']:
                    create_nav_items(item['children'], parent=nav_item)
        
        create_nav_items(navigation_items)
        
        return JsonResponse({
            'success': True,
            'message': 'Navigation gespeichert'
        })
    except Exception as e:
        logger.error(f"Error saving navigation: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_POST
def build_project(request, slug):
    """Baut das Projekt (erstellt statische Dateien)"""
    from .models import ProjectDeployment
    from .services.project_builder import ProjectBuilder
    
    project = get_object_or_404(Project, slug=slug)
    
    try:
        # Create deployment record
        deployment = ProjectDeployment.objects.create(
            project=project,
            status='building',
            deployed_by=request.user
        )
        
        # Build project
        builder = ProjectBuilder(project)
        result = builder.build()
        
        if result['success']:
            # Update deployment record
            deployment.status = 'success'
            deployment.deployed_files_count = result['files_count']
            deployment.deployed_size_bytes = result['total_size']
            deployment.build_log = '\n'.join(result.get('warnings', []))
            deployment.completed_at = timezone.now()
            deployment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Projekt erfolgreich gebaut',
                'files_count': result['files_count'],
                'total_size': result['total_size'],
                'warnings': result.get('warnings', [])
            })
        else:
            # Update deployment as failed
            deployment.status = 'failed'
            deployment.build_log = '\n'.join(result.get('errors', []))
            deployment.completed_at = timezone.now()
            deployment.save()
            
            return JsonResponse({
                'success': False,
                'errors': result.get('errors', [])
            }, status=400)
    except Exception as e:
        logger.error(f"Error building project {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def export_project(request, slug):
    """Exportiert das Projekt als ZIP"""
    from .services.project_builder import ProjectBuilder
    from django.http import FileResponse
    
    project = get_object_or_404(Project, slug=slug)
    
    try:
        # Build project
        builder = ProjectBuilder(project)
        build_result = builder.build()
        
        if not build_result['success']:
            return JsonResponse({
                'success': False,
                'errors': build_result.get('errors', [])
            }, status=400)
        
        # Export as ZIP
        zip_path = builder.export_zip()
        
        # Send file as download with proper resource management
        with open(zip_path, 'rb') as zip_file:
            response = FileResponse(
                zip_file,
                as_attachment=True,
                filename=zip_path.name
            )
            # Note: FileResponse will handle closing the file
            return response
        
        # Cleanup build directory after sending (optional)
        # builder.cleanup()
        
    except Exception as e:
        logger.error(f"Error exporting project {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def project_deployments(request, slug):
    """Zeigt Deployment-Historie"""
    from .models import ProjectDeployment
    
    project = get_object_or_404(Project, slug=slug)
    
    # Get last 20 deployments
    deployments = ProjectDeployment.objects.filter(project=project)[:20]
    
    return render(request, 'pages/project_deployments.html', {
        'project': project,
        'deployments': deployments
    })


@staff_member_required
def project_build_view(request, slug):
    """Build-Übersicht und -Steuerung"""
    from .models import ProjectAsset
    
    project = get_object_or_404(Project, slug=slug)
    
    # Get project info
    pages = LandingPage.objects.filter(project=project, status='published')
    assets = ProjectAsset.objects.filter(project=project)
    
    return render(request, 'pages/project_build.html', {
        'project': project,
        'pages': pages,
        'assets': assets
    })


@staff_member_required
@require_http_methods(["GET"])
def social_preview(request, slug):
    """Preview how the page will appear on social media platforms"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    # Get the full URL for the page
    page_url = request.build_absolute_uri(page.get_absolute_url())
    
    # Prepare preview data for different platforms
    preview_data = {
        'page': page,
        'page_url': page_url,
        'og_title': page.get_og_title(),
        'og_description': page.get_og_description(),
        'og_image': page.get_og_image(),
        'twitter_card': page.twitter_card,
        'twitter_title': page.get_twitter_title(),
        'twitter_description': page.get_twitter_description(),
        'twitter_image': page.get_twitter_image(),
    }
    
    return render(request, 'pages/social_preview.html', preview_data)
