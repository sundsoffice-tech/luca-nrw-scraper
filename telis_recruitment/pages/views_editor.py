"""Views for the website code editor"""
import json
import logging
import zipfile
import io
from pathlib import Path
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings

from .models import LandingPage, UploadedFile, FileVersion
from .services.editor_service import EditorService, EditorServiceError
from .services.version_service import VersionService, VersionServiceError
from .services.template_service import TemplateService, TemplateServiceError
from .services.upload_service import UploadService

logger = logging.getLogger(__name__)


# ===== Main Editor View =====

@staff_member_required
def website_editor(request, slug):
    """Main website code editor interface"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    # Get upload service for file tree
    upload_service = UploadService(page)
    file_tree = upload_service.get_file_tree()
    
    # Get file stats
    uploaded_files = UploadedFile.objects.filter(landing_page=page)
    total_files = uploaded_files.count()
    total_size = sum(f.file_size for f in uploaded_files)
    
    return render(request, 'pages/website_editor.html', {
        'page': page,
        'file_tree': file_tree,
        'total_files': total_files,
        'total_size': total_size,
        'entry_point': page.entry_point,
    })


# ===== File Operations =====

@staff_member_required
@require_GET
def get_file_content(request, slug):
    """Get file content for editing"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        file_path = request.GET.get('path')
        if not file_path:
            return JsonResponse({
                'success': False,
                'error': 'No file path provided'
            }, status=400)
        
        editor_service = EditorService(page)
        file_data = editor_service.get_file_content(file_path)
        
        # Add language info for Monaco
        language = editor_service.get_language_from_extension(file_path)
        file_data['language'] = language
        
        return JsonResponse({
            'success': True,
            'data': file_data
        })
    
    except EditorServiceError as e:
        logger.error(f"Error getting file content for {slug}/{file_path}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error getting file content for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error loading file'
        }, status=500)


@staff_member_required
@require_POST
def save_file_content(request, slug):
    """Save file content"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        file_path = data.get('path')
        content = data.get('content', '')
        create_version = data.get('create_version', True)
        version_note = data.get('version_note', '')
        
        if not file_path:
            return JsonResponse({
                'success': False,
                'error': 'No file path provided'
            }, status=400)
        
        # Save file
        editor_service = EditorService(page)
        result = editor_service.save_file_content(file_path, content)
        
        # Create version if requested
        if create_version:
            try:
                uploaded_file = UploadedFile.objects.get(
                    landing_page=page,
                    relative_path=file_path
                )
                version_service = VersionService(uploaded_file)
                
                # Check if we should create a version
                latest_version = version_service.get_versions(limit=1)
                should_create = True
                
                if latest_version:
                    old_content = latest_version[0].content
                    should_create = VersionService.should_create_version(
                        old_content, content
                    )
                
                if should_create:
                    version = version_service.create_version(
                        content=content,
                        user=request.user,
                        note=version_note
                    )
                    result['version'] = version.version
            except Exception as e:
                logger.warning(f"Could not create version: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'File saved successfully',
            'data': result
        })
    
    except EditorServiceError as e:
        logger.error(f"Error saving file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error saving file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error saving file'
        }, status=500)


@staff_member_required
@require_POST
def create_file(request, slug):
    """Create a new file"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        file_path = data.get('path')
        content = data.get('content', '')
        
        if not file_path:
            return JsonResponse({
                'success': False,
                'error': 'No file path provided'
            }, status=400)
        
        editor_service = EditorService(page)
        result = editor_service.create_file(file_path, content)
        
        return JsonResponse({
            'success': True,
            'message': 'File created successfully',
            'data': result
        })
    
    except EditorServiceError as e:
        logger.error(f"Error creating file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error creating file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error creating file'
        }, status=500)


@staff_member_required
@require_POST
def rename_file(request, slug):
    """Rename a file"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        old_path = data.get('old_path')
        new_path = data.get('new_path')
        
        if not old_path or not new_path:
            return JsonResponse({
                'success': False,
                'error': 'Both old_path and new_path are required'
            }, status=400)
        
        editor_service = EditorService(page)
        result = editor_service.rename_file(old_path, new_path)
        
        return JsonResponse({
            'success': True,
            'message': 'File renamed successfully',
            'data': result
        })
    
    except EditorServiceError as e:
        logger.error(f"Error renaming file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error renaming file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error renaming file'
        }, status=500)


@staff_member_required
@require_POST
def move_file(request, slug):
    """Move a file"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        old_path = data.get('old_path')
        new_path = data.get('new_path')
        
        if not old_path or not new_path:
            return JsonResponse({
                'success': False,
                'error': 'Both old_path and new_path are required'
            }, status=400)
        
        editor_service = EditorService(page)
        result = editor_service.move_file(old_path, new_path)
        
        return JsonResponse({
            'success': True,
            'message': 'File moved successfully',
            'data': result
        })
    
    except EditorServiceError as e:
        logger.error(f"Error moving file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error moving file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error moving file'
        }, status=500)


@staff_member_required
@require_POST
def duplicate_file(request, slug):
    """Duplicate a file"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        source_path = data.get('source_path')
        dest_path = data.get('dest_path')
        
        if not source_path or not dest_path:
            return JsonResponse({
                'success': False,
                'error': 'Both source_path and dest_path are required'
            }, status=400)
        
        editor_service = EditorService(page)
        result = editor_service.duplicate_file(source_path, dest_path)
        
        return JsonResponse({
            'success': True,
            'message': 'File duplicated successfully',
            'data': result
        })
    
    except EditorServiceError as e:
        logger.error(f"Error duplicating file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error duplicating file for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error duplicating file'
        }, status=500)


# ===== Folder Operations =====

@staff_member_required
@require_POST
def create_folder(request, slug):
    """Create a new folder"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        folder_path = data.get('path')
        
        if not folder_path:
            return JsonResponse({
                'success': False,
                'error': 'No folder path provided'
            }, status=400)
        
        editor_service = EditorService(page)
        result = editor_service.create_folder(folder_path)
        
        return JsonResponse({
            'success': True,
            'message': 'Folder created successfully',
            'data': result
        })
    
    except EditorServiceError as e:
        logger.error(f"Error creating folder for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error creating folder for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error creating folder'
        }, status=500)


@staff_member_required
@require_POST
def delete_folder(request, slug):
    """Delete a folder and all its contents"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        folder_path = data.get('path')
        
        if not folder_path:
            return JsonResponse({
                'success': False,
                'error': 'No folder path provided'
            }, status=400)
        
        editor_service = EditorService(page)
        result = editor_service.delete_folder(folder_path)
        
        return JsonResponse({
            'success': True,
            'message': f'Folder deleted (removed {result["files_deleted"]} files)',
            'data': result
        })
    
    except EditorServiceError as e:
        logger.error(f"Error deleting folder for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error deleting folder for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error deleting folder'
        }, status=500)


# ===== Search =====

@staff_member_required
@require_GET
def search_files(request, slug):
    """Search files by name or content"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        query = request.GET.get('query', '').strip()
        search_content = request.GET.get('search_content', 'true').lower() == 'true'
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'No search query provided'
            }, status=400)
        
        if len(query) < 2:
            return JsonResponse({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }, status=400)
        
        editor_service = EditorService(page)
        results = editor_service.search_files(query, search_content)
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })
    
    except EditorServiceError as e:
        logger.error(f"Error searching files for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error searching files for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error searching files'
        }, status=500)


# ===== Version Management =====

@staff_member_required
@require_GET
def file_versions(request, slug):
    """Get version history for a file"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        file_path = request.GET.get('path')
        if not file_path:
            return JsonResponse({
                'success': False,
                'error': 'No file path provided'
            }, status=400)
        
        # Get uploaded file
        uploaded_file = UploadedFile.objects.get(
            landing_page=page,
            relative_path=file_path
        )
        
        version_service = VersionService(uploaded_file)
        versions = version_service.get_versions(limit=50)
        
        versions_data = [{
            'version': v.version,
            'note': v.note,
            'created_at': v.created_at.isoformat(),
            'created_by': v.created_by.username if v.created_by else None
        } for v in versions]
        
        return JsonResponse({
            'success': True,
            'data': {
                'path': file_path,
                'versions': versions_data
            }
        })
    
    except UploadedFile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'File not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting versions for {slug}/{file_path}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error getting versions'
        }, status=500)


@staff_member_required
@require_POST
def restore_version(request, slug):
    """Restore a file to a specific version"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        file_path = data.get('path')
        version = data.get('version')
        
        if not file_path or version is None:
            return JsonResponse({
                'success': False,
                'error': 'Both path and version are required'
            }, status=400)
        
        # Get uploaded file
        uploaded_file = UploadedFile.objects.get(
            landing_page=page,
            relative_path=file_path
        )
        
        version_service = VersionService(uploaded_file)
        result = version_service.restore_version(int(version))
        
        # Save the restored content
        editor_service = EditorService(page)
        editor_service.save_file_content(file_path, result['content'])
        
        return JsonResponse({
            'success': True,
            'message': f'File restored to version {version}',
            'data': result
        })
    
    except UploadedFile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'File not found'
        }, status=404)
    except VersionServiceError as e:
        logger.error(f"Error restoring version for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error restoring version for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error restoring version'
        }, status=500)


# ===== Project Export/Import =====

@staff_member_required
@require_GET
def export_project(request, slug):
    """Export project as ZIP"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        # Get all files
        files = UploadedFile.objects.filter(landing_page=page)
        
        if not files.exists():
            return HttpResponse('No files to export', status=404)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            upload_base_path = Path(settings.MEDIA_ROOT) / 'landing_pages' / 'uploads'
            page_upload_path = upload_base_path / str(page.slug)
            
            for uploaded_file in files:
                file_path = page_upload_path / uploaded_file.relative_path
                
                if file_path.exists():
                    zip_file.write(file_path, uploaded_file.relative_path)
        
        # Return ZIP file
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{page.slug}.zip"'
        
        return response
    
    except Exception as e:
        logger.error(f"Error exporting project {slug}: {e}")
        return HttpResponse('Error exporting project', status=500)


@staff_member_required
@require_POST
def import_project(request, slug):
    """Import project from template"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        template_slug = data.get('template_slug')
        
        if not template_slug:
            return JsonResponse({
                'success': False,
                'error': 'No template slug provided'
            }, status=400)
        
        # Get and apply template
        template_service = TemplateService()
        template = template_service.get_template(template_slug)
        result = template_service.apply_template(template, page)
        
        return JsonResponse({
            'success': True,
            'message': f'Template "{template.name}" applied successfully',
            'data': result
        })
    
    except TemplateServiceError as e:
        logger.error(f"Error importing template for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error importing template for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error importing template'
        }, status=500)
