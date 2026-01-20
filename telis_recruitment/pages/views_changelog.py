"""Views for changelog and undo/redo functionality"""
import json
import logging
import uuid
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction

from ..models import LandingPage, ChangeLog, VersionSnapshot
from ..services.changelog_service import (
    ChangeLogService,
    ChangeLogServiceError,
    UndoRedoService
)

logger = logging.getLogger(__name__)


# ===== Undo/Redo Endpoints =====

@staff_member_required
@require_POST
def undo(request, slug):
    """Undo the last change"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        session_key = request.session.session_key or request.POST.get('session_key', 'default')
        
        undo_redo_service = UndoRedoService(page, request.user, session_key)
        result = undo_redo_service.undo()
        
        if result is None:
            return JsonResponse({
                'success': False,
                'error': 'Nothing to undo'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Changes undone',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"Error undoing changes for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error undoing changes'
        }, status=500)


@staff_member_required
@require_POST
def redo(request, slug):
    """Redo the last undone change"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        session_key = request.session.session_key or request.POST.get('session_key', 'default')
        
        undo_redo_service = UndoRedoService(page, request.user, session_key)
        result = undo_redo_service.redo()
        
        if result is None:
            return JsonResponse({
                'success': False,
                'error': 'Nothing to redo'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Changes redone',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"Error redoing changes for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error redoing changes'
        }, status=500)


@staff_member_required
@require_GET
def undo_redo_state(request, slug):
    """Get current undo/redo stack state"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        session_key = request.session.session_key or request.GET.get('session_key', 'default')
        
        undo_redo_service = UndoRedoService(page, request.user, session_key)
        state = undo_redo_service.get_stack_state()
        
        return JsonResponse({
            'success': True,
            'data': state
        })
    
    except Exception as e:
        logger.error(f"Error getting undo/redo state for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error getting undo/redo state'
        }, status=500)


# ===== Changelog Endpoints =====

@staff_member_required
@require_GET
def changelog_history(request, slug):
    """Get changelog history for a page"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        limit = int(request.GET.get('limit', 20))
        limit = min(limit, 100)  # Cap at 100
        
        changelog_service = ChangeLogService(page)
        changelogs = changelog_service.get_versions(limit=limit)
        
        data = [{
            'version': c.version,
            'change_type': c.change_type,
            'target_path': c.target_path,
            'note': c.note,
            'tags': c.tags,
            'is_snapshot': c.is_snapshot,
            'snapshot_name': c.snapshot_name,
            'transaction_id': str(c.transaction_id),
            'created_by': c.created_by.username if c.created_by else None,
            'created_at': c.created_at.isoformat(),
            'metadata': c.metadata
        } for c in changelogs]
        
        return JsonResponse({
            'success': True,
            'data': {
                'changelogs': data,
                'count': len(data)
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting changelog history for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error getting changelog history'
        }, status=500)


@staff_member_required
@require_GET
def changelog_version(request, slug, version):
    """Get details for a specific version"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        changelog_service = ChangeLogService(page)
        changelog = changelog_service.get_version(int(version))
        
        if not changelog:
            return JsonResponse({
                'success': False,
                'error': f'Version {version} not found'
            }, status=404)
        
        # Get transaction changes
        transaction_changes = list(changelog.get_transaction_changes().values(
            'id', 'version', 'change_type', 'target_path', 'note', 'created_at'
        ))
        
        return JsonResponse({
            'success': True,
            'data': {
                'version': changelog.version,
                'change_type': changelog.change_type,
                'target_path': changelog.target_path,
                'content_before': changelog.content_before,
                'content_after': changelog.content_after,
                'note': changelog.note,
                'tags': changelog.tags,
                'is_snapshot': changelog.is_snapshot,
                'snapshot_name': changelog.snapshot_name,
                'transaction_id': str(changelog.transaction_id),
                'transaction_changes': transaction_changes,
                'created_by': changelog.created_by.username if changelog.created_by else None,
                'created_at': changelog.created_at.isoformat(),
                'metadata': changelog.metadata,
                'integrity_valid': changelog.verify_integrity()
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting version {version} for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error getting version details'
        }, status=500)


@staff_member_required
@require_POST
def changelog_restore(request, slug):
    """Restore to a specific version"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        version = data.get('version')
        
        if version is None:
            return JsonResponse({
                'success': False,
                'error': 'Version number required'
            }, status=400)
        
        changelog_service = ChangeLogService(page)
        result = changelog_service.restore_version(int(version), user=request.user)
        
        return JsonResponse({
            'success': True,
            'message': f'Restored to version {version}',
            'data': result
        })
    
    except ChangeLogServiceError as e:
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


# ===== Snapshot Endpoints =====

@staff_member_required
@require_POST
def create_snapshot(request, slug):
    """Create a named snapshot of the current version"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        data = json.loads(request.body)
        name = data.get('name')
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Snapshot name required'
            }, status=400)
        
        snapshot_type = data.get('snapshot_type', 'manual')
        description = data.get('description', '')
        tags = data.get('tags', [])
        
        # Parse semver if provided
        semver = None
        if 'semver' in data:
            sv = data['semver']
            semver = (
                sv.get('major', 0),
                sv.get('minor', 0),
                sv.get('patch', 0),
                sv.get('prerelease', '')
            )
        
        changelog_service = ChangeLogService(page)
        snapshot = changelog_service.create_snapshot(
            name=name,
            snapshot_type=snapshot_type,
            description=description,
            user=request.user,
            tags=tags,
            semver=semver
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Snapshot "{name}" created',
            'data': {
                'id': snapshot.id,
                'name': snapshot.name,
                'snapshot_type': snapshot.snapshot_type,
                'description': snapshot.description,
                'version': snapshot.changelog_version.version,
                'semver': snapshot.semver,
                'tags': snapshot.tags,
                'created_at': snapshot.created_at.isoformat()
            }
        })
    
    except ChangeLogServiceError as e:
        logger.error(f"Error creating snapshot for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error creating snapshot for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error creating snapshot'
        }, status=500)


@staff_member_required
@require_GET
def list_snapshots(request, slug):
    """List all snapshots for a page"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        changelog_service = ChangeLogService(page)
        snapshots = changelog_service.get_snapshots()
        
        data = [{
            'id': s.id,
            'name': s.name,
            'snapshot_type': s.snapshot_type,
            'description': s.description,
            'version': s.changelog_version.version,
            'semver': s.semver,
            'tags': s.tags,
            'created_by': s.created_by.username if s.created_by else None,
            'created_at': s.created_at.isoformat()
        } for s in snapshots]
        
        return JsonResponse({
            'success': True,
            'data': {
                'snapshots': data,
                'count': len(data)
            }
        })
    
    except Exception as e:
        logger.error(f"Error listing snapshots for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error listing snapshots'
        }, status=500)


@staff_member_required
@require_POST
def restore_snapshot(request, slug, snapshot_id):
    """Restore to a specific snapshot"""
    page = get_object_or_404(LandingPage, slug=slug)
    
    try:
        snapshot = get_object_or_404(VersionSnapshot, id=snapshot_id, landing_page=page)
        
        changelog_service = ChangeLogService(page)
        result = changelog_service.restore_version(
            snapshot.changelog_version.version,
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Restored to snapshot "{snapshot.name}"',
            'data': result
        })
    
    except ChangeLogServiceError as e:
        logger.error(f"Error restoring snapshot for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error restoring snapshot for {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error restoring snapshot'
        }, status=500)
