# LUCA NRW Scraper - Architekturübersicht

## Zweck
Dieses Dokument beschreibt die Gesamtarchitektur des LUCA NRW Scraper Systems auf Engineering-Level. Es dient als Referenz für das Team, neue Contributors und bei der Planung von Features.

---

## Systemübersicht

LUCA ist ein modulares Lead-Scraping- und CRM-System, das automatisch Vertriebskontakte in NRW findet, bewertet und verwaltet.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LUCA NRW Scraper System                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Scraper    │───▶│    Parser    │───▶│   Scoring    │───▶│   Database   │
│    Layer     │    │    Layer     │    │    Layer     │    │    Layer     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                       │
                                                                       ▼
                                                            ┌──────────────────┐
                                                            │   Django CRM UI  │
                                                            │  (Presentation)  │
                                                            └──────────────────┘
```

---

## Module und Komponenten

### 1. Scraper Layer (Data Acquisition)
**Dateien**: `scriptname.py`, `browser_extractor.py`, `social_scraper.py`

**Verantwortlichkeiten**:
- Google Custom Search API Integration (mit Key-Rotation)
- Bing/DuckDuckGo Fallback-Suche
- Website-Crawling mit Respekt für robots.txt
- Sitemap-Parsing
- PDF-Extraktion
- Login-Handling für geschützte Portale
- Rate-Limiting und Backoff-Strategien

**Ausgabe**: Raw HTML, Text-Content, URLs, Metadaten

**Konfiguration**: 
- Dorks (Search Queries): `dorks_extended.py`, `adaptive_dorks.py`
- Portalspezifische Handler: `providers/` Verzeichnis
- Login-Credentials: `.env` Datei

**Key Dependencies**:
- `curl_cffi`, `aiohttp` - HTTP Requests
- `BeautifulSoup` - HTML Parsing
- `pypdf` - PDF Processing

---

### 2. Parser/Extraction Layer
**Dateien**: `stream2_extraction_layer/`, `phone_extractor.py`, `lead_validation.py`

**Verantwortlichkeiten**:
- Kontaktdaten-Extraktion (Email, Telefon, WhatsApp)
- Namen-Extraktion mit Heuristiken
- Rollen/Positions-Erkennung
- OpenAI/LLM-basierte Datenextraktion (optional)
- Firmeninfo-Anreicherung
- Open-Data-Integration (Handelsregister, etc.)
- Validation und Normalisierung

**Komponenten**:
- `extraction_enhanced.py`: Erweiterte Name/Role-Extraction
- `open_data_resolver.py`: Öffentliche Datenquellen-Integration
- `phone_extractor.py`: Telefonnummer-Extraktion und Validierung
- `lead_validation.py`: Lead-Qualitäts-Checks

**Eingabe**: Raw HTML/Text von Scraper
**Ausgabe**: Strukturierte Lead-Daten (Dict/JSON)

**Key Dependencies**:
- `openai` - LLM-basierte Extraktion (optional)
- `phonenumbers` - Telefonnummer-Validierung
- Regex patterns: `phone_patterns.py`

---

### 3. Scoring Layer
**Dateien**: `stream3_scoring_layer/`

**Verantwortlichkeiten**:
- Lead-Qualitätsbewertung (Quality Score: 0-100)
- Confidence-Berechnung
- Data-Quality-Bewertung
- Branchen-/Kontakt-Signal-Scoring
- WhatsApp/Telefon/Email-Boost
- Job-Posting-Erkennung und Penalty

**Komponenten**:
- `scoring_enhanced.py`: Hauptlogik für Scoring-Algorithmus
- `quality_metrics.py`: Qualitätsmetriken-Definitionen

**Eingabe**: Strukturierte Lead-Daten
**Ausgabe**: Lead-Daten mit Quality Score, Confidence, Data Quality

**Scoring-Faktoren**:
- Kontaktqualität: Email (40 Pkt), Telefon (30 Pkt), WhatsApp (20 Pkt)
- Branchensignale: Keywords, Firmentyp
- Vollständigkeit: Name, Rolle, Firma
- Penaltys: Job-Postings (-30 Pkt), Mobile-only (-10 Pkt)

---

### 4. Database Layer
**Dateien**: `telis_recruitment/leads/models.py`, SQLite DB

**Verantwortlichkeiten**:
- Persistierung von Leads
- Deduplication (URL, Email, Telefon)
- Tracking von Scraper-Runs
- Logs und Metriken
- Status-Tracking (NEW → CONTACTED → etc.)

**Schema-Haupttabellen**:
```
leads
├── id (PK)
├── name, email, telefon, whatsapp_link
├── status (NEW, CONTACTED, etc.)
├── source (scraper, landing_page, manual)
├── quality_score, confidence_score, data_quality
├── lead_type (active_salesperson, candidate, etc.)
├── company, role, location
├── ai_category, ai_summary
├── tags (JSON), skills (JSON)
├── created_at, updated_at
└── assigned_to (FK User)

scraper_runs
├── id (PK)
├── start_time, end_time
├── status (running, completed, failed)
├── industry, qpi, mode
├── leads_found, leads_inserted
└── logs (TEXT)

urls_seen
├── url (PK)
├── domain
├── first_seen, last_checked
└── status (scraped, skipped, failed)
```

**Migrations**: `telis_recruitment/leads/migrations/`, `telis_recruitment/*/migrations/`

**Key Dependencies**:
- Django ORM
- SQLite3 (default), PostgreSQL (production-ready)

---

### 5. CRM UI (Presentation Layer)
**Dateien**: `telis_recruitment/`

**Verantwortlichkeiten**:
- Lead-Management (Liste, Detail, Bearbeitung)
- Scraper-Steuerung (Start/Stop/Config)
- Dashboard mit KPIs
- Export (CSV/Excel)
- Landing Page Builder
- Email-Integration (Brevo)
- Mailbox (IMAP/SMTP)
- Benutzer- und Rechteverwaltung

**Django Apps**:
```
telis_recruitment/
├── leads/              # Lead-Management
├── scraper_control/    # Scraper-Steuerung
├── pages/              # Landing Page Builder
├── email_templates/    # Email-Automatisierung
├── mailbox/            # Email-Integration
├── reports/            # Reports & Analytics
├── ai_config/          # AI-Provider-Konfiguration
└── telis/              # Projekt-Settings
```

**Key Endpoints**:
- `/crm/` - Dashboard
- `/crm/leads/` - Lead-Liste
- `/crm/scraper/` - Scraper-Control
- `/api/leads/` - REST API
- `/admin/` - Django Admin

**Key Dependencies**:
- Django 5.0+
- Django REST Framework
- Bootstrap 5

---

## Datenfluss

### Standard Scraping Flow

```
1. Scraper Start
   ├─ User initiiert über CRM UI (/crm/scraper/)
   ├─ ProcessManager startet scriptname.py subprocess
   └─ ScraperRun-Objekt wird erstellt

2. Query-Generierung
   ├─ Adaptive Dorks wählt Search Queries basierend auf Industry
   ├─ Queries werden aus dorks_extended.py geladen
   └─ Learning Engine optimiert Dorks basierend auf Erfolg

3. Suche & Crawling
   ├─ Google CSE API Request (mit Key-Rotation)
   ├─ Fallback zu Bing/DuckDuckGo bei Fehler
   ├─ URL-Deduplication gegen urls_seen Tabelle
   └─ robots.txt-Check (gecached)

4. Content-Fetch
   ├─ HTTP GET mit curl_cffi (Browser-Simulation)
   ├─ Retry-Logik bei Timeout/Error
   ├─ SSL-Fallback bei Zertifikatsfehler
   └─ PDF-Download und Text-Extraktion bei Bedarf

5. Content-Filtering
   ├─ Domain-Blocklist (News, Behörden, Job-Boards)
   ├─ Path-Whitelist (team, kontakt, impressum)
   └─ Content-Validation (Min. Textlänge)

6. Extraktion
   ├─ BeautifulSoup HTML-Parsing
   ├─ Email-Regex-Extraktion
   ├─ Telefon-Extraktion mit phone_extractor.py
   ├─ WhatsApp-Link-Erkennung
   ├─ Namen-Heuristik (extract_name_enhanced)
   ├─ Rollen-Erkennung (extract_role_with_context)
   └─ Optional: OpenAI JSON-Extraktion

7. Validation
   ├─ validate_lead_before_insert() Check
   ├─ Telefonnummer-Normalisierung
   ├─ Email-Format-Validierung
   ├─ Job-Posting-Erkennung
   └─ Mobile-Number-Check

8. Scoring
   ├─ scoring_enhanced.py berechnet Quality Score
   ├─ Kontaktqualität-Bewertung
   ├─ Branchensignal-Erkennung
   ├─ Vollständigkeits-Check
   └─ Penalty-Anwendung (Job Ads, Mobile-only)

9. Enrichment
   ├─ Firma-Resolution (open_data_resolver)
   ├─ Standort-Extraktion
   ├─ Tags-Generierung
   └─ Confidence-Berechnung

10. Persistierung
    ├─ Deduplication-Check (email, telefon, url)
    ├─ INSERT INTO leads Table
    ├─ URL in urls_seen markieren
    └─ ScraperRun-Stats aktualisieren

11. Logging & Monitoring
    ├─ Real-time Logs über SSE an CRM UI
    ├─ Metriken in metrics.py tracken
    ├─ Rejection-Stats für Learning Engine
    └─ ScraperRun.logs persistent speichern
```

### Alternative Flows

**Landing Page Opt-In Flow**:
```
User füllt Formular → API POST /api/opt-in/ → Validation → Lead-Insert mit source='landing_page'
```

**Manueller Import Flow**:
```
CSV-Upload → CSVImporter → Validation → Batch-Insert → Deduplication-Report
```

**Email-Integration Flow**:
```
IMAP-Poll → Email-Parse → Thread-Detection → Lead-Matching → Conversation-Storage
```

---

## Schnittstellen und Datenformate

### Interne Schnittstellen

#### 1. Scraper → Parser
**Format**: Dict/JSON
```python
{
    "url": "https://example.com/team",
    "html": "<html>...</html>",
    "text": "Extracted text content...",
    "title": "Team - Example Company",
    "domain": "example.com",
    "metadata": {
        "status_code": 200,
        "content_type": "text/html",
        "fetch_timestamp": "2024-01-15T10:30:00Z"
    }
}
```

#### 2. Parser → Scoring
**Format**: Dict/JSON (Lead-Rohdaten)
```python
{
    "name": "Max Mustermann",
    "email": "max@example.com",
    "telefon": "+49 151 12345678",
    "phone_type": "mobile",
    "whatsapp_link": "https://wa.me/4915112345678",
    "company": "Example GmbH",
    "role": "Vertriebsleiter",
    "location": "Düsseldorf, NRW",
    "source_url": "https://example.com/team",
    "source_detail": "Google CSE: recruiter dork",
    "tags": ["sales", "b2b", "nrw"],
    "raw_context": "Bio text from page..."
}
```

#### 3. Scoring → Database
**Format**: Dict/JSON (Scored Lead)
```python
{
    # ... alle Felder von Parser →
    "quality_score": 85,
    "confidence_score": 75,
    "data_quality": 90,
    "lead_type": "active_salesperson",
    "ai_category": "B2B Sales",
    "ai_summary": "Experienced sales leader in B2B sector..."
}
```

### Externe Schnittstellen

#### 1. REST API (Django REST Framework)
**Base URL**: `/api/`

**Endpoints**:
- `GET /api/leads/` - List Leads (pagination, filtering)
- `GET /api/leads/{id}/` - Lead Detail
- `PUT /api/leads/{id}/` - Update Lead
- `POST /api/opt-in/` - Landing Page Opt-In
- `GET /api/scraper/status/` - Scraper Status
- `POST /api/scraper/start/` - Start Scraper
- `POST /api/scraper/stop/` - Stop Scraper

**Auth**: Session-based (Django) oder Token-based (geplant)

**Rate Limiting**: 
- Opt-In API: 10/minute, 100/hour (via django-ratelimit)
- Internal APIs: Session-based, keine Limits

#### 2. Google Custom Search API
**Endpoint**: `https://www.googleapis.com/customsearch/v1`

**Request**:
```
GET /customsearch/v1?key={API_KEY}&cx={CX_ID}&q={query}&start={offset}&dateRestrict={d30}
```

**Response**: JSON mit `items[]` Array von Search Results

**Rate Limits**: 100 Queries/Day pro Key (Key-Rotation implementiert)

#### 3. OpenAI API (Optional)
**Model**: gpt-4o-mini oder gpt-3.5-turbo

**Request**:
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "Extract contact info..."},
    {"role": "user", "content": "HTML: ..."}
  ],
  "response_format": {"type": "json_object"}
}
```

**Response**: JSON mit strukturierten Lead-Daten

#### 4. Brevo Email API
**Endpoint**: `https://api.brevo.com/v3/`

**Key Operations**:
- Create Contact: `POST /contacts`
- Send Email: `POST /smtp/email`
- Get Templates: `GET /smtp/templates`

**Auth**: API Key in Header `api-key: {BREVO_API_KEY}`

---

## Deployment-Architektur

### Development
```
Local Machine
├── SQLite DB (scraper.db)
├── Django Dev Server (runserver)
├── Scraper Subprocess (scriptname.py)
└── File-based Logs
```

### Production (Docker)
```
Docker Compose
├── web (Django Gunicorn)
│   ├── Port 8000
│   ├── SQLite Volume Mount
│   └── Environment Variables
├── (optional) nginx
│   ├── Port 80/443
│   ├── Static Files
│   └─ Reverse Proxy zu web
└── (optional) redis
    └── Celery Task Queue
```

### Production (Cloud Platform)
```
Railway/Render/Fly.io
├── Web Service (Django)
│   ├── Persistent Volume für SQLite
│   ├── Environment Variables
│   └── Auto-Deploy bei Git Push
├── (optional) PostgreSQL Service
└── (optional) Redis Service
```

**Persistence**:
- SQLite: Volume-mounted in `/app/data/`
- PostgreSQL: Managed Service (für Skalierung)
- Uploaded Files: Volume oder Object Storage (S3)

**Scaling Considerations**:
- Scraper: Single-Prozess (parallel crawling intern via asyncio)
- Web: Multi-Prozess möglich (Gunicorn workers)
- Database: SQLite für < 100k Leads, PostgreSQL darüber
- Queue: Celery + Redis für Background Tasks (geplant)

---

## Sicherheitsarchitektur

### Authentication & Authorization
- Django Session-based Auth
- CSRF-Protection auf allen POST-Requests
- Role-based Access Control (Admin, Manager, Telefonist)

### Data Protection
- SQL-Injection-Schutz via Django ORM
- XSS-Schutz via Template-Auto-Escaping
- Rate Limiting auf öffentlichen Endpoints
- Environment Variables für Secrets (nie im Code)

### External Access
- robots.txt-Respekt beim Crawling
- User-Agent-Identifikation
- Backoff bei Rate-Limiting
- SSL/TLS für alle externen APIs

---

## Performance & Monitoring

### Metrics
- `metrics.py`: Custom Performance Metrics
- Scraper-Run-Stats: Leads/Minute, Success Rate
- Database Query Performance (Django Debug Toolbar in Dev)

### Logging
- Django Logging Framework
- Log Levels: DEBUG, INFO, WARNING, ERROR
- Real-time Logs via Server-Sent Events (SSE)
- Persistent Logs in ScraperRun-Objekt

### Caching
- robots.txt Cache (in-memory)
- URL-Deduplication (urls_seen DB-Tabelle)
- (geplant) Redis für Session/Query-Cache

---

## Erweiterbarkeit

### Neues Portal integrieren
1. Provider-Handler in `providers/` erstellen
2. Dork in `dorks_extended.py` hinzufügen
3. Optional: Login-Handler in `login_handler.py`
4. Optional: Custom Extractor-Logik

### Neuer Datenquelle (neben Scraping)
1. API-Integration in `leads/services/` erstellen
2. Import-Command in `leads/management/commands/`
3. Serializer für Datenformat definieren
4. Source-Typ zu `Lead.Source` Choices hinzufügen

### Neue Bewertungsmetrik
1. Metric in `stream3_scoring_layer/quality_metrics.py`
2. Integration in `scoring_enhanced.py` Scoring-Funktion
3. Ggf. neues Feld in Lead-Model (mit Migration)

---

## Technologie-Stack

**Backend**:
- Python 3.11+
- Django 5.0+
- Django REST Framework
- SQLite/PostgreSQL

**Scraping**:
- curl_cffi (HTTP mit Browser-Fingerprinting)
- aiohttp (Async HTTP)
- BeautifulSoup (HTML Parsing)
- pypdf (PDF Extraction)

**Frontend**:
- Bootstrap 5
- Vanilla JavaScript
- GrapesJS (Landing Page Builder)

**External APIs**:
- Google Custom Search API
- OpenAI API (optional)
- Brevo Email API
- IMAP/SMTP

**Deployment**:
- Docker & Docker Compose
- Gunicorn (WSGI Server)
- nginx (optional Reverse Proxy)

---

## Bekannte Limitierungen

1. **SQLite Concurrency**: Bei hoher Last PostgreSQL empfohlen
2. **Google CSE**: 100 Queries/Day pro API-Key (Key-Rotation implementiert)
3. **Single Scraper Process**: Keine horizontale Skalierung (yet)
4. **robots.txt Caching**: Kein TTL, manueller Clear nötig
5. **Email-Extraktion**: Regex-basiert, kann False Positives haben

---

## Zukunftsplanung

**Geplante Features**:
- Celery Task Queue für Async-Processing
- PostgreSQL als Standard-DB
- Elasticsearch für Full-Text-Search
- WebSocket für Live-Updates (statt SSE)
- GraphQL API (zusätzlich zu REST)
- Multi-Tenant-Support

**Tech Debt**:
- Refactoring scriptname.py (zu groß, 400+ Zeilen)
- Test Coverage erhöhen (aktuell ~40%)
- API Dokumentation (OpenAPI/Swagger)
- Type Hints vervollständigen

---

## Weitere Ressourcen

- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Coding-Regeln und Konventionen
- [Playbooks](playbooks/) - Operative Anleitungen
- [INSTALLATION.md](INSTALLATION.md) - Setup-Anleitung
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment-Guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution-Guidelines
