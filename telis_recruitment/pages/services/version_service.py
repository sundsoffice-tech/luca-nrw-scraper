"""Version service for file version management"""
from typing import Dict, List, Optional
from django.contrib.auth.models import User
from django.db.models import Max
from ..models import UploadedFile, FileVersion


class VersionServiceError(Exception):
    """Custom exception for version service errors"""
    pass


class VersionService:
    """Service for handling file version management"""
    
    MAX_VERSIONS_PER_FILE = 50  # Keep last 50 versions
    
    def __init__(self, uploaded_file: UploadedFile):
        self.uploaded_file = uploaded_file
    
    def create_version(self, content: str, user: Optional[User] = None, 
                      note: str = '') -> FileVersion:
        """
        Create a new version of the file
        
        Args:
            content: File content to save
            user: User creating the version
            note: Optional note about changes
            
        Returns:
            FileVersion instance
        """
        # Get next version number
        max_version = FileVersion.objects.filter(
            uploaded_file=self.uploaded_file
        ).aggregate(Max('version'))['version__max']
        
        next_version = (max_version or 0) + 1
        
        # Create version
        version = FileVersion.objects.create(
            uploaded_file=self.uploaded_file,
            content=content,
            version=next_version,
            created_by=user,
            note=note
        )
        
        # Clean up old versions if exceeding limit
        self._cleanup_old_versions()
        
        return version
    
    def get_versions(self, limit: int = 20) -> List[FileVersion]:
        """
        Get version history for the file
        
        Args:
            limit: Maximum number of versions to return
            
        Returns:
            List of FileVersion instances
        """
        return FileVersion.objects.filter(
            uploaded_file=self.uploaded_file
        ).order_by('-version')[:limit]
    
    def get_version(self, version: int) -> FileVersion:
        """
        Get a specific version
        
        Args:
            version: Version number
            
        Returns:
            FileVersion instance
            
        Raises:
            VersionServiceError: If version doesn't exist
        """
        try:
            return FileVersion.objects.get(
                uploaded_file=self.uploaded_file,
                version=version
            )
        except FileVersion.DoesNotExist:
            raise VersionServiceError(f"Version {version} not found")
    
    def restore_version(self, version: int) -> Dict:
        """
        Restore file to a specific version
        
        Args:
            version: Version number to restore
            
        Returns:
            Dict with restored content
            
        Raises:
            VersionServiceError: If restore fails
        """
        try:
            file_version = self.get_version(version)
            
            return {
                'success': True,
                'content': file_version.content,
                'version': file_version.version,
                'note': file_version.note,
                'created_at': file_version.created_at.isoformat()
            }
        except Exception as e:
            raise VersionServiceError(f"Error restoring version: {str(e)}")
    
    def get_diff(self, version1: int, version2: int) -> Dict:
        """
        Get diff between two versions
        
        Args:
            version1: First version number
            version2: Second version number
            
        Returns:
            Dict with diff information
            
        Raises:
            VersionServiceError: If versions don't exist
        """
        try:
            v1 = self.get_version(version1)
            v2 = self.get_version(version2)
            
            return {
                'version1': {
                    'number': v1.version,
                    'content': v1.content,
                    'created_at': v1.created_at.isoformat(),
                    'note': v1.note
                },
                'version2': {
                    'number': v2.version,
                    'content': v2.content,
                    'created_at': v2.created_at.isoformat(),
                    'note': v2.note
                }
            }
        except Exception as e:
            raise VersionServiceError(f"Error getting diff: {str(e)}")
    
    def _cleanup_old_versions(self):
        """Remove old versions exceeding the limit"""
        versions = FileVersion.objects.filter(
            uploaded_file=self.uploaded_file
        ).order_by('-version')
        
        if versions.count() > self.MAX_VERSIONS_PER_FILE:
            # Delete oldest versions
            versions_to_delete = versions[self.MAX_VERSIONS_PER_FILE:]
            for version in versions_to_delete:
                version.delete()
    
    @staticmethod
    def should_create_version(old_content: str, new_content: str) -> bool:
        """
        Determine if a new version should be created
        
        Args:
            old_content: Previous content
            new_content: New content
            
        Returns:
            True if version should be created
        """
        # Create version if content has changed
        if old_content != new_content:
            # Don't create version for trivial changes (only whitespace)
            if old_content.strip() != new_content.strip():
                return True
        
        return False
