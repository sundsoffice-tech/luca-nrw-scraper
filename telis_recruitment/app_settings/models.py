from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserPreferences(models.Model):
    """
    User-specific preferences and settings
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # UI preferences
    theme = models.CharField(
        max_length=20,
        choices=[('dark', 'Dark'), ('light', 'Light')],
        default='dark',
        verbose_name='Theme'
    )
    
    language = models.CharField(
        max_length=10,
        choices=[('de', 'Deutsch'), ('en', 'English')],
        default='de',
        verbose_name='Sprache'
    )
    
    # Email preferences
    email_notifications = models.BooleanField(
        default=True,
        verbose_name='E-Mail-Benachrichtigungen'
    )
    
    # Dashboard preferences
    items_per_page = models.IntegerField(
        default=25,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
        verbose_name='Elemente pro Seite'
    )
    
    default_lead_view = models.CharField(
        max_length=20,
        choices=[('list', 'Liste'), ('grid', 'Kacheln')],
        default='list',
        verbose_name='Standard-Ansicht für Leads'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Benutzereinstellung'
        verbose_name_plural = 'Benutzereinstellungen'
    
    def __str__(self):
        return f"Einstellungen für {self.user.username}"


class SystemSettings(models.Model):
    """
    Global system-wide settings (singleton)
    """
    # General
    site_name = models.CharField(
        max_length=100,
        default='TELIS CRM',
        verbose_name='Seitenname'
    )
    
    site_url = models.URLField(
        blank=True,
        verbose_name='Seiten-URL'
    )
    
    admin_email = models.EmailField(
        blank=True,
        verbose_name='Admin E-Mail'
    )
    
    # Features
    enable_email_module = models.BooleanField(
        default=True,
        verbose_name='E-Mail-Modul aktivieren'
    )
    
    enable_scraper = models.BooleanField(
        default=True,
        verbose_name='Scraper aktivieren'
    )
    
    enable_ai_features = models.BooleanField(
        default=True,
        verbose_name='KI-Funktionen aktivieren'
    )
    
    enable_landing_pages = models.BooleanField(
        default=True,
        verbose_name='Landing Pages aktivieren'
    )
    
    # Maintenance
    maintenance_mode = models.BooleanField(
        default=False,
        verbose_name='Wartungsmodus'
    )
    
    maintenance_message = models.TextField(
        blank=True,
        verbose_name='Wartungsnachricht'
    )
    
    # Security
    session_timeout_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(5), MaxValueValidator(1440)],
        verbose_name='Sitzungszeitlimit (Minuten)'
    )
    
    max_login_attempts = models.IntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(10)],
        verbose_name='Max. Login-Versuche'
    )
    
    # Analytics & Tracking
    enable_analytics = models.BooleanField(
        default=False,
        verbose_name='Analytics aktivieren'
    )
    
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Google Analytics ID',
        help_text='z.B. G-XXXXXXXXXX oder UA-XXXXXXXXX-X'
    )
    
    meta_pixel_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Meta Pixel ID',
        help_text='Facebook/Meta Pixel ID'
    )
    
    custom_tracking_code = models.TextField(
        blank=True,
        verbose_name='Benutzerdefinierter Tracking-Code',
        help_text='Benutzerdefinierte Tracking-Scripts (z.B. Matomo, Plausible, etc.)'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Systemeinstellung'
        verbose_name_plural = 'Systemeinstellungen'
    
    def save(self, *args, **kwargs):
        """
        Enforce singleton pattern by ensuring pk=1.
        Note: This is a simple singleton implementation suitable for single-server deployments.
        For high-concurrency or multi-server setups, consider using database-level constraints
        or distributed locking mechanisms.
        """
        self.pk = 1  # Singleton pattern
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return "Systemeinstellungen"


class PageView(models.Model):
    """
    Track page views and user interactions for analytics
    """
    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Benutzer'
    )
    
    session_key = models.CharField(
        max_length=40,
        db_index=True,
        verbose_name='Sitzungsschlüssel'
    )
    
    # Page information
    path = models.CharField(
        max_length=500,
        db_index=True,
        verbose_name='Pfad'
    )
    
    page_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Seitentitel'
    )
    
    # Request information
    method = models.CharField(
        max_length=10,
        default='GET',
        verbose_name='HTTP-Methode'
    )
    
    referrer = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='Referrer'
    )
    
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='User-Agent'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP-Adresse'
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Zeitstempel'
    )
    
    # Performance metrics
    load_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Ladezeit (ms)'
    )
    
    class Meta:
        verbose_name = 'Seitenaufruf'
        verbose_name_plural = 'Seitenaufrufe'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'path']),
            models.Index(fields=['session_key', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.path} - {self.timestamp.strftime('%d.%m.%Y %H:%M')}"


class AnalyticsEvent(models.Model):
    """
    Track custom analytics events (button clicks, form submissions, etc.)
    """
    EVENT_CATEGORY_CHOICES = [
        ('navigation', 'Navigation'),
        ('interaction', 'Interaktion'),
        ('conversion', 'Conversion'),
        ('error', 'Fehler'),
        ('engagement', 'Engagement'),
    ]
    
    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Benutzer'
    )
    
    session_key = models.CharField(
        max_length=40,
        db_index=True,
        verbose_name='Sitzungsschlüssel'
    )
    
    # Event information
    category = models.CharField(
        max_length=50,
        choices=EVENT_CATEGORY_CHOICES,
        db_index=True,
        verbose_name='Kategorie'
    )
    
    action = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Aktion'
    )
    
    label = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Label'
    )
    
    value = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Wert'
    )
    
    # Context
    page_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Seitenpfad'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadaten'
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Zeitstempel'
    )
    
    class Meta:
        verbose_name = 'Analytics-Event'
        verbose_name_plural = 'Analytics-Events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'category']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.category} - {self.action} - {self.timestamp.strftime('%d.%m.%Y %H:%M')}"
