"""ProjectBuilder service for building and exporting projects"""
import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from django.conf import settings
from django.utils.text import slugify
from ..models import Project, LandingPage, ProjectAsset, ProjectSettings, ProjectNavigation


class ProjectBuilderError(Exception):
    """Custom exception for project builder errors"""
    pass


class ProjectBuilder:
    """Baut ein Projekt zu einer statischen Website zusammen"""
    
    def __init__(self, project: Project):
        self.project = project
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.build_dir = Path(settings.MEDIA_ROOT) / 'builds' / f"{project.slug}-{timestamp}"
        self.errors = []
        self.warnings = []
        self.files_count = 0
        self.total_size = 0
    
    def build(self) -> Dict:
        """Hauptmethode: Baut das gesamte Projekt"""
        try:
            # Erstelle Build-Verzeichnis
            self.build_dir.mkdir(parents=True, exist_ok=True)
            
            # Kopiere alle Assets
            self._copy_assets()
            
            # Baue alle Seiten
            self._build_pages()
            
            # Generiere sitemap.xml
            self._generate_sitemap()
            
            # Generiere robots.txt
            self._generate_robots_txt()
            
            return {
                'success': True,
                'build_dir': str(self.build_dir),
                'files_count': self.files_count,
                'total_size': self.total_size,
                'errors': self.errors,
                'warnings': self.warnings,
            }
        except Exception as e:
            self.errors.append(str(e))
            return {
                'success': False,
                'errors': self.errors,
                'warnings': self.warnings,
            }
    
    def _copy_assets(self):
        """Kopiert alle globalen Assets ins Build-Verzeichnis"""
        assets = ProjectAsset.objects.filter(project=self.project)
        
        for asset in assets:
            if not asset.file:
                continue
            
            try:
                # Ziel-Pfad im Build-Verzeichnis
                target_path = self.build_dir / asset.relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Kopiere Datei
                source_path = Path(asset.file.path)
                if source_path.exists():
                    shutil.copy2(source_path, target_path)
                    self.files_count += 1
                    self.total_size += source_path.stat().st_size
                else:
                    self.warnings.append(f"Asset file not found: {asset.name}")
            except Exception as e:
                self.warnings.append(f"Failed to copy asset {asset.name}: {str(e)}")
    
    def _build_pages(self):
        """Baut alle published Pages des Projekts als HTML-Dateien"""
        pages = LandingPage.objects.filter(
            project=self.project,
            status='published'
        )
        
        if not pages.exists():
            self.warnings.append("No published pages found in project")
        
        # Hole Projekteinstellungen
        try:
            project_settings = self.project.settings
        except ProjectSettings.DoesNotExist:
            project_settings = None
            self.warnings.append("Project has no settings configured")
        
        # Hole Navigation
        navigation_items = ProjectNavigation.objects.filter(
            project=self.project,
            is_visible=True,
            parent=None  # Top-level items
        ).prefetch_related('children')
        
        for page in pages:
            try:
                self._build_single_page(page, project_settings, navigation_items)
            except Exception as e:
                self.errors.append(f"Failed to build page {page.slug}: {str(e)}")
    
    def _build_single_page(self, page: LandingPage, settings: Optional[ProjectSettings], 
                          navigation: List[ProjectNavigation]):
        """Baut eine einzelne Seite"""
        # Bestimme Dateiname
        if page == self.project.main_page:
            filename = 'index.html'
        else:
            filename = f"{page.slug}.html"
        
        # Hole Seiten-HTML
        html_content = page.html or ''
        
        # Erstelle vollständiges HTML-Dokument
        full_html = self._wrap_page_html(page, html_content, settings, navigation)
        
        # Schreibe Datei
        file_path = self.build_dir / filename
        file_path.write_text(full_html, encoding='utf-8')
        
        self.files_count += 1
        self.total_size += len(full_html.encode('utf-8'))
    
    def _wrap_page_html(self, page: LandingPage, content: str, 
                       settings: Optional[ProjectSettings], 
                       navigation: List[ProjectNavigation]) -> str:
        """Wrapped den Seiten-Content in ein vollständiges HTML-Dokument"""
        
        # SEO Title
        seo_title = page.seo_title or page.title
        if settings and settings.default_seo_title_suffix:
            seo_title += f" - {settings.default_seo_title_suffix}"
        
        # SEO Description
        seo_description = page.seo_description
        if not seo_description and settings:
            seo_description = settings.default_seo_description
        
        # SEO Image
        seo_image = page.seo_image
        if not seo_image and settings:
            seo_image = settings.default_seo_image
        
        # Custom CSS aus ProjectSettings
        custom_css = ''
        if settings:
            custom_css = settings.get_css_variables()
        
        # Baue Navigation HTML
        nav_html = self._build_navigation_html(navigation)
        
        # Analytics Code
        analytics_code = ''
        if settings:
            if settings.google_analytics_id:
                analytics_code += f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={settings.google_analytics_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{settings.google_analytics_id}');
</script>
"""
            
            if settings.facebook_pixel_id:
                analytics_code += f"""
<!-- Facebook Pixel -->
<script>
  !function(f,b,e,v,n,t,s)
  {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '{settings.facebook_pixel_id}');
  fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
  src="https://www.facebook.com/tr?id={settings.facebook_pixel_id}&ev=PageView&noscript=1"
/></noscript>
"""
        
        # Custom Head Code
        custom_head = ''
        if settings and settings.custom_head_code:
            custom_head = settings.custom_head_code
        
        # Custom Body Code
        custom_body = ''
        if settings and settings.custom_body_code:
            custom_body = settings.custom_body_code
        
        # Globale Assets (CSS/JS)
        global_assets_html = self._build_global_assets_html()
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{seo_title}</title>
    {f'<meta name="description" content="{seo_description}">' if seo_description else ''}
    {f'<meta property="og:image" content="{seo_image}">' if seo_image else ''}
    {f'<link rel="icon" href="{settings.favicon.url}">' if settings and settings.favicon else ''}
    
    <style>
    {page.css or ''}
    {custom_css}
    </style>
    
    {global_assets_html}
    {analytics_code}
    {custom_head}
</head>
<body>
    {nav_html}
    {content}
    {custom_body}
</body>
</html>"""
    
    def _build_navigation_html(self, nav_items: List[ProjectNavigation]) -> str:
        """Baut HTML für die Navigation"""
        if not nav_items:
            return ''
        
        html = '<nav class="project-navigation"><ul>'
        
        for item in nav_items:
            target = ' target="_blank"' if item.open_in_new_tab else ''
            icon = f'<i class="{item.icon}"></i> ' if item.icon else ''
            
            html += f'<li><a href="{item.get_url()}"{target}>{icon}{item.title}</a>'
            
            # Rekursiv Kinder rendern
            if item.children.exists():
                html += '<ul>'
                for child in item.children.filter(is_visible=True):
                    child_target = ' target="_blank"' if child.open_in_new_tab else ''
                    child_icon = f'<i class="{child.icon}"></i> ' if child.icon else ''
                    html += f'<li><a href="{child.get_url()}"{child_target}>{child_icon}{child.title}</a></li>'
                html += '</ul>'
            
            html += '</li>'
        
        html += '</ul></nav>'
        return html
    
    def _build_global_assets_html(self) -> str:
        """Baut HTML für globale CSS/JS Assets"""
        assets = ProjectAsset.objects.filter(
            project=self.project,
            include_globally=True
        ).order_by('load_order')
        
        html = ''
        for asset in assets:
            if asset.asset_type == 'css':
                html += f'<link rel="stylesheet" href="{asset.relative_path}">\n    '
            elif asset.asset_type == 'js':
                html += f'<script src="{asset.relative_path}"></script>\n    '
        
        return html
    
    def _generate_sitemap(self):
        """Generiert sitemap.xml"""
        pages = LandingPage.objects.filter(
            project=self.project,
            status='published'
        )
        
        base_url = self.project.deployed_url or 'https://example.com'
        
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for page in pages:
            if page == self.project.main_page:
                url = base_url
            else:
                url = f"{base_url}/{page.slug}.html"
            
            lastmod = page.updated_at.strftime('%Y-%m-%d')
            
            sitemap_content += f"""  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""
        
        sitemap_content += '</urlset>'
        
        sitemap_path = self.build_dir / 'sitemap.xml'
        sitemap_path.write_text(sitemap_content, encoding='utf-8')
        
        self.files_count += 1
        self.total_size += len(sitemap_content.encode('utf-8'))
    
    def _generate_robots_txt(self):
        """Generiert robots.txt"""
        base_url = self.project.deployed_url or 'https://example.com'
        
        robots_content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
        
        robots_path = self.build_dir / 'robots.txt'
        robots_path.write_text(robots_content, encoding='utf-8')
        
        self.files_count += 1
        self.total_size += len(robots_content.encode('utf-8'))
    
    def export_zip(self) -> Path:
        """Exportiert das Build als ZIP-Datei"""
        if not self.build_dir.exists():
            raise ProjectBuilderError("Build directory does not exist. Run build() first.")
        
        # Erstelle ZIP-Datei
        zip_filename = f"{self.project.slug}-export-{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = self.build_dir.parent / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.build_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def cleanup(self):
        """Räumt Build-Verzeichnis auf"""
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
