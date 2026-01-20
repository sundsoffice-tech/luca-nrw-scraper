# Entity-Relationship Diagramm - LUCA NRW Scraper Database

## Übersicht

Dieses Dokument beschreibt das Entity-Relationship Model des LUCA NRW Scraper Systems.

## Hauptentitäten

```
┌─────────────────────────────────────────────────────────────┐
│                         Lead                                 │
├─────────────────────────────────────────────────────────────┤
│ PK  id: Integer                                             │
│     name: String(255)                                       │
│     email: Email                                            │
│     email_normalized: String(255) [INDEXED]                │
│     telefon: String(50)                                     │
│     normalized_phone: String(50) [INDEXED]                 │
│     status: Choice [NEW, CONTACTED, INTERESTED, ...]       │
│     source: Choice [scraper, landing_page, manual, ...]    │
│     quality_score: Integer [0-100] [CHECK]                 │
│     confidence_score: Integer? [0-100] [CHECK]             │
│     lead_type: Choice [talent_hunt, recruiter, ...]        │
│     company: String(255)?                                   │
│     role: String(255)?                                      │
│     location: String(255)?                                  │
│     tags: JSON?                                             │
│     skills: JSON?                                           │
│     created_at: DateTime [AUTO]                             │
│     updated_at: DateTime [AUTO]                             │
│ FK  assigned_to: User?                                      │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ 1:N
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                       CallLog                                │
├─────────────────────────────────────────────────────────────┤
│ PK  id: Integer                                             │
│ FK  lead: Lead [CASCADE]                                    │
│     outcome: Choice [CONNECTED, VOICEMAIL, NO_ANSWER, ...]  │
│     duration_seconds: Integer [≥0]                          │
│     interest_level: Integer [0-5]                           │
│     notes: Text?                                            │
│ FK  called_by: User?                                        │
│     called_at: DateTime [AUTO]                              │
└─────────────────────────────────────────────────────────────┘

                    Lead
                    │ 1:N
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                       EmailLog                               │
├─────────────────────────────────────────────────────────────┤
│ PK  id: Integer                                             │
│ FK  lead: Lead [CASCADE]                                    │
│     email_type: Choice [WELCOME, FOLLOWUP_1, ...]           │
│     subject: String(255)                                    │
│     brevo_message_id: String(100)?                          │
│     sent_at: DateTime [AUTO]                                │
│     opened_at: DateTime?                                    │
│     clicked_at: DateTime?                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      SyncStatus                              │
├─────────────────────────────────────────────────────────────┤
│ PK  source: String(50) [UNIQUE]                             │
│     last_sync_at: DateTime                                  │
│     last_lead_id: Integer                                   │
│     leads_imported: Integer [≥0]                            │
│     leads_updated: Integer [≥0]                             │
│     leads_skipped: Integer [≥0]                             │
└─────────────────────────────────────────────────────────────┘

                    User
                    │ 1:N
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    SavedFilter                               │
├─────────────────────────────────────────────────────────────┤
│ PK  id: Integer                                             │
│ FK  user: User [CASCADE]                                    │
│     name: String(100)                                       │
│     description: Text?                                      │
│     filter_params: JSON                                     │
│     is_shared: Boolean [default: False]                     │
│     created_at: DateTime [AUTO]                             │
│     updated_at: DateTime [AUTO]                             │
│ UNIQUE (user, name)                                         │
└─────────────────────────────────────────────────────────────┘
```

## Beziehungen

### Lead ↔ User (assigned_to)

- **Typ:** Many-to-One (Optional)
- **Cascade:** SET_NULL (Lead bleibt erhalten wenn User gelöscht wird)
- **Verwendung:** Zuweisung von Leads an Teammitglieder

### Lead ↔ CallLog

- **Typ:** One-to-Many
- **Cascade:** CASCADE (CallLogs werden gelöscht wenn Lead gelöscht wird)
- **Related Name:** `call_logs`
- **Verwendung:** Protokollierung aller Anrufe zu einem Lead

### Lead ↔ EmailLog

- **Typ:** One-to-Many
- **Cascade:** CASCADE
- **Related Name:** `email_logs`
- **Verwendung:** Tracking von Email-Kommunikation (Brevo Integration)

### User ↔ SavedFilter

- **Typ:** One-to-Many
- **Cascade:** CASCADE
- **Related Name:** `saved_filters`
- **Verwendung:** Gespeicherte Filter pro Benutzer

### User ↔ CallLog (called_by)

- **Typ:** Many-to-One (Optional)
- **Cascade:** SET_NULL
- **Verwendung:** Tracking wer den Anruf getätigt hat

## Indexes

### Lead Model

#### Single-Column Indexes

```sql
CREATE INDEX idx_status ON leads_lead(status);
CREATE INDEX idx_source ON leads_lead(source);
CREATE INDEX idx_quality_score ON leads_lead(quality_score);
CREATE INDEX idx_lead_type ON leads_lead(lead_type);
CREATE INDEX idx_created_at ON leads_lead(created_at);
CREATE INDEX idx_email_normalized ON leads_lead(email_normalized);
CREATE INDEX idx_normalized_phone ON leads_lead(normalized_phone);
CREATE INDEX idx_updated_at ON leads_lead(updated_at);
CREATE INDEX idx_last_called ON leads_lead(last_called_at);
CREATE INDEX idx_confidence ON leads_lead(confidence_score);
CREATE INDEX idx_data_quality ON leads_lead(data_quality);
CREATE INDEX idx_interest_level ON leads_lead(interest_level);
```

#### Composite Indexes

```sql
-- Häufige Filter-Kombinationen
CREATE INDEX idx_lead_type_status ON leads_lead(lead_type, status);
CREATE INDEX idx_status_quality ON leads_lead(status, quality_score);
CREATE INDEX idx_source_created ON leads_lead(source, created_at);
CREATE INDEX idx_assigned_status ON leads_lead(assigned_to, status);

-- Sortierung
CREATE INDEX idx_quality_created_desc 
    ON leads_lead(quality_score DESC, created_at DESC);
```

### CallLog Model

```sql
CREATE INDEX idx_calllog_lead ON leads_calllog(lead_id);
CREATE INDEX idx_calllog_called_by ON leads_calllog(called_by_id);
CREATE INDEX idx_calllog_called_at ON leads_calllog(called_at);
```

### EmailLog Model

```sql
CREATE INDEX idx_emaillog_lead ON leads_emaillog(lead_id);
CREATE INDEX idx_emaillog_sent_at ON leads_emaillog(sent_at);
```

## Constraints

### Lead Model

#### Check Constraints

```sql
-- Wertebereich-Constraints
ALTER TABLE leads_lead ADD CONSTRAINT quality_score_range
    CHECK (quality_score >= 0 AND quality_score <= 100);

ALTER TABLE leads_lead ADD CONSTRAINT confidence_score_range
    CHECK (confidence_score IS NULL OR 
           (confidence_score >= 0 AND confidence_score <= 100));

ALTER TABLE leads_lead ADD CONSTRAINT data_quality_range
    CHECK (data_quality IS NULL OR 
           (data_quality >= 0 AND data_quality <= 100));

ALTER TABLE leads_lead ADD CONSTRAINT interest_level_range
    CHECK (interest_level >= 0 AND interest_level <= 5);

-- Positive-Werte-Constraints
ALTER TABLE leads_lead ADD CONSTRAINT experience_years_positive
    CHECK (experience_years IS NULL OR experience_years >= 0);

ALTER TABLE leads_lead ADD CONSTRAINT hiring_volume_positive
    CHECK (hiring_volume IS NULL OR hiring_volume >= 0);

ALTER TABLE leads_lead ADD CONSTRAINT call_count_positive
    CHECK (call_count >= 0);

ALTER TABLE leads_lead ADD CONSTRAINT email_sent_count_positive
    CHECK (email_sent_count >= 0);

ALTER TABLE leads_lead ADD CONSTRAINT email_opens_positive
    CHECK (email_opens >= 0);

ALTER TABLE leads_lead ADD CONSTRAINT email_clicks_positive
    CHECK (email_clicks >= 0);
```

### SavedFilter Model

```sql
-- Unique Constraint
ALTER TABLE leads_savedfilter ADD CONSTRAINT unique_user_filter_name
    UNIQUE (user_id, name);
```

## Enumerations (Choices)

### Lead.Status

```python
NEW = 'NEW'                    # Neu
CONTACTED = 'CONTACTED'        # Kontaktiert
VOICEMAIL = 'VOICEMAIL'        # Voicemail
INTERESTED = 'INTERESTED'      # Interessiert
INTERVIEW = 'INTERVIEW'        # Interview
HIRED = 'HIRED'                # Eingestellt
NOT_INTERESTED = 'NOT_INTERESTED'  # Kein Interesse
INVALID = 'INVALID'            # Ungültig
```

### Lead.Source

```python
SCRAPER = 'scraper'            # Scraper
LANDING_PAGE = 'landing_page'  # Landing Page
MANUAL = 'manual'              # Manuell
REFERRAL = 'referral'          # Empfehlung
```

### Lead.LeadType

```python
ACTIVE_SALESPERSON = 'active_salesperson'  # Aktiver Vertriebler
TEAM_MEMBER = 'team_member'                # Team-Mitglied
FREELANCER = 'freelancer'                  # Freelancer
HR_CONTACT = 'hr_contact'                  # HR-Kontakt
CANDIDATE = 'candidate'                    # Jobsuchender
TALENT_HUNT = 'talent_hunt'                # Talent Hunt
RECRUITER = 'recruiter'                    # Recruiter
JOB_AD = 'job_ad'                         # Stellenanzeige
COMPANY = 'company'                        # Firmenkontakt
INDIVIDUAL = 'individual'                  # Einzelperson
UNKNOWN = 'unknown'                        # Unbekannt
```

### CallLog.Outcome

```python
CONNECTED = 'CONNECTED'              # Erreicht
VOICEMAIL = 'VOICEMAIL'              # Voicemail
NO_ANSWER = 'NO_ANSWER'              # Keine Antwort
BUSY = 'BUSY'                        # Besetzt
WRONG_NUMBER = 'WRONG_NUMBER'        # Falsche Nummer
CALLBACK = 'CALLBACK'                # Rückruf vereinbart
INTERESTED = 'INTERESTED'            # Interessiert
NOT_INTERESTED = 'NOT_INTERESTED'    # Kein Interesse
```

### EmailLog.EmailType

```python
WELCOME = 'WELCOME'                  # Willkommen
FOLLOWUP_1 = 'FOLLOWUP_1'           # Follow-Up 1
FOLLOWUP_2 = 'FOLLOWUP_2'           # Follow-Up 2
FOLLOWUP_3 = 'FOLLOWUP_3'           # Follow-Up 3
INTERVIEW_INVITE = 'INTERVIEW_INVITE'  # Interview-Einladung
CUSTOM = 'CUSTOM'                    # Individuell
```

## Query-Beispiele

### 1. Leads mit hoher Qualität und Status NEW

```python
from leads.models import Lead

high_quality_leads = Lead.objects.filter(
    status=Lead.Status.NEW,
    quality_score__gte=80
).select_related('assigned_to')

# Verwendet: idx_status_quality
```

### 2. Talent Hunt Leads ohne Kontaktperson

```python
unassigned_talent = Lead.objects.filter(
    lead_type=Lead.LeadType.TALENT_HUNT,
    assigned_to__isnull=True
).order_by('-quality_score')

# Verwendet: idx_lead_type_status, idx_quality_score
```

### 3. Leads mit erfolgreichen Anrufen

```python
from django.db.models import Q

contacted_leads = Lead.objects.filter(
    call_logs__outcome=CallLog.Outcome.CONNECTED,
    call_logs__interest_level__gte=3
).distinct()

# Verwendet: Foreign Key Index
```

### 4. Email-Engagement-Tracking

```python
engaged_leads = Lead.objects.filter(
    email_logs__opened_at__isnull=False
).annotate(
    total_opens=Count('email_logs__opened_at'),
    total_clicks=Count('email_logs__clicked_at')
).filter(total_opens__gte=2)

# Verwendet: Foreign Key Index, Aggregation
```

### 5. Leads nach Quelle und Datum

```python
from datetime import datetime, timedelta

recent_scraper_leads = Lead.objects.filter(
    source=Lead.Source.SCRAPER,
    created_at__gte=datetime.now() - timedelta(days=7)
).order_by('-created_at')

# Verwendet: idx_source_created
```

## Trigger und Automatisierungen

### CallLog.save() - Lead Update

Wenn ein CallLog gespeichert wird, werden automatisch folgende Lead-Felder aktualisiert:

```python
# In CallLog.save()
self.lead.call_count = self.lead.call_logs.count()
self.lead.last_called_at = self.called_at

if self.interest_level > 0:
    self.lead.interest_level = self.interest_level

if self.outcome == self.Outcome.CONNECTED and self.interest_level >= 3:
    self.lead.status = Lead.Status.INTERESTED
elif self.outcome == self.Outcome.VOICEMAIL:
    if self.lead.status == Lead.Status.NEW:
        self.lead.status = Lead.Status.VOICEMAIL
# ... weitere Status-Updates

self.lead.save()
```

### Lead.save() - Normalisierung

```python
# In Lead.save()
from leads.utils.normalization import normalize_email, normalize_phone

self.email_normalized = normalize_email(self.email)
self.normalized_phone = normalize_phone(self.telefon)

super().save(*args, **kwargs)
```

## Optimierungshinweise

### 1. Select Related verwenden

```python
# ✓ RICHTIG - 1 Query statt N+1
leads = Lead.objects.filter(
    status=Lead.Status.NEW
).select_related('assigned_to')

for lead in leads:
    print(lead.assigned_to.username)  # Kein zusätzlicher Query

# ✗ FALSCH - N+1 Queries
leads = Lead.objects.filter(status=Lead.Status.NEW)
for lead in leads:
    print(lead.assigned_to.username)  # Für jeden Lead 1 Query!
```

### 2. Prefetch Related für Reverse Relations

```python
# ✓ RICHTIG - 2 Queries total
leads = Lead.objects.prefetch_related('call_logs')

for lead in leads:
    for call in lead.call_logs.all():  # Kein zusätzlicher Query
        print(call.outcome)

# ✗ FALSCH - N+1 Queries
leads = Lead.objects.all()
for lead in leads:
    for call in lead.call_logs.all():  # Für jeden Lead 1 Query!
        print(call.outcome)
```

### 3. Only/Defer für große Felder

```python
# ✓ RICHTIG - Nur benötigte Felder laden
leads = Lead.objects.only('id', 'name', 'email', 'telefon')

# ✓ RICHTIG - Große Felder ausschließen
leads = Lead.objects.defer('ai_summary', 'profile_text', 'notes')
```

## Sicherheitsüberlegungen

### 1. SQL Injection Prevention

Alle Queries verwenden Django ORM parametrisierte Queries:

```python
# ✓ SICHER - Parametrisiert
Lead.objects.filter(email=user_input)

# ✗ UNSICHER - Raw SQL mit String-Interpolation
Lead.objects.raw(f"SELECT * FROM leads WHERE email = '{user_input}'")
```

### 2. Cascade-Verhalten

```
Lead gelöscht → CallLogs CASCADE → Automatisch gelöscht
Lead gelöscht → EmailLogs CASCADE → Automatisch gelöscht
User gelöscht → Lead.assigned_to SET NULL → Lead bleibt erhalten
User gelöscht → SavedFilter CASCADE → Filter gelöscht
```

## Weiterentwicklung

### Geplante Erweiterungen

1. **Lead-Activity-Tracking**
   ```python
   class LeadActivity(models.Model):
       lead = ForeignKey(Lead, CASCADE)
       action = CharField()  # 'created', 'updated', 'contacted'
       timestamp = DateTimeField(auto_now_add=True)
       user = ForeignKey(User, SET_NULL)
   ```

2. **Lead-Tags Normalisierung**
   ```python
   class Tag(models.Model):
       name = CharField(unique=True)
   
   class LeadTag(models.Model):
       lead = ForeignKey(Lead)
       tag = ForeignKey(Tag)
       created_at = DateTimeField(auto_now_add=True)
   ```

3. **Company Normalisierung**
   ```python
   class Company(models.Model):
       name = CharField()
       industry = CharField()
       size = CharField()
       
   # Lead.company wird zu ForeignKey
   ```
