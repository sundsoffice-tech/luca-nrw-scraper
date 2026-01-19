from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ScraperConfig(models.Model):
    """
    Singleton model for scraper configuration.
    Only one instance should exist.
    """
    
    # Industry/mode configuration
    INDUSTRY_CHOICES = [
        # Basis-Modi
        ('all', 'Alle'),
        ('recruiter', 'Recruiter'),
        ('candidates', 'Kandidaten'),
        ('talent_hunt', 'Talent Hunt'),
        ('handelsvertreter', 'Handelsvertreter'),
        
        # Erweiterte Branchen
        ('nrw', 'NRW Regional'),
        ('social', 'Social Media'),
        ('solar', 'Solar/Energie'),
        ('telekom', 'Telekommunikation'),
        ('versicherung', 'Versicherung'),
        ('bau', 'Baubranche'),
        ('ecom', 'E-Commerce'),
        ('household', 'Haushalt'),
        
        # Weitere spezifische
        ('d2d', 'Door-to-Door'),
        ('callcenter', 'Call Center'),
    ]
    
    MODE_CHOICES = [
        ('standard', 'Standard'),
        ('learning', 'Selbstlernend'),
        ('aggressive', 'Aggressiv'),
        ('snippet_only', 'Nur Snippets'),
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
    
    # === NEUE FELDER: HTTP & Networking ===
    http_timeout = models.IntegerField(
        default=10, 
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        verbose_name="HTTP Timeout (Sek)",
        help_text="Request Timeout in Sekunden"
    )
    async_limit = models.IntegerField(
        default=35,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Async Limit",
        help_text="Max. parallele Requests"
    )
    pool_size = models.IntegerField(
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name="Pool Size",
        help_text="Connection Pool Größe"
    )
    http2_enabled = models.BooleanField(default=True, verbose_name="HTTP/2 aktivieren")
    
    # === NEUE FELDER: Rate Limiting ===
    sleep_between_queries = models.FloatField(
        default=2.7,
        validators=[MinValueValidator(0.5), MaxValueValidator(30)],
        verbose_name="Query-Pause (Sek)",
        help_text="Pause zwischen Google-Queries"
    )
    max_google_pages = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Max. Google-Seiten",
        help_text="Seiten pro Query"
    )
    circuit_breaker_penalty = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0)],
        verbose_name="Circuit Breaker Penalty (Sek)",
        help_text="Pausenzeit wenn Circuit Breaker öffnet"
    )
    retry_max_per_url = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Max. Retries pro URL"
    )
    
    # === NEUE FELDER: Process Manager Retry & Circuit Breaker ===
    process_max_retry_attempts = models.IntegerField(
        default=3,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Max. Process-Restarts",
        help_text="Maximale automatische Neustarts bei Fehlern"
    )
    process_qpi_reduction_factor = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.1), MaxValueValidator(1.0)],
        verbose_name="QPI-Reduktionsfaktor",
        help_text="QPI-Anpassung bei Rate-Limits (0.7 = 70%)"
    )
    process_error_rate_threshold = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Fehlerquoten-Schwelle",
        help_text="Fehlerrate für Circuit Breaker (0.5 = 50%)"
    )
    process_circuit_breaker_failures = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name="Circuit Breaker Fehler-Schwelle",
        help_text="Anzahl Fehler bis Circuit Breaker öffnet"
    )
    process_retry_backoff_base = models.FloatField(
        default=30.0,
        validators=[MinValueValidator(5.0), MaxValueValidator(300.0)],
        verbose_name="Retry Backoff Basis (Sek)",
        help_text="Basis-Wartezeit für exponentiellen Backoff"
    )
    
    # === NEUE FELDER: Scoring ===
    min_score = models.IntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Mindest-Score",
        help_text="Leads unter diesem Score werden verworfen"
    )
    max_per_domain = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Max. Leads pro Domain"
    )
    default_quality_score = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Default Quality Score"
    )
    confidence_threshold = models.FloatField(
        default=0.35,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Confidence Threshold"
    )
    
    # === NEUE FELDER: Feature Flags ===
    enable_kleinanzeigen = models.BooleanField(default=True, verbose_name="Kleinanzeigen aktivieren")
    enable_telefonbuch = models.BooleanField(default=True, verbose_name="Telefonbuch-Enrichment")
    enable_perplexity = models.BooleanField(default=False, verbose_name="Perplexity AI aktivieren")
    enable_bing = models.BooleanField(default=False, verbose_name="Bing Search aktivieren")
    parallel_portal_crawl = models.BooleanField(default=True, verbose_name="Paralleles Portal-Crawling")
    max_concurrent_portals = models.IntegerField(
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name="Max. parallele Portale"
    )
    
    # === NEUE FELDER: Content ===
    allow_pdf = models.BooleanField(default=False, verbose_name="PDF-Dateien erlauben")
    max_content_length = models.IntegerField(
        default=2097152,
        validators=[MinValueValidator(1024), MaxValueValidator(104857600)],  # 1KB to 100MB
        verbose_name="Max. Content-Größe (Bytes)",
        help_text="Standard: 2MB, Max: 100MB"
    )
    
    # === NEUE FELDER: Sicherheit ===
    allow_insecure_ssl = models.BooleanField(
        default=False,
        verbose_name="Unsichere SSL-Verbindungen erlauben",
        help_text="⚠️ WARNUNG: Deaktiviert SSL-Zertifikat-Validierung. Nur für Entwicklung/Testing!"
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


class SearchRegion(models.Model):
    """Editierbare Regionen/Städte für Scraper"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Stadt/Region")
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    is_metropolis = models.BooleanField(default=False, verbose_name="Metropole", help_text="Große Stadt mit mehr Queries")
    priority = models.IntegerField(default=0, verbose_name="Priorität", help_text="Höher = wird zuerst gescraped")
    
    class Meta:
        ordering = ['-priority', 'name']
        verbose_name = "Such-Region"
        verbose_name_plural = "Such-Regionen"
    
    def __str__(self):
        return f"{self.name} {'(Metropole)' if self.is_metropolis else ''}"


class SearchDork(models.Model):
    """Editierbare Such-Queries/Dorks"""
    
    CATEGORY_CHOICES = [
        ('default', 'Standard'),
        ('candidates', 'Kandidaten'),
        ('recruiter', 'Recruiter'),
        ('talent_hunt', 'Talent Hunt'),
        ('social', 'Social Media'),
        ('portal', 'Portal-spezifisch'),
        ('custom', 'Benutzerdefiniert'),
    ]
    
    query = models.TextField(verbose_name="Such-Query", help_text="Google Dork Query")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='default', verbose_name="Kategorie")
    description = models.CharField(max_length=255, blank=True, verbose_name="Beschreibung")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    priority = models.IntegerField(default=0, verbose_name="Priorität")
    
    # Performance Tracking
    times_used = models.IntegerField(default=0, verbose_name="Verwendungen")
    leads_found = models.IntegerField(default=0, verbose_name="Leads gefunden")
    success_rate = models.FloatField(default=0.0, verbose_name="Erfolgsrate")
    last_used = models.DateTimeField(null=True, blank=True, verbose_name="Zuletzt verwendet")
    
    # AI-Generierung
    ai_generated = models.BooleanField(default=False, verbose_name="KI-generiert")
    ai_prompt = models.TextField(blank=True, verbose_name="KI-Prompt")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-success_rate']
        verbose_name = "Such-Dork"
        verbose_name_plural = "Such-Dorks"
    
    def __str__(self):
        return f"[{self.category}] {self.query[:50]}..."


class PortalSource(models.Model):
    """Editierbare Portal-Quellen"""
    
    DIFFICULTY_CHOICES = [
        ('low', 'Einfach'),
        ('medium', 'Mittel'),
        ('high', 'Schwer'),
        ('very_high', 'Sehr schwer'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Interner Name")
    display_name = models.CharField(max_length=200, verbose_name="Anzeigename")
    base_url = models.URLField(verbose_name="Basis-URL")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    
    # Rate Limiting
    rate_limit_seconds = models.FloatField(default=3.0, verbose_name="Rate Limit (Sek)", help_text="Pause zwischen Requests")
    max_results = models.IntegerField(default=20, verbose_name="Max. Ergebnisse")
    
    # Technische Config
    requires_login = models.BooleanField(default=False, verbose_name="Login erforderlich")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium', verbose_name="Schwierigkeit")
    
    # Custom URLs als JSON
    urls = models.JSONField(default=list, blank=True, verbose_name="URLs", help_text="Liste der zu crawlenden URLs")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_name']
        verbose_name = "Portal-Quelle"
        verbose_name_plural = "Portal-Quellen"
    
    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.display_name}"


class BlacklistEntry(models.Model):
    """Editierbare Blacklist-Einträge"""
    
    TYPE_CHOICES = [
        ('domain', 'Domain'),
        ('path_pattern', 'Pfad-Muster'),
        ('mailbox_prefix', 'Email-Prefix'),
    ]
    
    entry_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Typ")
    value = models.CharField(max_length=255, verbose_name="Wert")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Grund")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['entry_type', 'value']
        verbose_name = "Blacklist-Eintrag"
        verbose_name_plural = "Blacklist-Einträge"
        unique_together = ['entry_type', 'value']
    
    def __str__(self):
        return f"[{self.entry_type}] {self.value}"
