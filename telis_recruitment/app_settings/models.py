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
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Systemeinstellung'
        verbose_name_plural = 'Systemeinstellungen'
    
    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton pattern
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return "Systemeinstellungen"
