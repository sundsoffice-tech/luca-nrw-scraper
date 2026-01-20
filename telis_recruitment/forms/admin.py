"""Admin interface for form builder"""
from django.contrib import admin
from .models import Form, FormField, FormSubmission


class FormFieldInline(admin.TabularInline):
    """Inline admin for form fields"""
    model = FormField
    extra = 1
    fields = ['label', 'field_type', 'field_name', 'required', 'order', 'width']
    ordering = ['order']


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    """Admin for forms"""
    list_display = ['name', 'slug', 'status', 'created_by', 'get_submission_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FormFieldInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'status')
        }),
        ('Form Settings', {
            'fields': ('submit_button_text', 'success_message', 'redirect_url')
        }),
        ('Integration', {
            'fields': ('save_to_leads', 'send_email_notification', 'notification_email')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by on first save"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    """Admin for form fields"""
    list_display = ['label', 'form', 'field_type', 'required', 'order']
    list_filter = ['form', 'field_type', 'required']
    search_fields = ['label', 'field_name']
    ordering = ['form', 'order']


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    """Admin for form submissions"""
    list_display = ['form', 'submitted_at', 'lead_created', 'ip_address']
    list_filter = ['form', 'submitted_at', 'lead_created']
    search_fields = ['data']
    readonly_fields = ['form', 'data', 'submitted_at', 'ip_address', 'user_agent', 
                      'lead_created', 'lead_id']
    
    def has_add_permission(self, request):
        """Don't allow manual creation of submissions"""
        return False
