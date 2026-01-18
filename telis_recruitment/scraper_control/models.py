from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ScraperConfig(models.Model):
    """
    Singleton model for scraper configuration.
    Only one instance should exist.
    """
    
    # Industry/mode configuration
    INDUSTRY_CHOICES = [
        ('all', 'Alle'),
        ('recruiter', 'Recruiter'),
        ('candidates', 'Kandidaten'),
        ('talent_hunt', 'Talent Hunt'),
    ]
    
    MODE_CHOICES = [
        ('standard', 'Standard'),
        ('learning', 'Learning'),
        ('aggressive', 'Aggressive'),
        ('snippet_only', 'Snippet Only'),
    ]
    
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        default='recruiter',
        verbose_name="Branche/Industry"
    )
    
    mode = models.CharField(
        max_length=50,
        choices=MODE_CHOICES,
        default='standard',
        verbose_name="Modus"
    )
    
    qpi = models.IntegerField(
        default=15,
        verbose_name="QPI (Queries per Industry)",
        help_text="Anzahl der Queries pro Branche"
    )
    
    daterestrict = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Date Restrict",
        help_text="Google CSE dateRestrict, z.B. d30, w8, m3"
    )
    
    # Flags
    smart = models.BooleanField(
        default=True,
        verbose_name="Smart Mode",
        help_text="AI-generierte Dorks aktivieren"
    )
    
    force = models.BooleanField(
        default=False,
        verbose_name="Force",
        help_text="Historie ignorieren (queries_done)"
    )
    
    once = models.BooleanField(
        default=True,
        verbose_name="Once",
        help_text="Einmaliger Lauf"
    )
    
    dry_run = models.BooleanField(
        default=False,
        verbose_name="Dry Run",
        help_text="Test-Modus ohne tatsächliche Ausführung"
    )
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scraper_control_configs',
        verbose_name="Aktualisiert von"
    )
    
    class Meta:
        verbose_name = "Scraper-Konfiguration"
        verbose_name_plural = "Scraper-Konfigurationen"
    
    def __str__(self):
        return f"Scraper Config ({self.get_industry_display()} / {self.get_mode_display()})"
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton config instance"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)


class ScraperRun(models.Model):
    """
    Tracks individual scraper runs for monitoring and history.
    """
    
    STATUS_CHOICES = [
        ('running', 'Läuft'),
        ('completed', 'Abgeschlossen'),
        ('stopped', 'Gestoppt'),
        ('failed', 'Fehlgeschlagen'),
        ('error', 'Fehler'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running',
        verbose_name="Status"
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Gestartet am")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Beendet am")
    
    # Process info
    pid = models.IntegerField(null=True, blank=True, verbose_name="Prozess-ID")
    
    # Configuration snapshot
    params_snapshot = models.JSONField(default=dict, verbose_name="Parameter-Snapshot")
    
    # Results
    leads_found = models.IntegerField(default=0, verbose_name="Leads gefunden")
    api_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="API-Kosten (USD)"
    )
    
    # Logs
    logs = models.TextField(default='', blank=True, verbose_name="Logs")
    
    # Started by
    started_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scraper_control_runs',
        verbose_name="Gestartet von"
    )
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Scraper-Lauf"
        verbose_name_plural = "Scraper-Läufe"
    
    def __str__(self):
        return f"Run #{self.id} - {self.get_status_display()} ({self.started_at})"
    
    @property
    def duration(self):
        """Calculate duration as timedelta"""
        if self.finished_at:
            return self.finished_at - self.started_at
        elif self.status == 'running':
            return timezone.now() - self.started_at
        return None


class ScraperLog(models.Model):
    """
    Individual log entries for a scraper run.
    Used for real-time SSE streaming.
    """
    
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARN', 'Warning'),
        ('ERROR', 'Error'),
    ]
    
    run = models.ForeignKey(
        ScraperRun,
        on_delete=models.CASCADE,
        related_name='log_entries',
        verbose_name="Scraper-Lauf"
    )
    
    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default='INFO',
        verbose_name="Level"
    )
    
    message = models.TextField(verbose_name="Nachricht")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Scraper-Log"
        verbose_name_plural = "Scraper-Logs"
        indexes = [
            models.Index(fields=['run', 'created_at']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.message[:50]}"
