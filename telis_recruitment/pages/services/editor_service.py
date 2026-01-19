"""Editor service for code editing operations"""
import os
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.files.base import ContentFile
from ..models import LandingPage, UploadedFile


class EditorServiceError(Exception):
    """Custom exception for editor service errors"""
    pass


class EditorService:
    """Service for handling code editor operations"""
    
    # Text file extensions that can be edited
    EDITABLE_EXTENSIONS = {
        '.html', '.htm', '.css', '.js', '.json', '.txt', '.md',
        '.xml', '.svg', '.webmanifest', '.ts', '.jsx', '.tsx',
        '.py', '.php', '.rb', '.java', '.c', '.cpp', '.h',
        '.yaml', '.yml', '.toml', '.ini', '.conf', '.sh'
    }
    
    def __init__(self, landing_page: LandingPage):
        self.landing_page = landing_page
        self.upload_base_path = Path(settings.MEDIA_ROOT) / 'landing_pages' / 'uploads'
        self.page_upload_path = self.upload_base_path / str(landing_page.slug)
    
    def get_file_content(self, relative_path: str) -> Dict:
        """
        Get file content for editing
        
        Args:
            relative_path: Relative path of the file
            
        Returns:
            Dict with file content and metadata
            
        Raises:
            EditorServiceError: If file doesn't exist or can't be read
        """
        try:
            # Get UploadedFile record
            uploaded_file = UploadedFile.objects.get(
                landing_page=self.landing_page,
                relative_path=relative_path
            )
            
            # Get file path on disk
            file_path = self.page_upload_path / relative_path
            
            if not file_path.exists():
                raise EditorServiceError(f"File not found: {relative_path}")
            
            # Check if file is editable
            ext = file_path.suffix.lower()
            if ext not in self.EDITABLE_EXTENSIONS:
                raise EditorServiceError(f"File type '{ext}' is not editable")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return {
                'content': content,
                'path': relative_path,
                'size': uploaded_file.file_size,
                'type': uploaded_file.file_type,
                'extension': ext,
                'editable': True
            }
        
        except UploadedFile.DoesNotExist:
            raise EditorServiceError(f"File not found in database: {relative_path}")
        except Exception as e:
            raise EditorServiceError(f"Error reading file: {str(e)}")
    
    def save_file_content(self, relative_path: str, content: str) -> Dict:
        """
        Save file content
        
        Args:
            relative_path: Relative path of the file
            content: New file content
            
        Returns:
            Dict with success status
            
        Raises:
            EditorServiceError: If save fails
        """
        try:
            # Get or create UploadedFile record
            uploaded_file, created = UploadedFile.objects.get_or_create(
                landing_page=self.landing_page,
                relative_path=relative_path,
                defaults={
                    'original_filename': Path(relative_path).name,
                    'file_type': mimetypes.guess_type(relative_path)[0] or '',
                    'file_size': len(content.encode('utf-8'))
                }
            )
            
            # Get file path on disk
            file_path = self.page_upload_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update file size
            uploaded_file.file_size = len(content.encode('utf-8'))
            uploaded_file.save()
            
            return {
                'success': True,
                'path': relative_path,
                'size': uploaded_file.file_size
            }
        
        except Exception as e:
            raise EditorServiceError(f"Error saving file: {str(e)}")
    
    def create_file(self, relative_path: str, content: str = '') -> Dict:
        """
        Create a new file
        
        Args:
            relative_path: Relative path for the new file
            content: Initial content (default: empty)
            
        Returns:
            Dict with file info
            
        Raises:
            EditorServiceError: If creation fails
        """
        # Check if file already exists
        if UploadedFile.objects.filter(
            landing_page=self.landing_page,
            relative_path=relative_path
        ).exists():
            raise EditorServiceError(f"File already exists: {relative_path}")
        
        return self.save_file_content(relative_path, content)
    
    def rename_file(self, old_path: str, new_path: str) -> Dict:
        """
        Rename a file
        
        Args:
            old_path: Current relative path
            new_path: New relative path
            
        Returns:
            Dict with success status
            
        Raises:
            EditorServiceError: If rename fails
        """
        try:
            # Get UploadedFile record
            uploaded_file = UploadedFile.objects.get(
                landing_page=self.landing_page,
                relative_path=old_path
            )
            
            # Check if new path already exists
            if UploadedFile.objects.filter(
                landing_page=self.landing_page,
                relative_path=new_path
            ).exists():
                raise EditorServiceError(f"File already exists: {new_path}")
            
            # Rename file on disk
            old_file_path = self.page_upload_path / old_path
            new_file_path = self.page_upload_path / new_path
            
            if not old_file_path.exists():
                raise EditorServiceError(f"File not found: {old_path}")
            
            # Create parent directories if needed
            new_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rename file
            old_file_path.rename(new_file_path)
            
            # Update database record
            uploaded_file.relative_path = new_path
            uploaded_file.original_filename = Path(new_path).name
            uploaded_file.save()
            
            return {
                'success': True,
                'old_path': old_path,
                'new_path': new_path
            }
        
        except UploadedFile.DoesNotExist:
            raise EditorServiceError(f"File not found: {old_path}")
        except Exception as e:
            raise EditorServiceError(f"Error renaming file: {str(e)}")
    
    def move_file(self, old_path: str, new_path: str) -> Dict:
        """
        Move a file (same as rename)
        
        Args:
            old_path: Current relative path
            new_path: New relative path
            
        Returns:
            Dict with success status
        """
        return self.rename_file(old_path, new_path)
    
    def duplicate_file(self, source_path: str, dest_path: str) -> Dict:
        """
        Duplicate a file
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            
        Returns:
            Dict with success status
            
        Raises:
            EditorServiceError: If duplication fails
        """
        try:
            # Get source file content
            file_data = self.get_file_content(source_path)
            
            # Create new file with same content
            return self.create_file(dest_path, file_data['content'])
        
        except Exception as e:
            raise EditorServiceError(f"Error duplicating file: {str(e)}")
    
    def create_folder(self, folder_path: str) -> Dict:
        """
        Create a new folder
        
        Args:
            folder_path: Relative path for the new folder
            
        Returns:
            Dict with success status
        """
        try:
            # Create folder on disk
            full_path = self.page_upload_path / folder_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'path': folder_path
            }
        
        except Exception as e:
            raise EditorServiceError(f"Error creating folder: {str(e)}")
    
    def delete_folder(self, folder_path: str) -> Dict:
        """
        Delete a folder and all its contents
        
        Args:
            folder_path: Relative path of the folder
            
        Returns:
            Dict with success status
            
        Raises:
            EditorServiceError: If deletion fails
        """
        try:
            # Delete all files in folder from database
            files_to_delete = UploadedFile.objects.filter(
                landing_page=self.landing_page,
                relative_path__startswith=folder_path + '/'
            )
            
            # Delete from disk
            full_path = self.page_upload_path / folder_path
            if full_path.exists() and full_path.is_dir():
                import shutil
                shutil.rmtree(full_path)
            
            # Delete from database
            deleted_count = files_to_delete.count()
            files_to_delete.delete()
            
            return {
                'success': True,
                'path': folder_path,
                'files_deleted': deleted_count
            }
        
        except Exception as e:
            raise EditorServiceError(f"Error deleting folder: {str(e)}")
    
    def search_files(self, query: str, search_content: bool = True) -> List[Dict]:
        """
        Search for files by name or content
        
        Args:
            query: Search query
            search_content: Whether to search file contents (default: True)
            
        Returns:
            List of matching files with context
        """
        results = []
        
        try:
            # Search by filename
            files = UploadedFile.objects.filter(
                landing_page=self.landing_page,
                relative_path__icontains=query
            )
            
            for uploaded_file in files:
                results.append({
                    'path': uploaded_file.relative_path,
                    'match_type': 'filename',
                    'size': uploaded_file.file_size,
                    'type': uploaded_file.file_type
                })
            
            # Search file contents if requested
            if search_content:
                all_files = UploadedFile.objects.filter(landing_page=self.landing_page)
                
                for uploaded_file in all_files:
                    # Only search editable files
                    ext = Path(uploaded_file.relative_path).suffix.lower()
                    if ext not in self.EDITABLE_EXTENSIONS:
                        continue
                    
                    # Skip if already found by filename
                    if any(r['path'] == uploaded_file.relative_path for r in results):
                        continue
                    
                    try:
                        file_path = self.page_upload_path / uploaded_file.relative_path
                        if file_path.exists():
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    # Find context around match
                                    index = content.lower().find(query.lower())
                                    start = max(0, index - 50)
                                    end = min(len(content), index + len(query) + 50)
                                    context = content[start:end]
                                    
                                    results.append({
                                        'path': uploaded_file.relative_path,
                                        'match_type': 'content',
                                        'context': context,
                                        'size': uploaded_file.file_size,
                                        'type': uploaded_file.file_type
                                    })
                    except Exception:
                        # Skip files that can't be read
                        continue
            
            return results
        
        except Exception as e:
            raise EditorServiceError(f"Error searching files: {str(e)}")
    
    def get_language_from_extension(self, filename: str) -> str:
        """
        Get Monaco editor language ID from file extension
        
        Args:
            filename: Filename with extension
            
        Returns:
            Monaco language ID
        """
        ext = Path(filename).suffix.lower()
        
        language_map = {
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.json': 'json',
            '.md': 'markdown',
            '.xml': 'xml',
            '.svg': 'xml',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.py': 'python',
            '.php': 'php',
            '.rb': 'ruby',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.sh': 'shell',
            '.txt': 'plaintext',
        }
        
        return language_map.get(ext, 'plaintext')
