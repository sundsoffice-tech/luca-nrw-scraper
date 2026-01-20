from django.db import models
from django.contrib.auth.models import User
from telis_recruitment.leads.utils.normalization import normalize_email, normalize_phone


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
    email_normalized = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Normalisierte E-Mail",
        help_text="Klein geschrieben und getrimmt für schnelle Duplikatssuche",
    )
    telefon = models.CharField(max_length=50, null=True, blank=True, verbose_name="Telefon")
    normalized_phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Normalisierte Telefonnummer",
        db_index=True,
        help_text="Nur Ziffern für schnellen Abgleich",
    )
    phone_type = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefon-Typ")
    whatsapp_link = models.CharField(max_length=255, null=True, blank=True, verbose_name="WhatsApp-Link")
    
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
    confidence_score = models.IntegerField(null=True, blank=True, verbose_name="AI-Konfidenz-Score")
    data_quality = models.IntegerField(null=True, blank=True, verbose_name="Datenqualität")
    
    class LeadType(models.TextChoices):
        ACTIVE_SALESPERSON = 'active_salesperson', 'Aktiver Vertriebler'
        TEAM_MEMBER = 'team_member', 'Team-Mitglied'
        FREELANCER = 'freelancer', 'Freelancer'
        HR_CONTACT = 'hr_contact', 'HR-Kontakt'
        CANDIDATE = 'candidate', 'Jobsuchender'
        TALENT_HUNT = 'talent_hunt', 'Talent Hunt'
        RECRUITER = 'recruiter', 'Recruiter'
        JOB_AD = 'job_ad', 'Stellenanzeige'
        COMPANY = 'company', 'Firmenkontakt'
        INDIVIDUAL = 'individual', 'Einzelperson'
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
    
    # === AI-FELDER ===
    ai_category = models.CharField(max_length=100, null=True, blank=True, verbose_name="AI-Kategorie")
    ai_summary = models.TextField(null=True, blank=True, verbose_name="AI-Zusammenfassung")
    opening_line = models.TextField(null=True, blank=True, verbose_name="Eröffnungszeile")
    
    # === STRUKTURIERTE DATEN (JSON) ===
    tags = models.JSONField(null=True, blank=True, verbose_name="Tags", help_text="Array von Tags")
    skills = models.JSONField(null=True, blank=True, verbose_name="Fähigkeiten", help_text="Array von Fähigkeiten")
    qualifications = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Qualifikationen",
        help_text="Array von Qualifikationen",
    )
    
    # === KANDIDATEN-SPEZIFISCH ===
    availability = models.CharField(max_length=100, null=True, blank=True, verbose_name="Verfügbarkeit")
    candidate_status = models.CharField(max_length=100, null=True, blank=True, verbose_name="Kandidaten-Status")
    mobility = models.CharField(max_length=100, null=True, blank=True, verbose_name="Mobilität/Reisebereitschaft")
    
    # === UNTERNEHMENS-DETAILS ===
    salary_hint = models.CharField(max_length=100, null=True, blank=True, verbose_name="Gehaltshinweis")
    commission_hint = models.CharField(max_length=100, null=True, blank=True, verbose_name="Provisionshinweis")
    company_size = models.CharField(max_length=100, null=True, blank=True, verbose_name="Firmengröße")
    hiring_volume = models.IntegerField(null=True, blank=True, verbose_name="Einstellungsvolumen")
    industry = models.CharField(max_length=255, null=True, blank=True, verbose_name="Branche")
    
    # === KONTAKT-PRÄFERENZEN ===
    private_address = models.TextField(null=True, blank=True, verbose_name="Privatadresse")
    contact_preference = models.CharField(max_length=100, null=True, blank=True, verbose_name="Kontaktpräferenz")
    
    # === METADATEN ===
    recency_indicator = models.CharField(max_length=100, null=True, blank=True, verbose_name="Aktualitäts-Indikator")
    last_updated = models.CharField(max_length=100, null=True, blank=True, verbose_name="Letzte Aktualisierung (Scraper)")
    
    # === ZUSÄTZLICHE SCRAPER-FELDER ===
    profile_text = models.TextField(null=True, blank=True, verbose_name="Profil-Text")
    industries_experience = models.TextField(null=True, blank=True, verbose_name="Branchen-Erfahrung")
    source_type = models.CharField(max_length=50, null=True, blank=True, verbose_name="Quell-Typ")
    last_activity = models.CharField(max_length=100, null=True, blank=True, verbose_name="Letzte Aktivität")
    name_validated = models.BooleanField(null=True, blank=True, verbose_name="Name validiert")
    ssl_insecure = models.CharField(max_length=20, null=True, blank=True, verbose_name="SSL unsicher")
    
    # === SOCIAL PROFILES ===
    linkedin_url = models.URLField(null=True, blank=True, verbose_name="LinkedIn URL")
    xing_url = models.URLField(null=True, blank=True, verbose_name="XING URL")
    profile_url = models.URLField(null=True, blank=True, verbose_name="Profil-URL")
    cv_url = models.URLField(null=True, blank=True, verbose_name="Lebenslauf-URL")
    
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
            models.Index(fields=['email_normalized']),
            models.Index(fields=['normalized_phone']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def has_contact_info(self):
        return bool(self.email or self.telefon)
    
    @property
    def is_hot_lead(self):
        return self.quality_score >= 80 and self.interest_level >= 3

    def save(self, *args, **kwargs):
        self.email_normalized = normalize_email(self.email)
        self.normalized_phone = normalize_phone(self.telefon)
        super().save(*args, **kwargs)


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


class SavedFilter(models.Model):
    """Saved filters for quick access to filtered lead lists."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_filters',
        verbose_name="Benutzer"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Filter-Name",
        help_text="z.B. 'Callcenter NRW, mobile only, Score > 70'"
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Beschreibung"
    )
    
    # Filter criteria stored as JSON
    filter_params = models.JSONField(
        verbose_name="Filter-Parameter",
        help_text="JSON object with filter parameters"
    )
    
    # Sharing options
    is_shared = models.BooleanField(
        default=False,
        verbose_name="Geteilt",
        help_text="Für alle Benutzer sichtbar"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Gespeicherter Filter"
        verbose_name_plural = "Gespeicherte Filter"
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"


# Import ScraperConfig and ScraperRun from the main scraper_control module
# This avoids duplication and ensures consistency
from scraper_control.models import ScraperConfig, ScraperRun
