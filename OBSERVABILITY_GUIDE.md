# Observability & Operations Control Center

## Übersicht

Diese Implementierung fügt dem Luca NRW Scraper ein umfassendes Observability- und Operations-Control-System hinzu, das volle Transparenz und Kontrolle über den Scraper-Betrieb ermöglicht.

## Neue Features

### 1. Enhanced Run Model

Das `ScraperRun`-Modell wurde um folgende Metriken erweitert:

#### Link/URL-Tracking
- `links_checked`: Anzahl der geprüften Links
- `links_successful`: Erfolgreich verarbeitete Links
- `links_failed`: Fehlgeschlagene Links

#### Lead-Tracking
- `leads_accepted`: Akzeptierte Leads (nach Quality-Filter)
- `leads_rejected`: Verworfene Leads

#### Performance-Metriken
- `avg_request_time_ms`: Durchschnittliche Request-Zeit in Millisekunden
- `block_rate`: Block-Rate in Prozent (403, 429 Fehler)
- `timeout_rate`: Timeout-Rate in Prozent
- `error_rate`: Gesamtfehlerrate in Prozent

#### Circuit Breaker
- `circuit_breaker_triggered`: Boolean - wurde ausgelöst
- `circuit_breaker_count`: Anzahl der Auslösungen
- `portal_stats`: JSON - Detaillierte Statistiken pro Portal

#### Neue Status-Optionen
- `partial`: Teilweise erfolgreich (für Läufe mit Teilerfolg)

### 2. Error Classification System

Neues `ErrorLog`-Modell für strukturierte Fehlerklassifizierung:

#### Fehlertypen
- `block_403`: Block/403 - Zugriff verweigert
- `block_429`: Block/429 - Rate Limit
- `captcha`: Captcha/Login erforderlich
- `parsing`: Parsing fehlgeschlagen
- `network_timeout`: Netzwerk/Timeout
- `network_connection`: Netzwerk/Verbindung
- `data_quality`: Datenqualität zu niedrig
- `validation`: Validierung fehlgeschlagen
- `unknown`: Unbekannt

#### Severity-Levels
- `low`: Niedrig
- `medium`: Mittel
- `high`: Hoch
- `critical`: Kritisch

#### Zusätzliche Felder
- `portal`: Betroffenes Portal/Quelle
- `url`: Betroffene URL
- `message`: Fehlermeldung
- `details`: JSON mit technischen Details
- `count`: Häufigkeit des Fehlers
- `last_occurrence`: Zeitpunkt des letzten Auftretens

### 3. Enhanced Log View

#### ScraperLog-Erweiterungen
- Neue Log-Levels: `DEBUG`, `CRITICAL` (zusätzlich zu INFO, WARN, ERROR)
- `portal`-Feld für Quellenzuordnung
- Verbesserte Indexierung für schnelle Filterung

#### API-Endpoints für Logs

**GET /crm/scraper/api/logs/**
- Filtert Logs nach:
  - `run_id`: Spezifischer Lauf
  - `portal`: Portal/Quelle
  - `level`: Log-Level
  - `start_date`: Von-Datum (ISO format)
  - `end_date`: Bis-Datum (ISO format)
  - `limit`: Max. Ergebnisse (default 100)

**GET /crm/scraper/api/errors/**
- Filtert Fehler nach:
  - `run_id`: Spezifischer Lauf
  - `error_type`: Fehlertyp
  - `severity`: Schweregrad
  - `portal`: Portal/Quelle
  - `start_date`: Von-Datum
  - `end_date`: Bis-Datum
  - `limit`: Max. Ergebnisse

### 4. Control Center Functions

#### Rate Limit Management
**POST /crm/scraper/api/control/rate-limit/**
```json
{
  "portal": "portal_name",  // optional, global wenn nicht angegeben
  "rate_limit_seconds": 5.0
}
```

Live-Anpassung von Rate Limits während des Betriebs.

#### Portal Control
**POST /crm/scraper/api/control/portal/toggle/**
```json
{
  "portal": "portal_name",
  "active": true/false
}
```

Aktivieren/Deaktivieren von Portalen on-the-fly.

#### Portal Status
**GET /crm/scraper/api/control/portals/**

Gibt Status aller Portale zurück:
- Aktiv/Inaktiv
- Rate Limits
- Circuit Breaker Status
- Fehler-Zähler

#### Circuit Breaker Management
**POST /crm/scraper/api/control/circuit-breaker/reset/**
```json
{
  "portal": "portal_name"
}
```

Manuelles Zurücksetzen des Circuit Breakers für ein Portal.

### 5. Enhanced PortalSource Model

Neue Felder für Live-Control:

#### Circuit Breaker Configuration
- `circuit_breaker_enabled`: Boolean - Circuit Breaker aktiviert
- `circuit_breaker_threshold`: Schwellwert für Fehler
- `circuit_breaker_cooldown`: Cooldown-Zeit in Sekunden
- `circuit_breaker_tripped`: Aktueller Status
- `circuit_breaker_reset_at`: Zeitpunkt des automatischen Resets
- `consecutive_errors`: Anzahl aufeinanderfolgender Fehler

### 6. Enhanced Dashboard UI

#### Status-Übersicht
- Prozess-ID
- Laufzeit
- Leads gefunden
- CPU/RAM-Auslastung

#### Performance-Metriken-Dashboard
- Links geprüft
- Akzeptanzrate (Leads)
- Block-Rate
- Durchschnittliche Request-Zeit

#### Control Center Panel
- **Rate Limit Control**: Live-Anpassung des globalen Rate Limits
- **Portal Status**: Übersicht aller Portale mit Status-Indikatoren
  - Grün (✓): Aktiv und funktionsfähig
  - Rot (⚠️): Circuit Breaker ausgelöst
  - Grau (✗): Deaktiviert
- **Portal-Aktionen**:
  - Aktivieren/Deaktivieren per Knopfdruck
  - Circuit Breaker Reset
  - Auto-Refresh alle 10 Sekunden

#### Enhanced Runs Table
Neue Spalten:
- Links-Status (geprüft/erfolgreich)
- Akzeptanzrate mit Prozentanzeige
- Block-Rate (farbcodiert: rot >20%, gelb >10%)
- Circuit Breaker Indikator (⚠️)

#### Log-Filtering
- Dropdown-Filter für Log-Levels
- Echtzeit-Log-Stream mit Farbcodierung
- Auto-Scroll zum neuesten Eintrag

## Verwendung

### Scraper starten
1. Wähle Industry und Parameter
2. Klicke "Scraper starten"
3. Überwache Live-Logs und Metriken

### Rate Limits anpassen
1. Gebe neue Rate Limit in Sekunden ein
2. Klicke "Rate Limit aktualisieren"
3. Änderung wirkt sofort

### Portale verwalten
1. Öffne Control Center
2. Sehe Portal-Status in Echtzeit
3. Aktiviere/Deaktiviere Portale nach Bedarf
4. Setze Circuit Breaker bei Bedarf zurück

### Fehleranalyse
1. Navigiere zu einem Run in der Tabelle
2. Klicke auf Run für Details
3. Filtere Logs nach Portal/Level
4. Analysiere Fehler nach Typ und Severity

## Migration

Die Datenbank-Migration ist in `0007_observability_enhancements.py` enthalten.

Führe aus:
```bash
python manage.py migrate scraper_control
```

## API-Dokumentation

### Status Endpoint
**GET /crm/scraper/api/scraper/status/**

Erweiterte Response:
```json
{
  "status": "running",
  "pid": 12345,
  "run_id": 42,
  "uptime_seconds": 120,
  "cpu_percent": 45.2,
  "memory_mb": 128.5,
  "leads_found": 10,
  "leads_accepted": 8,
  "leads_rejected": 2,
  "links_checked": 50,
  "links_successful": 45,
  "links_failed": 5,
  "block_rate": 5.0,
  "timeout_rate": 2.0,
  "error_rate": 8.0,
  "avg_request_time_ms": 850.5,
  "lead_acceptance_rate": 80.0,
  "success_rate": 90.0,
  "circuit_breaker_triggered": false
}
```

### Runs Endpoint
**GET /crm/scraper/api/scraper/runs/**

Enthält alle neuen Metriken pro Run.

## Architektur

### Models
- `ScraperRun`: Enhanced mit Metriken
- `ScraperLog`: Enhanced mit Portal und Level
- `ErrorLog`: Neu - strukturierte Fehlerklassifizierung
- `PortalSource`: Enhanced mit Circuit Breaker

### Views
- Neue API-Endpoints für Filtering und Control
- Enhanced Status-Endpoint

### Process Manager
- Updated `get_status()` mit allen neuen Metriken
- Integration mit ScraperRun-Tracking

### Frontend
- Enhanced Dashboard-Template
- Neues Control Center Panel
- Performance-Metriken-Dashboard
- Enhanced Runs-Table
- JavaScript für Control Center Interaktion

## Best Practices

### Circuit Breaker
- Threshold: 5 Fehler (empfohlen)
- Cooldown: 300 Sekunden (5 Minuten)
- Manuelles Reset nur bei klarer Fehlerursache

### Rate Limits
- Starte mit 2-3 Sekunden
- Erhöhe bei Blocks/429-Fehlern
- Reduziere vorsichtig bei stabiler Performance

### Error Monitoring
- Überwache Block-Rate (sollte <10% sein)
- Checke Timeout-Rate (sollte <5% sein)
- Bei Critical-Errors sofort eingreifen

### Portal Management
- Deaktiviere Portale bei wiederkehrenden Problemen
- Nutze Circuit Breaker für automatische Pausen
- Reaktiviere nach Fehleranalyse

## Troubleshooting

### Hohe Block-Rate
1. Erhöhe Rate Limit
2. Prüfe Portal-spezifische Limits
3. Aktiviere Circuit Breaker

### Circuit Breaker ständig ausgelöst
1. Prüfe ErrorLog nach Fehlertyp
2. Passe Portal-Konfiguration an
3. Erhöhe Threshold oder Cooldown

### Niedrige Akzeptanzrate
1. Prüfe min_score-Konfiguration
2. Analysiere verworfene Leads
3. Passe Quality-Filter an

## Zukünftige Erweiterungen

- Run-Details-Modal mit vollständigen Metriken
- Error-Trend-Visualisierung
- Auto-Tuning von Rate Limits basierend auf Metriken
- Portal-Performance-Historie
- Alerting bei kritischen Schwellwerten
- Export von Metriken für externe Analyse
