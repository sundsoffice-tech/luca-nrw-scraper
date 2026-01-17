# Scraper → TELIS Integration

## Übersicht
Der Scraper speichert Leads in `scraper.db` (SQLite), und das TELIS Recruitment System nutzt eine eigene Django-Datenbank. Dieses Feature ermöglicht eine automatische Synchronisation zwischen beiden Systemen.

## Features

### 1. Management Command: `import_scraper_db`

Importiert Leads direkt aus der `scraper.db` SQLite-Datenbank ins Django-System.

**Hauptfunktionen:**
- ✅ Direktes Lesen aus `scraper.db` (relativ zu telis_recruitment)
- ✅ Unterstützt `--watch` Flag für kontinuierlichen Import (alle 60 Sekunden)
- ✅ Speichert den letzten Import-Zeitstempel im `SyncStatus` Model
- ✅ Inkrementeller Import: Nur neue Leads seit dem letzten Sync
- ✅ Intelligentes Feld-Mapping von Scraper-DB auf Django Lead-Model
- ✅ Deduplizierung über E-Mail und Telefon
- ✅ Dry-Run Modus zur Vorschau
- ✅ Force-Modus zum kompletten Neuimport

### 2. Model: `SyncStatus`

Verfolgt den Synchronisationsstatus zwischen `scraper.db` und Django.

**Felder:**
- `source`: Quellbezeichnung (z.B. 'scraper_db')
- `last_sync_at`: Zeitpunkt des letzten erfolgreichen Syncs
- `last_lead_id`: ID des letzten importierten Leads
- `leads_imported`: Anzahl der insgesamt importierten Leads
- `leads_updated`: Anzahl der aktualisierten Leads
- `leads_skipped`: Anzahl der übersprungenen Leads

### 3. API Endpoint: `/api/sync/`

Ermöglicht manuelles Triggern eines Syncs über die REST API.

**Authentifizierung:** Erfordert authentifizierten Benutzer

**Parameter:**
- `force` (boolean): Ignoriert letzten Sync und reimportiert alle Leads
- `db_path` (string): Optional - Custom-Pfad zu scraper.db

**Antwort:**
```json
{
  "success": true,
  "message": "Sync erfolgreich abgeschlossen",
  "output": "...",
  "sync_status": {
    "last_sync_at": "2024-01-17T22:25:20.500764Z",
    "last_lead_id": 4,
    "total_imported": 4,
    "total_updated": 0,
    "total_skipped": 0
  }
}
```

## Verwendung

### Kommandozeile

```bash
cd telis_recruitment

# Einmaliger Import (Standard-Pfad: ../scraper.db)
python manage.py import_scraper_db

# Mit spezifischem Pfad
python manage.py import_scraper_db --db /pfad/zu/scraper.db

# Watch-Modus (läuft kontinuierlich, alle 60 Sekunden)
python manage.py import_scraper_db --watch --interval 60

# Dry-Run (Vorschau ohne Speichern)
python manage.py import_scraper_db --dry-run

# Force: Alle Leads neu importieren (ignoriert last_sync)
python manage.py import_scraper_db --force
```

### API

```bash
# Mit curl
curl -X POST http://localhost:8000/api/sync/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Mit force parameter
curl -X POST http://localhost:8000/api/sync/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": true}'

# Mit custom db_path
curl -X POST http://localhost:8000/api/sync/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"db_path": "/custom/path/to/scraper.db"}'
```

### Python/Django Shell

```python
from django.core.management import call_command

# Einmaliger Import
call_command('import_scraper_db')

# Mit Optionen
call_command('import_scraper_db', '--db', '/path/to/scraper.db', '--force')
```

## Feld-Mapping

Mapping der Scraper-DB-Felder auf das Django Lead-Model:

| Scraper-DB Feld      | Django Lead Feld  | Anmerkungen                           |
|----------------------|-------------------|---------------------------------------|
| `name`               | `name`            | Direktes Mapping                      |
| `email`              | `email`           | Direktes Mapping                      |
| `telefon`            | `telefon`         | Direktes Mapping                      |
| `quelle`             | `source_url`      | Direktes Mapping                      |
| `score`              | `quality_score`   | Clamped auf 0-100                     |
| `rolle` / `role_guess` | `role`          | Bevorzugt `role_guess`                |
| `company_name`       | `company`         | Direktes Mapping                      |
| `region` / `location_specific` | `location` | Bevorzugt `location_specific` |
| `lead_type`          | `lead_type`       | Mit Typ-Mapping (siehe unten)         |
| `social_profile_url` | `linkedin_url` oder `xing_url` | Automatische Erkennung |

### Lead-Type Mapping

```python
LEAD_TYPE_MAPPING = {
    'active_salesperson': Lead.LeadType.ACTIVE_SALESPERSON,
    'team_member': Lead.LeadType.TEAM_MEMBER,
    'freelancer': Lead.LeadType.FREELANCER,
    'hr_contact': Lead.LeadType.HR_CONTACT,
    'candidate': Lead.LeadType.CANDIDATE,
}
```

Unbekannte Lead-Typen werden auf `Lead.LeadType.UNKNOWN` gesetzt.

## Deduplizierung

Das System erkennt Duplikate durch:
1. **E-Mail-Matching**: Wenn eine E-Mail bereits existiert
2. **Telefon-Matching**: Wenn eine Telefonnummer bereits existiert (falls keine E-Mail vorhanden)

Bei Duplikaten:
- Der Lead wird **aktualisiert**, wenn der neue Score höher ist
- Fehlende Felder (company, role, location, social URLs) werden ergänzt
- Der Lead wird **übersprungen**, wenn der neue Score niedriger oder gleich ist (außer im `--force` Modus)

## Inkrementeller Import

Der inkrementelle Import funktioniert über das `SyncStatus` Model:
- Speichert die ID des letzten importierten Leads
- Beim nächsten Import werden nur Leads mit höherer ID importiert
- Effizienter als vollständiger Reimport
- Kann mit `--force` überschrieben werden

## Django Admin Integration

Das `SyncStatus` Model ist im Django Admin verfügbar unter:
- **URL**: `/admin/leads/syncstatus/`
- **Anzeige**: Letzter Sync-Zeitpunkt mit Farbcodierung (grün = aktuell, gelb = älter, rot = sehr alt)
- **Statistiken**: Importiert, Aktualisiert, Übersprungen
- **Nur Lesezugriff**: Keine manuelle Bearbeitung möglich

## Tests

Das Feature ist vollständig getestet mit:
- ✅ 4 Tests für SyncStatus Model
- ✅ 12 Tests für import_scraper_db Command
- ✅ 3 Tests für API Endpoint
- ✅ Tests für Deduplizierung, Incremental Import, Force-Modus, Dry-Run
- ✅ Tests für Lead-Type Mapping und Social URL Extraktion

Tests ausführen:
```bash
cd telis_recruitment
python manage.py test leads.tests.SyncStatusModelTest
python manage.py test leads.tests.ImportScraperDBCommandTest
python manage.py test leads.tests.TriggerSyncAPITest
```

## Troubleshooting

### "Scraper-Datenbank nicht gefunden"
- Prüfen Sie den Pfad zur `scraper.db`
- Verwenden Sie `--db` Parameter mit absolutem Pfad
- Standard-Pfad: `../scraper.db` relativ zu `telis_recruitment`

### "no such table: leads_syncstatus"
- Führen Sie Migrationen aus: `python manage.py migrate`

### Duplikate werden nicht erkannt
- Prüfen Sie, ob E-Mail oder Telefon exakt übereinstimmen
- Whitespace und Groß-/Kleinschreibung werden bei E-Mails ignoriert

### Watch-Modus läuft nicht
- Prüfen Sie die Berechtigung für kontinuierliche Ausführung
- Verwenden Sie einen Process Manager wie `systemd` oder `supervisor` für Production

## Production Deployment

Für Production-Einsatz empfehlen wir:

1. **Systemd Service** für Watch-Modus:
```ini
[Unit]
Description=TELIS Scraper Sync Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/telis_recruitment
ExecStart=/path/to/venv/bin/python manage.py import_scraper_db --watch --interval 300
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Cron Job** für regelmäßigen Import:
```bash
# Alle 5 Minuten
*/5 * * * * cd /path/to/telis_recruitment && /path/to/venv/bin/python manage.py import_scraper_db >> /var/log/telis_sync.log 2>&1
```

3. **Logging** aktivieren:
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/telis_sync.log',
        },
    },
    'loggers': {
        'leads': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Sicherheit

- ✅ API-Endpoint erfordert Authentifizierung
- ✅ Keine SQL-Injection (Prepared Statements)
- ✅ Kein Remote Code Execution
- ✅ Validierung aller Eingabedaten
- ✅ Keine sensitive Daten in Logs

## Performance

- **Inkrementeller Import**: Nur neue Leads, nicht die gesamte DB
- **Batch Processing**: Alle Imports in einer Transaction
- **Index-basiert**: Schnelle Duplikaterkennung über DB-Indizes
- **Memory-effizient**: Row-by-Row Processing, kein Laden der gesamten DB in Memory

## Lizenz

Teil des TELIS Recruitment Systems.
