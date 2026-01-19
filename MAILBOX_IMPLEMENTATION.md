# Mailbox App - Vollständiges Email-Postfach-System

## Übersicht

Die Mailbox-App ist ein vollständiges Email-Posteingang/Postausgang-System für Django, das nahtlos in die bestehende LUCA CRM-Anwendung integriert ist.

## Implementierungsstatus

### ✅ Abgeschlossen

#### Phase 1: App-Struktur und Models
- ✅ Django-App `mailbox` erstellt
- ✅ 7 Hauptmodelle implementiert:
  - **EmailAccount**: Verwaltung von IMAP/SMTP/Brevo-Konten
  - **EmailConversation**: Email-Threading und Konversationsgruppierung
  - **Email**: Einzelne Email-Nachrichten mit vollständigem Tracking
  - **EmailAttachment**: Anhänge mit Virus-Scan-Support
  - **EmailLabel**: Labels/Tags für Organisation
  - **EmailSignature**: Benutzer-Signaturen
  - **QuickReply**: Schnellantworten/Canned Responses
- ✅ Migrationen erstellt und ausgeführt
- ✅ Admin-Interface mit Unfold-Theme konfiguriert
- ✅ App zu INSTALLED_APPS hinzugefügt
- ✅ Media-Upload für Anhänge konfiguriert

#### Phase 2: Core Services
- ✅ **encryption.py**: Fernet-basierte Verschlüsselung für Passwörter/API-Keys
- ✅ **email_sender.py**: Email-Versand via Brevo oder SMTP
- ✅ **email_receiver.py**: IMAP-basierter Email-Empfang
- ✅ **threading.py**: Intelligente Konversationsgruppierung via In-Reply-To/References/Subject
- ✅ **webhook_handlers.py**: Brevo Webhook-Handler für Tracking-Events
- ✅ **parser.py**: Email-Parsing (Header, Body, Anhänge)

#### Phase 3: API & Serializers
- ✅ REST API mit Django REST Framework
- ✅ ViewSets für alle Models
- ✅ Spezial-Endpoints:
  - `/api/accounts/{id}/sync/` - IMAP-Synchronisation
  - `/api/conversations/{id}/mark_read/` - Als gelesen markieren
  - `/api/conversations/{id}/star/` - Markieren/Entmarkieren
  - `/api/conversations/{id}/archive/` - Archivieren
  - `/api/conversations/{id}/assign/` - Zuweisen
  - `/api/emails/send/` - Email senden
  - `/api/emails/{id}/reply/` - Auf Email antworten
- ✅ Brevo Webhook-Endpoint: `/webhooks/brevo/`

#### Phase 4: Web Views
- ✅ Inbox-View mit Filterung (all, unread, starred, sent, trash)
- ✅ Conversation-Detail-View mit Thread-Ansicht
- ✅ Compose-View für neue Emails
- ✅ Reply/Forward-Views
- ✅ Settings-View für Kontoverwaltung
- ✅ URL-Routing konfiguriert

#### Phase 5: Templates (Basis-Implementation)
- ✅ `inbox.html` - Posteingang mit Sidebar-Navigation
- ✅ `thread_view.html` - Konversations-Thread-Ansicht
- ✅ `compose.html` - Email-Komposition-Formular
- ✅ `settings.html` - Konto-Einstellungen
- ✅ Bootstrap-basiertes Design (konsistent mit CRM)

#### Phase 6: Integration
- ✅ URLs in Haupt-URL-Config integriert (`/crm/mailbox/`)
- ✅ Mailbox-Sektion zur Admin-Sidebar hinzugefügt
- ✅ Verknüpfung mit Lead-Model via ForeignKey

#### Phase 7: Configuration
- ✅ Dependencies in requirements.txt:
  - `imapclient>=2.3.0` - IMAP-Client
  - `bleach>=6.0.0` - HTML-Sanitization
  - `python-magic>=0.4.27` - Dateityp-Erkennung
  - `cryptography>=41.0.0` - Verschlüsselung

## Architektur

### Models-Übersicht

```
EmailAccount (Konten)
    ↓
EmailConversation (Threads) → Lead (optional)
    ↓
Email (Nachrichten) → EmailTemplate (optional)
    ↓
EmailAttachment (Anhänge)

Nebenmodelle:
- EmailLabel (Tags)
- EmailSignature (Signaturen)
- QuickReply (Schnellantworten)
```

### Services-Übersicht

```
EmailReceiverService
    → IMAP-Verbindung
    → Email-Abruf
    → Parsing (EmailParser)
    → Threading (EmailThreadingService)
    → Lead-Verknüpfung

EmailSenderService
    → Brevo API oder SMTP
    → Anhänge
    → Threading-Header
    → Status-Tracking

BrevoWebhookHandler
    → delivered, opened, clicked
    → soft_bounce, hard_bounce
    → spam, unsubscribed
    → Status-Updates in Email-Model
```

## Verwendung

### Email-Konto einrichten

1. Im Admin-Bereich: **Mailbox → Email-Konten → Neu**
2. Felder ausfüllen:
   - Name: z.B. "Recruiting Team"
   - Email-Adresse
   - Konto-Typ wählen (IMAP/SMTP oder Brevo)
   - IMAP/SMTP-Einstellungen ODER Brevo API-Key
3. Synchronisation aktivieren

**Wichtig:** Passwörter werden automatisch verschlüsselt (Fernet)

### Via Web-Interface

1. **Posteingang öffnen**: `/crm/mailbox/`
2. **Filter nutzen**: Alle, Ungelesen, Markiert, Gesendet
3. **Konversation öffnen**: Klick auf Konversation
4. **Email schreiben**: "Neue Email"-Button

### Via API

**Email senden:**
```bash
POST /crm/mailbox/api/emails/send/
{
  "account_id": 1,
  "to_emails": ["recipient@example.com"],
  "subject": "Test",
  "body_text": "Hello",
  "body_html": "<p>Hello</p>"
}
```

**IMAP-Sync auslösen:**
```bash
POST /crm/mailbox/api/accounts/1/sync/
```

**Konversation als gelesen markieren:**
```bash
POST /crm/mailbox/api/conversations/1/mark_read/
```

### Via Django Admin

Alle Models sind vollständig im Admin-Interface verfügbar:
- `/admin/mailbox/emailaccount/`
- `/admin/mailbox/emailconversation/`
- `/admin/mailbox/email/`
- etc.

## Sicherheit

### Implementiert

1. **Passwort-Verschlüsselung**
   - Fernet symmetric encryption
   - PBKDF2-basierte Schlüsselableitung
   - Basiert auf Django SECRET_KEY

2. **Permission-Checks**
   - Benutzer sehen nur eigene/geteilte Konten
   - Row-Level-Permissions in ViewSets

3. **CSRF-Schutz**
   - Alle POST-Endpoints außer Webhooks

### TODO (Empfehlungen)

1. **Webhook-Signatur-Validierung**
   - Brevo-Webhook-Secret prüfen
   - Im `brevo_webhook`-View implementieren

2. **Attachment-Scanning**
   - Virus-Scan-Integration (ClamAV)
   - Dateityp-Whitelist

3. **Rate-Limiting**
   - django-ratelimit für Webhook-Endpoints
   - Schutz vor Brute-Force

4. **HTML-Sanitization**
   - bleach für email_body_html
   - XSS-Prävention

## Email-Threading-Algorithmus

Die `EmailThreadingService` gruppiert Emails intelligent:

1. **In-Reply-To**: Suche nach Message-ID in vorhandenen Emails
2. **References**: Suche in References-Header
3. **Normalisierter Subject + Kontakt**: Fallback (ohne Re:/Fwd:)
4. **Neue Konversation**: Falls keine Treffer

**Auto-Lead-Linking:**
- Prüft automatisch Email-Adresse gegen Lead-Database
- Verknüpft Konversation bei Treffer

## API-Dokumentation

### Endpoints-Übersicht

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/accounts/` | GET, POST | Liste/Erstelle Konten |
| `/api/accounts/{id}/` | GET, PUT, PATCH, DELETE | Konto-Details |
| `/api/accounts/{id}/sync/` | POST | IMAP-Sync |
| `/api/conversations/` | GET, POST | Liste/Erstelle Konversationen |
| `/api/conversations/{id}/` | GET, PUT, PATCH, DELETE | Konversations-Details |
| `/api/conversations/{id}/mark_read/` | POST | Als gelesen markieren |
| `/api/conversations/{id}/mark_unread/` | POST | Als ungelesen markieren |
| `/api/conversations/{id}/star/` | POST | Markierung togglen |
| `/api/conversations/{id}/archive/` | POST | Archivierung togglen |
| `/api/conversations/{id}/assign/` | POST | Zuweisen |
| `/api/emails/` | GET, POST | Liste/Erstelle Emails |
| `/api/emails/{id}/` | GET, PUT, PATCH, DELETE | Email-Details |
| `/api/emails/send/` | POST | Email senden |
| `/api/emails/{id}/reply/` | POST | Antworten |
| `/api/labels/` | GET, POST | Liste/Erstelle Labels |
| `/api/signatures/` | GET, POST | Liste/Erstelle Signaturen |
| `/api/quick-replies/` | GET, POST | Liste/Erstelle Schnellantworten |
| `/webhooks/brevo/` | POST | Brevo Webhook-Empfang |

### Authentifizierung

Alle API-Endpoints erfordern Authentifizierung:
- Session-basiert (Django)
- Permission: `IsAuthenticated`

## Brevo-Integration

### Transactional Email API

Verwendet `sib-api-v3-sdk` für:
- Email-Versand
- Template-Rendering
- Tracking

### Webhook-Events

Unterstützte Events:
- `delivered`: Email zugestellt
- `opened`: Email geöffnet (inkl. Count)
- `click`: Link geklickt (inkl. URL-Tracking)
- `soft_bounce`: Temporärer Fehler
- `hard_bounce`: Permanenter Fehler
- `spam`: Als Spam markiert
- `unsubscribed`: Abgemeldet

**Webhook-URL konfigurieren:**
```
https://ihr-domain.de/crm/mailbox/webhooks/brevo/
```

## Erweiterungsmöglichkeiten

### Geplant/Empfohlen

1. **Rich-Text-Editor**
   - TinyMCE oder Quill.js Integration
   - Compose-Formular erweitern

2. **Echtzeit-Updates**
   - WebSocket via Django Channels
   - Neue Emails ohne Reload

3. **Erweiterte Suche**
   - Volltext-Suche in Body
   - Datum-Filtering
   - Sender/Empfänger-Filter

4. **Email-Templates Integration**
   - Direkte Verwendung von `email_templates` im Compose-View
   - Variable-Mapping

5. **Scheduled Emails**
   - Celery-Task für scheduled_for
   - Automatisches Senden

6. **Bulk-Operations**
   - Multi-Select in Inbox
   - Batch-Archivieren/Löschen

7. **Mobile-Optimierung**
   - Responsive Design-Verbesserungen
   - Touch-Gesten

## Datenbank-Schema

Wichtige Indizes für Performance:
- `EmailConversation`: `(account, status, -last_message_at)`
- `EmailConversation`: `(contact_email)`
- `EmailConversation`: `(lead)`
- `Email`: `(conversation, created_at)`
- `Email`: `(direction, -created_at)`
- `Email`: `(message_id)` - UNIQUE
- `Email`: `(brevo_message_id)`

## Troubleshooting

### IMAP-Verbindung schlägt fehl
- Prüfen: Host, Port, Credentials
- SSL/TLS-Einstellungen korrekt?
- Firewall-Blockierung?

### Emails werden nicht gesendet
- Account `is_active`?
- SMTP-Credentials korrekt?
- Brevo API-Key gültig?
- Logs prüfen: `last_sync_error`

### Threading funktioniert nicht
- Message-IDs werden korrekt gesetzt?
- In-Reply-To/References-Header vorhanden?
- Normalisierter Subject wird korrekt berechnet

## Testing

Grundlegende Tests fehlen noch. Empfohlene Tests:

1. **Model Tests**
   - Konversations-Erstellung
   - Threading-Logik
   - Lead-Verknüpfung

2. **Service Tests**
   - Email-Parsing
   - Verschlüsselung/Entschlüsselung
   - Sender-Service (Mocking)

3. **API Tests**
   - Endpoint-Responses
   - Permissions
   - Validierung

4. **Integration Tests**
   - Vollständiger Email-Flow
   - Webhook-Verarbeitung

## Performance-Überlegungen

- **Pagination**: Inbox nutzt 50 Items/Seite
- **Select Related**: Views nutzen `select_related`/`prefetch_related`
- **Caching**: Noch nicht implementiert (empfohlen für Conversation-Counts)
- **IMAP-Sync**: Limit 50 Emails/Sync, konfigurierbar

## Wartung

### Regelmäßige Tasks

1. **IMAP-Sync**: Cron-Job oder Celery-Task
   ```python
   # Beispiel: Alle Konten synchronisieren
   from mailbox.models import EmailAccount
   from mailbox.services.email_receiver import EmailReceiverService
   
   for account in EmailAccount.objects.filter(sync_enabled=True, is_active=True):
       receiver = EmailReceiverService(account)
       receiver.fetch_new_emails()
       receiver.disconnect()
   ```

2. **Alte Emails archivieren**: Optional, nach Bedarf

3. **Attachment-Cleanup**: Alte/gelöschte Anhänge bereinigen

## Changelog

### Version 1.0.0 (Initial Implementation)
- ✅ Vollständige Model-Struktur
- ✅ IMAP/SMTP/Brevo-Integration
- ✅ REST API
- ✅ Basis-Web-Interface
- ✅ Admin-Integration
- ✅ Email-Threading
- ✅ Webhook-Support

## Lizenz

Integraler Bestandteil des LUCA CRM-Systems.
