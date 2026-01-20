"""Views for file upload and domain management"""
import json
import logging
import mimetypes
from pathlib import Path
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings

from .models import LandingPage, UploadedFile, DomainConfiguration
from .services.upload_service import UploadService, UploadServiceError
from .services.domain_service import StratoDomainService, DomainServiceError

logger = logging.getLogger(__name__)


# ===== Upload Management Views =====

@staff_member_required
def upload_manager(request, slug):
    """File upload manager interface"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    # Get upload service
    upload_service = UploadService(page)
    
    # Get file tree
    file_tree = upload_service.get_file_tree()
    
    # Get all uploaded files with stats
    uploaded_files = UploadedFile.objects.filter(landing_page=page)
    total_files = uploaded_files.count()
    total_size = sum(f.file_size for f in uploaded_files)
    
    return render(request, 'pages/upload_manager.html', {
        'page': page,
        'file_tree': file_tree,
        'total_files': total_files,
        'total_size': total_size,
        'entry_point': page.entry_point,
    })


@staff_member_required
@require_POST
def upload_zip(request, slug):
    """Handle ZIP file upload"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        # Get ZIP file from request
        if 'zip_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Keine ZIP-Datei hochgeladen'
            }, status=400)
        
        zip_file = request.FILES['zip_file']
        
        # Process ZIP upload
        upload_service = UploadService(page)
        result = upload_service.process_zip_upload(zip_file)
        
        return JsonResponse({
            'success': True,
            'message': f'{result["files_processed"]} Dateien erfolgreich hochgeladen',
            'data': result
        })
    
    except UploadServiceError as e:
        logger.error(f"ZIP upload error for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error during ZIP upload for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ein unerwarteter Fehler ist aufgetreten'
        }, status=500)


@staff_member_required
@require_POST
def upload_file(request, slug):
    """Handle single file upload"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        # Get file and path from request
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Keine Datei hochgeladen'
            }, status=400)
        
        file = request.FILES['file']
        relative_path = request.POST.get('path', file.name)
        
        # Upload file
        upload_service = UploadService(page)
        uploaded_file = upload_service.upload_single_file(file, relative_path)
        
        return JsonResponse({
            'success': True,
            'message': 'Datei erfolgreich hochgeladen',
            'data': {
                'path': uploaded_file.relative_path,
                'size': uploaded_file.file_size,
                'type': uploaded_file.file_type,
            }
        })
    
    except UploadServiceError as e:
        logger.error(f"File upload error for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error during file upload for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ein unerwarteter Fehler ist aufgetreten'
        }, status=500)


@staff_member_required
@require_POST
def delete_file(request, slug):
    """Delete a single uploaded file"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        # Get file path from request
        data = json.loads(request.body)
        relative_path = data.get('path')
        
        if not relative_path:
            return JsonResponse({
                'success': False,
                'error': 'Kein Dateipfad angegeben'
            }, status=400)
        
        # Delete file
        upload_service = UploadService(page)
        success = upload_service.delete_file(relative_path)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Datei erfolgreich gelöscht'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Datei nicht gefunden'
            }, status=404)
    
    except Exception as e:
        logger.error(f"Error deleting file for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ein Fehler ist beim Löschen aufgetreten'
        }, status=500)


@staff_member_required
@require_GET
def list_files(request, slug):
    """List all uploaded files"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        upload_service = UploadService(page)
        file_tree = upload_service.get_file_tree()
        
        return JsonResponse({
            'success': True,
            'data': file_tree
        })
    
    except Exception as e:
        logger.error(f"Error listing files for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Fehler beim Laden der Dateien'
        }, status=500)


@staff_member_required
@require_GET
def get_stats(request, slug):
    """Get file upload statistics"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        uploaded_files = UploadedFile.objects.filter(landing_page=page)
        total_files = uploaded_files.count()
        total_size = sum(f.file_size for f in uploaded_files)
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_files': total_files,
                'total_size': total_size,
                'entry_point': page.entry_point
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting stats for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Fehler beim Laden der Statistiken'
        }, status=500)


@staff_member_required
@require_POST
def set_entry_point(request, slug):
    """Set the entry point file"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        entry_point = data.get('entry_point')
        
        if not entry_point:
            return JsonResponse({
                'success': False,
                'error': 'Kein Entry Point angegeben'
            }, status=400)
        
        # Verify file exists
        if not UploadedFile.objects.filter(landing_page=page, relative_path=entry_point).exists():
            return JsonResponse({
                'success': False,
                'error': 'Datei existiert nicht'
            }, status=404)
        
        # Update entry point
        page.entry_point = entry_point
        page.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Entry Point erfolgreich gesetzt'
        })
    
    except Exception as e:
        logger.error(f"Error setting entry point for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Fehler beim Setzen des Entry Points'
        }, status=500)


def serve_uploaded_file(request, slug, file_path):
    """
    Serve uploaded static files (public)
    
    Security Note:
    -------------
    Uploaded files may contain JavaScript that executes in the visitor's browser.
    This view applies Content-Security-Policy headers to limit what the JavaScript can do:
    - Prevents framing by external sites
    - Restricts connection endpoints
    - Limits script sources
    
    See pages/SECURITY.md for more information about upload security.
    """
    page = get_object_or_404(LandingPage, slug=slug, status='published')
    
    # Check if this is an uploaded site
    if not page.is_uploaded_site:
        return HttpResponse('Not an uploaded site', status=404)
    
    try:
        # Get uploaded file from database
        uploaded_file = UploadedFile.objects.get(
            landing_page=page,
            relative_path=file_path
        )
        
        # Get file path on disk
        upload_service = UploadService(page)
        full_path = upload_service.page_upload_path / file_path
        
        if not full_path.exists():
            return HttpResponse('File not found', status=404)
        
        # Determine content type
        content_type = uploaded_file.file_type
        if not content_type:
            content_type = mimetypes.guess_type(str(full_path))[0] or 'application/octet-stream'
        
        # Serve file with proper resource cleanup
        try:
            file_handle = open(full_path, 'rb')
            response = FileResponse(file_handle, content_type=content_type)
            
            # Add security headers for HTML files to sandbox JavaScript
            if content_type in ['text/html', 'application/xhtml+xml']:
                # Content Security Policy to limit what uploaded JavaScript can do
                # Note: 'unsafe-inline' and 'unsafe-eval' are needed for most HTML/JS projects
                # but they do reduce security. Only upload trusted content.
                csp_policy = "; ".join([
                    "default-src 'self'",
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                    "style-src 'self' 'unsafe-inline'",
                    "img-src 'self' data: https:",
                    "font-src 'self' data:",
                    "connect-src 'self'",
                    "frame-ancestors 'none'",
                ])
                response['Content-Security-Policy'] = csp_policy
                
                # Prevent page from being embedded in iframes from other domains
                response['X-Frame-Options'] = 'DENY'
                
                # Prevent MIME type sniffing
                response['X-Content-Type-Options'] = 'nosniff'
            
            return response
        except Exception as e:
            logger.error(f"Error opening file {file_path} for page {slug}: {e}")
            return HttpResponse('Error opening file', status=500)
    
    except UploadedFile.DoesNotExist:
        return HttpResponse('File not found', status=404)
    except Exception as e:
        logger.error(f"Error serving file {file_path} for page {slug}: {e}")
        return HttpResponse('Error serving file', status=500)


# ===== Domain Management Views =====

@staff_member_required
def domain_settings(request, slug):
    """Domain configuration interface"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    # Get or create domain configuration
    domain_config, _ = DomainConfiguration.objects.get_or_create(landing_page=page)
    
    # Get domain service
    domain_service = StratoDomainService(page)
    
    # Get DNS instructions if domain is configured
    dns_instructions = None
    if page.get_full_domain():
        try:
            dns_instructions = domain_service.get_dns_instructions()
        except DomainServiceError as e:
            logger.warning(f"Could not generate DNS instructions for {slug}: {e}")
    
    return render(request, 'pages/domain_settings.html', {
        'page': page,
        'domain_config': domain_config,
        'dns_instructions': dns_instructions,
    })


@staff_member_required
@require_POST
def save_domain_settings(request, slug):
    """Save domain configuration"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        
        # Update hosting type
        hosting_type = data.get('hosting_type')
        if hosting_type in ['internal', 'strato', 'custom']:
            page.hosting_type = hosting_type
        
        # Update domain fields
        page.custom_domain = data.get('custom_domain', '').strip()
        page.strato_subdomain = data.get('strato_subdomain', '').strip()
        page.strato_main_domain = data.get('strato_main_domain', '').strip()
        page.ssl_enabled = data.get('ssl_enabled', True)
        
        # Reset DNS verification when domain changes
        page.dns_verified = False
        
        page.save()
        
        # Generate new verification token and instructions
        domain_service = StratoDomainService(page)
        domain_service.generate_verification_token()
        
        dns_instructions = None
        if page.get_full_domain():
            try:
                dns_instructions = domain_service.get_dns_instructions()
            except DomainServiceError:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Domain-Einstellungen erfolgreich gespeichert',
            'data': {
                'dns_instructions': dns_instructions,
                'verification_token': page.dns_verification_token,
            }
        })
    
    except Exception as e:
        logger.error(f"Error saving domain settings for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Fehler beim Speichern der Domain-Einstellungen'
        }, status=500)


@staff_member_required
@require_POST
def verify_dns(request, slug):
    """Verify DNS configuration"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        if not page.get_full_domain():
            return JsonResponse({
                'success': False,
                'error': 'Keine Domain konfiguriert'
            }, status=400)
        
        # Verify DNS
        domain_service = StratoDomainService(page)
        results = domain_service.verify_dns_configuration()
        
        return JsonResponse({
            'success': True,
            'verified': results['verified'],
            'data': results
        })
    
    except DomainServiceError as e:
        logger.error(f"DNS verification error for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error during DNS verification for page {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Fehler bei der DNS-Verifikation'
        }, status=500)


@staff_member_required
@require_GET
def get_nginx_config(request, slug):
    """Get nginx configuration"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        if not page.get_full_domain():
            return HttpResponse('Keine Domain konfiguriert', status=400)
        
        # Generate nginx config
        domain_service = StratoDomainService(page)
        config = domain_service.get_nginx_config()
        
        # Return as downloadable file
        response = HttpResponse(config, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{page.slug}_nginx.conf"'
        
        return response
    
    except DomainServiceError as e:
        logger.error(f"Error generating nginx config for page {slug}: {e}")
        return HttpResponse(f'Fehler: {e}', status=400)
    except Exception as e:
        logger.error(f"Unexpected error generating nginx config for page {slug}: {e}")
        return HttpResponse('Fehler beim Generieren der nginx-Konfiguration', status=500)
