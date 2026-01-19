# Playbook: Parsing für Portal bricht – so debuggen

## Zweck
Dieses Playbook hilft dir, Parsing-Probleme systematisch zu diagnostizieren und zu beheben, wenn die Datenextraktion für ein Portal nicht funktioniert oder unvollständige Daten liefert.

---

## Übersicht

**Typische Symptome**:
- Scraper findet URLs, aber extrahiert keine Kontaktdaten
- Email/Telefon-Felder sind leer, obwohl auf Seite sichtbar
- Handler wird nicht erkannt (fällt auf generic extraction zurück)
- Exceptions/Crashes bei bestimmten URLs
- Extrahierte Daten sind falsch oder unvollständig

**Dauer**: 30-90 Minuten (je nach Problemkomplexität)

---

## Phase 1: Problem-Identifikation (10 Min)

### 1.1 Logs analysieren

Prüfe die Scraper-Logs für Fehler:

```bash
cd /home/runner/work/luca-nrw-scraper/luca-nrw-scraper

# Letzte Scraper-Runs
tail -100 logs/scraper.log

# Suche nach Errors
grep -i "error\|exception\|failed" logs/scraper.log | tail -20

# Suche nach spezifischem Portal
grep -i "portal.de" logs/scraper.log | tail -20
```

**Wichtige Log-Muster**:
- `"No contact info found"` → Extraktion schlägt fehl
- `"Using generic extraction"` → Handler nicht erkannt
- `"KeyError"` / `"AttributeError"` → Code-Bug
- `"Timeout"` / `"ConnectionError"` → Netzwerk-Problem
- `"403"` / `"429"` → Rate-Limiting/Blocking

### 1.2 Betroffene URLs identifizieren

Finde URLs, die Probleme haben:

```bash
# Alle URLs vom Portal im Log
grep "Fetching.*portal.de" logs/scraper.log | head -10

# URLs ohne extrahierte Daten
sqlite3 scraper.db "
SELECT url, status 
FROM urls_seen 
WHERE domain LIKE '%portal.de%' 
AND status = 'skipped'
LIMIT 10;
"
```

**Notiere**:
- Beispiel-URLs die nicht funktionieren
- Gemeinsame URL-Muster (z.B. alle `/jobs/` URLs)

### 1.3 Symptom kategorisieren

| Symptom | Wahrscheinliche Ursache |
|---------|------------------------|
| Handler nicht erkannt | `can_handle()` zu restriktiv oder Handler nicht registriert |
| Keine Email extrahiert | CSS-Selektor falsch oder Email in JavaScript |
| Keine Telefonnummer | Telefon-Format nicht erkannt oder in Bild |
| Exception bei Parsing | HTML-Struktur geändert oder fehlerhaft |
| Timeout beim Fetch | Server langsam oder Anti-Bot-Maßnahmen |
| 403/429 Errors | Rate-Limiting oder IP-Block |

---

## Phase 2: Daten sammeln (15 Min)

### 2.1 Test-URL manuell fetchen

Speichere HTML einer Problem-URL:

```bash
# Mit curl (simuliert Scraper)
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
     -H "Accept-Language: de-DE,de;q=0.9" \
     -o test_page.html \
     "https://www.portal.de/problem-url"

# Prüfe Status Code
curl -I -A "Mozilla/5.0" "https://www.portal.de/problem-url"
```

**Alternativen bei JavaScript-Rendering**:
```python
# Mit browser_extractor.py
python3 << 'EOF'
from browser_extractor import BrowserExtractor

extractor = BrowserExtractor()
html = extractor.extract_with_browser("https://www.portal.de/problem-url")

with open('test_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
    
print(f"Saved {len(html)} bytes")
EOF
```

### 2.2 HTML-Struktur analysieren

Öffne `test_page.html` im Browser und prüfe:

**A. Kontaktdaten sichtbar?**
- Öffne DevTools (F12) → Elements
- Suche nach Email/Telefon mit Ctrl+F
- Sind Daten im HTML oder per JavaScript geladen?

**B. CSS-Selektoren identifizieren**
```
Beispiel:
<div class="contact-info">
  <span class="email">info@company.com</span>
  <span class="phone">+49 123 456789</span>
</div>

→ Selektoren: .email, .phone
```

**C. JavaScript-Check**
- Disable JavaScript im Browser
- Reload Seite
- Sind Kontaktdaten noch sichtbar?
  - **Ja** → Statisches HTML, einfaches Parsing
  - **Nein** → JavaScript-Rendering nötig (Browser-Extraction)

**D. Obfuscation-Check**
- Email als Bild? (→ OCR nötig)
- Email verschlüsselt? (→ JavaScript-Decoding)
- Telefon mit Leerzeichen/Sonderzeichen? (→ Normalisierung)

### 2.3 Aktuellen Parser testen

Teste Handler/Extraktion isoliert:

```python
# test_parser_debug.py
import sys
from bs4 import BeautifulSoup

# Wenn Portal-Handler existiert
try:
    from providers.portal_handler import PortalHandler
    handler = PortalHandler()
    has_handler = True
except ImportError:
    has_handler = False
    print("No custom handler found, testing generic extraction")

# Lade Test-HTML
with open('test_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

url = "https://www.portal.de/problem-url"

# Test Handler
if has_handler:
    print(f"\n{'='*60}")
    print("Testing Portal Handler")
    print(f"{'='*60}\n")
    
    # Check can_handle
    if not handler.can_handle(url):
        print(f"❌ Handler does not recognize URL: {url}")
        print(f"   Check can_handle() method")
    else:
        print(f"✅ Handler recognizes URL")
    
    # Test extraction
    try:
        result = handler.extract(html, url)
        
        if result:
            print(f"\n✅ Extraction successful:")
            for key, value in result.items():
                print(f"   {key}: {value}")
        else:
            print(f"\n❌ Extraction returned None")
            print(f"   No contact info found or validation failed")
            
    except Exception as e:
        print(f"\n❌ Exception during extraction:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

# Test generic extraction
print(f"\n{'='*60}")
print("Testing Generic Extraction")
print(f"{'='*60}\n")

from phone_extractor import extract_phone_numbers
import re

soup = BeautifulSoup(html, 'html.parser')
text = soup.get_text()

# Email
email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
emails = re.findall(email_pattern, text)
print(f"Emails found: {emails[:5]}")  # First 5

# Phone
phones = extract_phone_numbers(text, country='DE')
print(f"Phones found: {phones[:5]}")  # First 5

# WhatsApp
whatsapp_pattern = r'(?:https?://)?(?:wa\.me|api\.whatsapp\.com)/(?:\+)?(\d+)'
whatsapp = re.findall(whatsapp_pattern, text)
print(f"WhatsApp found: {whatsapp[:5]}")

if not emails and not phones:
    print(f"\n⚠️  No contact data in text content!")
    print(f"   → Check if data is in JavaScript or images")
```

Run:
```bash
python test_parser_debug.py
```

---

## Phase 3: Root Cause ermitteln (20-30 Min)

### 3.1 Szenario A: Handler nicht erkannt

**Symptom**: `"Using generic extraction"` im Log

**Debug**:
```python
# Test can_handle()
from providers.portal_handler import PortalHandler

handler = PortalHandler()
test_urls = [
    "https://www.portal.de/jobs/123",
    "https://portal.de/team",
    "https://www.portal.de/unternehmen/abc",
]

for url in test_urls:
    result = handler.can_handle(url)
    print(f"{url}: {result}")
```

**Fixes**:

1. **can_handle() zu streng**:
```python
# Vorher
def can_handle(self, url: str) -> bool:
    return url.startswith("https://www.portal.de")

# Nachher (flexibler)
def can_handle(self, url: str) -> bool:
    return "portal.de" in url.lower()
```

2. **Handler nicht registriert**:
```python
# In scriptname.py prüfen
PORTAL_HANDLERS = [
    StepstoneHandler(),
    IndeedHandler(),
    # PortalHandler(),  ← FEHLT!
]

# Fix: Handler hinzufügen
from providers.portal_handler import PortalHandler
PORTAL_HANDLERS = [
    StepstoneHandler(),
    IndeedHandler(),
    PortalHandler(),  # ← HINZUGEFÜGT
]
```

3. **Import-Fehler**:
```bash
# Prüfe ob Import funktioniert
python -c "from providers.portal_handler import PortalHandler; print('OK')"

# Bei Fehler: Prüfe __init__.py
ls providers/__init__.py
```

### 3.2 Szenario B: CSS-Selektor findet nichts

**Symptom**: Handler läuft, aber `extract()` returned None

**Debug mit BeautifulSoup**:
```python
from bs4 import BeautifulSoup

with open('test_page.html', 'r') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Test verschiedene Selektoren
selectors = [
    '.contact-email',
    '.email',
    '[data-email]',
    'a[href^="mailto:"]',
]

for selector in selectors:
    result = soup.select_one(selector)
    print(f"{selector}: {result}")
```

**Fixes**:

1. **Falscher Selektor**:
```python
# Vorher
email_elem = soup.select_one('.contact-email')

# Nachher (korrigierter Selektor)
email_elem = soup.select_one('.email-address')  # Klasse hat sich geändert
```

2. **Mehrere mögliche Selektoren**:
```python
# Robuster: Mehrere Selektoren testen
def _extract_email(self, soup):
    selectors = [
        '.contact-email',
        '.email-address', 
        'a[href^="mailto:"]',
        '[itemprop="email"]',
    ]
    
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            # Email aus href oder text
            if elem.name == 'a' and elem.get('href'):
                return elem['href'].replace('mailto:', '')
            return elem.get_text(strip=True)
    
    return None
```

3. **Email in Attribut statt Text**:
```python
# HTML: <div data-email="info@company.com">Contact</div>

# Vorher
email = elem.get_text()  # → "Contact" (falsch!)

# Nachher
email = elem.get('data-email')  # → "info@company.com"
```

### 3.3 Szenario C: JavaScript-gerenderte Daten

**Symptom**: Daten im Browser sichtbar, aber nicht in curl/HTML

**Lösung**: Browser-Extraction verwenden

1. **Für einzelne URLs testen**:
```python
from browser_extractor import BrowserExtractor

extractor = BrowserExtractor()
html = extractor.extract_with_browser("https://www.portal.de/problem-url")

# Jetzt mit dynamischem HTML parsen
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
email = soup.select_one('.email')  # Sollte jetzt funktionieren
```

2. **In Handler integrieren**:
```python
class PortalHandler:
    def __init__(self):
        self.browser_extractor = None
    
    def extract(self, html: str, url: str) -> dict:
        # Prüfe ob JavaScript-Rendering nötig
        if self._needs_browser(html):
            if not self.browser_extractor:
                from browser_extractor import BrowserExtractor
                self.browser_extractor = BrowserExtractor()
            
            logger.info(f"Using browser extraction for {url}")
            html = self.browser_extractor.extract_with_browser(url)
        
        # Normal extraction...
        return self._parse_html(html, url)
    
    def _needs_browser(self, html: str) -> bool:
        """Check if page needs browser rendering."""
        # Heuristik: Seite hat wenig Text aber viel JS
        soup = BeautifulSoup(html, 'html.parser')
        text_length = len(soup.get_text(strip=True))
        script_tags = len(soup.find_all('script'))
        
        return text_length < 500 and script_tags > 5
```

### 3.4 Szenario D: Telefonnummer nicht erkannt

**Symptom**: Telefon auf Seite vorhanden, aber nicht extrahiert

**Debug**:
```python
from phone_extractor import extract_phone_numbers

test_strings = [
    "+49 123 456789",
    "0123 / 456789",
    "Tel: 0123-456789",
    "Telefon: 0123 456 789",
    "(0123) 456789",
]

for s in test_strings:
    result = extract_phone_numbers(s, country='DE')
    print(f"{s} → {result}")
```

**Fixes**:

1. **Format nicht erkannt**:
```python
# Erweitere phone_patterns.py
PHONE_PATTERNS = [
    # ... existing patterns ...
    
    # Format: 0123 / 456789
    r'\b0\d{2,5}\s*/\s*\d{5,8}\b',
    
    # Format: (0123) 456789
    r'\(\d{3,5}\)\s*\d{5,8}\b',
]
```

2. **Telefon in Bild**:
```
→ Manuelle Lösung nötig oder OCR (pytesseract)
```

3. **Pre-Processing vor Extraktion**:
```python
def _extract_phone(self, soup):
    # Hole Text
    text = soup.get_text()
    
    # Normalisiere vor Extraktion
    text = text.replace('Tel.:', 'Tel:')
    text = text.replace('Telefon:', 'Tel:')
    text = re.sub(r'Tel:\s*', '', text)  # Entferne "Tel:" Label
    
    # Jetzt extrahieren
    phones = extract_phone_numbers(text, country='DE')
    return phones[0] if phones else None
```

### 3.5 Szenario E: Exception/Crash

**Symptom**: `KeyError`, `AttributeError`, `TypeError` im Log

**Debug mit Stack Trace**:
```python
# In Handler: Detailliertes Logging
try:
    email_elem = soup.select_one('.email')
    email = email_elem.get_text(strip=True)
except AttributeError as e:
    logger.error(f"AttributeError: email_elem is None for {url}")
    logger.error(f"HTML snippet: {str(soup)[:500]}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    raise
```

**Fixes**:

1. **None-Check fehlt**:
```python
# Vorher (crashed wenn elem None)
email = soup.select_one('.email').get_text()

# Nachher
email_elem = soup.select_one('.email')
if email_elem:
    email = email_elem.get_text(strip=True)
else:
    email = None
```

2. **Dict-Key fehlt**:
```python
# Vorher
company = lead_data['company']  # KeyError wenn nicht vorhanden

# Nachher
company = lead_data.get('company')  # None wenn nicht vorhanden
```

3. **Type-Mismatch**:
```python
# Vorher
phone_number = int(phone_text)  # ValueError bei "+49 123..."

# Nachher
phone_number = re.sub(r'\D', '', phone_text)  # Nur Zahlen
```

---

## Phase 4: Fix implementieren (20-30 Min)

### 4.1 Code anpassen

Basierend auf Root Cause, passe Handler an:

```python
# providers/portal_handler.py

class PortalHandler:
    def extract(self, html: str, url: str) -> Optional[Dict[str, any]]:
        """Extract lead data from portal page."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # FIX 1: Robuste Selektor-Logik
            email = self._extract_email(soup)
            phone = self._extract_phone(soup)
            
            # FIX 2: Bessere Validation
            if not email and not phone:
                logger.debug(f"No contact info on {url}")
                return None
            
            # FIX 3: Safe dict access
            lead_data = {
                'email': email,
                'telefon': phone,
                'company': self._extract_company(soup) or "Unknown",  # Fallback
                'source_url': url,
            }
            
            return lead_data
            
        except Exception as e:
            # FIX 4: Besseres Error-Handling
            logger.error(f"Extraction failed for {url}: {str(e)}", exc_info=True)
            return None
    
    def _extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract email with multiple fallbacks."""
        # Methode 1: CSS-Selektoren
        selectors = ['.email', '.contact-email', '[itemprop="email"]']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        # Methode 2: mailto: Links
        mailto = soup.select_one('a[href^="mailto:"]')
        if mailto:
            return mailto['href'].replace('mailto:', '').split('?')[0]
        
        # Methode 3: Regex über Text
        text = soup.get_text()
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            return email_match.group(0)
        
        return None
```

### 4.2 Unit Test schreiben

Erstelle Test für den Fix:

```python
# tests/test_portal_handler_fix.py
import unittest
from providers.portal_handler import PortalHandler


class TestPortalHandlerFix(unittest.TestCase):
    
    def setUp(self):
        self.handler = PortalHandler()
    
    def test_extract_with_multiple_selectors(self):
        """Test email extraction with fallback selectors."""
        # Email mit alternativer Klasse
        html = '<div class="email-address">test@example.com</div>'
        result = self.handler.extract(html, "https://portal.de/test")
        self.assertEqual(result['email'], "test@example.com")
    
    def test_extract_from_mailto_link(self):
        """Test email extraction from mailto link."""
        html = '<a href="mailto:info@company.com">Contact</a>'
        result = self.handler.extract(html, "https://portal.de/test")
        self.assertEqual(result['email'], "info@company.com")
    
    def test_extract_handles_missing_element_gracefully(self):
        """Test handler doesn't crash when element missing."""
        html = '<div>No contact info here</div>'
        result = self.handler.extract(html, "https://portal.de/test")
        self.assertIsNone(result)  # Should return None, not crash
    
    def test_extract_with_phone_only(self):
        """Test extraction works with phone only (no email)."""
        html = '<div class="phone">+49 123 456789</div>'
        result = self.handler.extract(html, "https://portal.de/test")
        self.assertIsNotNone(result)
        self.assertEqual(result['telefon'], "+49 123 456789")


if __name__ == '__main__':
    unittest.main()
```

Run:
```bash
python -m pytest tests/test_portal_handler_fix.py -v
```

### 4.3 Integration Test

Teste mit echter Problem-URL:

```bash
python test_parser_debug.py
```

**Erwartetes Ergebnis**:
- ✅ Handler erkannt
- ✅ Email/Telefon extrahiert
- ✅ Keine Exceptions

---

## Phase 5: Validierung (15 Min)

### 5.1 Dry-Run mit mehreren URLs

Teste Fix mit Scraper:

```bash
# Dry-Run (kein DB-Insert)
python scriptname.py \
    --once \
    --industry portal_recruiter \
    --qpi 10 \
    --dry-run

# Check Logs
tail -50 logs/scraper.log | grep -A 5 "portal.de"
```

**Prüfe**:
- Werden Leads extrahiert? (sollte > 0 sein)
- Gibt es noch Errors/Exceptions?
- Quality Score akzeptabel? (> 50)

### 5.2 Database Check

Wenn zufrieden, echter Run:

```bash
# Echter Run
python scriptname.py \
    --once \
    --industry portal_recruiter \
    --qpi 5
```

Check Results:
```bash
sqlite3 scraper.db << 'EOF'
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN email IS NOT NULL THEN 1 END) as with_email,
    COUNT(CASE WHEN telefon IS NOT NULL THEN 1 END) as with_phone,
    AVG(quality_score) as avg_score
FROM leads
WHERE source_url LIKE '%portal.de%'
AND created_at > datetime('now', '-1 hour');
EOF
```

**Ziel-Metriken**:
- Email-Rate: > 60%
- Phone-Rate: > 40%
- Avg Score: > 55

### 5.3 Regressions-Test

Prüfe dass andere Portale nicht broken sind:

```bash
# Test andere Portale
python scriptname.py --once --industry stepstone_recruiter --qpi 3 --dry-run
python scriptname.py --once --industry indeed_sales --qpi 3 --dry-run

# Prüfe Logs auf neue Errors
grep -i "error\|exception" logs/scraper.log | grep -v "portal.de" | tail -10
```

---

## Phase 6: Dokumentation & Deployment (10 Min)

### 6.1 Commit Changes

```bash
git add providers/portal_handler.py
git add tests/test_portal_handler_fix.py
git commit -m "[Fix] Improve portal.de parsing with fallback selectors

- Add multiple CSS selector fallbacks for email extraction
- Handle mailto: links
- Add None-checks to prevent crashes
- Add unit tests for edge cases

Fixes extraction failures on portal.de URLs."
```

### 6.2 Update Dokumentation

Falls Handler neu oder signifikant geändert:

```python
# providers/portal_handler.py Docstring
"""
Handler for Portal.de job portal.

Changes (2024-01-19):
- Added fallback selectors for email (.email, .email-address, mailto:)
- Fixed crash when contact info missing
- Improved phone extraction with normalization

Known Issues:
- Some pages require JavaScript (use browser_extractor)
- Contact info on images not supported
"""
```

### 6.3 Deploy

```bash
# Push changes
git push origin your-branch

# Create PR or deploy if authorized
```

---

## Troubleshooting-Matrix

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| Handler nicht erkannt | `can_handle()` zu streng | Erweitere URL-Match-Logic |
| Email nicht gefunden | Falscher CSS-Selektor | Multi-Selector-Fallback |
| Phone nicht gefunden | Format nicht erkannt | Erweitere phone_patterns.py |
| Daten in JS gerendert | Statisches HTML unvollständig | Browser-Extraction nutzen |
| Exception bei None | Fehlende None-Checks | Defensive Programmierung |
| Encoding-Fehler | Falsche Zeichenkodierung | Explicit UTF-8 handling |
| Rate-Limiting | Zu viele Requests | Delay erhöhen, Session-Rotation |
| Daten veraltet | HTML-Struktur geändert | Selektoren aktualisieren |

---

## Prävention

### Best Practices für robusten Parser

1. **Multiple Fallbacks**:
```python
# Nicht nur einen Weg
email = (
    self._extract_from_selector(soup, '.email') or
    self._extract_from_mailto(soup) or
    self._extract_from_regex(soup)
)
```

2. **Defensive Programming**:
```python
# Immer None-Checks
elem = soup.select_one('.contact')
if elem:
    text = elem.get_text(strip=True)
else:
    text = None
```

3. **Logging**:
```python
# Debug-Info bei Failure
if not email:
    logger.debug(f"No email found on {url}")
    logger.debug(f"HTML snippet: {html[:500]}")
```

4. **Graceful Degradation**:
```python
# Fail nicht bei einzelnem Fehler
try:
    company = self._extract_company(soup)
except Exception as e:
    logger.warning(f"Company extraction failed: {e}")
    company = None  # Continue with other fields
```

5. **Automated Testing**:
```python
# Regelmäßige Tests mit echten URLs
# test_portal_integration.py sollte in CI laufen
```

---

## Checkliste

Debug-Session abgeschlossen wenn:

- [ ] Problem identifiziert (Logs, Test-URLs)
- [ ] Root Cause ermittelt (einer der Szenarien oben)
- [ ] Fix implementiert (Code-Änderung)
- [ ] Unit Tests hinzugefügt
- [ ] Integration Test erfolgreich (echte URL)
- [ ] Dry-Run erfolgreich (mehrere URLs)
- [ ] Database Check positiv (Metriken OK)
- [ ] Keine Regressions (andere Portale OK)
- [ ] Code committed und deployed
- [ ] Dokumentation aktualisiert

---

## Weitere Ressourcen

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System-Übersicht
- [CODING_STANDARDS.md](../CODING_STANDARDS.md) - Code-Standards
- [NEW_PORTAL_INTEGRATION.md](NEW_PORTAL_INTEGRATION.md) - Portal integrieren
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - HTML Parsing
- [CSS Selectors Reference](https://www.w3schools.com/cssref/css_selectors.asp) - Selektor-Syntax
