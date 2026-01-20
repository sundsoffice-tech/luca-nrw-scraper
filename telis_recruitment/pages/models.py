"""Models for the pages app - landing page builder with GrapesJS"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Project(models.Model):
    """Container für Multipage-Projekte (Spiele, Websites, Apps)"""
    
    TYPE_CHOICES = [
        ('website', 'Multi-Page Website'),
        ('game', 'Browser-Spiel'),
        ('app', 'Web-App'),
        ('landing', 'Landing Page Sammlung'),
    ]
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    project_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='website')
    description = models.TextField(blank=True)
    
    # Verzeichnis für statische Dateien (CSS, JS, Bilder)
    static_path = models.CharField(max_length=500, blank=True)
    
    # Hauptseite (index.html)
    main_page = models.ForeignKey(
        'LandingPage', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='main_for_project'
    )
    
    # Navigation/Sitemap als JSON
    navigation = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    is_deployed = models.BooleanField(default=False)
    deployed_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f"{self.name} ({self.get_project_type_display()})"
    
    def get_absolute_url(self):
        """URL for the project detail page"""
        return reverse('pages:project-detail', kwargs={'slug': self.slug})


class LandingPage(models.Model):
    """Main landing page model for no-code builder"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    slug = models.SlugField(max_length=255, unique=True, db_index=True,
                           help_text="URL slug for the page (e.g., 'home' for /p/home/)")
    title = models.CharField(max_length=255, help_text="Internal title for the page")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Project relation
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True, 
                                related_name='pages',
                                help_text="Parent project for multipage sites")
    
    # GrapesJS data
    html_json = models.JSONField(default=dict, blank=True,
                                 help_text="GrapesJS components JSON")
    html = models.TextField(blank=True, help_text="Rendered HTML from GrapesJS")
    css = models.TextField(blank=True, help_text="CSS from GrapesJS")
    
    # SEO fields
    seo_title = models.CharField(max_length=255, blank=True,
                                help_text="SEO page title")
    seo_description = models.TextField(blank=True,
                                       help_text="SEO meta description")
    seo_image = models.URLField(blank=True, help_text="SEO image URL")
    
    # Social Media / OpenGraph fields
    og_title = models.CharField(max_length=255, blank=True,
                               help_text="OpenGraph title (defaults to seo_title)")
    og_description = models.TextField(blank=True,
                                     help_text="OpenGraph description (defaults to seo_description)")
    og_image = models.URLField(blank=True,
                              help_text="OpenGraph image URL (defaults to seo_image)")
    og_type = models.CharField(max_length=50, default='website',
                              help_text="OpenGraph type (website, article, etc.)")
    
    # Twitter Card fields
    twitter_card = models.CharField(max_length=50, default='summary_large_image',
                                   help_text="Twitter card type")
    twitter_title = models.CharField(max_length=255, blank=True,
                                    help_text="Twitter card title (defaults to og_title)")
    twitter_description = models.TextField(blank=True,
                                          help_text="Twitter card description (defaults to og_description)")
    twitter_image = models.URLField(blank=True,
                                   help_text="Twitter card image (defaults to og_image)")
    
    # Share button settings
    enable_share_buttons = models.BooleanField(default=False,
                                              help_text="Enable social media share buttons on the page")
    share_button_position = models.CharField(max_length=20, default='bottom-right',
                                            choices=[
                                                ('top-left', 'Top Left'),
                                                ('top-right', 'Top Right'),
                                                ('bottom-left', 'Bottom Left'),
                                                ('bottom-right', 'Bottom Right'),
                                                ('inline', 'Inline in content'),
                                            ],
                                            help_text="Position of share buttons")
    share_platforms = models.JSONField(default=list, blank=True,
                                      help_text="List of enabled share platforms (e.g., ['facebook', 'twitter', 'whatsapp', 'linkedin'])")
    # Extended SEO fields
    seo_keywords = models.TextField(blank=True, help_text="SEO keywords (comma-separated)")
    canonical_url = models.URLField(blank=True, help_text="Canonical URL for this page")
    robots_meta = models.CharField(max_length=100, blank=True, default='index, follow',
                                   help_text="Robots meta tag (e.g., 'index, follow', 'noindex, nofollow')")
    
    # Twitter metadata extensions
    twitter_site = models.CharField(max_length=100, blank=True, help_text="Twitter @username for site")
    twitter_creator = models.CharField(max_length=100, blank=True, help_text="Twitter @username for creator")
    
    # Sitemap fields
    sitemap_priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.5,
                                          help_text="Sitemap priority (0.0 to 1.0)")
    sitemap_changefreq = models.CharField(max_length=20, blank=True, default='weekly',
                                         help_text="Sitemap change frequency")
    
    # Form integration
    form_settings = models.JSONField(default=dict, blank=True,
                                    help_text="Form configuration (fields, validation, etc.)")
    brevo_list_id = models.IntegerField(null=True, blank=True,
                                       help_text="Brevo list ID for form submissions")
    
    # Upload-based Website
    is_uploaded_site = models.BooleanField(default=False, 
                                           help_text="True if this is an uploaded website (ZIP/files)")
    uploaded_files_path = models.CharField(max_length=500, blank=True,
                                          help_text="Path to uploaded files directory")
    entry_point = models.CharField(max_length=255, default='index.html',
                                   help_text="Main entry file for uploaded site")
    
    # Domain Hosting
    HOSTING_TYPE_CHOICES = [
        ('internal', 'Internes Hosting'),
        ('strato', 'STRATO Domain'),
        ('custom', 'Benutzerdefinierte Domain'),
    ]
    
    hosting_type = models.CharField(max_length=20, choices=HOSTING_TYPE_CHOICES, default='internal')
    custom_domain = models.CharField(max_length=255, blank=True, db_index=True)
    strato_subdomain = models.CharField(max_length=100, blank=True)
    strato_main_domain = models.CharField(max_length=255, blank=True)
    ssl_enabled = models.BooleanField(default=True)
    dns_verified = models.BooleanField(default=False)
    dns_verification_token = models.CharField(max_length=64, blank=True)
    
    # Tracking
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_pages',
                                   on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name='updated_pages',
                                   on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Landing Page'
        verbose_name_plural = 'Landing Pages'
    
    def __str__(self):
        return f"{self.title} ({self.slug})"
    
    def save(self, *args, **kwargs):
        """Auto-set published_at timestamp"""
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == 'draft':
            self.published_at = None
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Public URL for the landing page"""
        return reverse('pages_public:page-public', kwargs={'slug': self.slug})
    
    def get_builder_url(self):
        """Builder URL for editing"""
        return reverse('pages:page-builder', kwargs={'slug': self.slug})
    
    def get_full_domain(self):
        """Returns the full domain URL for this page"""
        if self.hosting_type == 'strato' and self.strato_subdomain and self.strato_main_domain:
            return f"{self.strato_subdomain}.{self.strato_main_domain}"
        elif self.hosting_type == 'custom' and self.custom_domain:
            return self.custom_domain
        return None
    
    def get_og_title(self):
        """Get OpenGraph title with fallback to seo_title or page title"""
        return self.og_title or self.seo_title or self.title
    
    def get_og_description(self):
        """Get OpenGraph description with fallback to seo_description"""
        return self.og_description or self.seo_description or ''
    
    def get_og_image(self):
        """Get OpenGraph image with fallback to seo_image"""
        return self.og_image or self.seo_image or ''
    
    def get_twitter_title(self):
        """Get Twitter card title with fallback to og_title"""
        return self.twitter_title or self.get_og_title()
    
    def get_twitter_description(self):
        """Get Twitter card description with fallback to og_description"""
        return self.twitter_description or self.get_og_description()
    
    def get_twitter_image(self):
        """Get Twitter card image with fallback to og_image"""
        return self.twitter_image or self.get_og_image()
    
    def get_share_platforms(self):
        """Get enabled share platforms with defaults"""
        if self.share_platforms:
            return self.share_platforms
        return ['facebook', 'twitter', 'whatsapp', 'linkedin']


class PageVersion(models.Model):
    """Version history for undo/redo functionality"""
    
    landing_page = models.ForeignKey(LandingPage, related_name='versions',
                                     on_delete=models.CASCADE)
    version = models.IntegerField(help_text="Sequential version number")
    html_json = models.JSONField(default=dict)
    html = models.TextField(blank=True)
    css = models.TextField(blank=True)
    note = models.CharField(max_length=255, blank=True,
                          help_text="Optional note about this version")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version']
        verbose_name = 'Page Version'
        verbose_name_plural = 'Page Versions'
        unique_together = ['landing_page', 'version']
    
    def __str__(self):
        return f"{self.landing_page.title} - v{self.version}"


class PageComponent(models.Model):
    """Reusable components/blocks for landing pages"""
    
    CATEGORY_CHOICES = [
        ('hero', 'Hero Section'),
        ('form', 'Form'),
        ('stats', 'Statistics'),
        ('testimonial', 'Testimonial'),
        ('cta', 'Call to Action'),
        ('feature', 'Feature'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255, help_text="Component name")
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, help_text="Component description")
    
    # Component data
    html_snippet = models.TextField(help_text="HTML snippet for the component")
    css_snippet = models.TextField(blank=True, help_text="CSS for the component")
    data_json = models.JSONField(default=dict, blank=True,
                                help_text="GrapesJS component JSON")
    
    # Preview
    thumbnail_url = models.URLField(blank=True, help_text="Preview thumbnail URL")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Page Component'
        verbose_name_plural = 'Page Components'
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class PageSubmission(models.Model):
    """Form submissions from landing pages"""
    
    landing_page = models.ForeignKey(LandingPage, related_name='submissions',
                                     on_delete=models.CASCADE)
    lead = models.ForeignKey('leads.Lead', related_name='page_submissions',
                            on_delete=models.SET_NULL, null=True, blank=True,
                            help_text="Associated lead record")
    
    # Form data
    data = models.JSONField(default=dict, help_text="Submitted form data")
    
    # UTM tracking
    utm_source = models.CharField(max_length=255, blank=True)
    utm_medium = models.CharField(max_length=255, blank=True)
    utm_campaign = models.CharField(max_length=255, blank=True)
    utm_term = models.CharField(max_length=255, blank=True)
    utm_content = models.CharField(max_length=255, blank=True)
    
    # Technical tracking
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, max_length=500)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Page Submission'
        verbose_name_plural = 'Page Submissions'
    
    def __str__(self):
        return f"Submission for {self.landing_page.title} at {self.created_at}"


class UploadedFile(models.Model):
    """Individual files uploaded for a landing page"""
    
    landing_page = models.ForeignKey(LandingPage, related_name='uploaded_files',
                                     on_delete=models.CASCADE)
    file = models.FileField(upload_to='landing_pages/uploads/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    relative_path = models.CharField(max_length=500, 
                                    help_text="Path relative to site root (e.g., 'css/style.css')")
    file_type = models.CharField(max_length=50, blank=True,
                                help_text="MIME type or file extension")
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['relative_path']
        unique_together = ['landing_page', 'relative_path']
        verbose_name = 'Uploaded File'
        verbose_name_plural = 'Uploaded Files'
    
    def __str__(self):
        return f"{self.landing_page.slug}/{self.relative_path}"


class DomainConfiguration(models.Model):
    """STRATO/Custom domain configuration and DNS records"""
    
    landing_page = models.OneToOneField(LandingPage, related_name='domain_config',
                                        on_delete=models.CASCADE)
    strato_customer_id = models.CharField(max_length=100, blank=True)
    strato_api_key_encrypted = models.TextField(blank=True)
    required_a_record = models.GenericIPAddressField(null=True, blank=True)
    required_cname = models.CharField(max_length=255, blank=True)
    required_txt_record = models.TextField(blank=True)
    last_dns_check = models.DateTimeField(null=True, blank=True)
    dns_check_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Domain Configuration'
        verbose_name_plural = 'Domain Configurations'
    
    def __str__(self):
        return f"Domain Config for {self.landing_page.slug}"


class PageAsset(models.Model):
    """Bilder und Medien für Landing Pages"""
    ASSET_TYPES = [('image', 'Bild'), ('video', 'Video'), ('document', 'Dokument')]
    
    landing_page = models.ForeignKey(LandingPage, on_delete=models.CASCADE,
                                    related_name='assets', null=True, blank=True)
    file = models.FileField(upload_to='landing_pages/assets/%Y/%m/')
    name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default='image')
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    folder = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Page Asset'
        verbose_name_plural = 'Page Assets'
    
    def __str__(self):
        return f"{self.name} ({self.folder or 'root'})"
    
    @property
    def url(self):
        return self.file.url if self.file else ''


class BrandSettings(models.Model):
    """Globale Marken-Einstellungen"""
    # Colors
    primary_color = models.CharField(max_length=7, default='#6366f1')
    secondary_color = models.CharField(max_length=7, default='#06b6d4')
    accent_color = models.CharField(max_length=7, default='#22c55e')
    text_color = models.CharField(max_length=7, default='#1f2937')
    text_light_color = models.CharField(max_length=7, default='#6b7280')
    background_color = models.CharField(max_length=7, default='#ffffff')
    
    # Typography
    heading_font = models.CharField(max_length=100, default='Inter')
    body_font = models.CharField(max_length=100, default='Inter')
    
    # Logo
    logo = models.ImageField(upload_to='brand/', blank=True)
    logo_dark = models.ImageField(upload_to='brand/', blank=True)
    favicon = models.ImageField(upload_to='brand/', blank=True)
    
    # Company
    company_name = models.CharField(max_length=255, default='LUCA')
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    
    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Legal
    privacy_url = models.URLField(blank=True)
    imprint_url = models.URLField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Marken-Einstellungen'
    
    def save(self, *args, **kwargs):
        """
        Enforce singleton pattern by ensuring pk=1.
        Note: This is a simple singleton implementation suitable for single-server deployments.
        For high-concurrency or multi-server setups, consider using database-level constraints
        or distributed locking mechanisms.
        """
        self.pk = 1  # Singleton
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    def get_css_variables(self):
        return f""":root {{ 
    --color-primary: {self.primary_color}; 
    --color-secondary: {self.secondary_color}; 
    --color-accent: {self.accent_color}; 
    --color-text: {self.text_color}; 
    --color-text-light: {self.text_light_color}; 
    --color-background: {self.background_color};
}}"""
    
    def __str__(self):
        return f"Brand Settings (ID: {self.id})"



class PageTemplate(models.Model):
    """Vorgefertigte Seiten-Templates"""
    CATEGORIES = [
        ('landing', 'Landingpage'),
        ('contact', 'Kontaktseite'),
        ('sales', 'Verkaufsseite'),
        ('info', 'Infoseite'),
        ('lead_gen', 'Lead Generation'),
        ('product', 'Produktseite'),
        ('coming_soon', 'Coming Soon'),
        ('thank_you', 'Danke-Seite'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField(blank=True)
    html_json = models.JSONField(default=dict)
    html = models.TextField(blank=True)
    css = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='templates/thumbnails/', blank=True)
    
    # Layout-Konfiguration für flexible Anpassung
    layout_config = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Flexible Layout-Konfiguration (Sektionen, Einstellungen, Optionen)"
    )
    
    usage_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Page Template'
        verbose_name_plural = 'Page Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class FileVersion(models.Model):
    """Version history for uploaded files"""
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, 
                                     related_name='versions')
    content = models.TextField(help_text="File content at this version")
    version = models.PositiveIntegerField(help_text="Sequential version number")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.CharField(max_length=255, blank=True, 
                          help_text="Optional note about changes")
    
    class Meta:
        ordering = ['-version']
        unique_together = ['uploaded_file', 'version']
        verbose_name = 'File Version'
        verbose_name_plural = 'File Versions'
    
    def __str__(self):
        return f"{self.uploaded_file.relative_path} - v{self.version}"


class ProjectTemplate(models.Model):
    """Website project templates for quick start"""
    CATEGORY_CHOICES = [
        ('blank', 'Blank Template'),
        ('basic', 'Basic HTML'),
        ('bootstrap', 'Bootstrap'),
        ('tailwind', 'Tailwind CSS'),
        ('business', 'Business'),
        ('portfolio', 'Portfolio'),
        ('landing', 'Landing Page'),
        ('blog', 'Blog'),
        ('ecommerce', 'E-Commerce'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, help_text="Template name")
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(blank=True, help_text="Template description")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    thumbnail = models.ImageField(upload_to='templates/thumbnails/', blank=True,
                                 help_text="Preview thumbnail")
    files_data = models.JSONField(default=dict, 
                                 help_text="Serialized file structure and content")
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0, 
                                             help_text="Number of times used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Project Template'
        verbose_name_plural = 'Project Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


# ============================================================================
# UNIFIED VERSION CONTROL & UNDO/REDO SYSTEM
# ============================================================================
# These models provide a comprehensive version control system with:
# - Unified change tracking across all content types
# - Transaction grouping for multi-file changes
# - Undo/Redo stack management
# - Snapshot/tagging support for releases
# - Content integrity verification
# ============================================================================

import hashlib
import uuid


class ChangeLog(models.Model):
    """Unified change tracking for all content modifications
    
    This model provides a comprehensive audit trail and version control system
    that supports:
    - Transaction grouping (multiple changes in one logical operation)
    - Snapshots/tagging for releases
    - Comprehensive audit trail
    - Content integrity verification
    - Delta storage capability for efficiency
    """
    
    CHANGE_TYPE_CHOICES = [
        ('page_content', 'Page Content Change'),
        ('file_edit', 'File Edit'),
        ('file_create', 'File Create'),
        ('file_delete', 'File Delete'),
        ('file_rename', 'File Rename'),
        ('settings', 'Settings Change'),
        ('asset_upload', 'Asset Upload'),
        ('asset_delete', 'Asset Delete'),
    ]
    
    # Relations
    landing_page = models.ForeignKey(
        'LandingPage',
        on_delete=models.CASCADE,
        related_name='changelogs',
        help_text="Page this change belongs to"
    )
    
    # Transaction grouping
    transaction_id = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        help_text="Groups related changes together (e.g., multi-file save)"
    )
    
    # Change metadata
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    target_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="File path or component identifier affected by this change"
    )
    
    # Version tracking
    version = models.PositiveIntegerField(
        help_text="Sequential version number within this page"
    )
    parent_version = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Previous version (for branching support)"
    )
    
    # Content storage
    content_before = models.TextField(
        blank=True,
        help_text="Content before the change (for undo)"
    )
    content_after = models.TextField(
        blank=True,
        help_text="Content after the change"
    )
    content_delta = models.TextField(
        blank=True,
        help_text="Delta/diff for efficient storage (optional)"
    )
    content_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA256 hash of content_after for integrity verification"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (file type, component type, etc.)"
    )
    
    # User tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='changelogs'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Notes and tagging
    note = models.CharField(
        max_length=255,
        blank=True,
        help_text="User-provided note about this change"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorizing changes (e.g., ['release', 'v1.0'])"
    )
    
    # Snapshot/Release support
    is_snapshot = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark this version as a snapshot/release point"
    )
    snapshot_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name for this snapshot (e.g., 'Release 1.0', 'Backup before redesign')"
    )
    
    class Meta:
        ordering = ['-version']
        verbose_name = 'Change Log'
        verbose_name_plural = 'Change Logs'
        indexes = [
            models.Index(fields=['landing_page', '-version']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['landing_page', 'is_snapshot']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ['landing_page', 'version']
    
    def __str__(self):
        return f"{self.landing_page.slug} - v{self.version} ({self.get_change_type_display()})"
    
    def save(self, *args, **kwargs):
        """Auto-generate content hash on save"""
        if self.content_after and not self.content_hash:
            self.content_hash = hashlib.sha256(
                self.content_after.encode('utf-8')
            ).hexdigest()
        super().save(*args, **kwargs)
    
    def verify_integrity(self) -> bool:
        """Verify content integrity using hash"""
        if not self.content_hash or not self.content_after:
            return True  # No hash to verify
        
        computed_hash = hashlib.sha256(
            self.content_after.encode('utf-8')
        ).hexdigest()
        
        return computed_hash == self.content_hash
    
    def get_transaction_changes(self):
        """Get all changes in the same transaction"""
        return ChangeLog.objects.filter(
            transaction_id=self.transaction_id
        ).order_by('id')


class UndoRedoStack(models.Model):
    """Tracks undo/redo state for each user's editing session
    
    This enables proper undo/redo functionality with:
    - Per-user, per-page undo stacks
    - Redo support
    - Session-based state management
    """
    
    landing_page = models.ForeignKey(
        'LandingPage',
        on_delete=models.CASCADE,
        related_name='undo_stacks'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='undo_stacks'
    )
    session_key = models.CharField(
        max_length=255,
        help_text="Browser session identifier"
    )
    
    # Stack pointers
    current_version = models.PositiveIntegerField(
        help_text="Current position in the version history"
    )
    max_version = models.PositiveIntegerField(
        help_text="Highest version number (for redo boundary)"
    )
    
    # Stack state
    undo_stack = models.JSONField(
        default=list,
        help_text="List of transaction IDs that can be undone"
    )
    redo_stack = models.JSONField(
        default=list,
        help_text="List of transaction IDs that can be redone"
    )
    
    # Metadata
    last_action = models.CharField(
        max_length=20,
        choices=[('undo', 'Undo'), ('redo', 'Redo'), ('edit', 'Edit')],
        default='edit'
    )
    last_action_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Undo/Redo Stack'
        verbose_name_plural = 'Undo/Redo Stacks'
        unique_together = ['landing_page', 'user', 'session_key']
        indexes = [
            models.Index(fields=['landing_page', 'user', 'session_key']),
        ]
    
    def __str__(self):
        return f"{self.user.username} @ {self.landing_page.slug} (v{self.current_version})"
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0
    
    def push_transaction(self, transaction_id: str):
        """Push a new transaction onto the undo stack"""
        self.undo_stack.append(str(transaction_id))
        self.redo_stack = []  # Clear redo stack on new action
        self.last_action = 'edit'
        self.save()
    
    def undo(self) -> str | None:
        """Pop from undo stack, return transaction ID"""
        if not self.can_undo():
            return None
        
        transaction_id = self.undo_stack.pop()
        self.redo_stack.append(transaction_id)
        self.last_action = 'undo'
        self.save()
        return transaction_id
    
    def redo(self) -> str | None:
        """Pop from redo stack, return transaction ID"""
        if not self.can_redo():
            return None
        
        transaction_id = self.redo_stack.pop()
        self.undo_stack.append(transaction_id)
        self.last_action = 'redo'
        self.save()
        return transaction_id


class VersionSnapshot(models.Model):
    """Named snapshots/tags for version history
    
    Enables semantic versioning and release management:
    - Tag specific versions as releases
    - Create restore points before major changes
    - Compare between snapshots
    """
    
    SNAPSHOT_TYPE_CHOICES = [
        ('manual', 'Manual Snapshot'),
        ('auto', 'Automatic Snapshot'),
        ('release', 'Release'),
        ('backup', 'Backup'),
    ]
    
    landing_page = models.ForeignKey(
        'LandingPage',
        on_delete=models.CASCADE,
        related_name='snapshots'
    )
    
    # Snapshot metadata
    name = models.CharField(
        max_length=100,
        help_text="Snapshot name (e.g., 'v1.0.0', 'Pre-redesign backup')"
    )
    snapshot_type = models.CharField(
        max_length=20,
        choices=SNAPSHOT_TYPE_CHOICES,
        default='manual'
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of this snapshot"
    )
    
    # Version reference
    changelog_version = models.ForeignKey(
        ChangeLog,
        on_delete=models.CASCADE,
        related_name='snapshots',
        help_text="ChangeLog entry this snapshot references"
    )
    
    # Semantic versioning support
    semver_major = models.PositiveIntegerField(null=True, blank=True)
    semver_minor = models.PositiveIntegerField(null=True, blank=True)
    semver_patch = models.PositiveIntegerField(null=True, blank=True)
    semver_prerelease = models.CharField(max_length=50, blank=True)
    
    # Tags
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional tags for categorization"
    )
    
    # User tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Version Snapshot'
        verbose_name_plural = 'Version Snapshots'
        indexes = [
            models.Index(fields=['landing_page', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.landing_page.slug} - {self.name}"
    
    @property
    def semver(self) -> str:
        """Get semantic version string"""
        if all([
            self.semver_major is not None,
            self.semver_minor is not None,
            self.semver_patch is not None
        ]):
            version = f"{self.semver_major}.{self.semver_minor}.{self.semver_patch}"
            if self.semver_prerelease:
                version += f"-{self.semver_prerelease}"
            return version
        return ""


class ProjectNavigation(models.Model):
    """Navigationsstruktur für Multipage-Projekte"""
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='nav_items')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    title = models.CharField(max_length=100, help_text="Angezeigter Menütext")
    page = models.ForeignKey('LandingPage', on_delete=models.SET_NULL, null=True, blank=True)
    external_url = models.URLField(blank=True, help_text="Externe URL (überschreibt Seiten-Link)")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon-Klasse (z.B. 'fa-home')")
    
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Project Navigation'
        verbose_name_plural = 'Project Navigations'
    
    def __str__(self):
        return f"{self.project.name} - {self.title}"
    
    def get_url(self):
        if self.external_url:
            return self.external_url
        if self.page:
            return self.page.get_absolute_url()
        return '#'


class ProjectAsset(models.Model):
    """Gemeinsame Assets für ein Projekt (CSS, JS, Fonts)"""
    
    ASSET_TYPE_CHOICES = [
        ('css', 'Stylesheet'),
        ('js', 'JavaScript'),
        ('font', 'Font'),
        ('image', 'Bild'),
        ('other', 'Sonstiges'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='project_assets')
    file = models.FileField(upload_to='projects/assets/%Y/%m/')
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    relative_path = models.CharField(max_length=500)
    
    include_globally = models.BooleanField(default=False, help_text="In alle Projekt-Seiten einbinden")
    load_order = models.PositiveIntegerField(default=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['load_order', 'name']
        verbose_name = 'Project Asset'
        verbose_name_plural = 'Project Assets'
    
    def __str__(self):
        return f"{self.project.name} - {self.name} ({self.asset_type})"


class ProjectSettings(models.Model):
    """Projekt-spezifische Einstellungen"""
    
    project = models.OneToOneField('Project', on_delete=models.CASCADE, related_name='settings')
    
    # SEO Defaults
    default_seo_title_suffix = models.CharField(max_length=100, blank=True)
    default_seo_description = models.TextField(blank=True)
    default_seo_image = models.URLField(blank=True)
    
    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)
    custom_head_code = models.TextField(blank=True, help_text="Wird in <head> eingefügt")
    custom_body_code = models.TextField(blank=True, help_text="Wird vor </body> eingefügt")
    
    # Design
    primary_color = models.CharField(max_length=7, default='#3B82F6')
    secondary_color = models.CharField(max_length=7, default='#10B981')
    font_family = models.CharField(max_length=100, default='Inter, sans-serif')
    
    favicon = models.ImageField(upload_to='projects/favicons/', blank=True)
    custom_404_page = models.ForeignKey('LandingPage', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Project Settings'
        verbose_name_plural = 'Project Settings'
    
    def __str__(self):
        return f"Settings for {self.project.name}"
    
    def get_css_variables(self):
        return f""":root {{
    --project-primary: {self.primary_color};
    --project-secondary: {self.secondary_color};
    --project-font: {self.font_family};
}}"""


class ProjectDeployment(models.Model):
    """Deployment-Historie für Projekte"""
    
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('building', 'Wird erstellt'),
        ('deploying', 'Wird deployed'),
        ('success', 'Erfolgreich'),
        ('failed', 'Fehlgeschlagen'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='deployments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    version = models.CharField(max_length=50, blank=True)
    
    target_domain = models.CharField(max_length=255, blank=True)
    target_path = models.CharField(max_length=255, default='/')
    
    build_log = models.TextField(blank=True)
    deployed_files_count = models.PositiveIntegerField(default=0)
    deployed_size_bytes = models.PositiveBigIntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deployed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Project Deployment'
        verbose_name_plural = 'Project Deployments'
    
    def __str__(self):
        return f"{self.project.name} - {self.get_status_display()} ({self.started_at})"

