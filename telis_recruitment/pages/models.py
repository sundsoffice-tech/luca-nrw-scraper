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
