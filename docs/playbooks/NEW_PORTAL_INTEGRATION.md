# Playbook: Neues Portal integrieren

## Zweck
Dieses Playbook beschreibt Schritt für Schritt, wie ein neues Job-Portal oder eine neue Datenquelle in den LUCA Scraper integriert wird.

---

## Übersicht

**Dauer**: 2-4 Stunden (je nach Portal-Komplexität)

**Voraussetzungen**:
- Entwicklungsumgebung eingerichtet
- Zugriff auf das Ziel-Portal
- Grundverständnis der LUCA-Architektur

**Ergebnis**: Portal ist integriert und liefert valide Leads

---

## Phase 1: Analyse (30 Min)

### 1.1 Portal-Eigenschaften ermitteln

Untersuche das Ziel-Portal systematisch:

**A. URL-Struktur**
```
Beispiele:
- https://www.stepstone.de/jobs/vertrieb/nordrhein-westfalen
- https://www.indeed.com/jobs?q=Recruiter&l=Düsseldorf
- https://www.xing.com/jobs/duesseldorf-recruiter-jobs
```

Notiere:
- Base URL: `https://www.portal.de`
- Job-Listing-Muster: `/jobs/`, `/stellenanzeigen/`, etc.
- Pagination: Query-Parameter oder URL-Pfad?
- Filter: Wie werden Location/Category angegeben?

**B. Content-Struktur analysieren**

Öffne mehrere Beispiel-Seiten und prüfe:

```bash
# Im Browser DevTools → Network Tab
# Oder mit curl
curl -A "Mozilla/5.0" "https://portal.de/example-page" > sample.html
```

Identifiziere:
- **Kontakt-Daten**: Wo stehen Email/Telefon/WhatsApp?
- **CSS-Selektoren**: Welche Klassen/IDs für relevante Elemente?
- **JSON-LD/Microdata**: Strukturierte Daten vorhanden?
- **JavaScript-Rendering**: Benötigt das Portal JS? (Browser-Extraktion nötig)

**C. Anti-Bot-Maßnahmen**
- Captcha vorhanden?
- Rate Limiting erkennbar?
- Login-Pflicht für Kontaktdaten?
- Cloudflare/Bot-Protection?

**D. robots.txt prüfen**
```bash
curl https://portal.de/robots.txt
```

Suche nach:
- Erlaubte Pfade für Crawler
- Crawl-Delay-Anforderungen
- Disallowed-Pfade

---

## Phase 2: Dork-Erstellung (20 Min)

### 2.1 Google Search Dorks entwickeln

Teste verschiedene Dorks in Google:

```
# Basic Site Search
site:portal.de Vertrieb NRW

# Mit Intitle (findet spezifische Seiten)
site:portal.de intitle:"Team" Düsseldorf

# Mit Inurl (URLs filtern)
site:portal.de inurl:jobs recruiter

# Kombinationen
site:portal.de "Personalvermittlung" OR "Headhunter" Köln
```

**Ziel**: Finde Dorks, die hohe Relevanz haben (> 50% der Results sind Treffer).

### 2.2 Dorks in Code eintragen

Bearbeite `dorks_extended.py`:

```python
# dorks_extended.py
INDUSTRY_DORKS = {
    # ... existing dorks ...
    
    # Neues Portal
    "portal_recruiter": [
        'site:portal.de intitle:"Recruiter" NRW',
        'site:portal.de "Personalvermittlung" Düsseldorf OR Köln OR Essen',
        'site:portal.de inurl:team "Headhunter"',
    ],
    "portal_sales": [
        'site:portal.de "Vertriebsleiter" OR "Sales Manager" Nordrhein-Westfalen',
        'site:portal.de intitle:"Stellenangebot" Vertrieb',
    ],
}

# Optional: Portal zu Industry-Mapping
PORTAL_TO_INDUSTRY = {
    # ... existing ...
    "portal.de": ["portal_recruiter", "portal_sales"],
}
```

**Naming Convention**: `{portal_name}_{category}`

---

## Phase 3: Content-Extraktion (60-90 Min)

### 3.1 Entscheiden: Generischer Scraper vs. Portal-Handler

**Generischer Scraper ausreichend wenn**:
- Standard HTML mit Kontaktdaten im Text
- Keine Login-Pflicht
- Kein spezielles Parsing nötig

➔ **Weiter zu Phase 4** (Testing)

**Portal-Handler nötig wenn**:
- Custom HTML-Struktur (z.B. React-App)
- Login-Pflicht
- API-Zugriff statt HTML
- Spezielle Daten-Extraktion nötig

➔ **Weiter zu 3.2**

### 3.2 Portal-Handler erstellen

Erstelle neue Datei: `providers/{portal_name}_handler.py`

```python
"""
Handler for {PortalName} portal.
Extracts contact information from {portal.de} pages.
"""

import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class {PortalName}Handler:
    """
    Custom handler for {portal.de} pages.
    """
    
    PORTAL_NAME = "{portal}"
    BASE_URL = "https://www.portal.de"
    
    def can_handle(self, url: str) -> bool:
        """
        Check if this handler can process the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if handler can process this URL
        """
        return "portal.de" in url.lower()
    
    def extract(self, html: str, url: str) -> Optional[Dict[str, any]]:
        """
        Extract lead data from portal page.
        
        Args:
            html: Raw HTML content
            url: Source URL
            
        Returns:
            Dictionary with extracted data or None if extraction failed
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extrahiere Kontaktdaten
            email = self._extract_email(soup)
            phone = self._extract_phone(soup)
            company = self._extract_company(soup)
            
            # Mindestens Email oder Telefon erforderlich
            if not email and not phone:
                logger.debug(f"No contact info found on {url}")
                return None
            
            lead_data = {
                'email': email,
                'telefon': phone,
                'company': company,
                'source_url': url,
                'source_detail': f'{self.PORTAL_NAME} portal',
            }
            
            # Optional: Weitere Felder
            lead_data['name'] = self._extract_name(soup)
            lead_data['role'] = self._extract_role(soup)
            lead_data['location'] = self._extract_location(soup)
            
            logger.info(f"Extracted lead from {self.PORTAL_NAME}: {email or phone}")
            return lead_data
            
        except Exception as e:
            logger.error(f"Error extracting from {url}: {str(e)}")
            return None
    
    def _extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract email from page."""
        # Methode 1: CSS-Selektor
        email_elem = soup.select_one('.contact-email')
        if email_elem:
            return email_elem.get_text(strip=True)
        
        # Methode 2: Regex über gesamten Text
        text = soup.get_text()
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            return email_match.group(0)
        
        return None
    
    def _extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract phone number from page."""
        # Nutze phone_extractor.py aus Hauptprojekt
        from phone_extractor import extract_phone_numbers
        
        text = soup.get_text()
        phones = extract_phone_numbers(text, country='DE')
        return phones[0] if phones else None
    
    def _extract_company(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name."""
        # CSS-Selektor-Beispiel
        company_elem = soup.select_one('.company-name, .employer-name')
        if company_elem:
            return company_elem.get_text(strip=True)
        
        # Fallback: Title-Tag
        title = soup.find('title')
        if title:
            # Extrahiere Firmennamen aus "Jobs bei Firma XYZ"
            match = re.search(r'bei\s+(.+?)(?:\s+-|\s+\||$)', title.text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract contact person name."""
        # Implementiere spezifische Logik
        pass
    
    def _extract_role(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job role/title."""
        # Implementiere spezifische Logik
        pass
    
    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location."""
        location_elem = soup.select_one('.location, .address, [itemprop="addressLocality"]')
        if location_elem:
            return location_elem.get_text(strip=True)
        return None
```

### 3.3 Handler registrieren

Bearbeite `scriptname.py` (oder zentrales Handler-Registry wenn vorhanden):

```python
# In scriptname.py, bei den Imports
from providers.portal_handler import PortalHandler

# In der HANDLERS-Liste oder init-Funktion
PORTAL_HANDLERS = [
    PortalHandler(),
    # ... weitere Handler
]

# In der Extraction-Logik
def extract_lead_data(html, url):
    # Prüfe ob spezieller Handler verfügbar
    for handler in PORTAL_HANDLERS:
        if handler.can_handle(url):
            logger.info(f"Using {handler.PORTAL_NAME} handler for {url}")
            return handler.extract(html, url)
    
    # Fallback zu generischer Extraktion
    return generic_extract(html, url)
```

### 3.4 Login-Handler (falls nötig)

Falls das Portal Login benötigt, nutze/erweitere `login_handler.py`:

```python
# login_handler.py
PORTAL_LOGINS = {
    # ... existing ...
    
    "portal.de": {
        "login_url": "https://www.portal.de/login",
        "username_field": "email",
        "password_field": "password",
        "submit_button": "button[type='submit']",
        "success_indicator": ".user-menu",  # Element das nach Login sichtbar ist
    }
}
```

Credentials in `.env`:
```bash
PORTAL_USERNAME=your_user@example.com
PORTAL_PASSWORD=your_password
```

---

## Phase 4: Testing (30-45 Min)

### 4.1 Unit Tests erstellen

Erstelle `tests/test_{portal}_handler.py`:

```python
import unittest
from providers.portal_handler import PortalHandler


class TestPortalHandler(unittest.TestCase):
    
    def setUp(self):
        self.handler = PortalHandler()
    
    def test_can_handle_valid_url(self):
        """Test handler recognizes portal URLs."""
        self.assertTrue(self.handler.can_handle("https://www.portal.de/jobs/123"))
        self.assertFalse(self.handler.can_handle("https://other-site.com"))
    
    def test_extract_email(self):
        """Test email extraction from sample HTML."""
        html = """
        <html>
            <div class="contact-email">contact@company.com</div>
        </html>
        """
        result = self.handler.extract(html, "https://portal.de/test")
        self.assertEqual(result['email'], "contact@company.com")
    
    def test_extract_returns_none_without_contact(self):
        """Test handler returns None when no contact info found."""
        html = "<html><body>No contacts here</body></html>"
        result = self.handler.extract(html, "https://portal.de/test")
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
```

Run Tests:
```bash
python -m pytest tests/test_portal_handler.py -v
# oder
python tests/test_portal_handler.py
```

### 4.2 Integration Test mit echten URLs

Erstelle Test-Script `test_portal_integration.py`:

```python
"""
Integration test for Portal Handler.
Tests with real portal URLs.
"""

import sys
from providers.portal_handler import PortalHandler
from curl_cffi.requests import Session

# Test-URLs (öffentlich zugängliche Beispiel-Seiten)
TEST_URLS = [
    "https://www.portal.de/jobs/example-1",
    "https://www.portal.de/jobs/example-2",
    "https://www.portal.de/jobs/example-3",
]


def test_portal_extraction():
    """Test extraction with real URLs."""
    handler = PortalHandler()
    session = Session()
    
    print(f"\n{'='*60}")
    print(f"Testing {handler.PORTAL_NAME} Handler")
    print(f"{'='*60}\n")
    
    success = 0
    failed = 0
    
    for url in TEST_URLS:
        print(f"Testing: {url}")
        try:
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}")
                failed += 1
                continue
            
            lead_data = handler.extract(response.text, url)
            
            if lead_data:
                print(f"  ✅ Success")
                print(f"     Email: {lead_data.get('email', 'N/A')}")
                print(f"     Phone: {lead_data.get('telefon', 'N/A')}")
                print(f"     Company: {lead_data.get('company', 'N/A')}")
                success += 1
            else:
                print(f"  ⚠️  No data extracted")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            failed += 1
        
        print()
    
    print(f"{'='*60}")
    print(f"Results: {success} success, {failed} failed")
    print(f"Success Rate: {success/(success+failed)*100:.1f}%")
    print(f"{'='*60}\n")
    
    # Minimum Success Rate: 60%
    if success / (success + failed) < 0.6:
        print("❌ Success rate too low! Needs improvement.")
        sys.exit(1)
    else:
        print("✅ Integration test passed!")


if __name__ == '__main__':
    test_portal_extraction()
```

Run:
```bash
python test_portal_integration.py
```

**Ziel**: Mindestens 60% Success Rate bei Test-URLs.

### 4.3 Dry-Run im Scraper

Teste das Portal mit dem Haupt-Scraper (ohne DB-Insert):

```bash
cd /path/to/luca-nrw-scraper

# Dry-Run mit Portal-Dork
python scriptname.py \
    --once \
    --industry portal_recruiter \
    --qpi 5 \
    --dry-run

# Prüfe Logs
tail -f scraper.log
```

**Prüfpunkte**:
- Werden URLs vom Portal gefunden?
- Wird Handler korrekt erkannt?
- Werden Kontaktdaten extrahiert?
- Keine Crashes/Exceptions?

---

## Phase 5: Quality-Tuning (30 Min)

### 5.1 Scoring anpassen

Falls Portal spezielle Scoring-Regeln braucht, erweitere `stream3_scoring_layer/scoring_enhanced.py`:

```python
def score_lead(lead_data: dict) -> dict:
    # ... existing logic ...
    
    # Portal-spezifische Boosts
    if 'portal.de' in lead_data.get('source_url', ''):
        # Bonus für vertrauenswürdiges Portal
        score += 5
        logger.debug("Portal bonus: +5")
        
        # Penalty wenn Job-Posting
        if is_job_posting(lead_data):
            score -= 20
            logger.debug("Job posting penalty: -20")
    
    # ... rest of logic ...
```

### 5.2 Filter-Regeln anpassen

Falls Portal false-positives produziert, füge Filter hinzu:

```python
# In scriptname.py oder portal_handler.py

PORTAL_BLOCKLIST = [
    "job-posting",
    "stellenanzeige",
    "bewerbung",
]

def is_valid_portal_page(url, html):
    """Check if page is valid lead source."""
    text = html.lower()
    
    # Blocke offensichtliche Job-Ads
    if any(keyword in text for keyword in PORTAL_BLOCKLIST):
        if text.count('bewerbung') > 3:  # Threshold
            return False
    
    return True
```

### 5.3 Performance-Check

Prüfe Performance-Metriken:

```bash
# Run mit Timing
time python scriptname.py --once --industry portal_recruiter --qpi 10
```

**Ziele**:
- Query-Rate: > 5 URLs/Min
- Extraction-Rate: > 80% Success bei validen URLs
- False-Positive-Rate: < 20%

---

## Phase 6: Dokumentation (15 Min)

### 6.1 Handler dokumentieren

Füge Docstring zum Handler hinzu mit:
- Unterstützte Seiten-Typen
- Bekannte Limitierungen
- Beispiel-URLs

```python
"""
Handler for Portal.de job portal.

Supported Page Types:
- Job listings: /jobs/*
- Company profiles: /unternehmen/*
- Team pages: /team

Limitations:
- Login required for some contact details
- Rate limit: 100 requests/hour
- JavaScript-heavy pages need browser extraction

Example URLs:
- https://www.portal.de/jobs/vertrieb-duesseldorf-123
- https://www.portal.de/unternehmen/abc-gmbh
"""
```

### 6.2 Dorks dokumentieren

Füge Kommentare zu Dorks hinzu:

```python
INDUSTRY_DORKS = {
    "portal_recruiter": [
        # Findet Recruiter-Profile auf Portal
        'site:portal.de intitle:"Recruiter" NRW',
        
        # Findet Personalvermittlungen (high quality)
        'site:portal.de "Personalvermittlung" Düsseldorf OR Köln OR Essen',
    ],
}
```

### 6.3 README aktualisieren

Falls relevant, erwähne neues Portal in README:

```markdown
## Unterstützte Portale

- ✅ Google Custom Search (alle Websites)
- ✅ StepStone (spezieller Handler)
- ✅ Indeed (spezieller Handler)
- ✅ **Portal.de (spezieller Handler)** ← NEU
```

---

## Phase 7: Deployment (15 Min)

### 7.1 Code Review

Erstelle Pull Request mit:

**PR-Titel**: `[Feature] Add Portal.de integration`

**PR-Beschreibung**:
```markdown
## Neues Portal integriert: Portal.de

### Änderungen
- Portal-Handler in `providers/portal_handler.py`
- Dorks für recruiter + sales in `dorks_extended.py`
- Unit Tests in `tests/test_portal_handler.py`
- Integration Test in `test_portal_integration.py`

### Testing
- ✅ Unit Tests passing (100% coverage)
- ✅ Integration Test: 85% success rate
- ✅ Dry-Run: 23 Leads gefunden, 0 Crashes

### Metrics
- Extraction Success: 85%
- False Positive Rate: 12%
- Avg. Quality Score: 68

### Known Issues
- Login required für manche Detailseiten (geplant)
```

### 7.2 Merge und Deploy

Nach Code Review:

```bash
git checkout main
git pull origin main
git merge feature/portal-integration
git push origin main
```

Falls Deployment auf Server:

```bash
# SSH zum Server
ssh user@server

# Pull changes
cd /path/to/luca
git pull

# Restart services (falls nötig)
sudo systemctl restart luca-scraper
# oder
docker-compose restart
```

### 7.3 Monitoring

Beobachte erste Runs mit neuem Portal:

```bash
# Check Scraper Logs
tail -f logs/scraper.log | grep -i portal

# Check Lead Quality
sqlite3 scraper.db "SELECT 
    COUNT(*) as total,
    AVG(quality_score) as avg_score,
    source_detail
FROM leads 
WHERE source_detail LIKE '%portal%' 
GROUP BY source_detail;"
```

**Zielmetriken nach 24h**:
- Mindestens 10 neue Leads vom Portal
- Avg. Quality Score > 60
- Keine Crashes im Log

---

## Troubleshooting

### Problem: Handler wird nicht erkannt

**Symptom**: Logs zeigen "Using generic extraction" statt "Using portal handler"

**Lösung**:
1. Prüfe `can_handle()` Methode:
   ```python
   print(handler.can_handle("https://www.portal.de/test"))  # Should be True
   ```
2. Prüfe Handler-Registrierung in `scriptname.py`
3. Prüfe Import-Fehler: `python -c "from providers.portal_handler import PortalHandler"`

### Problem: Keine Kontaktdaten extrahiert

**Symptom**: Handler läuft, aber `extract()` returned None

**Lösung**:
1. Speichere HTML für debugging:
   ```python
   with open('debug.html', 'w') as f:
       f.write(html)
   ```
2. Prüfe CSS-Selektoren im Browser DevTools
3. Prüfe ob JavaScript-Rendering nötig (→ Browser-Extraction)

### Problem: Rate-Limiting / 429 Errors

**Symptom**: HTTP 429 oder Captcha-Seiten

**Lösung**:
1. Reduziere QPI (Queries per Industry): `--qpi 3`
2. Erhöhe Delay zwischen Requests in `scriptname.py`:
   ```python
   FETCH_DELAY = 5  # Sekunden
   ```
3. Verwende Browser-Extraction: `browser_extractor.py`
4. Implementiere Session-Rotation

### Problem: Viele False Positives

**Symptom**: Viele Leads mit niedrigem Quality Score

**Lösung**:
1. Verbessere Dorks (spezifischer)
2. Füge Content-Filter hinzu (siehe 5.2)
3. Erhöhe Quality-Threshold in Scoring
4. Blocke Job-Posting-Seiten explizit

---

## Checkliste

Nach Abschluss aller Phasen:

- [ ] Portal analysiert und dokumentiert
- [ ] Dorks erstellt und getestet (Success Rate > 50%)
- [ ] Handler implementiert (falls nötig)
- [ ] Unit Tests erstellt und passing
- [ ] Integration Test durchgeführt (Success Rate > 60%)
- [ ] Dry-Run erfolgreich (keine Crashes)
- [ ] Scoring/Filtering angepasst
- [ ] Dokumentation aktualisiert
- [ ] Code-Review abgeschlossen
- [ ] Gemerged und deployed
- [ ] 24h-Monitoring durchgeführt
- [ ] Metriken dokumentiert

---

## Nächste Schritte

Nach erfolgreicher Integration:

1. **Optimierung**: Beobachte Metrics und optimiere Dorks/Filter
2. **A/B-Testing**: Teste verschiedene Dork-Varianten
3. **Learning**: Nutze Learning-Engine für automatische Verbesserung
4. **Skalierung**: Erhöhe QPI wenn Portal gut performed

---

## Weitere Ressourcen

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System-Architektur
- [CODING_STANDARDS.md](../CODING_STANDARDS.md) - Code-Standards
- [PARSING_DEBUG.md](PARSING_DEBUG.md) - Debug-Hilfe wenn Extraktion nicht klappt
