from django.db import models
from django.contrib.auth.models import User


class EmailAccount(models.Model):
    """Email-Konten (IMAP/SMTP oder Brevo)"""
    
    class AccountType(models.TextChoices):
        BREVO = 'brevo', 'Brevo'
        IMAP_SMTP = 'imap_smtp', 'IMAP/SMTP'
        GMAIL = 'gmail', 'Gmail API'
        OUTLOOK = 'outlook', 'Microsoft Outlook'
    
    name = models.CharField(max_length=100, verbose_name="Name")  # z.B. "Recruiting Team"
    email_address = models.EmailField(unique=True, verbose_name="Email-Adresse")
    account_type = models.CharField(max_length=20, choices=AccountType.choices, verbose_name="Konto-Typ")
    
    # IMAP Settings
    imap_host = models.CharField(max_length=255, blank=True, verbose_name="IMAP Host")
    imap_port = models.IntegerField(default=993, verbose_name="IMAP Port")
    imap_username = models.CharField(max_length=255, blank=True, verbose_name="IMAP Benutzername")
    imap_password_encrypted = models.TextField(blank=True, verbose_name="IMAP Passwort (verschlüsselt)")
    imap_use_ssl = models.BooleanField(default=True, verbose_name="IMAP SSL verwenden")
    
    # SMTP Settings
    smtp_host = models.CharField(max_length=255, blank=True, verbose_name="SMTP Host")
    smtp_port = models.IntegerField(default=587, verbose_name="SMTP Port")
    smtp_username = models.CharField(max_length=255, blank=True, verbose_name="SMTP Benutzername")
    smtp_password_encrypted = models.TextField(blank=True, verbose_name="SMTP Passwort (verschlüsselt)")
    smtp_use_tls = models.BooleanField(default=True, verbose_name="SMTP TLS verwenden")
    
    # Brevo Settings
    brevo_api_key_encrypted = models.TextField(blank=True, verbose_name="Brevo API Key (verschlüsselt)")
    
    # Settings
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    is_default = models.BooleanField(default=False, verbose_name="Standard-Konto")
    sync_enabled = models.BooleanField(default=True, verbose_name="Synchronisation aktiviert")
    sync_interval_minutes = models.IntegerField(default=5, verbose_name="Synchronisationsintervall (Minuten)")
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name="Letzte Synchronisation")
    last_sync_error = models.TextField(blank=True, verbose_name="Letzter Synchronisationsfehler")
    
    # Access Control
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_accounts', verbose_name="Besitzer")
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_email_accounts', verbose_name="Geteilt mit")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    class Meta:
        ordering = ['-is_default', 'name']
        verbose_name = 'Email-Konto'
        verbose_name_plural = 'Email-Konten'
    
    def __str__(self):
        return f"{self.name} ({self.email_address})"


class EmailConversation(models.Model):
    """Email-Thread/Konversation - gruppiert zusammengehörige Emails"""
    
    subject = models.CharField(max_length=500, verbose_name="Betreff")
    subject_normalized = models.CharField(
        max_length=500, 
        db_index=True,
        help_text="Subject ohne Re:/Fwd: für Threading",
        verbose_name="Normalisierter Betreff"
    )
    
    # Verknüpfung zu Lead (optional, auto-detected)
    lead = models.ForeignKey(
        'leads.Lead', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='email_conversations',
        verbose_name="Lead"
    )
    
    # Haupt-Kontakt
    contact_email = models.EmailField(db_index=True, verbose_name="Kontakt-Email")
    contact_name = models.CharField(max_length=255, blank=True, verbose_name="Kontakt-Name")
    
    # Account
    account = models.ForeignKey(
        EmailAccount, 
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name="Email-Konto"
    )
    
    # Status
    class Status(models.TextChoices):
        OPEN = 'open', 'Offen'
        PENDING = 'pending', 'Wartend auf Antwort'
        RESOLVED = 'resolved', 'Erledigt'
        SPAM = 'spam', 'Spam'
        TRASH = 'trash', 'Papierkorb'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, verbose_name="Status")
    
    # Zuweisung
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='assigned_conversations',
        verbose_name="Zugewiesen an"
    )
    
    # Flags
    is_starred = models.BooleanField(default=False, verbose_name="Markiert")
    is_archived = models.BooleanField(default=False, verbose_name="Archiviert")
    is_read = models.BooleanField(default=False, verbose_name="Gelesen")
    
    # Counters
    message_count = models.IntegerField(default=0, verbose_name="Anzahl Nachrichten")
    unread_count = models.IntegerField(default=0, verbose_name="Anzahl ungelesene")
    
    # Timing
    last_message_at = models.DateTimeField(db_index=True, verbose_name="Letzte Nachricht")
    last_inbound_at = models.DateTimeField(null=True, blank=True, verbose_name="Letzte eingehende Nachricht")
    last_outbound_at = models.DateTimeField(null=True, blank=True, verbose_name="Letzte ausgehende Nachricht")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    class Meta:
        ordering = ['-last_message_at']
        verbose_name = 'Email-Konversation'
        verbose_name_plural = 'Email-Konversationen'
        indexes = [
            models.Index(fields=['account', 'status', '-last_message_at']),
            models.Index(fields=['contact_email']),
            models.Index(fields=['lead']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.contact_email}"


class Email(models.Model):
    """Einzelne Email-Nachricht (eingehend oder ausgehend)"""
    
    class Direction(models.TextChoices):
        INBOUND = 'inbound', 'Eingehend'
        OUTBOUND = 'outbound', 'Ausgehend'
    
    conversation = models.ForeignKey(
        EmailConversation, 
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Konversation"
    )
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, verbose_name="Email-Konto")
    
    # Richtung
    direction = models.CharField(max_length=10, choices=Direction.choices, verbose_name="Richtung")
    
    # Message-ID für Threading
    message_id = models.CharField(max_length=255, unique=True, db_index=True, verbose_name="Message-ID")
    in_reply_to = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="In-Reply-To")
    references = models.TextField(blank=True, verbose_name="Referenzen")  # Space-separated Message-IDs
    
    # Absender/Empfänger
    from_email = models.EmailField(verbose_name="Von (Email)")
    from_name = models.CharField(max_length=255, blank=True, verbose_name="Von (Name)")
    to_emails = models.JSONField(default=list, verbose_name="An")  # [{"email": "...", "name": "..."}]
    cc_emails = models.JSONField(default=list, verbose_name="CC")
    bcc_emails = models.JSONField(default=list, verbose_name="BCC")
    reply_to_email = models.EmailField(blank=True, verbose_name="Antwort an")
    
    # Inhalt
    subject = models.CharField(max_length=500, verbose_name="Betreff")
    body_text = models.TextField(blank=True, verbose_name="Text-Inhalt")
    body_html = models.TextField(blank=True, verbose_name="HTML-Inhalt")
    snippet = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Kurze Vorschau des Inhalts",
        verbose_name="Vorschau"
    )
    
    # Template (falls verwendet)
    template_used = models.ForeignKey(
        'email_templates.EmailTemplate',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Verwendetes Template"
    )
    
    # Status (für ausgehende)
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Entwurf'
        QUEUED = 'queued', 'In Warteschlange'
        SENDING = 'sending', 'Wird gesendet'
        SENT = 'sent', 'Gesendet'
        DELIVERED = 'delivered', 'Zugestellt'
        OPENED = 'opened', 'Geöffnet'
        CLICKED = 'clicked', 'Link geklickt'
        REPLIED = 'replied', 'Beantwortet'
        BOUNCED = 'bounced', 'Bounced'
        FAILED = 'failed', 'Fehlgeschlagen'
        RECEIVED = 'received', 'Empfangen'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name="Status")
    status_detail = models.TextField(blank=True, help_text="Fehlerdetails etc.", verbose_name="Status-Details")
    
    # Tracking (Brevo)
    brevo_message_id = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="Brevo Message-ID")
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Gesendet am")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Zugestellt am")
    opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Geöffnet am")
    opened_count = models.IntegerField(default=0, verbose_name="Öffnungen")
    clicked_at = models.DateTimeField(null=True, blank=True, verbose_name="Geklickt am")
    clicked_links = models.JSONField(default=list, verbose_name="Geklickte Links")  # [{"url": "...", "clicked_at": "..."}]
    
    # Für eingehende
    received_at = models.DateTimeField(null=True, blank=True, verbose_name="Empfangen am")
    is_read = models.BooleanField(default=False, verbose_name="Gelesen")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Gelesen am")
    
    # IMAP
    imap_uid = models.CharField(max_length=100, blank=True, verbose_name="IMAP UID")
    imap_folder = models.CharField(max_length=100, blank=True, verbose_name="IMAP Ordner")
    
    # Scheduled
    scheduled_for = models.DateTimeField(null=True, blank=True, verbose_name="Geplant für")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Email'
        verbose_name_plural = 'Emails'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['direction', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.from_email}"


class EmailAttachment(models.Model):
    """Email-Anhänge"""
    
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='attachments', verbose_name="Email")
    
    file = models.FileField(upload_to='email_attachments/%Y/%m/', verbose_name="Datei")
    filename = models.CharField(max_length=255, verbose_name="Dateiname")
    content_type = models.CharField(max_length=100, verbose_name="Content-Type")
    size = models.PositiveIntegerField(verbose_name="Größe (Bytes)")  # Bytes
    
    # Inline-Bilder (CID)
    content_id = models.CharField(max_length=255, blank=True, verbose_name="Content-ID")
    is_inline = models.BooleanField(default=False, verbose_name="Inline")
    
    # Virus-Scan
    is_scanned = models.BooleanField(default=False, verbose_name="Gescannt")
    is_safe = models.BooleanField(default=True, verbose_name="Sicher")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    
    class Meta:
        ordering = ['filename']
        verbose_name = 'Email-Anhang'
        verbose_name_plural = 'Email-Anhänge'
    
    def __str__(self):
        return self.filename


class EmailLabel(models.Model):
    """Labels/Tags für Email-Organisation"""
    
    name = models.CharField(max_length=50, verbose_name="Name")
    color = models.CharField(max_length=7, default='#6366f1', verbose_name="Farbe")
    
    # System-Labels vs User-Labels
    is_system = models.BooleanField(default=False, verbose_name="System-Label")
    
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True, 
        related_name='email_labels',
        verbose_name="Besitzer"
    )
    
    conversations = models.ManyToManyField(
        EmailConversation, 
        blank=True,
        related_name='labels',
        verbose_name="Konversationen"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    
    class Meta:
        unique_together = ['name', 'owner']
        ordering = ['name']
        verbose_name = 'Email-Label'
        verbose_name_plural = 'Email-Labels'
    
    def __str__(self):
        return self.name


class EmailSignature(models.Model):
    """Email-Signaturen pro User"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_signatures', verbose_name="Benutzer")
    name = models.CharField(max_length=100, verbose_name="Name")  # z.B. "Standard", "Formal"
    content_html = models.TextField(verbose_name="HTML-Inhalt")
    content_text = models.TextField(verbose_name="Text-Inhalt")
    is_default = models.BooleanField(default=False, verbose_name="Standard-Signatur")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    class Meta:
        ordering = ['-is_default', 'name']
        verbose_name = 'Email-Signatur'
        verbose_name_plural = 'Email-Signaturen'
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class QuickReply(models.Model):
    """Schnellantworten / Canned Responses"""
    
    name = models.CharField(max_length=100, verbose_name="Name")
    shortcut = models.CharField(max_length=20, blank=True, verbose_name="Tastenkürzel")  # z.B. "/danke"
    subject = models.CharField(max_length=255, blank=True, verbose_name="Betreff")
    content_html = models.TextField(verbose_name="HTML-Inhalt")
    content_text = models.TextField(verbose_name="Text-Inhalt")
    
    # Shared vs Private
    is_shared = models.BooleanField(default=False, verbose_name="Öffentlich geteilt")
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True, 
        related_name='quick_replies',
        verbose_name="Besitzer"
    )
    
    usage_count = models.IntegerField(default=0, verbose_name="Anzahl Verwendungen")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    class Meta:
        ordering = ['-usage_count', 'name']
        verbose_name = 'Schnellantwort'
        verbose_name_plural = 'Schnellantworten'
    
    def __str__(self):
        return self.name
