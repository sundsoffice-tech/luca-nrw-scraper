"""Template service for project template management"""
import json
from pathlib import Path
from typing import Dict, List
from django.conf import settings
from ..models import ProjectTemplate, LandingPage, UploadedFile


class TemplateServiceError(Exception):
    """Custom exception for template service errors"""
    pass


class TemplateService:
    """Service for handling project templates"""
    
    def __init__(self):
        self.templates_base_path = Path(settings.MEDIA_ROOT) / 'templates' / 'projects'
        self.templates_base_path.mkdir(parents=True, exist_ok=True)
    
    def get_template(self, slug: str) -> ProjectTemplate:
        """
        Get a template by slug
        
        Args:
            slug: Template slug
            
        Returns:
            ProjectTemplate instance
            
        Raises:
            TemplateServiceError: If template doesn't exist
        """
        try:
            return ProjectTemplate.objects.get(slug=slug, is_active=True)
        except ProjectTemplate.DoesNotExist:
            raise TemplateServiceError(f"Template not found: {slug}")
    
    def list_templates(self, category: str = None) -> List[ProjectTemplate]:
        """
        List available templates
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of ProjectTemplate instances
        """
        templates = ProjectTemplate.objects.filter(is_active=True)
        
        if category:
            templates = templates.filter(category=category)
        
        return templates.order_by('category', 'name')
    
    def apply_template(self, template: ProjectTemplate, 
                      landing_page: LandingPage) -> Dict:
        """
        Apply a template to a landing page
        
        Args:
            template: ProjectTemplate instance
            landing_page: LandingPage to apply template to
            
        Returns:
            Dict with result information
            
        Raises:
            TemplateServiceError: If application fails
        """
        try:
            from .upload_service import UploadService
            
            # Get files data from template
            files_data = template.files_data
            
            if not files_data:
                raise TemplateServiceError("Template has no files")
            
            # Create UploadService for the landing page
            upload_service = UploadService(landing_page)
            
            # Create files from template
            files_created = 0
            for file_path, file_content in files_data.items():
                try:
                    # Create file
                    upload_service.upload_single_file(
                        file=self._create_file_object(file_content),
                        relative_path=file_path
                    )
                    files_created += 1
                except Exception as e:
                    # Log error but continue
                    print(f"Error creating file {file_path}: {e}")
            
            # Mark as uploaded site
            landing_page.is_uploaded_site = True
            landing_page.save()
            
            # Increment usage count
            template.increment_usage()
            
            return {
                'success': True,
                'template': template.name,
                'files_created': files_created
            }
        
        except Exception as e:
            raise TemplateServiceError(f"Error applying template: {str(e)}")
    
    def create_template_from_page(self, landing_page: LandingPage,
                                 name: str, slug: str, 
                                 category: str = 'other',
                                 description: str = '') -> ProjectTemplate:
        """
        Create a template from an existing landing page
        
        Args:
            landing_page: LandingPage to create template from
            name: Template name
            slug: Template slug
            category: Template category
            description: Template description
            
        Returns:
            ProjectTemplate instance
            
        Raises:
            TemplateServiceError: If creation fails
        """
        try:
            # Get all files from the page
            files = UploadedFile.objects.filter(landing_page=landing_page)
            
            if not files.exists():
                raise TemplateServiceError("Page has no files to export")
            
            # Create files data dictionary
            files_data = {}
            
            upload_base_path = Path(settings.MEDIA_ROOT) / 'landing_pages' / 'uploads'
            page_upload_path = upload_base_path / str(landing_page.slug)
            
            for uploaded_file in files:
                file_path = page_upload_path / uploaded_file.relative_path
                
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            files_data[uploaded_file.relative_path] = content
                    except Exception:
                        # Skip binary files
                        continue
            
            # Create template
            template = ProjectTemplate.objects.create(
                name=name,
                slug=slug,
                category=category,
                description=description,
                files_data=files_data,
                is_active=True
            )
            
            return template
        
        except Exception as e:
            raise TemplateServiceError(f"Error creating template: {str(e)}")
    
    def _create_file_object(self, content: str):
        """Create a file-like object from content string"""
        from django.core.files.base import ContentFile
        return ContentFile(content.encode('utf-8'))
    
    @staticmethod
    def get_default_templates() -> List[Dict]:
        """
        Get default starter templates
        
        Returns:
            List of template definitions
        """
        return [
            {
                'name': 'Blank HTML',
                'slug': 'blank-html',
                'category': 'blank',
                'description': 'Empty HTML file to start from scratch',
                'files': {
                    'index.html': '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Page</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Hello World</h1>
    <script src="script.js"></script>
</body>
</html>''',
                    'style.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: system-ui, -apple-system, sans-serif;
    line-height: 1.6;
    color: #333;
}

h1 {
    padding: 2rem;
    text-align: center;
}''',
                    'script.js': '''// Your JavaScript code here
console.log('Page loaded');'''
                }
            },
            {
                'name': 'Bootstrap Starter',
                'slug': 'bootstrap-starter',
                'category': 'bootstrap',
                'description': 'Bootstrap 5 starter template',
                'files': {
                    'index.html': '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bootstrap Starter</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="#">Brand</a>
        </div>
    </nav>
    
    <div class="container mt-5">
        <h1>Bootstrap Starter</h1>
        <p class="lead">Get started with Bootstrap 5</p>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
                }
            },
            {
                'name': 'Tailwind Starter',
                'slug': 'tailwind-starter',
                'category': 'tailwind',
                'description': 'Tailwind CSS starter template',
                'files': {
                    'index.html': '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tailwind Starter</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg">
        <div class="container mx-auto px-6 py-4">
            <h1 class="text-2xl font-bold">Brand</h1>
        </div>
    </nav>
    
    <div class="container mx-auto px-6 py-8">
        <h1 class="text-4xl font-bold text-gray-800">Tailwind Starter</h1>
        <p class="text-xl text-gray-600 mt-4">Get started with Tailwind CSS</p>
    </div>
</body>
</html>'''
                }
            }
        ]
