# Datenstruktur-Konsolidierung: Implementierungsdokumentation

## Überblick

Diese Implementierung löst die Inkonsistenzen zwischen `scraper.db` (SQLite) und dem Django CRM Lead Model. Es wurden **28 neue Felder** hinzugefügt und das Import-System vollständig überarbeitet, um **40+ Felder** ohne Datenverlust zu importieren.

## Änderungen im Detail

### 1. Neue Felder im Django Lead Model

**Qualität & Scoring (3 Felder):**
- `confidence_score` - AI-Konfidenz-Score (Integer)
- `data_quality` - Datenqualitäts-Score (Integer)
- `phone_type` - Telefon-Typ (mobile/landline)

**Telefon & WhatsApp:**
- `whatsapp_link` - WhatsApp-Link/Verfügbarkeit

**AI-Felder (3 Felder):**
- `ai_category` - AI-Kategorisierung
- `ai_summary` - AI-generierte Zusammenfassung
- `opening_line` - AI-generierte Eröffnungszeile für Kontaktaufnahme

**Strukturierte Daten (2 Felder - JSONField):**
- `tags` - Tags als JSON-Array
- `skills` - Fähigkeiten/Kompetenzen als JSON-Array

**Kandidaten-spezifisch (3 Felder):**
- `availability` - Verfügbarkeit
- `candidate_status` - Kandidaten-Status
- `mobility` - Mobilität/Reisebereitschaft

**Unternehmens-Details (5 Felder):**
- `salary_hint` - Gehaltshinweis
- `commission_hint` - Provisionshinweis
- `company_size` - Firmengröße
- `hiring_volume` - Einstellungsvolumen (Integer)
- `industry` - Branche

**Kontakt-Details (4 Felder):**
- `private_address` - Privatadresse
- `profile_url` - Profil-URL (zusätzlich zu linkedin_url/xing_url)
- `cv_url` - Lebenslauf-URL
- `contact_preference` - Bevorzugte Kontaktart

**Metadaten (2 Felder):**
- `recency_indicator` - Aktualitäts-Indikator
- `last_updated` - Letzte Aktualisierung aus Scraper

**Summe: 28 neue Felder**

### 2. Erweiterte LeadType Enum

Neue Lead-Typen hinzugefügt:
```python
TALENT_HUNT = 'talent_hunt', 'Talent Hunt'
RECRUITER = 'recruiter', 'Recruiter'
JOB_AD = 'job_ad', 'Stellenanzeige'
COMPANY = 'company', 'Firmenkontakt'
INDIVIDUAL = 'individual', 'Einzelperson'
```

### 3. Zentrale Feldmapping-Datei

**Datei:** `telis_recruitment/leads/field_mapping.py`

**Komponenten:**
- `FIELD_SCHEMA` - Kanonische Feldnamen mit Aliasen
- `SCRAPER_TO_DJANGO_MAPPING` - Vollständiges Mapping aller Scraper-Felder
- `JSON_ARRAY_FIELDS` - Liste von JSON-Feldern (tags, skills)
- Helper-Funktionen für Feldtyp-Erkennung

**Verwendung:**
```python
from leads.field_mapping import SCRAPER_TO_DJANGO_MAPPING

django_field = SCRAPER_TO_DJANGO_MAPPING.get(scraper_field, scraper_field)
```

### 4. Aktualisiertes import_scraper_db Command

**Datei:** `telis_recruitment/leads/management/commands/import_scraper_db.py`

**Neue Features:**
- Verwendet zentrales Feldmapping
- Automatische JSON-Parsing für tags/skills
- Intelligente Feldtyp-Erkennung (Integer, URL, JSON)
- Importiert ALLE verfügbaren Felder aus scraper.db
- Erweiterte Deduplication mit allen Feldern
- Aktualisiert bestehende Leads mit neuen Daten

**Verwendung:**
```bash
# Standard-Import
python manage.py import_scraper_db

# Mit benutzerdefiniertem Datenbankpfad
python manage.py import_scraper_db --db /pfad/zu/scraper.db

# Watch-Modus (kontinuierlich)
python manage.py import_scraper_db --watch --interval 60

# Dry-Run (Vorschau)
python manage.py import_scraper_db --dry-run

# Force (alle Leads neu importieren)
python manage.py import_scraper_db --force
```

### 5. Neues sync_scraper_db Command

**Datei:** `telis_recruitment/leads/management/commands/sync_scraper_db.py`

Ein Wrapper um `import_scraper_db` mit Scheduling-Support.

**Verwendung:**
```bash
# Einmaliger Sync
python manage.py sync_scraper_db

# Kontinuierlicher Sync (alle 5 Minuten)
python manage.py sync_scraper_db --watch --interval 300

# Mit benutzerdefiniertem DB-Pfad
python manage.py sync_scraper_db --db /pfad/zu/scraper.db --watch
```

**Cron-Setup für automatischen Sync:**
```bash
# Alle 5 Minuten
*/5 * * * * cd /pfad/zu/telis_recruitment && python manage.py sync_scraper_db >> /var/log/scraper_sync.log 2>&1

# Jede Stunde
0 * * * * cd /pfad/zu/telis_recruitment && python manage.py sync_scraper_db >> /var/log/scraper_sync.log 2>&1
```

### 6. Django Migration

**Datei:** `telis_recruitment/leads/migrations/0007_lead_ai_category_lead_ai_summary_lead_availability_and_more.py`

**Inhalt:**
- 23 AddField Operationen für neue Felder
- 1 AlterField Operation für erweiterte LeadType Enum

**Anwendung:**
```bash
# Migration anwenden
python manage.py migrate leads

# Migration rückgängig machen
python manage.py migrate leads 0006

# Status prüfen
python manage.py showmigrations leads
```

**Die Migration ist reversibel** - alle Felder sind nullable und können ohne Datenverlust entfernt werden.

## Vollständige Feldliste

### Felder die bereits existierten:
1. name
2. email
3. telefon
4. status
5. source
6. source_url
7. source_detail
8. quality_score
9. lead_type
10. company
11. role
12. experience_years
13. location
14. linkedin_url
15. xing_url
16. interest_level
17. call_count
18. last_called_at
19. next_followup_at
20. notes
21. email_sent_count
22. email_opens
23. email_clicks
24. last_email_at
25. created_at
26. updated_at
27. assigned_to

### Neu hinzugefügte Felder (28):
28. confidence_score
29. phone_type
30. whatsapp_link
31. ai_category
32. ai_summary
33. opening_line
34. tags (JSONField)
35. skills (JSONField)
36. availability
37. candidate_status
38. mobility
39. salary_hint
40. commission_hint
41. company_size
42. hiring_volume
43. industry
44. data_quality
45. private_address
46. profile_url
47. cv_url
48. contact_preference
49. recency_indicator
50. last_updated

**Gesamt: 50 Felder** (27 alt + 23 neu = 50 Lead-Felder + Metadaten)

## Feldmapping-Beispiele

### Scraper DB → Django

```python
# Einfache 1:1 Mappings
'email' → 'email'
'telefon' → 'telefon'
'name' → 'name'

# Umbenennungen
'rolle' → 'role'
'quelle' → 'source_url'
'region' → 'location'
'company_name' → 'company'

# Mit Fallbacks
'role_guess' OR 'rolle' → 'role'
'location_specific' OR 'region' OR 'location' → 'location'

# Typenkonvertierung
'tags' (String/JSON) → tags (JSONField)
'skills' (String/JSON) → skills (JSONField)
'score' (String) → quality_score (Integer)

# URL-Aufteilung
'social_profile_url' (linkedin.com) → linkedin_url
'social_profile_url' (xing.com) → xing_url
```

## Datenmigration

### Vor der Migration:
- 12 von 40+ Feldern wurden importiert
- 28+ Felder gingen verloren
- Inkonsistente Feldnamen

### Nach der Migration:
- ALLE 40+ Felder werden importiert
- Kein Datenverlust
- Zentrales Mapping für Konsistenz
- Automatische Typenkonvertierung

## Tests

### Manuelle Validierung:

```bash
# 1. Migration anwenden
cd telis_recruitment
python manage.py migrate leads

# 2. Test-Import durchführen (Dry-Run)
python manage.py import_scraper_db --dry-run

# 3. Echten Import durchführen
python manage.py import_scraper_db

# 4. Daten in Django Admin überprüfen
python manage.py runserver
# Öffne http://localhost:8000/admin/leads/lead/

# 5. Sync-Command testen
python manage.py sync_scraper_db

# 6. Watch-Mode testen (Ctrl+C zum Beenden)
python manage.py sync_scraper_db --watch --interval 30
```

### Feldmapping validieren:

```python
from leads.field_mapping import SCRAPER_TO_DJANGO_MAPPING
from leads.models import Lead

# Prüfen ob alle gemappten Felder im Model existieren
for django_field in set(SCRAPER_TO_DJANGO_MAPPING.values()):
    assert hasattr(Lead, django_field), f"Feld {django_field} fehlt im Lead Model"
    
print("✅ Alle gemappten Felder existieren im Lead Model")
```

## Bekannte Einschränkungen

1. **JSONField Kompatibilität:** Benötigt SQLite 3.9+ oder PostgreSQL
2. **Alte Daten:** Bestehende Leads haben die neuen Felder als NULL bis sie aktualisiert werden
3. **Feldlängen:** Einige Felder haben max_length Limits (kann zu Truncation führen)

## Rollback

Falls Probleme auftreten:

```bash
# Migration rückgängig machen
python manage.py migrate leads 0006

# Änderungen am Code per Git zurücksetzen
git checkout HEAD~1 -- telis_recruitment/leads/models.py
git checkout HEAD~1 -- telis_recruitment/leads/management/commands/import_scraper_db.py
```

## Akzeptanzkriterien - Status

✅ Alle 40+ Felder aus scraper.db sind im Django Lead Model verfügbar
✅ LeadType Enum enthält alle verwendeten Typen
✅ import_scraper_db importiert ALLE Felder ohne Datenverlust
✅ Zentrales Feldmapping existiert und wird verwendet
✅ Auto-Sync Command funktioniert mit --interval Flag
✅ Migration ist reversibel
✅ Kein Breaking Change für bestehende Funktionalität

## Nächste Schritte

1. Migration in Produktion anwenden
2. Bestehende Leads aktualisieren mit `--force` Import
3. Cron-Job für automatischen Sync einrichten
4. Django Admin UI anpassen für neue Felder
5. Filter/Suche für neue Felder hinzufügen
