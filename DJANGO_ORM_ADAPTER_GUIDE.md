# Django ORM Adapter - Usage Guide

## Übersicht

Das neue Modul `luca_scraper/django_db.py` bietet einen Drop-in-Ersatz für die SQLite-basierten Datenbankoperationen und nutzt stattdessen das Django ORM zur Interaktion mit dem Lead-Model im CRM.

## Hauptfunktionen

### `upsert_lead(data: dict) -> tuple[int, bool]`

Erstellt oder aktualisiert einen Lead. Deduplication-Logik:
1. Suche zuerst nach Email (case-insensitive)
2. Falls nicht gefunden, suche nach Telefon (normalisierte Ziffern)
3. Update bei Fund, ansonsten neuen Lead erstellen

**Beispiel:**
```python
from luca_scraper.django_db import upsert_lead

data = {
    'name': 'Max Mustermann',
    'email': 'max@example.com',
    'telefon': '+49123456789',
    'rolle': 'Sales Manager',
    'score': 85,
}

lead_id, created = upsert_lead(data)
print(f"Lead ID: {lead_id}, Neu erstellt: {created}")
```

### `get_lead_count() -> int`

Gibt die Gesamtzahl der Leads zurück.

```python
from luca_scraper.django_db import get_lead_count

count = get_lead_count()
print(f"Anzahl Leads: {count}")
```

### `lead_exists(email=None, telefon=None) -> bool`

Prüft, ob ein Lead mit der angegebenen Email oder Telefonnummer existiert.

```python
from luca_scraper.django_db import lead_exists

if lead_exists(email='max@example.com'):
    print("Lead existiert bereits")
```

### `get_lead_by_id(lead_id: int) -> dict | None`

Ruft einen Lead anhand seiner ID ab. Gibt ein Dictionary mit Scraper-Feldnamen zurück.

```python
from luca_scraper.django_db import get_lead_by_id

lead_data = get_lead_by_id(123)
if lead_data:
    print(f"Name: {lead_data['name']}, Email: {lead_data['email']}")
```

### `update_lead(lead_id: int, data: dict) -> bool`

Aktualisiert einen bestehenden Lead.

```python
from luca_scraper.django_db import update_lead

update_data = {
    'name': 'Max Mustermann Updated',
    'score': 95,
}

success = update_lead(123, update_data)
print(f"Update erfolgreich: {success}")
```

## Field Mapping

Das Modul nutzt automatisch das Field Mapping aus `telis_recruitment/leads/field_mapping.py`:

| Scraper-Feld | Django-Feld |
|--------------|-------------|
| `name` | `name` |
| `email` | `email` |
| `telefon` | `telefon` |
| `rolle` | `role` |
| `company_name` | `company` |
| `region` | `location` |
| `quelle` | `source_url` |
| `score` | `quality_score` |
| ... | ... |

## Datentyp-Konvertierung

Das Modul behandelt automatisch:

- **JSON Arrays**: `tags`, `skills`, `qualifications` werden als JSON-Arrays gespeichert
- **Integer**: `score`, `experience_years`, `confidence_score` werden zu Integers konvertiert
- **Boolean**: `name_validated` wird zu Boolean konvertiert
- **Strings**: Alle anderen Felder werden als Text gespeichert

## Django Setup

Das Django-Setup erfolgt automatisch beim Import des Moduls:

```python
# Django wird automatisch konfiguriert
from luca_scraper.django_db import upsert_lead
```

Falls Django noch nicht konfiguriert ist, wird `DJANGO_SETTINGS_MODULE` auf `telis_recruitment.telis.settings` gesetzt.

## Migration von SQLite zu Django ORM

Um von der SQLite-Version (`luca_scraper/database.py`) zur Django ORM-Version zu wechseln:

**Vorher:**
```python
from luca_scraper.database import db, transaction

with transaction() as con:
    cur = con.cursor()
    cur.execute("INSERT INTO leads ...")
```

**Nachher:**
```python
from luca_scraper.django_db import upsert_lead

upsert_lead({'name': '...', 'email': '...'})
```

## Tests

Unit Tests befinden sich in `tests/test_django_db.py`:

```bash
# Mit pytest-django
pytest tests/test_django_db.py -v

# Manueller Test
python3 test_django_db_manual.py
```

## Anforderungen

- Django 4.2+
- Python 3.11+
- Zugriff auf das Django CRM Model (`telis_recruitment.leads.models.Lead`)

## Hinweise

1. **Source-Tracking**: Alle über dieses Modul erstellten Leads werden automatisch mit `source=Lead.Source.SCRAPER` markiert
2. **Transaktionssicherheit**: Alle Operationen nutzen Django's atomare Transaktionen
3. **Performance**: Die Telefonnummern-Deduplizierung nutzt normalisierte Ziffern für genaue Matches
4. **Fehlerbehandlung**: Fehler beim Django-Setup werden als Warnings geloggt, nicht als Exceptions

## Support

Bei Fragen oder Problemen siehe:
- `luca_scraper/django_db.py` für die Implementierung
- `tests/test_django_db.py` für Beispiele
- `telis_recruitment/leads/field_mapping.py` für Field Mapping Details
