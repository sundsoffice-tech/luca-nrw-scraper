"""Upload service for handling ZIP and file uploads"""
import os
import zipfile
import shutil
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.core.files.uploadedfile import UploadedFile as DjangoUploadedFile
from django.conf import settings
from ..models import LandingPage, UploadedFile


# Maximum file sizes
MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100MB
MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES_IN_ZIP = 500

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    '.html', '.htm', '.css', '.js', '.json',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.pdf', '.txt', '.xml', '.webmanifest',
    '.mp4', '.webm', '.mp3', '.wav'
}

# Common entry point filenames
ENTRY_POINTS = ['index.html', 'index.htm', 'home.html', 'default.html']


class UploadServiceError(Exception):
    """Custom exception for upload service errors"""
    pass


class UploadService:
    """Service for handling file uploads for landing pages"""
    
    def __init__(self, landing_page: LandingPage):
        self.landing_page = landing_page
        self.upload_base_path = Path(settings.MEDIA_ROOT) / 'landing_pages' / 'uploads'
        self.page_upload_path = self.upload_base_path / str(landing_page.slug)
    
    def process_zip_upload(self, zip_file: DjangoUploadedFile) -> Dict:
        """
        Process ZIP file upload
        
        Args:
            zip_file: Django UploadedFile object
            
        Returns:
            Dict with success status and metadata
            
        Raises:
            UploadServiceError: If validation fails
        """
        # Validate ZIP file size
        if zip_file.size > MAX_ZIP_SIZE:
            raise UploadServiceError(f"ZIP file is too large. Maximum size is {MAX_ZIP_SIZE / (1024*1024):.0f}MB")
        
        # Create temporary directory for extraction
        temp_extract_path = self.page_upload_path / 'temp_extract'
        temp_extract_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Extract ZIP file
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Check for ZIP bomb
                total_uncompressed_size = sum(info.file_size for info in zip_ref.infolist())
                if total_uncompressed_size > MAX_ZIP_SIZE * 3:
                    raise UploadServiceError("ZIP file appears to be a ZIP bomb (too much uncompressed data)")
                
                # Check file count
                file_count = len([f for f in zip_ref.namelist() if not f.endswith('/')])
                if file_count > MAX_FILES_IN_ZIP:
                    raise UploadServiceError(f"Too many files in ZIP. Maximum is {MAX_FILES_IN_ZIP} files")
                
                # Extract all files
                zip_ref.extractall(temp_extract_path)
            
            # Find root directory in ZIP (handle single root folder case)
            root_dir = self._find_root_directory(temp_extract_path)
            
            # Process all files
            processed_files = []
            for file_path in root_dir.rglob('*'):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(root_dir))
                    
                    # Validate file
                    if not self._is_valid_file(file_path):
                        continue
                    
                    # Save file
                    uploaded_file = self._save_uploaded_file(file_path, relative_path)
                    processed_files.append(uploaded_file)
            
            # Auto-detect entry point
            entry_point = self._detect_entry_point(processed_files)
            if entry_point:
                self.landing_page.entry_point = entry_point
            
            # Mark as uploaded site
            self.landing_page.is_uploaded_site = True
            self.landing_page.uploaded_files_path = str(self.page_upload_path)
            self.landing_page.save()
            
            return {
                'success': True,
                'files_processed': len(processed_files),
                'entry_point': entry_point,
                'total_size': sum(f.file_size for f in processed_files)
            }
        
        finally:
            # Clean up temporary directory
            if temp_extract_path.exists():
                shutil.rmtree(temp_extract_path)
    
    def upload_single_file(self, file: DjangoUploadedFile, relative_path: str) -> UploadedFile:
        """
        Upload a single file
        
        Args:
            file: Django UploadedFile object
            relative_path: Relative path for the file (e.g., 'css/style.css')
            
        Returns:
            UploadedFile instance
            
        Raises:
            UploadServiceError: If validation fails
        """
        # Validate file size
        if file.size > MAX_SINGLE_FILE_SIZE:
            raise UploadServiceError(f"File is too large. Maximum size is {MAX_SINGLE_FILE_SIZE / (1024*1024):.0f}MB")
        
        # Sanitize path
        relative_path = self._sanitize_path(relative_path)
        
        # Validate file extension
        ext = os.path.splitext(relative_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UploadServiceError(f"File type '{ext}' is not allowed")
        
        # Create directory structure
        file_path = self.page_upload_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file to disk
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Get file type
        file_type = mimetypes.guess_type(relative_path)[0] or ext
        
        # Create or update UploadedFile record
        uploaded_file, created = UploadedFile.objects.update_or_create(
            landing_page=self.landing_page,
            relative_path=relative_path,
            defaults={
                'file': file,
                'original_filename': file.name,
                'file_type': file_type,
                'file_size': file.size,
            }
        )
        
        # Mark as uploaded site if not already
        if not self.landing_page.is_uploaded_site:
            self.landing_page.is_uploaded_site = True
            self.landing_page.uploaded_files_path = str(self.page_upload_path)
            self.landing_page.save()
        
        return uploaded_file
    
    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a single uploaded file
        
        Args:
            relative_path: Relative path of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Sanitize path
            relative_path = self._sanitize_path(relative_path)
            
            # Get UploadedFile record
            uploaded_file = UploadedFile.objects.get(
                landing_page=self.landing_page,
                relative_path=relative_path
            )
            
            # Delete file from disk
            file_path = self.page_upload_path / relative_path
            if file_path.exists():
                file_path.unlink()
            
            # Delete database record
            uploaded_file.delete()
            
            return True
        except UploadedFile.DoesNotExist:
            return False
    
    def get_file_tree(self) -> Dict:
        """
        Get file tree structure for all uploaded files
        
        Returns:
            Dict representing the file tree
        """
        files = UploadedFile.objects.filter(landing_page=self.landing_page)
        
        tree = {
            'name': self.landing_page.slug,
            'type': 'directory',
            'children': []
        }
        
        for uploaded_file in files:
            path_parts = uploaded_file.relative_path.split('/')
            current_level = tree
            
            for i, part in enumerate(path_parts):
                is_file = i == len(path_parts) - 1
                
                # Find or create node
                node = None
                for child in current_level.get('children', []):
                    if child['name'] == part:
                        node = child
                        break
                
                if not node:
                    node = {
                        'name': part,
                        'type': 'file' if is_file else 'directory',
                        'path': uploaded_file.relative_path if is_file else None,
                        'size': uploaded_file.file_size if is_file else None,
                        'file_type': uploaded_file.file_type if is_file else None,
                    }
                    
                    if not is_file:
                        node['children'] = []
                    
                    current_level['children'].append(node)
                
                if not is_file:
                    current_level = node
        
        return tree
    
    def _find_root_directory(self, extract_path: Path) -> Path:
        """
        Find the root directory of extracted files
        
        Some ZIPs have a single root folder, others have files at the top level
        """
        items = list(extract_path.iterdir())
        
        # If there's only one directory, use it as root
        if len(items) == 1 and items[0].is_dir():
            return items[0]
        
        # Otherwise, use the extract path itself
        return extract_path
    
    def _detect_entry_point(self, uploaded_files: List[UploadedFile]) -> Optional[str]:
        """Detect the entry point file (index.html, etc.)"""
        file_paths = [f.relative_path for f in uploaded_files]
        
        # Check for common entry points in root
        for entry_point in ENTRY_POINTS:
            if entry_point in file_paths:
                return entry_point
        
        # Check for entry points in subdirectories
        for entry_point in ENTRY_POINTS:
            matching = [p for p in file_paths if p.endswith(f'/{entry_point}')]
            if matching:
                return matching[0]
        
        # Default to first HTML file found
        html_files = [p for p in file_paths if p.endswith(('.html', '.htm'))]
        if html_files:
            return html_files[0]
        
        return None
    
    def _is_valid_file(self, file_path: Path) -> bool:
        """Check if file is valid for upload"""
        ext = file_path.suffix.lower()
        
        # Check extension
        if ext not in ALLOWED_EXTENSIONS:
            return False
        
        # Check file size
        if file_path.stat().st_size > MAX_SINGLE_FILE_SIZE:
            return False
        
        return True
    
    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize file path to prevent directory traversal
        
        Args:
            path: Input path
            
        Returns:
            Sanitized path
            
        Raises:
            UploadServiceError: If path is invalid
        """
        # Remove leading/trailing slashes and spaces
        path = path.strip().strip('/')
        
        # Check for directory traversal attempts
        if '..' in path or path.startswith('/'):
            raise UploadServiceError("Invalid file path: directory traversal not allowed")
        
        # Normalize path
        normalized = os.path.normpath(path)
        
        # Ensure normalized path doesn't start with .. or /
        if normalized.startswith('..') or normalized.startswith('/'):
            raise UploadServiceError("Invalid file path after normalization")
        
        return normalized
    
    def _save_uploaded_file(self, file_path: Path, relative_path: str) -> UploadedFile:
        """Save a file to the uploads directory and create database record"""
        # Get file info
        file_size = file_path.stat().st_size
        file_type = mimetypes.guess_type(str(file_path))[0] or file_path.suffix
        
        # Copy file to final location
        dest_path = self.page_upload_path / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_path)
        
        # Create or update database record
        uploaded_file, created = UploadedFile.objects.update_or_create(
            landing_page=self.landing_page,
            relative_path=relative_path,
            defaults={
                'original_filename': file_path.name,
                'file_type': file_type,
                'file_size': file_size,
            }
        )
        
        return uploaded_file
