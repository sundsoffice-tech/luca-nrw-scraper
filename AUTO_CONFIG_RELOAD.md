# Automatic Configuration Reload Feature

## Überblick

Der Scraper unterstützt jetzt die automatische Übernahme von Konfigurationsänderungen während der Laufzeit. Wenn ein Administrator Einstellungen im CRM ändert, wird der laufende Scraper-Prozess automatisch neu gestartet, um die neuen Einstellungen zu übernehmen.

## Funktionsweise

### Versionierung

Das Modell `ScraperConfig` besitzt ein Feld `config_version`, das bei jeder Speicherung automatisch inkrementiert wird:

```python
def save(self, *args, **kwargs):
    self.pk = 1
    if self._state.adding:
        self.config_version = self.config_version or 1
    else:
        self.config_version = (self.config_version or 0) + 1
    super().save(*args, **kwargs)
```

### Polling-basierte Überwachung

Der `ProcessManager` startet beim Initialisieren einen Hintergrund-Thread, der:

1. Alle 10 Sekunden die `config_version` aus der Datenbank abruft
2. Die Version mit der zuletzt bekannten Version vergleicht
3. Bei Änderung automatisch `restart_process()` aufruft

```python
def _start_config_watcher(self):
    """Start background thread that watches for configuration changes."""
    # Polling-Thread wird als Daemon gestartet
    # Prüft alle 10 Sekunden auf Änderungen
    # Löst automatischen Neustart aus
```

### Automatischer Neustart

Die Methode `restart_process()`:

1. Verwendet einen Lock, um gleichzeitige Neustarts zu verhindern
2. Stoppt den aktuellen Prozess sauber
3. Speichert die Parameter und den Benutzerkontext
4. Lädt die neue Konfiguration aus der Datenbank
5. Startet den Prozess mit denselben Parametern neu

```python
def restart_process(self) -> Dict[str, Any]:
    """Restart the running scraper process with the same parameters."""
    # Lock verhindert gleichzeitige Neustarts
    # Preserviert Benutzer und Parameter
    # Lädt neue Konfiguration
    # Startet mit gleichen Parametern neu
```

### Signal-Handler

Ein `post_save` Signal-Handler protokolliert alle Konfigurationsänderungen:

```python
@receiver(post_save, sender=ScraperConfig)
def scraper_config_changed(sender, instance, created, **kwargs):
    """Log configuration changes for observability."""
    logger.info(f"ScraperConfig updated to version {instance.config_version}")
```

## Benutzer-Benachrichtigungen

### Django Admin Interface

Beim Speichern der Konfiguration im Django Admin wird automatisch eine Nachricht angezeigt:

- **Scraper läuft**: "Konfiguration gespeichert. Der laufende Scraper wird automatisch neu gestartet..."
- **Scraper gestoppt**: "Konfiguration gespeichert. Die Änderungen werden beim nächsten Start angewendet."

### API-Endpunkt

Der API-Endpunkt `/crm/scraper/api/scraper/config/` (PUT) gibt nach erfolgreicher Aktualisierung zurück:

```json
{
    "success": true,
    "message": "Konfiguration aktualisiert. Der laufende Scraper wird automatisch neu gestartet...",
    "config_version": 42
}
```

### Status-Endpunkt

Der Status-Endpunkt `/crm/scraper/api/scraper/status/` (GET) enthält jetzt auch:

```json
{
    "status": "running",
    "config_version": 42,
    "config_updated_at": "2024-01-21T10:00:00Z",
    ...
}
```

## Log-Ausgaben

Der automatische Neustart erzeugt folgende Log-Einträge:

```
INFO: Configuration version changed: 41 -> 42
INFO: Triggering automatic restart due to config change
INFO: Restarting scraper process due to configuration change
INFO: Scraper restarted successfully
```

Im Scraper-Output-Monitor werden folgende Meldungen angezeigt:

```
🔄 Konfigurationsänderung erkannt – automatischer Neustart wird durchgeführt...
✅ Scraper erfolgreich mit neuer Konfiguration neu gestartet
```

## Konfigurierbare Parameter

### Polling-Intervall

Das Standard-Polling-Intervall beträgt 10 Sekunden und ist in `ProcessManager.__init__` konfiguriert:

```python
self.config_check_interval: int = 10  # Check every 10 seconds
```

### Betroffene Einstellungen

Folgende Einstellungen werden automatisch übernommen:

- **Basis**: `industry`, `mode`, `qpi`, `daterestrict`
- **Flags**: `smart`, `force`, `once`, `dry_run`
- **HTTP & Performance**: `http_timeout`, `async_limit`, `pool_size`, `http2_enabled`
- **Rate Limiting**: `sleep_between_queries`, `max_google_pages`, `circuit_breaker_penalty`, `retry_max_per_url`
- **Scoring**: `min_score`, `max_per_domain`, `default_quality_score`, `confidence_threshold`
- **Feature Flags**: `enable_kleinanzeigen`, `enable_telefonbuch`, `enable_perplexity`, `enable_bing`
- **Content**: `allow_pdf`, `max_content_length`
- **Sicherheit**: `allow_insecure_ssl`

## Fehlerbehandlung

### Gleichzeitige Neustarts

Ein `threading.Lock` verhindert gleichzeitige Neustart-Versuche:

```python
if not self.restart_lock.acquire(blocking=False):
    return {'success': False, 'error': 'Restart already in progress'}
```

### Fehler beim Neustart

Bei Fehlern während des Neustarts:

1. Der Lock wird in einem `finally`-Block freigegeben
2. Fehlermeldungen werden geloggt
3. Der Status wird korrekt aktualisiert
4. Der Benutzer erhält eine Fehlermeldung

### Prozess nicht laufend

Wenn kein Prozess läuft, wird kein Neustart durchgeführt:

```python
if not self.is_running():
    return {'success': False, 'error': 'Kein Scraper-Prozess läuft'}
```

## Testing

Umfassende Tests in `test_config_reload.py`:

### Unit-Tests

- `test_config_version_tracking`: Überprüft Versionstracking
- `test_config_watcher_thread_starts`: Überprüft Thread-Start
- `test_restart_process_method`: Testet Neustart-Logik
- `test_restart_process_not_running`: Testet Fehlerfall
- `test_restart_process_concurrent_prevention`: Testet Lock-Mechanismus

### Integrationstests

- `test_config_version_change_triggers_restart`: Simuliert Konfigurationsänderung
- `test_signal_logs_config_change`: Überprüft Signal-Logging
- `test_config_reload_updates_tracked_version`: Testet Versions-Update
- `test_restart_preserves_user_context`: Überprüft Kontext-Erhaltung

## Vorteile

1. **Keine manuellen Neustarts**: Administratoren müssen den Scraper nicht mehr manuell stoppen und starten
2. **Keine zusätzlichen Abhängigkeiten**: Funktioniert ohne Redis oder andere Message-Bus-Systeme
3. **Einfach und zuverlässig**: Polling ist robust und funktioniert in allen Umgebungen
4. **Vollständige Observability**: Alle Änderungen werden protokolliert
5. **Sichere Neustarts**: Lock-Mechanismus verhindert Race Conditions
6. **Kontext-Erhaltung**: Benutzer und Parameter werden über Neustarts hinweg erhalten

## Einschränkungen

1. **Latenz**: Änderungen werden innerhalb von ~10 Sekunden erkannt (Polling-Intervall)
2. **Nur laufende Prozesse**: Der Watcher reagiert nur, wenn ein Scraper läuft
3. **Kompletter Neustart**: Der Prozess wird komplett neu gestartet (kein Hot-Reload)

## Alternative Ansätze (nicht implementiert)

### Redis Pub/Sub

Eine Message-Bus-Lösung mit Redis Pub/Sub wäre schneller, würde aber:

- Eine zusätzliche Abhängigkeit einführen (Redis)
- Mehr Konfiguration erfordern
- Komplexer in der Wartung sein

### Unix-Signale (SIGHUP)

Ein Signal-basierter Ansatz wäre eleganter, würde aber:

- Plattform-abhängig sein (nur Unix-Systeme)
- Komplexere Implementierung erfordern
- Weniger robust sein

Die Polling-Lösung bietet die beste Balance zwischen Einfachheit, Zuverlässigkeit und Funktionalität.

## Zusammenfassung

Das Feature ermöglicht automatische Konfigurationsübernahme durch:

1. **Versionstracking** im ScraperConfig-Modell
2. **Polling-Thread** im ProcessManager (alle 10 Sekunden)
3. **Automatischer Neustart** bei Versionsänderung
4. **Signal-Handler** für Logging
5. **UI-Benachrichtigungen** in Admin und API

Dies eliminiert die Notwendigkeit manueller Neustarts und verbessert die Benutzererfahrung erheblich.
