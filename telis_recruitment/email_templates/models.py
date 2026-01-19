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


class EmailFlow(models.Model):
    """Automatisierter Email-Flow (wie Zapier/Brevo Automation)"""
    name = models.CharField(max_length=255, verbose_name="Name")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    is_active = models.BooleanField(default=False, verbose_name="Aktiv")
    
    # Trigger-Konfiguration
    TRIGGER_TYPES = [
        ('lead_created', 'Lead erstellt'),
        ('lead_status_changed', 'Status geändert'),
        ('lead_score_reached', 'Score erreicht'),
        ('tag_added', 'Tag hinzugefügt'),
        ('time_based', 'Zeitbasiert (Cron)'),
        ('form_submitted', 'Formular eingereicht'),
        ('email_opened', 'Email geöffnet'),
        ('email_clicked', 'Email geklickt'),
        ('manual', 'Manuell ausgelöst'),
    ]
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES, verbose_name="Trigger-Typ")
    trigger_config = models.JSONField(default=dict, verbose_name="Trigger-Konfiguration")
    
    # Statistiken
    execution_count = models.PositiveIntegerField(default=0, verbose_name="Ausführungen")
    last_executed_at = models.DateTimeField(null=True, blank=True, verbose_name="Zuletzt ausgeführt")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_flows', verbose_name="Erstellt von")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        verbose_name = "Email-Flow"
        verbose_name_plural = "Email-Flows"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name}"


class FlowStep(models.Model):
    """Einzelner Schritt in einem Flow"""
    flow = models.ForeignKey(EmailFlow, related_name='steps', on_delete=models.CASCADE, verbose_name="Flow")
    order = models.PositiveIntegerField(verbose_name="Reihenfolge")
    name = models.CharField(max_length=255, blank=True, verbose_name="Name")
    
    ACTION_TYPES = [
        ('send_email', 'Email senden'),
        ('wait', 'Warten'),
        ('condition', 'Bedingung prüfen'),
        ('update_lead', 'Lead aktualisieren'),
        ('add_tag', 'Tag hinzufügen'),
        ('remove_tag', 'Tag entfernen'),
        ('webhook', 'Webhook aufrufen'),
        ('notify_team', 'Team benachrichtigen'),
        ('update_score', 'Score anpassen'),
    ]
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, verbose_name="Aktion")
    action_config = models.JSONField(default=dict, verbose_name="Aktions-Konfiguration")
    
    # Für Email-Aktionen
    email_template = models.ForeignKey(
        EmailTemplate, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name="Email-Template"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    
    class Meta:
        verbose_name = "Flow-Schritt"
        verbose_name_plural = "Flow-Schritte"
        ordering = ['flow', 'order']
        unique_together = [['flow', 'order']]
    
    def __str__(self):
        return f"{self.flow.name} - Step {self.order}: {self.get_action_type_display()}"


class FlowExecution(models.Model):
    """Tracking einer Flow-Ausführung pro Lead"""
    flow = models.ForeignKey(EmailFlow, on_delete=models.CASCADE, related_name='executions', verbose_name="Flow")
    lead = models.ForeignKey('leads.Lead', on_delete=models.CASCADE, related_name='flow_executions', verbose_name="Lead")
    
    current_step = models.ForeignKey(FlowStep, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Aktueller Schritt")
    
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('running', 'Läuft'),
        ('waiting', 'Wartet'),
        ('completed', 'Abgeschlossen'),
        ('paused', 'Pausiert'),
        ('failed', 'Fehlgeschlagen'),
        ('cancelled', 'Abgebrochen'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Gestartet am")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Abgeschlossen am")
    next_execution_at = models.DateTimeField(null=True, blank=True, verbose_name="Nächste Ausführung")
    
    error_message = models.TextField(blank=True, verbose_name="Fehlermeldung")
    execution_log = models.JSONField(default=list, verbose_name="Ausführungs-Log")
    
    class Meta:
        verbose_name = "Flow-Ausführung"
        verbose_name_plural = "Flow-Ausführungen"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.flow.name} - {self.lead.name} ({self.get_status_display()})"


class FlowStepExecution(models.Model):
    """Log für jeden ausgeführten Step"""
    execution = models.ForeignKey(FlowExecution, on_delete=models.CASCADE, related_name='step_executions', verbose_name="Ausführung")
    step = models.ForeignKey(FlowStep, on_delete=models.CASCADE, verbose_name="Schritt")
    
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('running', 'Läuft'),
        ('completed', 'Abgeschlossen'),
        ('failed', 'Fehlgeschlagen'),
        ('skipped', 'Übersprungen'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Gestartet am")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Abgeschlossen am")
    
    result_data = models.JSONField(default=dict, verbose_name="Ergebnis-Daten")
    error_message = models.TextField(blank=True, verbose_name="Fehlermeldung")
    
    class Meta:
        verbose_name = "Step-Ausführung"
        verbose_name_plural = "Step-Ausführungen"
        ordering = ['execution', 'step__order']
    
    def __str__(self):
        return f"{self.execution.flow.name} - Step {self.step.order} ({self.get_status_display()})"
