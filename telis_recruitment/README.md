# TELIS Recruitment System

Django-basiertes Rekrutierungssystem für die Verwaltung und Verarbeitung von Leads aus dem LUCA NRW Scraper.

## Quick Start

### 1. Einrichtung der Umgebung

```bash
cd telis_recruitment

# Erstelle eine virtuelle Umgebung
python -m venv venv

# Aktiviere die virtuelle Umgebung
# Unter Linux/Mac:
source venv/bin/activate
# Unter Windows:
# venv\Scripts\activate

# Installiere die Abhängigkeiten
pip install -r requirements.txt
```

### 2. Konfiguration

Erstelle eine `.env` Datei aus der Vorlage:

```bash
cp .env.example .env
```

Bearbeite die `.env` Datei und passe die Werte nach Bedarf an:
- `SECRET_KEY`: Generiere einen sicheren Secret Key für die Produktion
- `DEBUG`: Setze auf `False` für die Produktion
- `ALLOWED_HOSTS`: Füge deine Domain(s) hinzu
- `DATABASE_URL`: Konfiguriere deine Datenbank (Standard: SQLite)
- `SCRAPER_PATH`: Pfad zum LUCA Scraper (Standard: `../`)

### 3. Datenbank initialisieren

```bash
# Führe Migrationen aus
python manage.py migrate

# Erstelle einen Admin-Benutzer
python manage.py createsuperuser
```

### 4. Development Server starten

```bash
python manage.py runserver
```

Der Server läuft jetzt auf http://127.0.0.1:8000/

- Admin-Interface: http://127.0.0.1:8000/admin/
- CRM Dashboard: http://127.0.0.1:8000/crm/
- Scraper Control: http://127.0.0.1:8000/crm/scraper/ (Admin only)
- API-Endpoints: http://127.0.0.1:8000/api/

### 5. Statische Dateien (für Produktion)

```bash
python manage.py collectstatic
```

## Projektstruktur

```
telis_recruitment/
├── manage.py              # Django Management-Skript
├── requirements.txt       # Python-Abhängigkeiten
├── .env.example          # Vorlage für Umgebungsvariablen
├── .env                  # Lokale Umgebungsvariablen (nicht in Git)
├── db.sqlite3            # SQLite-Datenbank (nicht in Git)
├── telis/                # Django-Projektverzeichnis
│   ├── __init__.py
│   ├── settings.py       # Projekteinstellungen
│   ├── urls.py           # URL-Konfiguration
│   ├── wsgi.py           # WSGI-Konfiguration
│   └── asgi.py           # ASGI-Konfiguration
└── leads/                # Lead-Management-App
    ├── __init__.py
    ├── apps.py           # App-Konfiguration
    ├── models.py         # Datenmodelle (PR #1b)
    ├── admin.py          # Admin-Konfiguration (PR #1c)
    ├── views.py          # API-Views (PR #1d)
    └── urls.py           # App-URLs (PR #1d)
```

## Deployment

Für die Produktion mit Gunicorn:

```bash
gunicorn telis.wsgi:application --bind 0.0.0.0:8000
```

## Nächste Schritte

Nach diesem Setup (PR #1a) folgen:
- **PR #1b**: Hinzufügen der Datenmodelle (Lead, Company, Contact, etc.)
- **PR #1c**: Admin-Konfiguration für die Verwaltung im Django Admin
- **PR #1d**: REST API-Endpoints für Lead-Management
- **PR #1e**: Import-Command für das Einlesen von Scraper-Daten

## Technologie-Stack

- **Django 4.2**: Web-Framework
- **Django REST Framework**: API-Entwicklung
- **SQLite**: Datenbank (Standard, kann geändert werden)
- **Gunicorn**: WSGI-Server für Produktion
- **Whitenoise**: Statische Dateien
- **CORS Headers**: API-Zugriffskontrolle
- **psutil**: Prozess-Monitoring für Scraper-Control
- **openpyxl**: Excel-Export-Funktionalität

## Features

### 🎯 CRM Dashboard
- Echtzeit-KPIs und Statistiken
- Lead-Verwaltung mit Filterung und Suche
- Aktivitäts-Feed
- Team-Performance-Übersicht (Manager/Admin)

### 🤖 Scraper-Steuerung (Admin only)
Das integrierte Scraper-Control-Panel ermöglicht die vollständige Verwaltung des LUCA Scraper:

- **Start/Stop**: Scraper mit verschiedenen Modi und Parametern starten
- **Live-Monitoring**: Echtzeit-Status, CPU/RAM-Auslastung, Leads-Count
- **Live-Logs**: Server-Sent Events (SSE) für Log-Streaming
- **Historie**: Übersicht über vergangene Scraper-Läufe
- **Export**: CSV/Excel-Export mit erweiterten Filtern

**Zugriff:** http://127.0.0.1:8000/crm/scraper/ (erfordert Admin-Berechtigung)

**API-Endpunkte:**
- `POST /crm/api/scraper/start/` - Scraper starten
- `POST /crm/api/scraper/stop/` - Scraper stoppen
- `GET /crm/api/scraper/status/` - Aktueller Status
- `GET /crm/api/scraper/logs/` - Live-Log-Stream (SSE)
- `GET /crm/api/export/csv/` - Lead-Export als CSV
- `GET /crm/api/export/excel/` - Lead-Export als Excel

### 📊 Export-Funktionen
- CSV-Export mit Filtern
- Excel-Export mit Formatierung
- Filterung nach Status, Quelle, Lead-Typ, Score, Datum
- Automatische Spaltenbreite und Styling

### 🔐 Berechtigungssystem
- **Admin**: Vollzugriff inkl. Scraper-Control und Einstellungen
- **Manager**: Leads einsehen, Reports, Team-Performance
- **Telefonist**: Nur zugewiesene Leads und Anruf-Funktionen

## Support

Bei Fragen oder Problemen erstelle bitte ein Issue im Repository.
