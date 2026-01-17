# GitHub Actions - Dokumentation

## Übersicht

Das Projekt verwendet GitHub Actions für:
1. **Nightly Scraper**: Automatischer Scraper-Lauf um 03:00 CET
2. **Manual Import**: Manueller CSV-Import
3. **Django CI**: Tests bei jedem Push/PR

## Workflows

### 1. Nightly Scraper (`nightly-scraper.yml`)

**Zeitplan**: Täglich um 03:00 CET (02:00 UTC)

**Was passiert**:
1. Chrome + ChromeDriver werden installiert
2. Scraper läuft im Headless-Modus
3. CSV wird erstellt
4. Django Import Command wird ausgeführt
5. CSV wird als Artifact gespeichert (30 Tage)

**Manueller Trigger**:
- Gehe zu Actions → Nightly Scraper Run → Run workflow
- Optional: `max_pages` und `dry_run` Parameter setzen

**Secrets benötigt**:
- `DJANGO_SECRET_KEY` (optional, für Produktion)
- `DATABASE_URL` (optional, für externe DB)
- `SLACK_WEBHOOK_URL` (optional, für Benachrichtigungen)

### 2. Manual Import (`manual-import.yml`)

**Trigger**: Nur manuell

**Parameter**:
- `csv_url`: URL zu CSV-Datei (optional)
- `dry_run`: Testlauf ohne Import
- `force_update`: Bestehende Leads aktualisieren

### 3. Django CI (`django-ci.yml`)

**Trigger**: Push/PR zu `main` Branch (nur `telis_recruitment/` Änderungen)

**Was passiert**:
1. Tests werden ausgeführt
2. Migrations werden geprüft
3. Code-Qualität wird geprüft (flake8, black)

## Secrets einrichten

1. Gehe zu Repository → Settings → Secrets and variables → Actions
2. Füge folgende Secrets hinzu:

| Secret | Beschreibung | Erforderlich |
|--------|--------------|--------------|
| `DJANGO_SECRET_KEY` | Django Secret Key | Empfohlen |
| `DATABASE_URL` | PostgreSQL URL | Für Produktion |
| `SLACK_WEBHOOK_URL` | Slack Webhook | Optional |
| `BREVO_API_KEY` | Brevo API Key | Für Emails |

## Artifacts

Nach jedem Scraper-Lauf werden Artifacts erstellt:
- `leads-{run_number}`: CSV-Datei mit Leads
- `leads-xlsx-{run_number}`: XLSX-Datei (falls erstellt)

Artifacts werden 30 Tage aufbewahrt.

## Troubleshooting

### Scraper schlägt fehl
1. Prüfe Logs im Actions-Tab
2. Chrome/ChromeDriver Version prüfen
3. Manuell mit `dry_run=true` testen

### Import schlägt fehl
1. Prüfe `DATABASE_URL` Secret
2. Prüfe CSV-Format
3. Führe `--dry-run` aus

### Tests schlagen fehl
1. Lokal testen: `python manage.py test`
2. Migrations prüfen: `python manage.py makemigrations --check`
