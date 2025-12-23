# VOLLGAS: Maximale Lead-Produktion + Erweitertes Learning

## Übersicht

Diese Implementierung erweitert den Luca NRW Scraper um:
- ✅ **95+ erweiterte Google Dorks** für maximale Lead-Generierung
- ✅ **Erweiterte Telefon-Extraktion** mit Konfidenz-Scoring
- ✅ **Social Media Integration** (Facebook, LinkedIn, XING, Telegram)
- ✅ **Intelligente Deduplizierung** zur Vermeidung doppelter Leads
- ✅ **13 Portal-Konfigurationen** mit Prioritäts-System
- ✅ **Erweiterte Dashboard-Statistiken**

---

## Neue Module

### 1. `dorks_extended.py` - Erweiterte Dork-Sammlung

**95+ spezialisierte Google Dorks** in 8 Kategorien:
- **Job Seeker Dorks** (35): Direkte Stellengesuche mit Ortsangaben
- **Site-Specific Dorks** (19): Portal-spezifische Suchen
- **URL-Pattern Dorks** (7): URL-basierte Suchen
- **Contact-Pattern Dorks** (11): Telefon/Kontakt-fokussiert
- **Power Dorks** (8): Kombinierte komplexe Suchen
- **Job Portal Dorks** (5): Indeed, StepStone, Monster, etc.
- **Mobile Dorks** (5): WhatsApp, Telegram
- **Freelancer Dorks** (5): Freelancer-Portale

**Funktionen:**
```python
from dorks_extended import get_all_dorks, get_random_dorks, get_dorks_by_category

# Alle Dorks abrufen
all_dorks = get_all_dorks()  # 95 Dorks

# Zufällige Dorks zum Testen
random_dorks = get_random_dorks(10)  # 10 zufällige

# Nach Kategorie
job_seeker = get_dorks_by_category("job_seeker")  # 35 Dorks
power = get_dorks_by_category("power")  # 8 Dorks
```

---

### 2. `phone_extractor.py` - Erweiterte Telefon-Extraktion

**Fortgeschrittene Telefonnummern-Erkennung** mit:
- Multiple Regex-Patterns für verschiedene Formate
- Verschleierte Nummern (Worte, Sterne, Leerzeichen)
- **Konfidenz-Score** basierend auf Kontext
- Blacklist für Fake-Nummern

**Funktionen:**
```python
from phone_extractor import extract_phones_advanced, get_best_phone

text = "Kontaktieren Sie mich unter 0176 12345678 oder per WhatsApp"

# Erweiterte Extraktion mit Konfidenz
results = extract_phones_advanced(text)
# Returns: [("+4917612345678", "0176 12345678", 0.80)]

# Beste Nummer auswählen
best_phone = get_best_phone(results)  # "+4917612345678"
```

**Konfidenz-Scoring:**
- Positive Signale: "telefon", "mobil", "erreichbar", "whatsapp"
- Negative Signale: "fax", "impressum", "hotline"
- Score: 0.0 - 1.0 (höher = vertrauenswürdiger)

---

### 3. `social_scraper.py` - Social Media Integration

**URLs und Dorks für:**
- Facebook Gruppen (7 URLs)
- LinkedIn Suchen (4 URLs)
- XING Kandidaten (4 URLs)
- Telegram Kanäle (5 URLs)
- **39 Social Media Dorks**

**Funktionen:**
```python
from social_scraper import SocialMediaScraper, get_all_social_dorks

scraper = SocialMediaScraper()

# Facebook Gruppen
fb_groups = scraper.get_facebook_group_urls()

# LinkedIn Suchen
linkedin = scraper.build_linkedin_search_urls()

# Alle Social Media URLs
all_urls = scraper.get_all_social_urls()  # 20 URLs

# Social Media Dorks
social_dorks = get_all_social_dorks()  # 39 Dorks
```

---

### 4. `deduplication.py` - Intelligente Deduplizierung

**Verhindert doppelte Leads durch:**
- Telefonnummern-Index (normalisiert)
- E-Mail-Index (case-insensitive)
- Name+Stadt Fuzzy-Matching (85% Ähnlichkeit)

**Funktionen:**
```python
from deduplication import get_deduplicator

dedup = get_deduplicator()

lead = {
    "name": "Max Mustermann",
    "telefon": "0176 12345678",
    "email": "max@example.com",
    "stadt": "Düsseldorf"
}

# Duplikat-Check
is_dup, reason = dedup.is_duplicate(lead)

if not is_dup:
    # Lead speichern
    lead_id = save_lead_to_db(lead)
    # Für Deduplizierung registrieren
    dedup.register_lead(lead, lead_id)

# Statistiken
stats = dedup.get_stats()
# {'unique_phones': 100, 'unique_emails': 80, 'unique_name_city': 90}
```

---

## Neue Portal-Konfigurationen

**13 Portale** mit Prioritäts-System:

```python
PORTAL_CONFIGS = {
    "kleinanzeigen": {"priority": 1, "delay": 3.0},
    "markt_de": {"priority": 2, "delay": 4.0},
    "quoka": {"priority": 3, "delay": 6.0},
    "indeed": {"priority": 4, "delay": 3.0},        # NEU
    "stepstone": {"priority": 5, "delay": 3.0},     # NEU
    "arbeitsagentur": {"priority": 6, "delay": 2.0}, # NEU
    "monster": {"priority": 7, "delay": 3.0},       # NEU
    "stellenanzeigen": {"priority": 8, "delay": 2.5}, # NEU
    "meinestadt": {"priority": 9, "delay": 3.0},    # REAKTIVIERT
    "freelancermap": {"priority": 10, "delay": 3.0},
    "freelance_de": {"priority": 11, "delay": 3.0},
    # Deaktiviert:
    "dhd24": {"enabled": False},
    "kalaydo": {"enabled": False},
}
```

---

## Integration in `scriptname.py`

### Smart Dork Selection

Neue Funktion kombiniert:
1. **50%** Top-Performer aus Learning
2. **25%** Power-Dorks
3. **25%** Zufällige neue Dorks
4. **Bonus:** Social Media Dorks + Job Seeker (für Candidates Mode)

```python
from scriptname import get_smart_dorks_extended

# Holt 20 intelligente Dorks
dorks = get_smart_dorks_extended("candidates", count=20)
```

---

## Dashboard-Erweiterungen

### Neue Sektionen in `dashboard.py`:

#### 1. 🎯 Dork Kategorien
```
Kategorie             Dorks    Leads
-------------------- -------- --------
Site-Specific              19       45
Power-Dorks                 8       32
URL-Pattern                 7       18
Standard                   61       89
```

#### 2. 🔄 Deduplizierung
```
Eindeutige Telefonnummern:      150
Eindeutige E-Mails:             120
Eindeutige Name+Stadt:          130
Geschätzte Duplikate verhindert: 400
```

#### 3. 📊 Portal Vergleich
```
Portal               URLs   Leads Effizienz
-------------------- -------- -------- ----------
kleinanzeigen             150       30     20.0% ██████████
markt_de                   80       12     15.0% ███████
quoka                      60        6     10.0% █████
indeed                     40        8     20.0% ██████████
```

---

## Erwartete Ergebnisse

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| Portale | 4-5 | **13** |
| Dorks | ~20 | **95+** |
| Leads pro Run | 0-5 | **15-30** |
| Leads mit Telefon | ~50% | **~70%** |
| Duplikate | Viele | **Keine** |
| Social Media Leads | 0 | **10-20%** |

---

## Verwendung

### 1. Dashboard starten
```bash
python dashboard.py
```

### 2. Scraper mit erweiterten Features
```bash
python scriptname.py --once --industry candidates
```

### 3. Tests ausführen
```bash
python -m pytest tests/test_extended_features.py -v
```

---

## Tests

**19 Tests** für alle Module:
- ✅ Dorks Extended: 5 Tests
- ✅ Phone Extractor: 5 Tests
- ✅ Social Scraper: 4 Tests
- ✅ Deduplication: 4 Tests
- ✅ Integration: 1 Test

Alle Tests bestanden! 🎉

```bash
============== 19 passed in 0.10s ==============
```

---

## Technische Details

### Telefon-Extraktion Confidence

```python
# Konfidenz-Score Berechnung
Base: 0.5

Positive Signale:
+ "telefon": +0.2
+ "mobil": +0.2
+ "erreichbar": +0.15
+ "whatsapp": +0.1

Negative Signale:
- "fax": -0.3
- "impressum": -0.2
- "hotline": -0.2

Ergebnis: 0.1 - 1.0
```

### Deduplizierung Algorithmus

1. **Telefon**: Exakt-Match (normalisiert, letzte 10 Ziffern)
2. **E-Mail**: Case-insensitive Exakt-Match
3. **Name+Stadt**: Fuzzy-Match mit 85% Ähnlichkeit (SequenceMatcher)

### Portal Prioritäten

Portale werden nach Priorität verarbeitet (1 = höchste):
1. kleinanzeigen (beste Ergebnisse)
2. markt_de
3. quoka
4. indeed (neue Job-Board)
5. stepstone (neue Job-Board)
6. arbeitsagentur
7. monster
8. stellenanzeigen
...

---

## Lizenz

Dieses Projekt ist Teil des Luca NRW Scrapers.

---

## Support

Bei Fragen oder Problemen:
1. Schaue in die Tests: `tests/test_extended_features.py`
2. Starte Dashboard für Live-Statistiken: `python dashboard.py`
3. Prüfe Logs in der Konsole
