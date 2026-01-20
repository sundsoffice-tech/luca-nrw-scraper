"""Unified changelog service for version control and undo/redo functionality

This service provides a comprehensive version control system that:
- Tracks all content changes with transaction grouping
- Supports undo/redo operations
- Manages snapshots and releases
- Ensures content integrity
- Provides efficient diff storage
"""

import uuid
from typing import Dict, List, Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from ..models import ChangeLog, UndoRedoStack, VersionSnapshot, LandingPage


class ChangeLogServiceError(Exception):
    """Custom exception for changelog service errors"""
    pass


class ChangeLogService:
    """Service for managing unified changelog and version control"""
    
    MAX_VERSIONS_PER_PAGE = 100  # Keep last 100 versions per page
    MAX_UNDO_STACK_SIZE = 50  # Maximum undo stack size
    
    def __init__(self, landing_page: LandingPage):
        self.landing_page = landing_page
    
    @transaction.atomic
    def create_change(
        self,
        change_type: str,
        content_before: str = '',
        content_after: str = '',
        target_path: str = '',
        user: Optional[User] = None,
        note: str = '',
        tags: Optional[List[str]] = None,
        transaction_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict] = None
    ) -> ChangeLog:
        """
        Create a new change log entry
        
        Args:
            change_type: Type of change (from CHANGE_TYPE_CHOICES)
            content_before: Content before the change
            content_after: Content after the change
            target_path: Path to the affected file/component
            user: User making the change
            note: Optional note about the change
            tags: Optional tags for categorization
            transaction_id: Optional transaction ID for grouping changes
            metadata: Optional additional metadata
            
        Returns:
            ChangeLog instance
            
        Raises:
            ChangeLogServiceError: If change creation fails
        """
        try:
            # Get next version number
            max_version = ChangeLog.objects.filter(
                landing_page=self.landing_page
            ).aggregate(Max('version'))['version__max']
            
            next_version = (max_version or 0) + 1
            
            # Get or create transaction ID
            if transaction_id is None:
                transaction_id = uuid.uuid4()
            
            # Create changelog entry
            changelog = ChangeLog.objects.create(
                landing_page=self.landing_page,
                change_type=change_type,
                target_path=target_path,
                version=next_version,
                content_before=content_before,
                content_after=content_after,
                transaction_id=transaction_id,
                created_by=user,
                note=note,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Clean up old versions if exceeding limit
            self._cleanup_old_versions()
            
            return changelog
            
        except Exception as e:
            raise ChangeLogServiceError(f"Error creating change log: {str(e)}")
    
    @transaction.atomic
    def create_transaction(
        self,
        changes: List[Dict],
        user: Optional[User] = None,
        note: str = '',
        tags: Optional[List[str]] = None
    ) -> Tuple[uuid.UUID, List[ChangeLog]]:
        """
        Create multiple changes as a single transaction
        
        Args:
            changes: List of change dictionaries with keys:
                     {change_type, content_before, content_after, target_path, metadata}
            user: User making the changes
            note: Optional note for all changes in this transaction
            tags: Optional tags for all changes
            
        Returns:
            Tuple of (transaction_id, list of ChangeLog instances)
            
        Raises:
            ChangeLogServiceError: If transaction creation fails
        """
        transaction_id = uuid.uuid4()
        changelogs = []
        
        try:
            for change_data in changes:
                changelog = self.create_change(
                    change_type=change_data.get('change_type', 'file_edit'),
                    content_before=change_data.get('content_before', ''),
                    content_after=change_data.get('content_after', ''),
                    target_path=change_data.get('target_path', ''),
                    user=user,
                    note=note,
                    tags=tags,
                    transaction_id=transaction_id,
                    metadata=change_data.get('metadata')
                )
                changelogs.append(changelog)
            
            return transaction_id, changelogs
            
        except Exception as e:
            raise ChangeLogServiceError(f"Error creating transaction: {str(e)}")
    
    def get_version(self, version: int) -> Optional[ChangeLog]:
        """Get a specific version"""
        try:
            return ChangeLog.objects.get(
                landing_page=self.landing_page,
                version=version
            )
        except ChangeLog.DoesNotExist:
            return None
    
    def get_versions(self, limit: int = 20) -> List[ChangeLog]:
        """Get version history"""
        return ChangeLog.objects.filter(
            landing_page=self.landing_page
        ).select_related('created_by').order_by('-version')[:limit]
    
    def get_transaction_changes(self, transaction_id: uuid.UUID) -> List[ChangeLog]:
        """Get all changes in a transaction"""
        return ChangeLog.objects.filter(
            transaction_id=transaction_id
        ).order_by('id')
    
    @transaction.atomic
    def restore_version(self, version: int, user: Optional[User] = None) -> Dict:
        """
        Restore to a specific version
        
        Args:
            version: Version number to restore
            user: User performing the restore
            
        Returns:
            Dict with restored content and metadata
            
        Raises:
            ChangeLogServiceError: If restore fails
        """
        try:
            changelog = self.get_version(version)
            if not changelog:
                raise ChangeLogServiceError(f"Version {version} not found")
            
            # Verify content integrity
            if not changelog.verify_integrity():
                raise ChangeLogServiceError(
                    f"Content integrity check failed for version {version}"
                )
            
            # Create a new change entry for the restore operation
            restore_changelog = self.create_change(
                change_type=changelog.change_type,
                content_before='',  # Current content would go here
                content_after=changelog.content_after,
                target_path=changelog.target_path,
                user=user,
                note=f"Restored from version {version}",
                tags=['restore'],
                metadata={
                    'restored_from_version': version,
                    'original_transaction': str(changelog.transaction_id)
                }
            )
            
            return {
                'success': True,
                'content': changelog.content_after,
                'version': restore_changelog.version,
                'restored_from': version,
                'metadata': changelog.metadata
            }
            
        except Exception as e:
            raise ChangeLogServiceError(f"Error restoring version: {str(e)}")
    
    @transaction.atomic
    def create_snapshot(
        self,
        name: str,
        snapshot_type: str = 'manual',
        description: str = '',
        user: Optional[User] = None,
        tags: Optional[List[str]] = None,
        semver: Optional[Tuple[int, int, int, str]] = None
    ) -> VersionSnapshot:
        """
        Create a named snapshot of the current version
        
        Args:
            name: Snapshot name
            snapshot_type: Type of snapshot (manual/auto/release/backup)
            description: Detailed description
            user: User creating the snapshot
            tags: Optional tags
            semver: Optional semantic version (major, minor, patch, prerelease)
            
        Returns:
            VersionSnapshot instance
            
        Raises:
            ChangeLogServiceError: If snapshot creation fails
        """
        try:
            # Get current version
            latest_changelog = ChangeLog.objects.filter(
                landing_page=self.landing_page
            ).order_by('-version').first()
            
            if not latest_changelog:
                raise ChangeLogServiceError("No versions to snapshot")
            
            # Mark the changelog as a snapshot
            latest_changelog.is_snapshot = True
            latest_changelog.snapshot_name = name
            latest_changelog.save()
            
            # Create snapshot record
            snapshot_data = {
                'landing_page': self.landing_page,
                'name': name,
                'snapshot_type': snapshot_type,
                'description': description,
                'changelog_version': latest_changelog,
                'created_by': user,
                'tags': tags or []
            }
            
            # Add semantic versioning if provided
            if semver:
                snapshot_data['semver_major'] = semver[0]
                snapshot_data['semver_minor'] = semver[1]
                snapshot_data['semver_patch'] = semver[2]
                if len(semver) > 3:
                    snapshot_data['semver_prerelease'] = semver[3]
            
            snapshot = VersionSnapshot.objects.create(**snapshot_data)
            
            return snapshot
            
        except Exception as e:
            raise ChangeLogServiceError(f"Error creating snapshot: {str(e)}")
    
    def get_snapshots(self) -> List[VersionSnapshot]:
        """Get all snapshots for this page"""
        return VersionSnapshot.objects.filter(
            landing_page=self.landing_page
        ).select_related('changelog_version', 'created_by').order_by('-created_at')
    
    def _cleanup_old_versions(self):
        """Remove old versions exceeding the limit"""
        versions = ChangeLog.objects.filter(
            landing_page=self.landing_page,
            is_snapshot=False  # Don't delete snapshots
        ).order_by('-version')
        
        if versions.count() > self.MAX_VERSIONS_PER_PAGE:
            # Delete oldest non-snapshot versions
            versions_to_delete = versions[self.MAX_VERSIONS_PER_PAGE:]
            for version in versions_to_delete:
                version.delete()


class UndoRedoService:
    """Service for managing undo/redo operations"""
    
    def __init__(self, landing_page: LandingPage, user: User, session_key: str):
        self.landing_page = landing_page
        self.user = user
        self.session_key = session_key
        self._stack = None
    
    def get_or_create_stack(self) -> UndoRedoStack:
        """Get or create undo/redo stack for this session"""
        if self._stack is None:
            # Get latest version
            latest_version = ChangeLog.objects.filter(
                landing_page=self.landing_page
            ).aggregate(Max('version'))['version__max'] or 0
            
            self._stack, created = UndoRedoStack.objects.get_or_create(
                landing_page=self.landing_page,
                user=self.user,
                session_key=self.session_key,
                defaults={
                    'current_version': latest_version,
                    'max_version': latest_version,
                    'undo_stack': [],
                    'redo_stack': []
                }
            )
        return self._stack
    
    @transaction.atomic
    def push_transaction(self, transaction_id: uuid.UUID):
        """Push a new transaction onto the undo stack"""
        stack = self.get_or_create_stack()
        stack.push_transaction(transaction_id)
    
    @transaction.atomic
    def undo(self) -> Optional[Dict]:
        """
        Undo the last transaction
        
        Returns:
            Dict with undone changes or None if nothing to undo
        """
        stack = self.get_or_create_stack()
        transaction_id = stack.undo()
        
        if not transaction_id:
            return None
        
        # Get changes to undo
        changelog_service = ChangeLogService(self.landing_page)
        changes = changelog_service.get_transaction_changes(uuid.UUID(transaction_id))
        
        # Revert changes (apply content_before)
        reverted = []
        for change in changes:
            reverted.append({
                'target_path': change.target_path,
                'content': change.content_before,
                'change_type': change.change_type
            })
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'changes': reverted,
            'can_undo': stack.can_undo(),
            'can_redo': stack.can_redo()
        }
    
    @transaction.atomic
    def redo(self) -> Optional[Dict]:
        """
        Redo the last undone transaction
        
        Returns:
            Dict with redone changes or None if nothing to redo
        """
        stack = self.get_or_create_stack()
        transaction_id = stack.redo()
        
        if not transaction_id:
            return None
        
        # Get changes to redo
        changelog_service = ChangeLogService(self.landing_page)
        changes = changelog_service.get_transaction_changes(uuid.UUID(transaction_id))
        
        # Reapply changes (apply content_after)
        reapplied = []
        for change in changes:
            reapplied.append({
                'target_path': change.target_path,
                'content': change.content_after,
                'change_type': change.change_type
            })
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'changes': reapplied,
            'can_undo': stack.can_undo(),
            'can_redo': stack.can_redo()
        }
    
    def get_stack_state(self) -> Dict:
        """Get current undo/redo stack state"""
        stack = self.get_or_create_stack()
        
        return {
            'can_undo': stack.can_undo(),
            'can_redo': stack.can_redo(),
            'current_version': stack.current_version,
            'max_version': stack.max_version,
            'undo_count': len(stack.undo_stack),
            'redo_count': len(stack.redo_stack),
            'last_action': stack.last_action,
            'last_action_at': stack.last_action_at.isoformat()
        }
