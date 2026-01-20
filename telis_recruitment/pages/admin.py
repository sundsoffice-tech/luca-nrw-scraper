"""Admin interface for pages app"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline
from . import models
from .models import (
    Project, LandingPage, PageVersion, PageComponent, PageSubmission, 
    UploadedFile, DomainConfiguration, PageAsset, BrandSettings, PageTemplate,
    FileVersion, ProjectTemplate, ChangeLog, UndoRedoStack, VersionSnapshot
)


class PageVersionInline(TabularInline):
    """Inline display of page versions"""
    model = PageVersion
    extra = 0
    can_delete = False
    readonly_fields = ['version', 'created_by', 'created_at', 'note']
    fields = ['version', 'note', 'created_by', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LandingPage)
class LandingPageAdmin(ModelAdmin):
    """Admin interface for landing pages"""
    
    list_display = ['title', 'slug', 'status_badge', 'hosting_badge', 'published_at', 'builder_link', 'upload_link', 'domain_link', 'preview_link', 'created_at']
    list_filter = ['status', 'hosting_type', 'is_uploaded_site', 'created_at', 'published_at']
    search_fields = ['title', 'slug', 'seo_title', 'custom_domain']
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'slug', 'status']
        }),
        ('Upload Settings', {
            'fields': ['is_uploaded_site', 'uploaded_files_path', 'entry_point'],
            'classes': ['collapse'],
        }),
        ('Domain Settings', {
            'fields': ['hosting_type', 'custom_domain', 'strato_subdomain', 'strato_main_domain', 
                      'ssl_enabled', 'dns_verified', 'dns_verification_token'],
            'classes': ['collapse'],
        }),
        ('Content (Managed via Builder)', {
            'fields': ['html_json', 'html', 'css'],
            'classes': ['collapse'],
        }),
        ('SEO Settings', {
            'fields': ['seo_title', 'seo_description', 'seo_keywords', 'seo_image', 'canonical_url', 'robots_meta'],
        }),
        ('Open Graph / Social Media', {
            'fields': ['og_title', 'og_description', 'og_image', 'og_type'],
            'classes': ['collapse'],
        }),
        ('Twitter Card', {
            'fields': ['twitter_card', 'twitter_site', 'twitter_creator'],
            'classes': ['collapse'],
        }),
        ('Sitemap Settings', {
            'fields': ['sitemap_priority', 'sitemap_changefreq'],
            'classes': ['collapse'],
        }),
        ('Form Integration', {
            'fields': ['form_settings', 'brevo_list_id'],
            'classes': ['collapse'],
        }),
        ('Metadata', {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at', 'published_at'],
            'classes': ['collapse'],
        }),
    ]
    
    inlines = [PageVersionInline]
    actions = ['publish_pages', 'unpublish_pages', 'duplicate_page']
    
    def status_badge(self, obj):
        """Show status as colored badge"""
        if obj.status == 'published':
            return format_html(
                '<span style="background-color: #22c55e; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 500;">Published</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">Draft</span>'
        )
    status_badge.short_description = 'Status'
    
    def hosting_badge(self, obj):
        """Show hosting type as badge"""
        colors = {
            'internal': '#6b7280',
            'strato': '#3b82f6',
            'custom': '#8b5cf6',
        }
        color = colors.get(obj.hosting_type, '#6b7280')
        
        label = obj.get_hosting_type_display()
        if obj.is_uploaded_site:
            label += ' 📦'
        if obj.dns_verified:
            label += ' ✓'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, label
        )
    hosting_badge.short_description = 'Hosting'
    
    def builder_link(self, obj):
        """Link to builder interface"""
        url = reverse('pages:page-builder', kwargs={'slug': obj.slug})
        return format_html('<a href="{}" target="_blank">Edit in Builder</a>', url)
    builder_link.short_description = 'Builder'
    
    def upload_link(self, obj):
        """Link to upload manager"""
        url = reverse('pages:upload-manager', kwargs={'slug': obj.slug})
        return format_html('<a href="{}" target="_blank">Upload Manager</a>', url)
    upload_link.short_description = 'Upload'
    
    def domain_link(self, obj):
        """Link to domain settings"""
        url = reverse('pages:domain-settings', kwargs={'slug': obj.slug})
        return format_html('<a href="{}" target="_blank">Domain Settings</a>', url)
    domain_link.short_description = 'Domain'
    
    def preview_link(self, obj):
        """Link to preview page at /p/"""
        if obj.status == 'published':
            url = f'/p/{obj.slug}/'
            return format_html('<a href="{}" target="_blank">View Live</a>', url)
        return format_html('<span style="color: gray;">Draft only</span>')
    preview_link.short_description = 'Preview'
    
    def publish_pages(self, request, queryset):
        """Publish selected pages"""
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} page(s) successfully published.')
    publish_pages.short_description = 'Publish selected pages'
    
    def unpublish_pages(self, request, queryset):
        """Unpublish selected pages"""
        updated = queryset.update(status='draft', published_at=None)
        self.message_user(request, f'{updated} page(s) unpublished.')
    unpublish_pages.short_description = 'Unpublish selected pages'
    
    def duplicate_page(self, request, queryset):
        """Duplicate selected pages"""
        for page in queryset:
            page.pk = None
            page.slug = f"{page.slug}-copy"
            page.title = f"{page.title} (Copy)"
            page.status = 'draft'
            page.published_at = None
            page.save()
        self.message_user(request, f'{queryset.count()} page(s) duplicated.')
    duplicate_page.short_description = 'Duplicate selected pages'
    
    def save_model(self, request, obj, form, change):
        """Track who created/updated the page"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PageVersion)
class PageVersionAdmin(ModelAdmin):
    """Admin interface for page versions"""
    
    list_display = ['landing_page', 'version', 'created_by', 'created_at', 'note']
    list_filter = ['landing_page', 'created_at']
    search_fields = ['landing_page__title', 'note']
    readonly_fields = ['landing_page', 'version', 'html_json', 'html', 'css', 'created_by', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PageComponent)
class PageComponentAdmin(ModelAdmin):
    """Admin interface for reusable page components"""
    
    list_display = ['name', 'category', 'slug', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    
    fieldsets = [
        ('Component Information', {
            'fields': ['name', 'slug', 'category', 'description', 'is_active']
        }),
        ('Content', {
            'fields': ['html_snippet', 'css_snippet', 'data_json']
        }),
        ('Preview', {
            'fields': ['thumbnail_url'],
        }),
    ]


@admin.register(PageSubmission)
class PageSubmissionAdmin(ModelAdmin):
    """Admin interface for page submissions"""
    
    list_display = ['landing_page', 'lead_link', 'created_at', 'utm_source', 'utm_campaign', 'client_ip']
    list_filter = ['landing_page', 'created_at', 'utm_source', 'utm_medium', 'utm_campaign']
    search_fields = ['landing_page__title', 'data', 'client_ip']
    readonly_fields = ['landing_page', 'lead', 'data', 'utm_source', 'utm_medium', 
                      'utm_campaign', 'utm_term', 'utm_content', 'client_ip', 
                      'user_agent', 'referrer', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Submission Information', {
            'fields': ['landing_page', 'lead', 'data', 'created_at']
        }),
        ('UTM Tracking', {
            'fields': ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
        }),
        ('Technical Information', {
            'fields': ['client_ip', 'user_agent', 'referrer'],
            'classes': ['collapse'],
        }),
    ]
    
    def lead_link(self, obj):
        """Link to associated lead"""
        if obj.lead:
            url = reverse('admin:leads_lead_change', args=[obj.lead.pk])
            return format_html('<a href="{}">{}</a>', url, obj.lead.name)
        return '-'
    lead_link.short_description = 'Lead'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UploadedFile)
class UploadedFileAdmin(ModelAdmin):
    """Admin interface for uploaded files"""
    
    list_display = ['landing_page', 'relative_path', 'file_type', 'file_size_display', 'created_at']
    list_filter = ['landing_page', 'file_type', 'created_at']
    search_fields = ['landing_page__title', 'relative_path', 'original_filename']
    readonly_fields = ['landing_page', 'file', 'original_filename', 'relative_path', 
                      'file_type', 'file_size', 'created_at', 'updated_at']
    
    fieldsets = [
        ('File Information', {
            'fields': ['landing_page', 'relative_path', 'original_filename']
        }),
        ('File Details', {
            'fields': ['file', 'file_type', 'file_size']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'Size'
    
    def has_add_permission(self, request):
        return False


@admin.register(DomainConfiguration)
class DomainConfigurationAdmin(ModelAdmin):
    """Admin interface for domain configurations"""
    
    list_display = ['landing_page', 'dns_status', 'last_dns_check', 'created_at']
    list_filter = ['last_dns_check', 'created_at']
    search_fields = ['landing_page__title', 'landing_page__custom_domain', 
                    'landing_page__strato_subdomain', 'landing_page__strato_main_domain']
    readonly_fields = ['landing_page', 'last_dns_check', 'dns_check_result', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Landing Page', {
            'fields': ['landing_page']
        }),
        ('STRATO Configuration', {
            'fields': ['strato_customer_id', 'strato_api_key_encrypted'],
            'classes': ['collapse'],
        }),
        ('DNS Records', {
            'fields': ['required_a_record', 'required_cname', 'required_txt_record']
        }),
        ('Verification', {
            'fields': ['last_dns_check', 'dns_check_result']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    def dns_status(self, obj):
        """Show DNS verification status"""
        if obj.landing_page.dns_verified:
            return format_html(
                '<span style="color: #22c55e; font-weight: 500;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: #f59e0b; font-weight: 500;">⏳ Pending</span>'
        )
    dns_status.short_description = 'DNS Status'
    
    def has_add_permission(self, request):
        return False


@admin.register(PageAsset)
class PageAssetAdmin(ModelAdmin):
    """Admin interface for page assets"""
    
    list_display = ['name', 'asset_type', 'landing_page', 'file_size_display', 'uploaded_by', 'created_at']
    list_filter = ['asset_type', 'folder', 'created_at', 'uploaded_by']
    search_fields = ['name', 'alt_text', 'folder']
    readonly_fields = ['file_size', 'width', 'height', 'created_at', 'uploaded_by']
    
    fieldsets = [
        ('File Information', {
            'fields': ['landing_page', 'file', 'name', 'asset_type', 'folder', 'alt_text']
        }),
        ('Metadata', {
            'fields': ['mime_type', 'file_size', 'width', 'height']
        }),
        ('Upload Information', {
            'fields': ['uploaded_by', 'created_at']
        }),
    ]
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'Size'
    
    def save_model(self, request, obj, form, change):
        """Track uploader"""
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BrandSettings)
class BrandSettingsAdmin(ModelAdmin):
    """Admin interface for brand settings"""
    
    list_display = ['__str__', 'company_name', 'primary_color', 'heading_font', 'body_font']
    
    fieldsets = [
        ('Farben', {
            'fields': ['primary_color', 'secondary_color', 'accent_color', 'text_color', 'background_color']
        }),
        ('Typography', {
            'fields': ['heading_font', 'body_font']
        }),
        ('Logo', {
            'fields': ['logo', 'logo_dark', 'favicon']
        }),
        ('Unternehmen', {
            'fields': ['company_name', 'contact_email', 'contact_phone']
        }),
        ('Social', {
            'fields': ['facebook_url', 'instagram_url', 'linkedin_url']
        }),
        ('Legal', {
            'fields': ['privacy_url', 'imprint_url']
        }),
    ]
    
    def has_add_permission(self, request):
        """Only allow one brand settings instance"""
        return not BrandSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of brand settings"""
        return False


@admin.register(PageTemplate)
class PageTemplateAdmin(ModelAdmin):
    """Admin interface for page templates"""
    
    list_display = ['name', 'category_badge', 'usage_count', 'is_active', 'created_at', 'preview_thumbnail']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['usage_count', 'created_at']
    
    fieldsets = [
        ('Template Information', {
            'fields': ['name', 'slug', 'category', 'description', 'is_active', 'thumbnail']
        }),
        ('Layout Configuration', {
            'fields': ['layout_config'],
            'description': 'Flexible Layout-Konfiguration (Sektionen, Einstellungen, Optionen)'
        }),
        ('Content', {
            'fields': ['html_json', 'html', 'css']
        }),
        ('Statistics', {
            'fields': ['usage_count', 'created_at']
        }),
    ]
    
    def category_badge(self, obj):
        """Show category as colored badge"""
        colors = {
            'landing': '#667eea',
            'contact': '#22c55e',
            'sales': '#f5576c',
            'info': '#3b82f6',
            'lead_gen': '#8b5cf6',
            'product': '#f59e0b',
            'coming_soon': '#6b7280',
            'thank_you': '#10b981',
        }
        color = colors.get(obj.category, '#6b7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def preview_thumbnail(self, obj):
        """Display thumbnail preview"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 60px;" />',
                obj.thumbnail.url
            )
        return '-'
    preview_thumbnail.short_description = 'Preview'


class FileVersionInlineForUploadedFile(TabularInline):
    """Inline display of file versions"""
    model = FileVersion
    extra = 0
    can_delete = False
    readonly_fields = ['version', 'created_by', 'created_at', 'note']
    fields = ['version', 'note', 'created_by', 'created_at']
    ordering = ['-version']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FileVersion)
class FileVersionAdmin(ModelAdmin):
    """Admin interface for file versions"""
    
    list_display = ['uploaded_file', 'version', 'created_by', 'created_at', 'note']
    list_filter = ['created_at', 'created_by']
    search_fields = ['uploaded_file__relative_path', 'note']
    readonly_fields = ['uploaded_file', 'version', 'content', 'created_at', 'created_by']
    
    fieldsets = [
        ('Version Information', {
            'fields': ['uploaded_file', 'version', 'note']
        }),
        ('Content', {
            'fields': ['content'],
            'classes': ['collapse'],
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at']
        }),
    ]
    
    def has_add_permission(self, request):
        """Versions are created automatically"""
        return False


@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(ModelAdmin):
    """Admin interface for project templates"""
    
    list_display = ['name', 'category', 'usage_count', 'is_active', 'created_at', 'preview_thumbnail']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Template Information', {
            'fields': ['name', 'slug', 'category', 'description', 'is_active', 'thumbnail']
        }),
        ('Files Data', {
            'fields': ['files_data'],
            'description': 'JSON structure containing all template files and their contents'
        }),
        ('Statistics', {
            'fields': ['usage_count', 'created_at', 'updated_at']
        }),
    ]
    
    def preview_thumbnail(self, obj):
        """Display thumbnail preview"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 60px;" />',
                obj.thumbnail.url
            )
        return '-'
    preview_thumbnail.short_description = 'Preview'


class LandingPageInlineForProject(TabularInline):
    """Inline display of landing pages for a project"""
    model = LandingPage
    extra = 0
    can_delete = False
    readonly_fields = ['slug', 'title', 'status', 'created_at']
    fields = ['slug', 'title', 'status', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    """Admin interface for projects"""
    
    list_display = ['name', 'slug', 'project_type', 'page_count', 'created_by', 'created_at', 'detail_link']
    list_filter = ['project_type', 'is_deployed', 'created_at', 'created_by']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Project Information', {
            'fields': ['name', 'slug', 'project_type', 'description']
        }),
        ('Configuration', {
            'fields': ['static_path', 'main_page', 'navigation']
        }),
        ('Deployment', {
            'fields': ['is_deployed', 'deployed_url'],
            'classes': ['collapse'],
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
    
    inlines = [LandingPageInlineForProject]
    
    def page_count(self, obj):
        """Count of pages in project"""
        count = obj.pages.count()
        return format_html(
            '<span style="background-color: #3b82f6; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">{} pages</span>',
            count
        )
    page_count.short_description = 'Pages'
    
    def detail_link(self, obj):
        """Link to project detail page"""
        url = reverse('pages:project-detail', kwargs={'slug': obj.slug})
        return format_html('<a href="{}" target="_blank">View Project</a>', url)
    detail_link.short_description = 'Detail'
    
    def save_model(self, request, obj, form, change):
        """Track who created the project"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# Project Navigation, Assets, Settings, and Deployment Admin
# ============================================================================

class ProjectNavigationInline(TabularInline):
    """Inline display of project navigation items"""
    model = models.ProjectNavigation
    extra = 0
    fields = ['title', 'page', 'external_url', 'icon', 'order', 'is_visible', 'open_in_new_tab', 'parent']
    readonly_fields = []


@admin.register(models.ProjectNavigation)
class ProjectNavigationAdmin(ModelAdmin):
    """Admin interface for project navigation"""
    
    list_display = ['title', 'project', 'page', 'external_url', 'order', 'is_visible', 'parent']
    list_filter = ['project', 'is_visible']
    search_fields = ['title', 'project__name']
    list_editable = ['order', 'is_visible']
    ordering = ['project', 'order']
    
    fieldsets = [
        ('Navigation Item', {
            'fields': ['project', 'parent', 'title', 'icon', 'order']
        }),
        ('Link Target', {
            'fields': ['page', 'external_url', 'open_in_new_tab']
        }),
        ('Visibility', {
            'fields': ['is_visible']
        }),
    ]


@admin.register(models.ProjectAsset)
class ProjectAssetAdmin(ModelAdmin):
    """Admin interface for project assets"""
    
    list_display = ['name', 'asset_type', 'project', 'include_globally', 'load_order', 'created_at']
    list_filter = ['project', 'asset_type', 'include_globally']
    search_fields = ['name', 'project__name', 'relative_path']
    list_editable = ['load_order', 'include_globally']
    ordering = ['project', 'load_order', 'name']
    
    fieldsets = [
        ('Asset Information', {
            'fields': ['project', 'name', 'asset_type', 'file', 'relative_path']
        }),
        ('Loading Options', {
            'fields': ['include_globally', 'load_order']
        }),
        ('Metadata', {
            'fields': ['created_at'],
            'classes': ['collapse'],
        }),
    ]
    
    readonly_fields = ['created_at']


class ProjectSettingsInline(TabularInline):
    """Inline display of project settings in ProjectAdmin"""
    model = models.ProjectSettings
    can_delete = False
    extra = 0
    max_num = 1
    
    fields = ['primary_color', 'secondary_color', 'font_family', 'google_analytics_id']
    readonly_fields = []


@admin.register(models.ProjectSettings)
class ProjectSettingsAdmin(ModelAdmin):
    """Admin interface for project settings"""
    
    list_display = ['project', 'primary_color', 'secondary_color', 'google_analytics_id', 'facebook_pixel_id']
    search_fields = ['project__name']
    
    fieldsets = [
        ('Project', {
            'fields': ['project']
        }),
        ('SEO Defaults', {
            'fields': ['default_seo_title_suffix', 'default_seo_description', 'default_seo_image']
        }),
        ('Analytics', {
            'fields': ['google_analytics_id', 'facebook_pixel_id', 'custom_head_code', 'custom_body_code']
        }),
        ('Design', {
            'fields': ['primary_color', 'secondary_color', 'font_family', 'favicon']
        }),
        ('Error Pages', {
            'fields': ['custom_404_page']
        }),
    ]
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion - settings should always exist for a project
        return False


@admin.register(models.ProjectDeployment)
class ProjectDeploymentAdmin(ModelAdmin):
    """Admin interface for project deployments (read-only)"""
    
    list_display = ['project', 'version', 'status_badge', 'started_at', 'completed_at', 
                   'deployed_files_count', 'deployed_size_mb', 'deployed_by']
    list_filter = ['status', 'project', 'started_at']
    search_fields = ['project__name', 'version', 'target_domain']
    readonly_fields = ['project', 'status', 'version', 'target_domain', 'target_path',
                      'build_log', 'deployed_files_count', 'deployed_size_bytes',
                      'started_at', 'completed_at', 'deployed_by']
    ordering = ['-started_at']
    
    fieldsets = [
        ('Deployment Information', {
            'fields': ['project', 'version', 'status', 'deployed_by']
        }),
        ('Target', {
            'fields': ['target_domain', 'target_path']
        }),
        ('Build Results', {
            'fields': ['deployed_files_count', 'deployed_size_bytes', 'build_log']
        }),
        ('Timestamps', {
            'fields': ['started_at', 'completed_at']
        }),
    ]
    
    def status_badge(self, obj):
        """Show status as colored badge"""
        colors = {
            'pending': '#6b7280',
            'building': '#f59e0b',
            'deploying': '#3b82f6',
            'success': '#22c55e',
            'failed': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def deployed_size_mb(self, obj):
        """Show size in MB"""
        BYTES_TO_MB = 1024 * 1024
        if obj.deployed_size_bytes:
            size_mb = obj.deployed_size_bytes / BYTES_TO_MB
            return f"{size_mb:.2f} MB"
        return "0 MB"
    deployed_size_mb.short_description = 'Size'
    
    def has_add_permission(self, request):
        # Deployments are created programmatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion of old deployments
        return True


# ============================================================================
# UNIFIED VERSION CONTROL ADMIN
# ============================================================================

@admin.register(ChangeLog)
class ChangeLogAdmin(ModelAdmin):
    """Admin interface for change logs"""
    
    list_display = ['version', 'landing_page', 'change_type', 'target_path', 
                   'is_snapshot', 'snapshot_name', 'created_by', 'created_at', 'integrity_status']
    list_filter = ['change_type', 'is_snapshot', 'landing_page', 'created_at']
    search_fields = ['landing_page__slug', 'target_path', 'note', 'snapshot_name']
    readonly_fields = ['version', 'transaction_id', 'content_hash', 'created_at', 
                      'created_by', 'integrity_verified']
    date_hierarchy = 'created_at'
    ordering = ['-version', '-created_at']
    
    fieldsets = [
        ('Version Information', {
            'fields': ['landing_page', 'version', 'parent_version', 'transaction_id']
        }),
        ('Change Details', {
            'fields': ['change_type', 'target_path', 'note', 'tags']
        }),
        ('Content', {
            'fields': ['content_before', 'content_after', 'content_delta', 
                      'content_hash', 'integrity_verified'],
            'classes': ['collapse'],
        }),
        ('Snapshot', {
            'fields': ['is_snapshot', 'snapshot_name'],
        }),
        ('Metadata', {
            'fields': ['metadata', 'created_by', 'created_at'],
            'classes': ['collapse'],
        }),
    ]
    
    def integrity_status(self, obj):
        """Show content integrity status as badge"""
        is_valid = obj.verify_integrity()
        
        if not obj.content_hash:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px;">No Hash</span>'
            )
        
        if is_valid:
            return format_html(
                '<span style="background-color: #22c55e; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px;">✓ Valid</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px;">✗ Corrupt</span>'
            )
    integrity_status.short_description = 'Integrity'
    
    def integrity_verified(self, obj):
        """Display integrity verification result"""
        is_valid = obj.verify_integrity()
        if is_valid:
            return format_html('<strong style="color: #22c55e;">✓ Content is valid</strong>')
        else:
            return format_html('<strong style="color: #ef4444;">✗ Content may be corrupted</strong>')
    integrity_verified.short_description = 'Integrity Check'
    
    def has_add_permission(self, request):
        # Change logs are created programmatically
        return False


@admin.register(UndoRedoStack)
class UndoRedoStackAdmin(ModelAdmin):
    """Admin interface for undo/redo stacks"""
    
    list_display = ['landing_page', 'user', 'current_version', 'last_action', 
                   'undo_count', 'redo_count', 'last_action_at']
    list_filter = ['last_action', 'user', 'landing_page', 'last_action_at']
    search_fields = ['landing_page__slug', 'user__username', 'session_key']
    readonly_fields = ['landing_page', 'user', 'session_key', 'current_version', 
                      'max_version', 'last_action', 'last_action_at', 'created_at']
    date_hierarchy = 'last_action_at'
    ordering = ['-last_action_at']
    
    fieldsets = [
        ('Stack Information', {
            'fields': ['landing_page', 'user', 'session_key']
        }),
        ('Version Pointers', {
            'fields': ['current_version', 'max_version']
        }),
        ('Stacks', {
            'fields': ['undo_stack', 'redo_stack'],
            'classes': ['collapse'],
        }),
        ('Activity', {
            'fields': ['last_action', 'last_action_at', 'created_at']
        }),
    ]
    
    def undo_count(self, obj):
        """Show number of undoable actions"""
        count = len(obj.undo_stack)
        return format_html(
            '<span style="font-weight: 500;">{} action{}</span>',
            count, 's' if count != 1 else ''
        )
    undo_count.short_description = 'Undo Stack'
    
    def redo_count(self, obj):
        """Show number of redoable actions"""
        count = len(obj.redo_stack)
        return format_html(
            '<span style="font-weight: 500;">{} action{}</span>',
            count, 's' if count != 1 else ''
        )
    redo_count.short_description = 'Redo Stack'
    
    def has_add_permission(self, request):
        # Stacks are created automatically
        return False


@admin.register(VersionSnapshot)
class VersionSnapshotAdmin(ModelAdmin):
    """Admin interface for version snapshots"""
    
    list_display = ['name', 'landing_page', 'snapshot_type_badge', 'semver_display', 
                   'version_number', 'created_by', 'created_at']
    list_filter = ['snapshot_type', 'landing_page', 'created_at']
    search_fields = ['name', 'description', 'landing_page__slug', 'tags']
    readonly_fields = ['changelog_version', 'created_by', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = [
        ('Snapshot Information', {
            'fields': ['name', 'landing_page', 'snapshot_type', 'description']
        }),
        ('Version Reference', {
            'fields': ['changelog_version']
        }),
        ('Semantic Versioning', {
            'fields': ['semver_major', 'semver_minor', 'semver_patch', 'semver_prerelease'],
            'classes': ['collapse'],
        }),
        ('Metadata', {
            'fields': ['tags', 'created_by', 'created_at']
        }),
    ]
    
    def snapshot_type_badge(self, obj):
        """Show snapshot type as colored badge"""
        colors = {
            'manual': '#6b7280',
            'auto': '#3b82f6',
            'release': '#22c55e',
            'backup': '#f59e0b',
        }
        color = colors.get(obj.snapshot_type, '#6b7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, obj.get_snapshot_type_display()
        )
    snapshot_type_badge.short_description = 'Type'
    
    def semver_display(self, obj):
        """Display semantic version if available"""
        semver = obj.semver
        if semver:
            return format_html('<code style="font-weight: 600;">{}</code>', semver)
        return '-'
    semver_display.short_description = 'Version'
    
    def version_number(self, obj):
        """Display changelog version number"""
        return obj.changelog_version.version
    version_number.short_description = 'Changelog Version'
