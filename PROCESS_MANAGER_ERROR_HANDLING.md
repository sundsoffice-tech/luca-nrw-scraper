# ProcessManager Error Handling & Automatic Retry

## Overview

Der ProcessManager wurde mit einem robusten Fehlerbehandlungssystem erweitert, das automatische Retries und einen Circuit Breaker zur Vermeidung von wiederholten Fehlern implementiert.

## Features

### 1. Error Tracking (Fehlerverfolgung)

Der ProcessManager verfolgt verschiedene Fehlertypen:

- **missing_module**: ModuleNotFoundError - fehlende Python-Module
- **rate_limit**: Rate-Limit-Fehler von APIs/Portalen
- **config_error**: Konfigurationsfehler (KeyError, AttributeError)
- **crash**: Prozessabstürze (frühe Exits)
- **other**: Andere Fehler

Jeder Fehler wird gezählt und mit Zeitstempel gespeichert, um die Fehlerrate zu berechnen.

### 2. Automatic Retry (Automatische Wiederholungen)

Bei wiederholten Fehlern startet der ProcessManager automatisch neu:

- **Exponentieller Backoff**: Wartezeit verdoppelt sich bei jedem Retry (30s, 60s, 120s, ...)
- **Maximale Versuche**: Konfigurierbar über `process_max_retry_attempts` (Standard: 3)
- **QPI-Reduktion**: Bei Rate-Limit-Fehlern wird QPI automatisch reduziert
- **Intelligente Parameter-Anpassung**: Scraper-Parameter werden basierend auf Fehlertyp angepasst

#### QPI-Reduktion bei Rate Limits

Wenn Rate-Limit-Fehler erkannt werden, reduziert der ProcessManager automatisch den QPI-Wert:

```python
# Beispiel: QPI 20 mit Reduktionsfaktor 0.7
Original QPI: 20
Angepasster QPI: 14 (20 * 0.7)
```

Der Reduktionsfaktor ist über `process_qpi_reduction_factor` konfigurierbar (Standard: 0.7 = 70%).

### 3. Circuit Breaker

Der Circuit Breaker verhindert wiederholte Fehler durch temporäres Blockieren:

#### Zustände

1. **CLOSED** (Geschlossen): Normaler Betrieb, alle Operationen erlaubt
2. **OPEN** (Offen): Zu viele Fehler, alle Operationen blockiert
3. **HALF_OPEN** (Halb-offen): Test-Betrieb nach Penalty-Zeit

#### Verhalten

- **Öffnen**: Nach Erreichen der Fehler-Schwelle (`process_circuit_breaker_failures`, Standard: 5)
- **Penalty**: Wartezeit bevor Test möglich ist (`circuit_breaker_penalty`, Standard: 30 Sekunden)
- **Test**: Nach Penalty-Zeit wird ein Test-Betrieb erlaubt (HALF_OPEN)
- **Schließen**: Bei erfolgreichem Test-Betrieb schließt der Circuit Breaker wieder

#### Fehlerrate-Überwachung

Der Circuit Breaker überwacht auch die Fehlerrate über ein Zeitfenster:

- **Zeitfenster**: 5 Minuten (300 Sekunden)
- **Schwelle**: Konfigurierbar über `process_error_rate_threshold` (Standard: 0.5 = 50%)
- **Aktion**: Öffnet Circuit Breaker bei Überschreitung der Schwelle

## Konfiguration

Alle Einstellungen sind über die ScraperConfig-Model im Django Admin konfigurierbar:

### Process Manager - Retry & Circuit Breaker

| Feld | Typ | Standard | Beschreibung |
|------|-----|----------|--------------|
| `process_max_retry_attempts` | Integer | 3 | Maximale automatische Neustarts bei Fehlern |
| `process_qpi_reduction_factor` | Float | 0.7 | QPI-Anpassung bei Rate-Limits (0.7 = 70%) |
| `process_error_rate_threshold` | Float | 0.5 | Fehlerrate für Circuit Breaker (0.5 = 50%) |
| `process_circuit_breaker_failures` | Integer | 5 | Anzahl Fehler bis Circuit Breaker öffnet |
| `process_retry_backoff_base` | Float | 30.0 | Basis-Wartezeit für exponentiellen Backoff (Sekunden) |
| `circuit_breaker_penalty` | Integer | 30 | Pausenzeit wenn Circuit Breaker öffnet (Sekunden) |

### Zugriff über Django Admin

1. Navigiere zu `/admin/scraper_control/scraperconfig/`
2. Öffne den Config-Eintrag (ID 1)
3. Suche die Sektion "Process Manager - Retry & Circuit Breaker"
4. Passe die Werte nach Bedarf an
5. Speichern

## Monitoring

### Status-Informationen

Die `get_status()`-Methode liefert erweiterte Informationen:

```python
{
    "status": "running",
    "pid": 12345,
    "error_counts": {
        "missing_module": 0,
        "rate_limit": 2,
        "config_error": 0,
        "crash": 1,
        "other": 0
    },
    "consecutive_failures": 1,
    "retry_count": 1,
    "max_retry_attempts": 3,
    "error_rate": 0.15,
    "circuit_breaker_state": "closed",
    "circuit_breaker_failures": 3,
    # Optional wenn Circuit Breaker offen:
    "circuit_breaker_penalty_seconds": 30,
    "circuit_breaker_elapsed_seconds": 15,
    "circuit_breaker_remaining_seconds": 15
}
```

### Log-Einträge

Der ProcessManager schreibt detaillierte Log-Einträge für alle Fehler und Aktionen:

#### Error Tracking
```
Error tracked: rate_limit, total: 2, circuit breaker failures: 3
```

#### Circuit Breaker
```
Circuit breaker OPENED after 5 failures
Circuit breaker transitioning to HALF_OPEN after 30.5s penalty
Circuit breaker CLOSED - normal operation resumed
```

#### Retry Logic
```
Scheduling retry 1/3 after 30.0s backoff
Executing automatic retry 1
```

#### QPI Reduction
```
Reducing QPI from 20 to 14 due to rate limit errors
⚙️ Automatically reducing QPI: 20 → 14 to avoid rate limits
```

## API-Änderungen

### `start(params, user)` - Erweitert

Prüft jetzt Circuit Breaker Status vor dem Start:

```python
result = manager.start({'industry': 'recruiter', 'qpi': 15}, user=user)

# Bei geöffnetem Circuit Breaker:
{
    'success': False,
    'error': 'Circuit breaker is OPEN - please wait 15s before retrying',
    'status': 'circuit_breaker_open',
    'circuit_breaker_state': 'open',
    'remaining_penalty_seconds': 15
}
```

### `stop()` - Erweitert

Setzt jetzt Retry-Zähler zurück bei manuellem Stop.

### `get_status()` - Erweitert

Liefert umfangreiche Error-Tracking- und Circuit-Breaker-Informationen (siehe oben).

### `reset_error_tracking()` - Neu

Manuelles Zurücksetzen aller Fehler-Zähler und Circuit Breaker:

```python
manager.reset_error_tracking()
```

**Verwendung**: Nach Behebung von Problemen oder bei False Positives.

## Workflow-Beispiele

### Szenario 1: Rate Limit Error

1. **Fehler erkannt**: ProcessManager erkennt "rate limit" in Logs
2. **Error Tracking**: `error_counts['rate_limit'] += 1`
3. **Retry mit QPI-Reduktion**: 
   - Original QPI: 20
   - Neuer QPI: 14 (20 * 0.7)
   - Backoff: 30 Sekunden
4. **Automatischer Neustart**: Nach 30s mit reduziertem QPI

### Szenario 2: Wiederholte Crashes

1. **Crash erkannt**: Prozess endet nach < 5 Sekunden
2. **Error Tracking**: `error_counts['crash'] += 1`
3. **Circuit Breaker**: Nach 5 Crashes → OPEN
4. **Blockierung**: Weitere Starts werden blockiert
5. **Penalty-Zeit**: 30 Sekunden warten
6. **Test-Betrieb**: HALF_OPEN → Versuch mit gleichen Parametern
7. **Erfolg**: CLOSED → Normaler Betrieb
8. **Fehler**: OPEN → Penalty erneut

### Szenario 3: Hohe Fehlerrate

1. **Viele kleine Fehler**: 150 Fehler in 5 Minuten
2. **Fehlerrate**: 150 / 300 = 0.5 (50%)
3. **Schwelle überschritten**: 0.5 >= 0.5
4. **Circuit Breaker**: OPEN
5. **Pause**: 30 Sekunden
6. **Wiederaufnahme**: HALF_OPEN → Test

## Best Practices

### 1. Monitoring

- Überwache `error_rate` in Dashboards
- Setze Alerts bei hohen Fehlerraten
- Prüfe Log-Einträge regelmäßig

### 2. Konfiguration

- **Entwicklung**: Höhere Schwellen (z.B. 10 Failures)
- **Produktion**: Konservative Schwellen (z.B. 5 Failures)
- **Rate-Limits**: Niedrigerer QPI-Reduktionsfaktor (z.B. 0.5)

### 3. Circuit Breaker Reset

Nach Behebung von Problemen:

```python
manager = get_manager()
manager.reset_error_tracking()
```

### 4. QPI-Anpassung

Bei häufigen Rate-Limits:

1. Erhöhe `sleep_between_queries` (z.B. von 2.7s auf 4.0s)
2. Reduziere `qpi` im Config dauerhaft
3. Oder passe `process_qpi_reduction_factor` an (z.B. 0.5 statt 0.7)

## Technische Details

### Error Detection in `_read_output()`

```python
# Detect common errors and track them
if 'ModuleNotFoundError' in line:
    self._log_error("Missing module - check dependencies")
    self._track_error('missing_module')
elif 'KeyError' in line or 'AttributeError' in line:
    self._log_error(f"Configuration error: {line.strip()}")
    self._track_error('config_error')
elif 'rate limit' in message_lower:
    self._log_error("Rate limit hit - consider reducing QPI")
    self._track_error('rate_limit')
```

### Circuit Breaker State Machine

```
      [CLOSED]
         |
    5 Fehler
         |
         v
      [OPEN] ----30s Penalty----> [HALF_OPEN]
         ^                            |
         |                            |
         +-------Fehler---------------+
                                      |
                                   Erfolg
                                      |
                                      v
                                  [CLOSED]
```

### Retry Backoff Calculation

```python
def _calculate_retry_backoff(self) -> float:
    return self.retry_backoff_base * (2 ** self.retry_count)

# Beispiel mit base=30:
# retry_count=0: 30s
# retry_count=1: 60s
# retry_count=2: 120s
# retry_count=3: 240s
```

## Migration

Die neuen Felder werden durch Migration `0007_add_process_retry_circuit_breaker_fields.py` hinzugefügt.

```bash
# Migration anwenden
python manage.py migrate scraper_control
```

## Tests

Umfangreiche Tests in `test_process_manager_retry.py`:

- `ProcessManagerErrorTrackingTest`: Error Tracking Funktionalität
- `ProcessManagerRetryLogicTest`: Retry-Logik und QPI-Anpassung
- `ProcessManagerIntegrationTest`: Integration und Status-API
- `ProcessManagerConfigLoadTest`: Konfigurations-Laden

```bash
# Tests ausführen
python manage.py test scraper_control.test_process_manager_retry
```

## Troubleshooting

### Problem: Circuit Breaker öffnet zu häufig

**Lösung**: Erhöhe `process_circuit_breaker_failures` von 5 auf z.B. 10

### Problem: Zu viele Retries

**Lösung**: Reduziere `process_max_retry_attempts` von 3 auf z.B. 2

### Problem: QPI wird zu stark reduziert

**Lösung**: Erhöhe `process_qpi_reduction_factor` von 0.7 auf z.B. 0.85

### Problem: Circuit Breaker blockiert zu lange

**Lösung**: Reduziere `circuit_breaker_penalty` von 30 auf z.B. 15 Sekunden

### Problem: False Positives bei Fehlerrate

**Lösung**: 
1. Erhöhe `process_error_rate_threshold` von 0.5 auf z.B. 0.7
2. Oder manuell zurücksetzen: `manager.reset_error_tracking()`

## Logging-Beispiele

### Erfolgreicher Retry
```
2024-01-19 19:00:00 INFO Error tracked: crash, total: 1, circuit breaker failures: 1
2024-01-19 19:00:00 INFO Scheduling retry 1/3 after 30.0s backoff
2024-01-19 19:00:30 INFO Executing scheduled retry 1
2024-01-19 19:00:30 INFO Scraper started with PID 12345
```

### Circuit Breaker Zyklus
```
2024-01-19 19:00:00 ERROR Circuit breaker OPENED after 5 failures
2024-01-19 19:00:30 INFO Circuit breaker transitioning to HALF_OPEN after 30.5s penalty
2024-01-19 19:00:35 INFO Circuit breaker CLOSED - normal operation resumed
```

### QPI Reduktion
```
2024-01-19 19:00:00 INFO Reducing QPI from 20 to 14 due to rate limit errors
2024-01-19 19:00:00 INFO Built scraper command: python -m luca_scraper --industry recruiter --qpi 14 --once
```

## Zusammenfassung

Das erweiterte Fehlerbehandlungssystem macht den Scraper robuster und zuverlässiger:

✅ **Automatische Fehlerbehandlung**: Keine manuelle Intervention nötig
✅ **Intelligente Anpassung**: QPI-Reduktion bei Rate-Limits
✅ **Schutz vor Überlastung**: Circuit Breaker verhindert Cascade-Failures
✅ **Vollständig konfigurierbar**: Alle Parameter anpassbar
✅ **Umfangreiches Monitoring**: Detaillierte Status-Informationen
✅ **Gut getestet**: Umfangreiche Test-Suite

Das System ist produktionsreif und kann sofort eingesetzt werden.
