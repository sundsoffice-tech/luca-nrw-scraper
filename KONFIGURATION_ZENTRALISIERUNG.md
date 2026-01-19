# Zentrale Konfigurationsverwaltung

## Übersicht

Die Konfiguration des LUCA NRW Scrapers wurde zentralisiert, um Inkonsistenzen zwischen verschiedenen Konfigurationsquellen zu vermeiden. Alle Scraper-Parameter werden nun über ein dreistufiges Prioritätssystem verwaltet.

## Prioritätssystem

Die Konfiguration wird in folgender Reihenfolge geladen:

### 1. Django-Datenbank (Höchste Priorität) ✅
- **Quelle**: `ScraperConfig` Model in der Datenbank
- **Verwaltung**: Django Admin UI unter `/admin/scraper_control/scraperconfig/`
- **Persistenz**: Permanent über alle Läufe hinweg
- **Verwendung**: Produktionsumgebungen, zentrale Verwaltung

**Vorteile:**
- Änderungen ohne Code-Deployment
- Versionierung durch Django
- Benutzerfreundliche UI
- Audit-Trail (wer hat wann geändert)

### 2. Umgebungsvariablen (Mittlere Priorität) 🔧
- **Quelle**: `.env` Datei oder System-Umgebungsvariablen
- **Verwendung**: Lokale Entwicklung, Testing, Container-Deployments
- **Fallback**: Wenn Datenbank nicht verfügbar ist

**Beispiel `.env`:**
```bash
HTTP_TIMEOUT=15
ASYNC_LIMIT=50
POOL_SIZE=20
MIN_SCORE=45
ENABLE_KLEINANZEIGEN=1
PARALLEL_PORTAL_CRAWL=1
MAX_CONCURRENT_PORTALS=8
```

### 3. Hardcodierte Defaults (Niedrigste Priorität) 📋
- **Quelle**: `_CONFIG_DEFAULTS` in `luca_scraper/config.py`
- **Verwendung**: Letzter Fallback
- **Zweck**: Sicherstellen, dass der Scraper immer valide Konfiguration hat

## Verfügbare Parameter

### HTTP & Networking
| Parameter | DB-Feld | Env-Variable | Default | Beschreibung |
|-----------|---------|--------------|---------|--------------|
| `http_timeout` | `http_timeout` | `HTTP_TIMEOUT` | 10 | Request-Timeout in Sekunden |
| `async_limit` | `async_limit` | `ASYNC_LIMIT` | 35 | Max. parallele Requests |
| `pool_size` | `pool_size` | `POOL_SIZE` | 12 | Connection-Pool-Größe |
| `http2_enabled` | `http2_enabled` | `HTTP2` | True | HTTP/2 aktivieren |

### Rate Limiting
| Parameter | DB-Feld | Env-Variable | Default | Beschreibung |
|-----------|---------|--------------|---------|--------------|
| `sleep_between_queries` | `sleep_between_queries` | `SLEEP_BETWEEN_QUERIES` | 2.7 | Pause zwischen Queries (Sek) |
| `max_google_pages` | `max_google_pages` | `MAX_GOOGLE_PAGES` | 2 | Max. Seiten pro Query |
| `circuit_breaker_penalty` | `circuit_breaker_penalty` | `CB_BASE_PENALTY` | 30 | Circuit-Breaker Penalty (Sek) |
| `retry_max_per_url` | `retry_max_per_url` | `RETRY_MAX_PER_URL` | 2 | Max. Retries pro URL |

### Scoring & Filtering
| Parameter | DB-Feld | Env-Variable | Default | Beschreibung |
|-----------|---------|--------------|---------|--------------|
| `min_score` | `min_score` | `MIN_SCORE` | 40 | Mindest-Score für Leads |
| `max_per_domain` | `max_per_domain` | `MAX_PER_DOMAIN` | 5 | Max. Leads pro Domain |
| `default_quality_score` | `default_quality_score` | - | 50 | Default Quality-Score |
| `confidence_threshold` | `confidence_threshold` | - | 0.35 | Confidence Schwellenwert |

### Feature Flags
| Parameter | DB-Feld | Env-Variable | Default | Beschreibung |
|-----------|---------|--------------|---------|--------------|
| `enable_kleinanzeigen` | `enable_kleinanzeigen` | `ENABLE_KLEINANZEIGEN` | True | Kleinanzeigen-Crawling |
| `enable_telefonbuch` | `enable_telefonbuch` | `TELEFONBUCH_ENRICHMENT_ENABLED` | True | Telefonbuch-Enrichment |
| `parallel_portal_crawl` | `parallel_portal_crawl` | `PARALLEL_PORTAL_CRAWL` | True | Paralleles Portal-Crawling |
| `max_concurrent_portals` | `max_concurrent_portals` | `MAX_CONCURRENT_PORTALS` | 5 | Max. parallele Portale |

### Content & Security
| Parameter | DB-Feld | Env-Variable | Default | Beschreibung |
|-----------|---------|--------------|---------|--------------|
| `allow_pdf` | `allow_pdf` | `ALLOW_PDF` | False | PDF-Verarbeitung erlauben |
| `max_content_length` | `max_content_length` | `MAX_CONTENT_LENGTH` | 2MB | Max. Content-Größe |
| `allow_insecure_ssl` | `allow_insecure_ssl` | `ALLOW_INSECURE_SSL` | False | Unsichere SSL-Verbindungen |

## Verwendung

### Im Code

Die Konfiguration wird automatisch beim Import geladen:

```python
from luca_scraper.config import HTTP_TIMEOUT, ASYNC_LIMIT, MIN_SCORE_ENV

# Direkte Verwendung der globalen Variablen (Abwärtskompatibilität)
timeout = HTTP_TIMEOUT  # Verwendet die zentralisierte Konfiguration

# Oder dynamisch neu laden
from luca_scraper.config import get_scraper_config

config = get_scraper_config()  # Gesamte Konfiguration
timeout = get_scraper_config('http_timeout')  # Spezifischer Parameter
```

### Im Django Admin

1. Navigiere zu: http://localhost:8000/admin/scraper_control/scraperconfig/
2. Bearbeite das Singleton-Objekt (ID=1)
3. Speichern → Änderungen werden beim nächsten Scraper-Start aktiv

### Via Umgebungsvariablen

```bash
# .env Datei bearbeiten
echo "ASYNC_LIMIT=50" >> .env
echo "MIN_SCORE=45" >> .env

# Oder direkt setzen
export HTTP_TIMEOUT=15
export PARALLEL_PORTAL_CRAWL=1

# Scraper starten
python scriptname.py --once --industry recruiter
```

## Migration

### Bestehende Installation

Die Migration `0007_init_config_from_env.py` liest beim ersten Mal automatisch die Umgebungsvariablen ein und speichert sie in der Datenbank:

```bash
cd telis_recruitment
python manage.py migrate scraper_control
```

**Wichtig:** Die Migration aktualisiert nur neue Konfigurationen. Existierende Einstellungen im Admin bleiben erhalten.

### Manuelle Initialisierung

Falls die Datenbank-Konfiguration zurückgesetzt werden soll:

```python
from telis_recruitment.scraper_control.models import ScraperConfig
import os

config = ScraperConfig.get_config()
config.http_timeout = int(os.getenv("HTTP_TIMEOUT", "10"))
config.async_limit = int(os.getenv("ASYNC_LIMIT", "35"))
# ... weitere Parameter
config.save()
```

## Best Practices

### Produktionsumgebung
1. ✅ Verwende **Django Admin** für zentrale Konfiguration
2. ✅ Setze kritische Werte in der Datenbank
3. ✅ Verwende `.env` nur für API-Keys und Secrets
4. ✅ Dokumentiere Änderungen im Admin

### Entwicklungsumgebung
1. ✅ Verwende `.env` für schnelle Experimente
2. ✅ Teste verschiedene Konfigurationen ohne DB-Änderungen
3. ✅ Committe keine `.env` Dateien

### Testing
1. ✅ Verwende Environment-Variablen für CI/CD
2. ✅ Überschreibe Werte temporär für Tests
3. ✅ Stelle sicher, dass Tests mit Defaults funktionieren

## Troubleshooting

### Problem: Konfiguration wird nicht geladen

**Symptom:** Scraper verwendet alte Werte

**Lösung:**
```python
# Prüfe Priorität
from luca_scraper.config import get_scraper_config, SCRAPER_CONFIG_AVAILABLE

print(f"DB verfügbar: {SCRAPER_CONFIG_AVAILABLE}")
config = get_scraper_config()
print(f"HTTP_TIMEOUT: {config['http_timeout']}")
```

### Problem: Datenbank nicht verfügbar

**Symptom:** `SCRAPER_CONFIG_AVAILABLE = False`

**Lösung:**
- Prüfe Django-Setup: `cd telis_recruitment && python manage.py check`
- Führe Migrationen aus: `python manage.py migrate`
- Verwende `.env` als Fallback

### Problem: Inkonsistente Werte

**Symptom:** Unterschiedliche Werte in DB und Code

**Lösung:**
1. Prüfe aktuelle Quelle:
```python
from luca_scraper.config import get_scraper_config
import os

print(f"DB Wert: {get_scraper_config('http_timeout')}")
print(f"Env Wert: {os.getenv('HTTP_TIMEOUT', 'nicht gesetzt')}")
```

2. Entscheide für eine Quelle:
   - **DB**: Lösche/kommentiere Env-Variablen aus
   - **Env**: Aktualisiere DB über Admin

## Vorteile der Zentralisierung

### Vorher ❌
- Konfiguration verstreut über:
  - `luca_scraper/config.py` (Environment-Variablen)
  - `ScraperConfig` Model (Datenbank)
  - `scriptname.py` (lokale Überschreibungen)
- Inkonsistenzen möglich
- Schwer nachvollziehbar, welcher Wert aktiv ist

### Nachher ✅
- **Single Source of Truth**: Eine klare Priorität
- **Transparent**: Nachvollziehbar woher Werte kommen
- **Flexibel**: Verschiedene Quellen für verschiedene Umgebungen
- **Sicher**: Fallbacks verhindern Fehler
- **Administrierbar**: Änderungen ohne Code-Deployment

## Siehe auch

- [SCRAPER_CONFIG_IMPLEMENTATION.md](SCRAPER_CONFIG_IMPLEMENTATION.md) - Ursprüngliche Implementation
- [telis_recruitment/README.md](telis_recruitment/README.md) - Django CRM Dokumentation
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - Weitere Konfigurationsoptionen
