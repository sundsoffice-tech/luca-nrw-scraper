# LUCA NRW Scraper - Coding Standards

## Zweck
Dieses Dokument definiert verbindliche Coding Standards für das LUCA-Projekt als Team-Vertrag. Alle Entwickler und Contributors müssen sich an diese Standards halten, um Code-Qualität, Wartbarkeit und Konsistenz sicherzustellen.

---

## 1. Allgemeine Prinzipien

### 1.1 Code-Qualität
- **Lesbarkeit über Cleverness**: Code wird öfter gelesen als geschrieben
- **Explizit über Implizit**: Keine "Magic" oder versteckte Side-Effects
- **DRY (Don't Repeat Yourself)**: Gemeinsame Logik extrahieren
- **KISS (Keep It Simple, Stupid)**: Einfache Lösungen bevorzugen
- **YAGNI (You Aren't Gonna Need It)**: Keine Features auf Vorrat

### 1.2 Konsistenz
- Folge existierenden Patterns im Codebase
- Bei Unsicherheit: Schaue dir ähnliche Implementierungen an
- Änderungen sollten sich nahtlos einfügen, nicht herausstechen

### 1.3 Verantwortlichkeit
- Jeder Commit sollte getestet sein (lokal)
- Code Review ist Pflicht für alle Änderungen
- Breche nie bewusst funktionierende Features

---

## 2. Python Code Style

### 2.1 PEP 8 Compliance
Wir folgen [PEP 8](https://peps.python.org/pep-0008/) mit diesen Spezifikationen:

**Indentation**:
- 4 Spaces (keine Tabs)
- Fortsetzungszeilen: 4 Spaces zusätzlich

**Line Length**:
- Max. 100 Zeichen (weich)
- Max. 120 Zeichen (hart)
- Docstrings: Max. 80 Zeichen

**Imports**:
```python
# Reihenfolge (mit Leerzeilen getrennt):
# 1. Standard Library
import os
import sys
from typing import Dict, List

# 2. Third-Party
from django.db import models
import requests

# 3. Local/App
from .models import Lead
from .utils import validate_email
```

**Whitespace**:
```python
# Gut
def function(arg1, arg2):
    result = arg1 + arg2
    return result

x = 5
y = 10

# Schlecht
def function( arg1,arg2 ):
    result=arg1+arg2
    return result
x=5
y=10
```

### 2.2 Naming Conventions

**Funktionen und Variablen**: `snake_case`
```python
def process_lead_data(lead_info):
    user_email = lead_info.get('email')
    is_valid = validate_email(user_email)
```

**Klassen**: `PascalCase`
```python
class LeadProcessor:
    pass

class ScraperManager:
    pass
```

**Konstanten**: `UPPER_SNAKE_CASE`
```python
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"
```

**Private Methoden/Attribute**: `_leading_underscore`
```python
class ScraperManager:
    def __init__(self):
        self._internal_state = {}
    
    def _helper_method(self):
        pass
```

**Geschützte Attribute**: `__double_leading_underscore` (selten)
```python
class Base:
    def __init__(self):
        self.__private = "truly private"
```

### 2.3 Type Hints
Verwende Type Hints für alle öffentlichen Funktionen:

```python
from typing import Optional, List, Dict, Any

def extract_emails(text: str, validate: bool = True) -> List[str]:
    """Extract email addresses from text."""
    pass

def get_lead(lead_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve lead by ID."""
    pass
```

**Wann Type Hints verwenden**:
- ✅ Alle öffentlichen Funktionen/Methoden
- ✅ Komplexe Datenstrukturen
- ❌ Triviale Lambdas oder Closures
- ❌ Offensichtliche Fälle (z.B. `def __str__(self) -> str`)

### 2.4 Docstrings
Alle öffentlichen Funktionen, Klassen und Module müssen Docstrings haben.

**Format**: Google Style Docstrings

```python
def import_leads_from_csv(
    file_path: str,
    dry_run: bool = False,
    skip_validation: bool = False
) -> Dict[str, Any]:
    """
    Import leads from a CSV file into the database.
    
    This function reads a CSV file, validates each row, and inserts
    valid leads into the database. Duplicates are automatically skipped.
    
    Args:
        file_path: Path to the CSV file to import.
        dry_run: If True, perform validation only without saving. Defaults to False.
        skip_validation: If True, skip email/phone validation. Defaults to False.
    
    Returns:
        Dictionary containing import statistics:
            - 'total_rows': Total number of rows processed
            - 'inserted': Number of leads successfully inserted
            - 'skipped': Number of duplicates skipped
            - 'errors': List of error messages
    
    Raises:
        FileNotFoundError: If the CSV file does not exist.
        PermissionError: If the file cannot be read.
        ValueError: If the CSV format is invalid.
    
    Example:
        >>> result = import_leads_from_csv('/path/to/leads.csv')
        >>> print(f"Inserted: {result['inserted']}")
        Inserted: 42
    """
    pass
```

**Kürzer für einfache Funktionen**:
```python
def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format."""
    pass
```

### 2.5 Kommentare
- **Bevorzuge Code, der sich selbst erklärt** über Kommentare
- Kommentare sollen das **WARUM** erklären, nicht das **WAS**
- Kommentare aktualisieren, wenn Code sich ändert

```python
# Gut: Erklärt WARUM
# We use a timeout of 10s because some portals have slow response times
# but longer timeouts lead to queue buildup
timeout = 10

# Schlecht: Erklärt offensichtliches WAS
# Set timeout to 10
timeout = 10
```

**TODO-Kommentare**:
```python
# TODO(username): Add rate limiting for this endpoint
# FIXME(username): Race condition when two processes insert same lead
# XXX: This is a temporary workaround for Issue #123
```

---

## 3. Logging-Konventionen

### 3.1 Log Levels

**DEBUG**: Detaillierte Informationen für Debugging
```python
logger.debug(f"Fetching URL: {url} with params: {params}")
logger.debug(f"Regex matched: {match.groups()}")
```

**INFO**: Normale Programm-Ereignisse
```python
logger.info(f"Scraper started with industry={industry}, qpi={qpi}")
logger.info(f"Lead inserted: {lead.name} ({lead.email})")
logger.info(f"ScraperRun completed: {stats['leads_found']} leads found")
```

**WARNING**: Unerwartete, aber handhabbare Ereignisse
```python
logger.warning(f"API rate limit reached, switching to backup key")
logger.warning(f"robots.txt not found for {domain}, proceeding anyway")
logger.warning(f"Lead validation failed: {validation_errors}")
```

**ERROR**: Fehler, die ein Feature beeinträchtigen
```python
logger.error(f"Failed to fetch {url}: {str(e)}")
logger.error(f"Database insert failed for lead {lead_id}: {str(e)}")
logger.error(f"OpenAI API error: {response.status_code}")
```

**CRITICAL**: Schwere Fehler, die das gesamte System beeinträchtigen
```python
logger.critical(f"Database connection lost: {str(e)}")
logger.critical(f"All API keys exhausted, cannot continue")
```

### 3.2 Logging Best Practices

**Immer Logger verwenden, nie `print()`**:
```python
# Gut
import logging
logger = logging.getLogger(__name__)
logger.info("Lead processed")

# Schlecht
print("Lead processed")
```

**Strukturiertes Logging**:
```python
# Gut: Strukturiert, maschinell parsbar
logger.info(
    "Lead created",
    extra={
        'lead_id': lead.id,
        'source': lead.source,
        'quality_score': lead.quality_score
    }
)

# Akzeptabel: Wenn extra nicht möglich
logger.info(f"Lead created: id={lead.id}, source={lead.source}, score={lead.quality_score}")
```

**Exception-Logging mit Stack Trace**:
```python
try:
    process_lead(lead)
except Exception as e:
    logger.error(f"Failed to process lead {lead.id}: {str(e)}", exc_info=True)
    # exc_info=True fügt automatisch Stack Trace hinzu
```

**Sensible Daten nicht loggen**:
```python
# Schlecht
logger.info(f"User logged in: {username} with password {password}")

# Gut
logger.info(f"User logged in: {username}")
```

### 3.3 Performance-Logging
Für Performance-kritische Operationen:

```python
import time

start_time = time.time()
result = expensive_operation()
elapsed = time.time() - start_time

if elapsed > 5.0:  # Nur langsame Ops loggen
    logger.warning(f"Slow operation: {operation_name} took {elapsed:.2f}s")
```

---

## 4. Error Handling

### 4.1 Exception-Handling-Regeln

**Regel 1: Fange spezifische Exceptions**
```python
# Gut
try:
    lead = Lead.objects.get(email=email)
except Lead.DoesNotExist:
    logger.warning(f"Lead not found: {email}")
    return None
except Lead.MultipleObjectsReturned:
    logger.error(f"Multiple leads with email: {email}")
    raise

# Schlecht
try:
    lead = Lead.objects.get(email=email)
except:  # Niemals bare except!
    return None
```

**Regel 2: Exceptions nicht verschlucken**
```python
# Gut
try:
    process_lead(lead)
except ValueError as e:
    logger.error(f"Validation error: {str(e)}")
    raise  # Re-raise wenn nicht handhabbar

# Schlecht
try:
    process_lead(lead)
except ValueError:
    pass  # Fehler wird verschluckt!
```

**Regel 3: Eigene Exception-Klassen für Domain-Logik**
```python
class LeadValidationError(Exception):
    """Raised when lead data fails validation."""
    pass

class ScraperConfigError(Exception):
    """Raised when scraper configuration is invalid."""
    pass

# Verwendung
def validate_lead(lead):
    if not lead.email and not lead.telefon:
        raise LeadValidationError("Lead must have email or phone")
```

### 4.2 Retry-Logik

**Wann Retry**:
- Netzwerk-Timeouts (3x mit Backoff)
- Rate-Limit-Errors (1x nach Delay)
- Temporäre Server-Errors (5xx, 2x)

**Wann Skip**:
- Validation-Errors (4xx Client Errors)
- Permission-Errors (401, 403)
- Resource Not Found (404)

**Wann Fail (Run abbrechen)**:
- Database Connection Lost
- Alle API-Keys erschöpft
- Kritische Config-Fehler

**Implementierung**:
```python
import time

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def fetch_with_retry(url: str) -> str:
    """Fetch URL with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.Timeout:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Timeout fetching {url} after {MAX_RETRIES} attempts")
                raise
            delay = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {delay}s")
            time.sleep(delay)
        except requests.HTTPError as e:
            if e.response.status_code >= 500:
                # Server error, retry
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
            # Client error (4xx) oder finale 5xx, nicht retry
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise
```

### 4.3 Graceful Degradation
Bei nicht-kritischen Fehlern: Feature deaktivieren, aber weiterlaufen

```python
# Beispiel: OpenAI-Extraktion fehlschlägt
try:
    lead_data = extract_with_openai(html)
except OpenAIError as e:
    logger.warning(f"OpenAI extraction failed, falling back to regex: {e}")
    lead_data = extract_with_regex(html)

# Beispiel: Enrichment fehlschlägt
try:
    company_info = enrich_with_open_data(company_name)
except Exception as e:
    logger.warning(f"Enrichment failed for {company_name}: {e}")
    company_info = None  # Proceed without enrichment
```

---

## 5. Naming Schemas

### 5.1 Neue Crawler/Portale

**Dateiname**: `providers/{portal_name}_handler.py`

Beispiele:
- `providers/stepstone_handler.py`
- `providers/indeed_handler.py`
- `providers/xing_handler.py`

**Klassenname**: `{PortalName}Handler`
```python
# providers/stepstone_handler.py
class StepstoneHandler:
    """Handler for Stepstone job portal."""
    
    PORTAL_NAME = "stepstone"
    BASE_URL = "https://www.stepstone.de"
    
    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL."""
        return "stepstone.de" in url
    
    def extract(self, html: str, url: str) -> dict:
        """Extract lead data from Stepstone page."""
        pass
```

**Dork-Key**: `{portal}_{context}`
```python
# dorks_extended.py
INDUSTRY_DORKS = {
    "stepstone_recruiter": [
        'site:stepstone.de "personalvermittlung" NRW',
        'site:stepstone.de intitle:"Recruiter" Düsseldorf',
    ],
    "indeed_sales": [
        'site:indeed.com "Vertriebsmitarbeiter" Nordrhein-Westfalen',
    ],
}
```

### 5.2 Database-Modelle

**Model-Namen**: Singular, PascalCase
```python
class Lead(models.Model):
    pass

class ScraperRun(models.Model):
    pass

class EmailTemplate(models.Model):
    pass
```

**Feld-Namen**: `snake_case`, beschreibend
```python
# Gut
quality_score = models.IntegerField()
source_url = models.URLField()
created_at = models.DateTimeField(auto_now_add=True)

# Schlecht
q_score = models.IntegerField()  # Zu kurz
url = models.URLField()  # Nicht spezifisch genug
date = models.DateTimeField()  # Welches Datum?
```

**Related Names**: `{source_model}_{relationship}`
```python
class Lead(models.Model):
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_leads'  # User.assigned_leads.all()
    )
```

### 5.3 API-Endpoints

**REST Pattern**: `/api/{resource}/`
- Liste: `GET /api/leads/`
- Detail: `GET /api/leads/{id}/`
- Create: `POST /api/leads/`
- Update: `PUT /api/leads/{id}/`
- Partial Update: `PATCH /api/leads/{id}/`
- Delete: `DELETE /api/leads/{id}/`

**Custom Actions**: `/api/{resource}/{id}/{action}/`
- `POST /api/leads/{id}/convert/`
- `POST /api/scraper/start/`
- `POST /api/scraper/stop/`

**URL-Namen**: `{app}_{resource}_{action}`
```python
# urls.py
urlpatterns = [
    path('leads/', LeadListView.as_view(), name='leads_list'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='leads_detail'),
    path('scraper/start/', scraper_start, name='scraper_start'),
]

# Verwendung
reverse('leads_detail', kwargs={'pk': lead.id})
```

### 5.4 Django Apps

**App-Namen**: Plural, `snake_case`
- `leads` (nicht `lead`)
- `email_templates` (nicht `emailTemplates`)
- `scraper_control` (nicht `scraper_ctrl`)

**Views**: `{model}_{action}`
```python
# views.py
def lead_list(request):
    pass

def lead_detail(request, pk):
    pass

class LeadViewSet(viewsets.ModelViewSet):
    pass
```

**Templates**: `{app}/{model}_{template}.html`
```
templates/
├── leads/
│   ├── lead_list.html
│   ├── lead_detail.html
│   └── lead_form.html
└── scraper_control/
    └── scraper_dashboard.html
```

---

## 6. Database Migrations

### 6.1 Migration-Workflow

**Immer Migrations erstellen nach Model-Änderungen**:
```bash
python manage.py makemigrations
python manage.py migrate
```

**Vor Commit prüfen**:
```bash
# Check Migration
python manage.py makemigrations --dry-run --verbosity 3

# Check for unapplied migrations
python manage.py showmigrations
```

### 6.2 Migration-Regeln

**Regel 1: Nie Migrations rückgängig machen in Produktion**
- Stattdessen: Neue Migration für Revert

**Regel 2: Große Datenmigrationen separat**
```python
# migrations/0005_populate_lead_types.py
from django.db import migrations

def populate_lead_types(apps, schema_editor):
    """Populate lead_type field for existing leads."""
    Lead = apps.get_model('leads', 'Lead')
    # Batch-Update in Chunks
    for lead in Lead.objects.filter(lead_type__isnull=True).iterator(chunk_size=100):
        lead.lead_type = infer_lead_type(lead)
        lead.save(update_fields=['lead_type'])

class Migration(migrations.Migration):
    dependencies = [
        ('leads', '0004_lead_lead_type'),
    ]
    operations = [
        migrations.RunPython(populate_lead_types, reverse_code=migrations.RunPython.noop),
    ]
```

**Regel 3: Keine SQL direkt, nur wenn unvermeidbar**
```python
# Bevorzugt: Django ORM
operations = [
    migrations.AddField(
        model_name='lead',
        name='score',
        field=models.IntegerField(default=0),
    ),
]

# Nur wenn nötig: Raw SQL
operations = [
    migrations.RunSQL(
        sql="CREATE INDEX idx_lead_quality ON leads_lead(quality_score DESC);",
        reverse_sql="DROP INDEX idx_lead_quality;",
    ),
]
```

**Regel 4: Default-Werte für NOT NULL Felder**
```python
# Gut: Default definiert
field = models.IntegerField(default=0)

# Schlecht: NOT NULL ohne Default (breaking für existierende Daten)
field = models.IntegerField()
```

### 6.3 Schema-Änderungs-Prozess

**Für Breaking Changes (Drop Column, Rename)**:

1. **Migration 1**: Neue Spalte hinzufügen (optional)
2. **Deploy**: Code läuft mit beiden Spalten
3. **Migration 2**: Daten migrieren (Data Migration)
4. **Migration 3**: Alte Spalte entfernen

Beispiel:
```python
# 0001: Add new column
operations = [
    migrations.AddField('lead', 'phone', CharField(null=True)),
]

# Deploy: Code verwendet beide telefon und phone

# 0002: Migrate data
def copy_telefon_to_phone(apps, schema_editor):
    Lead = apps.get_model('leads', 'Lead')
    Lead.objects.update(phone=F('telefon'))

operations = [
    migrations.RunPython(copy_telefon_to_phone),
]

# 0003: Remove old column
operations = [
    migrations.RemoveField('lead', 'telefon'),
]
```

---

## 7. Testing Standards

### 7.1 Test-Struktur

**Test-Dateien**: `tests/test_{module}.py` oder `test_{feature}.py`
```
tests/
├── test_models.py
├── test_views.py
├── test_api.py
├── test_scraper.py
└── test_lead_validation.py
```

**Test-Klassen**: `Test{Feature}`
```python
class TestLeadModel(TestCase):
    def test_create_lead(self):
        pass
    
    def test_lead_validation(self):
        pass

class TestScraperManager(TestCase):
    def test_start_scraper(self):
        pass
```

### 7.2 Test-Naming

**Test-Methoden**: `test_{what}_{condition}_{expected}`
```python
def test_validate_lead_with_valid_email_returns_true(self):
    pass

def test_validate_lead_without_contact_raises_error(self):
    pass

def test_scraper_start_with_invalid_industry_returns_error(self):
    pass
```

### 7.3 Test-Coverage-Ziele

**Minimum-Coverage**:
- Models: 80%
- Views/APIs: 70%
- Utility Functions: 90%
- Business Logic: 85%

**Was testen**:
- ✅ Model-Methoden und Properties
- ✅ API-Endpoints (alle HTTP-Methoden)
- ✅ Validation-Logik
- ✅ Error-Handling
- ✅ Edge Cases
- ❌ Django-Framework-Code (schon getestet)
- ❌ Third-Party-Libraries

### 7.4 Test-Best-Practices

**Setup/Teardown**:
```python
class TestLeadAPI(TestCase):
    def setUp(self):
        """Run before each test."""
        self.user = User.objects.create_user('test', 'test@example.com', 'pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def tearDown(self):
        """Run after each test."""
        # Cleanup if needed
        pass
```

**Fixtures verwenden**:
```python
class TestLeadModel(TestCase):
    fixtures = ['leads.json']
    
    def test_something(self):
        lead = Lead.objects.get(pk=1)
        self.assertEqual(lead.name, "Test Lead")
```

**Mocking für External APIs**:
```python
from unittest.mock import patch, MagicMock

class TestOpenAIExtraction(TestCase):
    @patch('openai.ChatCompletion.create')
    def test_extract_with_openai(self, mock_openai):
        mock_openai.return_value = {
            'choices': [{'message': {'content': '{"name": "Test"}'}}]
        }
        result = extract_with_openai("<html>test</html>")
        self.assertEqual(result['name'], "Test")
```

---

## 8. Security Standards

### 8.1 Input Validation

**Alle User-Inputs validieren**:
```python
# Django Forms
class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'email', 'telefon']
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not email:
            raise forms.ValidationError("Email is required")
        # Additional validation
        return email.lower().strip()
```

**API-Inputs validieren**:
```python
# DRF Serializers
class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
    
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required")
        # Email format check (built-in EmailField validation)
        return value
```

### 8.2 SQL-Injection-Prävention

**Immer Django ORM verwenden**:
```python
# Gut: ORM parametrisiert automatisch
leads = Lead.objects.filter(email=user_email)

# Schlecht: SQL-Injection-Risiko
cursor.execute(f"SELECT * FROM leads WHERE email = '{user_email}'")

# Gut: Wenn Raw SQL nötig, parametrisiert
cursor.execute("SELECT * FROM leads WHERE email = %s", [user_email])
```

### 8.3 XSS-Prävention

**Django-Templates escapen automatisch**:
```html
<!-- Automatisch escaped -->
<p>{{ lead.name }}</p>

<!-- Nur wenn HTML explizit erlaubt -->
<div>{{ lead.description|safe }}</div>  <!-- Vorsicht! -->
```

**In JavaScript**:
```javascript
// Gut: Textinhalt, kein HTML
element.textContent = userData;

// Schlecht: HTML-Injection möglich
element.innerHTML = userData;
```

### 8.4 Secrets Management

**Nie Secrets im Code**:
```python
# Schlecht
API_KEY = "sk-abc123xyz"

# Gut: Environment Variables
import os
API_KEY = os.getenv('OPENAI_API_KEY')

# Gut: Django Settings
from django.conf import settings
API_KEY = settings.OPENAI_API_KEY
```

**`.env` in `.gitignore`**:
```
# .gitignore
.env
*.env
.env.local
```

### 8.5 Authentication & Authorization

**Require Authentication**:
```python
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated

@login_required
def lead_detail(request, pk):
    pass

class LeadViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
```

**Check Permissions**:
```python
def delete_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not request.user.is_staff:
        return HttpResponseForbidden("Nur Admins können Leads löschen")
    lead.delete()
    return HttpResponse("Lead gelöscht")
```

---

## 9. Performance Best Practices

### 9.1 Database Queries

**N+1-Problem vermeiden**:
```python
# Schlecht: N+1 Queries
leads = Lead.objects.all()
for lead in leads:
    print(lead.assigned_to.username)  # Query für jeden Lead!

# Gut: Select Related
leads = Lead.objects.select_related('assigned_to').all()
for lead in leads:
    print(lead.assigned_to.username)  # Nur 1 Query
```

**Prefetch für Many-to-Many**:
```python
# Schlecht
leads = Lead.objects.all()
for lead in leads:
    for tag in lead.tags.all():  # N Queries
        print(tag)

# Gut
leads = Lead.objects.prefetch_related('tags').all()
for lead in leads:
    for tag in lead.tags.all():  # Nur 1 zusätzlicher Query
        print(tag)
```

**Nur benötigte Felder laden**:
```python
# Nur IDs und Names
leads = Lead.objects.only('id', 'name')

# Alle außer großen Feldern
leads = Lead.objects.defer('ai_summary', 'opening_line')
```

### 9.2 Bulk-Operationen

**Bulk Create**:
```python
# Schlecht: N Queries
for lead_data in lead_list:
    Lead.objects.create(**lead_data)

# Gut: 1 Query
leads = [Lead(**data) for data in lead_list]
Lead.objects.bulk_create(leads, batch_size=100)
```

**Bulk Update**:
```python
# Bulk Update mit F-Expressions
Lead.objects.filter(status='NEW').update(
    quality_score=F('quality_score') + 10
)
```

### 9.3 Caching

**View-Caching**:
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 Minuten
def lead_stats(request):
    pass
```

**Query-Caching (manuell)**:
```python
from django.core.cache import cache

def get_lead_count():
    count = cache.get('lead_count')
    if count is None:
        count = Lead.objects.count()
        cache.set('lead_count', count, 300)  # 5 Minuten
    return count
```

---

## 10. Git & Version Control

### 10.1 Commit Messages

**Format**: `[Type] Short description`

**Types**:
- `[Feature]` - Neues Feature
- `[Fix]` - Bugfix
- `[Refactor]` - Code-Refactoring ohne Funktionsänderung
- `[Docs]` - Dokumentation
- `[Test]` - Tests hinzugefügt/geändert
- `[Chore]` - Wartungsarbeiten (Dependencies, etc.)

**Beispiele**:
```
[Feature] Add WhatsApp link extraction
[Fix] Resolve SQL injection in CSV import
[Refactor] Extract scoring logic to separate module
[Docs] Update ARCHITECTURE.md with new flow
[Test] Add unit tests for lead validation
[Chore] Update Django to 5.0.1
```

### 10.2 Branch-Naming

**Pattern**: `{type}/{short-description}`

```
feature/whatsapp-extraction
fix/sql-injection-csv
refactor/scoring-module
docs/architecture-update
```

### 10.3 Pull Requests

**PR-Titel**: Wie Commit-Message

**PR-Beschreibung** muss enthalten:
- **Was**: Welche Änderungen
- **Warum**: Grund/Kontext
- **Testing**: Wie getestet
- **Breaking Changes**: Falls zutreffend

---

## 11. Code-Review-Checkliste

Vor Merge prüfen:

- [ ] Code folgt Style-Guide (PEP 8)
- [ ] Type Hints vorhanden
- [ ] Docstrings vorhanden
- [ ] Tests vorhanden und passing
- [ ] Keine Secrets im Code
- [ ] SQL-Injection-sicher
- [ ] XSS-sicher
- [ ] Error-Handling korrekt
- [ ] Logging angemessen
- [ ] Performance akzeptabel
- [ ] Migrations erstellt (bei Model-Änderungen)
- [ ] Dokumentation aktualisiert

---

## 12. Enforcement

### 12.1 Automatisierung
- **Pre-Commit-Hooks**: PEP 8-Check, Type-Check
- **CI/CD**: Tests bei jedem Push
- **Code-Review**: Mindestens 1 Approval vor Merge

### 12.2 Konsequenzen
- Nicht-konforme PRs werden nicht gemerged
- Bei wiederholten Verstößen: Team-Gespräch

### 12.3 Updates
Dieses Dokument ist living documentation:
- Vorschläge via Pull Request
- Team-Diskussion bei größeren Änderungen
- Mindestens einmal pro Quartal Review

---

## Weitere Ressourcen

- [ARCHITECTURE.md](ARCHITECTURE.md) - System-Architektur
- [Playbooks](playbooks/) - Operative Anleitungen
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution-Guide
- [PEP 8](https://peps.python.org/pep-0008/) - Python Style Guide
- [Django Coding Style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
