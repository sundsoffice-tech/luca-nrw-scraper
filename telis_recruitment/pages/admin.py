"""Admin interface for pages app"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import LandingPage, PageVersion, PageComponent, PageSubmission


class PageVersionInline(admin.TabularInline):
    """Inline display of page versions"""
    model = PageVersion
    extra = 0
    can_delete = False
    readonly_fields = ['version', 'created_by', 'created_at', 'note']
    fields = ['version', 'note', 'created_by', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    """Admin interface for landing pages"""
    
    list_display = ['title', 'slug', 'status_badge', 'published_at', 'builder_link', 'preview_link', 'created_at']
    list_filter = ['status', 'created_at', 'published_at']
    search_fields = ['title', 'slug', 'seo_title']
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'slug', 'status']
        }),
        ('Content (Managed via Builder)', {
            'fields': ['html_json', 'html', 'css'],
            'classes': ['collapse'],
        }),
        ('SEO Settings', {
            'fields': ['seo_title', 'seo_description', 'seo_image'],
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
        color = 'green' if obj.status == 'published' else 'gray'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def builder_link(self, obj):
        """Link to builder interface"""
        url = reverse('pages:page-builder', kwargs={'slug': obj.slug})
        return format_html('<a href="{}" target="_blank">Edit in Builder</a>', url)
    builder_link.short_description = 'Builder'
    
    def preview_link(self, obj):
        """Link to preview page"""
        if obj.status == 'published':
            url = obj.get_absolute_url()
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
class PageVersionAdmin(admin.ModelAdmin):
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
class PageComponentAdmin(admin.ModelAdmin):
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
class PageSubmissionAdmin(admin.ModelAdmin):
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
