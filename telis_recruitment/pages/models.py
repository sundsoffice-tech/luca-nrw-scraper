"""Models for the pages app - landing page builder with GrapesJS"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


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

