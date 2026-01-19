from django.db import models
from django.contrib.auth.models import User


class EmailTemplate(models.Model):
    """Editierbare Email-Templates mit KI-Unterstützung"""
    
    CATEGORY_CHOICES = [
        ('welcome', 'Willkommen'),
        ('follow_up', 'Follow-Up'),
        ('reminder', 'Erinnerung'),
        ('confirmation', 'Bestätigung'),
        ('newsletter', 'Newsletter'),
        ('custom', 'Benutzerdefiniert'),
    ]
    
    slug = models.SlugField(unique=True, verbose_name="Slug")
    name = models.CharField(max_length=255, verbose_name="Name")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="Kategorie")
    
    # Email Content
    subject = models.CharField(max_length=255, help_text="Betreff mit {variablen}", verbose_name="Betreff")
    html_content = models.TextField(help_text="HTML-Inhalt mit {variablen}", verbose_name="HTML-Inhalt")
    text_content = models.TextField(blank=True, help_text="Plain-Text Fallback", verbose_name="Text-Inhalt")
    
    # Verfügbare Variablen
    available_variables = models.JSONField(
        default=list, 
        help_text="Liste der verfügbaren Variablen: ['name', 'email', 'company']",
        verbose_name="Verfügbare Variablen"
    )
    
    # AI-Generierung
    ai_generated = models.BooleanField(default=False, verbose_name="KI-generiert")
    ai_prompt_used = models.TextField(blank=True, verbose_name="Verwendeter KI-Prompt")
    
    # Brevo Integration
    brevo_template_id = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Falls mit Brevo synchronisiert",
        verbose_name="Brevo Template-ID"
    )
    sync_to_brevo = models.BooleanField(default=False, verbose_name="Mit Brevo synchronisieren")
    
    # Status & Tracking
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    send_count = models.IntegerField(default=0, verbose_name="Anzahl Versendungen")
    last_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Zuletzt gesendet")
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_email_templates',
        verbose_name="Erstellt von"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        verbose_name = "Email-Template"
        verbose_name_plural = "Email-Templates"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class EmailTemplateVersion(models.Model):
    """Versionshistorie für Templates"""
    template = models.ForeignKey(
        EmailTemplate, 
        related_name='versions', 
        on_delete=models.CASCADE,
        verbose_name="Template"
    )
    version = models.IntegerField(verbose_name="Version")
    subject = models.CharField(max_length=255, verbose_name="Betreff")
    html_content = models.TextField(verbose_name="HTML-Inhalt")
    text_content = models.TextField(blank=True, verbose_name="Text-Inhalt")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Erstellt von"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    note = models.CharField(max_length=255, blank=True, verbose_name="Notiz")

    class Meta:
        verbose_name = "Template-Version"
        verbose_name_plural = "Template-Versionen"
        ordering = ['-version']
        unique_together = [['template', 'version']]
    
    def __str__(self):
        return f"{self.template.name} v{self.version}"


class EmailSendLog(models.Model):
    """Log aller gesendeten Emails"""
    template = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='send_logs',
        verbose_name="Template"
    )
    lead = models.ForeignKey(
        'leads.Lead', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='email_template_logs',
        verbose_name="Lead"
    )
    
    to_email = models.EmailField(verbose_name="An (Email)")
    subject_rendered = models.CharField(max_length=255, verbose_name="Betreff (gerendert)")
    
    # Status
    STATUS_CHOICES = [
        ('sent', 'Gesendet'),
        ('delivered', 'Zugestellt'),
        ('opened', 'Geöffnet'),
        ('clicked', 'Geklickt'),
        ('bounced', 'Bounced'),
        ('failed', 'Fehlgeschlagen'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='sent',
        verbose_name="Status"
    )
    
    # Brevo Tracking
    brevo_message_id = models.CharField(max_length=255, blank=True, verbose_name="Brevo Nachricht-ID")
    
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Gesendet am")
    opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Geöffnet am")
    clicked_at = models.DateTimeField(null=True, blank=True, verbose_name="Geklickt am")

    class Meta:
        verbose_name = "Email-Versand-Log"
        verbose_name_plural = "Email-Versand-Logs"
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['-sent_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.to_email} - {self.get_status_display()}"
