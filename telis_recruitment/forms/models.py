"""Models for the form builder app"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Form(models.Model):
    """Main form model representing a custom form"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    name = models.CharField(max_length=255, help_text="Internal form name")
    slug = models.SlugField(max_length=255, unique=True, db_index=True,
                           help_text="URL slug for the form (e.g., 'contact-form')")
    description = models.TextField(blank=True, help_text="Form description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Form configuration
    submit_button_text = models.CharField(max_length=100, default='Submit',
                                         help_text="Text for submit button")
    success_message = models.TextField(default='Thank you for your submission!',
                                       help_text="Message shown after successful submission")
    redirect_url = models.URLField(blank=True, 
                                   help_text="Optional URL to redirect to after submission")
    
    # Integration settings
    save_to_leads = models.BooleanField(default=False,
                                       help_text="Save form submissions to leads database")
    send_email_notification = models.BooleanField(default=False,
                                                  help_text="Send email notification on submission")
    notification_email = models.EmailField(blank=True,
                                          help_text="Email address for notifications")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_forms')
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Form'
        verbose_name_plural = 'Forms'
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_submission_count(self):
        """Get total number of submissions for this form"""
        return self.submissions.count()


class FormField(models.Model):
    """Individual form field within a form"""
    
    FIELD_TYPE_CHOICES = [
        ('text', 'Text Input'),
        ('email', 'Email Input'),
        ('phone', 'Phone Input'),
        ('textarea', 'Text Area'),
        ('dropdown', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio Buttons'),
        ('file', 'File Upload'),
        ('date', 'Date Picker'),
        ('number', 'Number Input'),
    ]
    
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=255, help_text="Field label shown to user")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    field_name = models.CharField(max_length=100,
                                 help_text="Internal field name (used in backend)")
    placeholder = models.CharField(max_length=255, blank=True,
                                   help_text="Placeholder text")
    help_text = models.CharField(max_length=500, blank=True,
                                help_text="Help text shown below field")
    
    # Field options (for dropdown, radio, checkbox)
    options = models.JSONField(default=list, blank=True,
                              help_text="Options for dropdown/radio/checkbox fields")
    
    # Validation
    required = models.BooleanField(default=False, help_text="Is this field required?")
    min_length = models.IntegerField(null=True, blank=True,
                                    help_text="Minimum length (for text fields)")
    max_length = models.IntegerField(null=True, blank=True,
                                    help_text="Maximum length (for text fields)")
    pattern = models.CharField(max_length=255, blank=True,
                              help_text="Regex pattern for validation")
    
    # File upload settings
    allowed_file_types = models.CharField(max_length=255, blank=True,
                                         help_text="Comma-separated file extensions (e.g., pdf,doc,docx)")
    max_file_size = models.IntegerField(null=True, blank=True,
                                       help_text="Maximum file size in MB")
    
    # Display
    order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")
    width = models.CharField(max_length=20, default='full',
                            help_text="Field width: full, half, third")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Form Field'
        verbose_name_plural = 'Form Fields'
    
    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"


class FormSubmission(models.Model):
    """Form submission data"""
    
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')
    data = models.JSONField(help_text="Submitted form data")
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Integration tracking
    lead_created = models.BooleanField(default=False,
                                      help_text="Was a lead created from this submission?")
    lead_id = models.IntegerField(null=True, blank=True,
                                 help_text="ID of created lead")
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Form Submission'
        verbose_name_plural = 'Form Submissions'
    
    def __str__(self):
        return f"Submission for {self.form.name} at {self.submitted_at}"
