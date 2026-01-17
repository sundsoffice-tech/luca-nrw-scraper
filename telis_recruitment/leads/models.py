from django.db import models
from django.contrib.auth.models import User


class Lead(models.Model):
    """
    Vereinheitlichtes Lead-Model für alle Quellen:
    - Scraper (talent_hunt, candidates, etc.)
    - Landing Page (Opt-In)
    - Manuell eingetragen
    """
    
    # === KERN-FELDER ===
    name = models.CharField(max_length=255, verbose_name="Name")
    email = models.EmailField(null=True, blank=True, verbose_name="E-Mail")
    telefon = models.CharField(max_length=50, null=True, blank=True, verbose_name="Telefon")
    
    # === STATUS-TRACKING ===
    class Status(models.TextChoices):
        NEW = 'NEW', 'Neu'
        CONTACTED = 'CONTACTED', 'Kontaktiert'
        VOICEMAIL = 'VOICEMAIL', 'Voicemail'
        INTERESTED = 'INTERESTED', 'Interessiert'
        INTERVIEW = 'INTERVIEW', 'Interview'
        HIRED = 'HIRED', 'Eingestellt'
        NOT_INTERESTED = 'NOT_INTERESTED', 'Kein Interesse'
        INVALID = 'INVALID', 'Ungültig'
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.NEW,
        verbose_name="Status"
    )
    
    # === QUELLE ===
    class Source(models.TextChoices):
        SCRAPER = 'scraper', 'Scraper'
        LANDING_PAGE = 'landing_page', 'Landing Page'
        MANUAL = 'manual', 'Manuell'
        REFERRAL = 'referral', 'Empfehlung'
    
    source = models.CharField(
        max_length=20, 
        choices=Source.choices,
        default=Source.SCRAPER,
        verbose_name="Quelle"
    )
    source_url = models.URLField(null=True, blank=True, verbose_name="Quell-URL")
    source_detail = models.CharField(max_length=100, null=True, blank=True, verbose_name="Quell-Detail")
    
    # === QUALITÄT (vom Scraper) ===
    quality_score = models.IntegerField(default=50, verbose_name="Qualitäts-Score")
    
    class LeadType(models.TextChoices):
        ACTIVE_SALESPERSON = 'active_salesperson', 'Aktiver Vertriebler'
        TEAM_MEMBER = 'team_member', 'Team-Mitglied'
        FREELANCER = 'freelancer', 'Freelancer'
        HR_CONTACT = 'hr_contact', 'HR-Kontakt'
        CANDIDATE = 'candidate', 'Jobsuchender'
        UNKNOWN = 'unknown', 'Unbekannt'
    
    lead_type = models.CharField(
        max_length=30, 
        choices=LeadType.choices,
        default=LeadType.UNKNOWN,
        verbose_name="Lead-Typ"
    )
    
    # === PROFIL-DETAILS ===
    company = models.CharField(max_length=255, null=True, blank=True, verbose_name="Firma")
    role = models.CharField(max_length=255, null=True, blank=True, verbose_name="Position/Rolle")
    experience_years = models.IntegerField(null=True, blank=True, verbose_name="Jahre Erfahrung")
    location = models.CharField(max_length=255, null=True, blank=True, verbose_name="Standort")
    
    # === SOCIAL PROFILES ===
    linkedin_url = models.URLField(null=True, blank=True, verbose_name="LinkedIn URL")
    xing_url = models.URLField(null=True, blank=True, verbose_name="XING URL")
    
    # === TELEFON-TRACKING ===
    interest_level = models.IntegerField(
        default=0, 
        verbose_name="Interesse-Level",
        help_text="1-5 Skala, 0 = nicht bewertet"
    )
    call_count = models.IntegerField(default=0, verbose_name="Anzahl Anrufe")
    last_called_at = models.DateTimeField(null=True, blank=True, verbose_name="Letzter Anruf")
    next_followup_at = models.DateTimeField(null=True, blank=True, verbose_name="Nächstes Follow-Up")
    notes = models.TextField(null=True, blank=True, verbose_name="Notizen")
    
    # === EMAIL-TRACKING ===
    email_sent_count = models.IntegerField(default=0, verbose_name="Emails gesendet")
    email_opens = models.IntegerField(default=0, verbose_name="Email Öffnungen")
    email_clicks = models.IntegerField(default=0, verbose_name="Email Klicks")
    last_email_at = models.DateTimeField(null=True, blank=True, verbose_name="Letzte Email")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    # === ASSIGNED TO ===
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_leads',
        verbose_name="Zugewiesen an"
    )
    
    class Meta:
        ordering = ['-quality_score', '-created_at']
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['source']),
            models.Index(fields=['quality_score']),
            models.Index(fields=['lead_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def has_contact_info(self):
        return bool(self.email or self.telefon)
    
    @property
    def is_hot_lead(self):
        return self.quality_score >= 80 and self.interest_level >= 3


class CallLog(models.Model):
    """Protokoll für jeden Anruf"""
    
    lead = models.ForeignKey(
        Lead, 
        on_delete=models.CASCADE, 
        related_name='call_logs',
        verbose_name="Lead"
    )
    
    class Outcome(models.TextChoices):
        CONNECTED = 'CONNECTED', 'Erreicht'
        VOICEMAIL = 'VOICEMAIL', 'Voicemail'
        NO_ANSWER = 'NO_ANSWER', 'Keine Antwort'
        BUSY = 'BUSY', 'Besetzt'
        WRONG_NUMBER = 'WRONG_NUMBER', 'Falsche Nummer'
        CALLBACK = 'CALLBACK', 'Rückruf vereinbart'
        INTERESTED = 'INTERESTED', 'Interessiert'
        NOT_INTERESTED = 'NOT_INTERESTED', 'Kein Interesse'
    
    outcome = models.CharField(
        max_length=20, 
        choices=Outcome.choices,
        verbose_name="Ergebnis"
    )
    duration_seconds = models.IntegerField(default=0, verbose_name="Dauer (Sekunden)")
    interest_level = models.IntegerField(
        default=0, 
        verbose_name="Interesse-Level",
        help_text="1-5 Skala"
    )
    notes = models.TextField(null=True, blank=True, verbose_name="Notizen")
    
    called_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Angerufen von"
    )
    called_at = models.DateTimeField(auto_now_add=True, verbose_name="Angerufen am")
    
    class Meta:
        ordering = ['-called_at']
        verbose_name = "Anruf-Log"
        verbose_name_plural = "Anruf-Logs"
    
    def __str__(self):
        return f"{self.lead.name} - {self.get_outcome_display()}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update Lead nach Anruf
        self.lead.call_count = self.lead.call_logs.count()
        self.lead.last_called_at = self.called_at
        if self.interest_level > 0:
            self.lead.interest_level = self.interest_level
        if self.outcome == self.Outcome.CONNECTED and self.interest_level >= 3:
            self.lead.status = Lead.Status.INTERESTED
        elif self.outcome == self.Outcome.VOICEMAIL:
            if self.lead.status == Lead.Status.NEW:
                self.lead.status = Lead.Status.VOICEMAIL
        elif self.outcome == self.Outcome.CONNECTED:
            if self.lead.status in [Lead.Status.NEW, Lead.Status.VOICEMAIL]:
                self.lead.status = Lead.Status.CONTACTED
        elif self.outcome == self.Outcome.WRONG_NUMBER:
            self.lead.status = Lead.Status.INVALID
        self.lead.save()


class EmailLog(models.Model):
    """Protokoll für Email-Kommunikation (Brevo Integration)"""
    
    lead = models.ForeignKey(
        Lead, 
        on_delete=models.CASCADE, 
        related_name='email_logs',
        verbose_name="Lead"
    )
    
    class EmailType(models.TextChoices):
        WELCOME = 'WELCOME', 'Willkommen'
        FOLLOWUP_1 = 'FOLLOWUP_1', 'Follow-Up 1'
        FOLLOWUP_2 = 'FOLLOWUP_2', 'Follow-Up 2'
        FOLLOWUP_3 = 'FOLLOWUP_3', 'Follow-Up 3'
        INTERVIEW_INVITE = 'INTERVIEW_INVITE', 'Interview-Einladung'
        CUSTOM = 'CUSTOM', 'Individuell'
    
    email_type = models.CharField(
        max_length=20, 
        choices=EmailType.choices,
        verbose_name="Email-Typ"
    )
    subject = models.CharField(max_length=255, verbose_name="Betreff")
    
    # Brevo Tracking
    brevo_message_id = models.CharField(max_length=100, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Gesendet am")
    opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Geöffnet am")
    clicked_at = models.DateTimeField(null=True, blank=True, verbose_name="Geklickt am")
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Email-Log"
        verbose_name_plural = "Email-Logs"
    
    def __str__(self):
        return f"{self.lead.name} - {self.get_email_type_display()}"


class SyncStatus(models.Model):
    """Tracks sync status between scraper.db and Django"""
    
    source = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Quelle",
        help_text="z.B. 'scraper_db'"
    )
    last_sync_at = models.DateTimeField(
        verbose_name="Letzter Sync",
        help_text="Zeitpunkt des letzten erfolgreichen Syncs"
    )
    last_lead_id = models.IntegerField(
        default=0,
        verbose_name="Letzte Lead-ID",
        help_text="ID des letzten importierten Leads aus der Quelle"
    )
    leads_imported = models.IntegerField(
        default=0,
        verbose_name="Leads importiert",
        help_text="Anzahl der insgesamt importierten Leads"
    )
    leads_updated = models.IntegerField(
        default=0,
        verbose_name="Leads aktualisiert",
        help_text="Anzahl der aktualisierten Leads"
    )
    leads_skipped = models.IntegerField(
        default=0,
        verbose_name="Leads übersprungen",
        help_text="Anzahl der übersprungenen Leads"
    )
    
    class Meta:
        verbose_name = "Sync-Status"
        verbose_name_plural = "Sync-Status"
        ordering = ['-last_sync_at']
    
    def __str__(self):
        return f"{self.source} (letzter Sync: {self.last_sync_at})"


class ScraperRun(models.Model):
    """
    Tracks individual scraper runs for monitoring and history.
    """
    
    class Status(models.TextChoices):
        RUNNING = 'running', 'Läuft'
        COMPLETED = 'completed', 'Abgeschlossen'
        FAILED = 'failed', 'Fehlgeschlagen'
        STOPPED = 'stopped', 'Gestoppt'
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Gestartet am")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Beendet am")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RUNNING,
        verbose_name="Status"
    )
    
    # Results
    leads_found = models.IntegerField(default=0, verbose_name="Leads gefunden")
    leads_saved = models.IntegerField(default=0, verbose_name="Leads gespeichert")
    leads_rejected = models.IntegerField(default=0, verbose_name="Leads abgelehnt")
    
    # Configuration snapshot
    config_snapshot = models.JSONField(default=dict, verbose_name="Konfiguration")
    
    # Logs
    logs = models.TextField(default='', blank=True, verbose_name="Logs")
    
    # Process info
    pid = models.IntegerField(null=True, blank=True, verbose_name="Prozess-ID")
    
    # Started by
    started_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Gestartet von"
    )
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Scraper-Lauf"
        verbose_name_plural = "Scraper-Läufe"
    
    def __str__(self):
        return f"Run #{self.id} - {self.get_status_display()} ({self.started_at})"
    
    @property
    def duration_seconds(self):
        """Calculate duration in seconds"""
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        elif self.status == self.Status.RUNNING:
            from django.utils import timezone
            return (timezone.now() - self.started_at).total_seconds()
        return 0


class ScraperConfig(models.Model):
    """
    Singleton model for scraper configuration.
    Only one instance should exist.
    """
    
    # Basic scoring settings
    min_score = models.IntegerField(
        default=40,
        verbose_name="Minimaler Score",
        help_text="Minimaler Qualitäts-Score für Leads (0-100)"
    )
    
    # Scraper behavior
    max_results_per_domain = models.IntegerField(
        default=3,
        verbose_name="Max. Ergebnisse pro Domain",
        help_text="Maximale Anzahl von Ergebnissen pro Domain"
    )
    
    request_timeout = models.IntegerField(
        default=12,
        verbose_name="Request Timeout (Sekunden)",
        help_text="Timeout für HTTP-Requests in Sekunden"
    )
    
    pool_size = models.IntegerField(
        default=10,
        verbose_name="Pool-Größe",
        help_text="Anzahl paralleler Worker"
    )
    
    internal_depth_per_domain = models.IntegerField(
        default=2,
        verbose_name="Interne Tiefe pro Domain",
        help_text="Wie tief interne Links verfolgt werden sollen"
    )
    
    # Flags
    allow_pdf = models.BooleanField(
        default=True,
        verbose_name="PDFs erlauben",
        help_text="PDF-Dateien crawlen"
    )
    
    allow_insecure_ssl = models.BooleanField(
        default=False,
        verbose_name="Unsichere SSL-Verbindungen erlauben",
        help_text="Selbstsignierte SSL-Zertifikate akzeptieren"
    )
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Aktualisiert von"
    )
    
    class Meta:
        verbose_name = "Scraper-Konfiguration"
        verbose_name_plural = "Scraper-Konfigurationen"
    
    def __str__(self):
        return f"Scraper Config (Score >= {self.min_score})"
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton config instance"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)
