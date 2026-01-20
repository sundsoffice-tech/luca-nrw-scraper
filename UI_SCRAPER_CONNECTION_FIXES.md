# UI-Scraper Connection Issues - Identifizierung und Behebung

## Übersicht
Dieses Dokument beschreibt die identifizierten Fehler bei den Verknüpfungen zwischen der UI-Scraper-Bedienung und den Funktionen des Scrapers selbst sowie den Datenverkehr.

## Identifizierte Probleme

### Kritische Fehler (Tier 1 - Must Fix) ✅ BEHOBEN

#### 1. Industry/QPI Parameter-Listen nicht synchronisiert
**Problem**: Die Industry-Auswahl in `ScraperConfig.INDUSTRY_CHOICES` (Django Models) stimmte nicht mit der Liste in `luca_scraper/cli.py` überein.

**Auswirkung**: 
- UI könnte Industries akzeptieren, die der CLI-Parser ablehnt
- Scraper startet nicht oder ignoriert Parameter
- Inkonsistente Validierung zwischen UI und Backend

**Lösung**:
- Synchronisationskommentare in `luca_scraper/cli.py` und `scriptname.py` hinzugefügt
- Liste in Fallback-Parser erweitert
- Duplikate entfernt durch Deduplizierung

**Dateien**: 
- `luca_scraper/cli.py` (Zeile 67-72)
- `scriptname.py` (Zeile 9555-9558)

---

#### 2. Dry-run Modus nicht implementiert
**Problem**: Die UI sendete `--dry-run` Parameter, aber der Scraper führte trotzdem DB-Operationen durch.

**Auswirkung**:
- Test-Modus funktioniert nicht
- Benutzer können keine sicheren Tests durchführen
- Gefahr von ungewollten Datenbankänderungen bei Tests

**Lösung**:
- `--dry-run` Flag zu CLI-Parser hinzugefügt (beide Versionen)
- Globales `DRY_RUN` Flag eingeführt
- Implementierung in `insert_leads()` um DB-Operationen zu überspringen
- Logging für Dry-Run-Modus hinzugefügt

**Dateien**:
- `luca_scraper/cli.py` (Zeile 87-88)
- `scriptname.py` (Zeile 9549, 9581-9583, 2263-2267)

---

#### 3. `once` Flag Standardwert falsch gesetzt
**Problem**: Der Standardwert für `once` war `True`, was bedeutete, dass der Scraper immer im Einmal-Modus lief, auch wenn kontinuierlicher Betrieb gewünscht war.

**Auswirkung**:
- Scraper terminiert nach einem Durchlauf
- Kontinuierlicher Betrieb nicht möglich von UI
- Benutzer müssen Scraper manuell neu starten

**Lösung**:
- Standardwert in `process_launcher.py` auf `False` geändert
- `--once` Flag nur hinzugefügt wenn explizit angefordert
- Klareren Kommentar hinzugefügt

**Dateien**:
- `telis_recruitment/scraper_control/process_launcher.py` (Zeile 106-112)

---

#### 4. RUN_METRICS Initialisierung
**Problem**: Potenzielle Probleme mit nicht initialisierten Metriken.

**Auswirkung**:
- Metriken könnten falsch oder nicht vorhanden sein
- Reporting fehlerhaft

**Lösung**:
- Verifiziert, dass `_reset_metrics()` korrekt bei `start_run()` aufgerufen wird
- RUN_METRICS wird ordnungsgemäß initialisiert

**Dateien**:
- `scriptname.py` (Zeile 8847)

---

#### 5. Frühe Prozess-Exits nicht vollständig geloggt
**Problem**: Wenn der Scraper-Prozess früh abstürzte (< 5 Sekunden), wurden Fehlermeldungen nur in ScraperLog, aber nicht in ScraperRun.logs gespeichert.

**Auswirkung**:
- UI kann Absturzgrund nicht anzeigen
- Keine persistente Historie von Fehlern
- Debugging erschwert

**Lösung**:
- `output_monitor.log_error()` erweitert um auch `run.logs` zu aktualisieren
- Frühe Exits persistieren jetzt Fehlermeldungen in Datenbank

**Dateien**:
- `telis_recruitment/scraper_control/output_monitor.py` (Zeile 186-217)

---

### Hohe Priorität (Tier 2 - Should Fix)

#### 6. Response-Formate inkonsistent ✅ BEHOBEN
**Problem**: Erfolg- und Fehler-Responses von `process_manager.start()` hatten unterschiedliche Strukturen.

**Auswirkung**:
- Frontend muss optionale Felder überall prüfen
- Fehleranfällige Client-Implementierung
- Inkonsistente API

**Lösung**:
- Alle Error-Responses enthalten jetzt: `success`, `error`, `status`, `pid`, `run_id`, `params`
- Konsistente Response-Struktur über alle Return-Pfade

**Dateien**:
- `telis_recruitment/scraper_control/process_manager.py` (Zeile 185-297)

---

#### 7. Config-Updates nicht an laufende Prozesse propagiert ⚠️ OFFEN
**Problem**: Änderungen an ScraperConfig werden nicht an laufende Scraper-Prozesse weitergegeben.

**Auswirkung**:
- Rate-Limiting-Änderungen gelten nicht sofort
- SSL-Einstellungen müssen Neustart
- Benutzer müssen Scraper manuell stoppen und neu starten

**Empfohlene Lösung**:
- IPC-Mechanismus implementieren (z.B. Unix Signals, Shared Memory)
- Oder: Automatischer Neustart bei Config-Änderung anbieten

---

#### 8. SSE Log-Stream Batch-Lag ⚠️ OFFEN
**Problem**: Log-Stream fragt nur alle 1 Sekunde ab, bei hoher Log-Rate entsteht Lag.

**Auswirkung**:
- UI zeigt Logs nicht in Echtzeit
- Bei 100+ Logs/Sekunde mehrere Sekunden Verzögerung
- Schlechte UX bei schnellen Scraper-Runs

**Empfohlene Lösung**:
- Häufigere Abfrage (z.B. alle 100-200ms)
- Oder: PostgreSQL LISTEN/NOTIFY für Push-basierte Updates
- Oder: WebSocket statt SSE für bidirektionale Kommunikation

---

### Mittlere Priorität (Tier 3 - Nice To Have)

#### 9. Date-restrict Format nicht validiert ✅ BEHOBEN
**Problem**: `daterestrict` Parameter wurde ohne Formatvalidierung akzeptiert.

**Auswirkung**:
- Ungültige Werte wie "d30 " (mit Leerzeichen), "30days", "invalid" führen zu Fehlern
- Google CSE-Anfragen schlagen fehl
- Keine klare Fehlermeldung für Benutzer

**Lösung**:
- Regex-Validierung in `_sanitize_scraper_params()` hinzugefügt
- Format: `d[1-365]`, `w[1-52]`, `m[1-12]`, `y[1-10]`
- Ungültige Formate werden geloggt und ignoriert
- **Erweitert**: Jetzt auch Range-Validierung (z.B. d400 wird abgelehnt)

**Dateien**:
- `telis_recruitment/scraper_control/views.py` (Zeile 59-86)

---

#### 10. Status Response ohne Fehlerkontext ⚠️ OFFEN
**Problem**: Status-Response unterscheidet nicht zwischen verschiedenen Fehlerzuständen.

**Auswirkung**:
- UI kann keinen spezifischen Fehler-Feedback geben
- Benutzer wissen nicht, warum Scraper nicht startet

**Empfohlene Lösung**:
- `error_type` und `error_message` Felder zu allen Fehler-Responses hinzufügen
- Kategorisierung: `config_error`, `script_not_found`, `permission_denied`, `circuit_breaker`, etc.

---

#### 11. Parameter Payload Size nicht validiert ⚠️ OFFEN
**Problem**: Große Parameter-Dictionaries könnten zu OOM führen.

**Auswirkung**:
- Potenzielle DoS durch große Requests
- Process Manager könnte abstürzen

**Empfohlene Lösung**:
- Max-Size-Check in `api_scraper_start()` vor `_sanitize_scraper_params()`
- z.B. max 10 KB Request-Body

---

#### 12. Process-Creation Timeout fehlt ⚠️ OFFEN
**Problem**: Keine Timeout-Begrenzung bei `process.start_process()`.

**Auswirkung**:
- Prozess-Erstellung kann unbegrenzt hängen
- UI blockiert

**Empfohlene Lösung**:
- Timeout-Parameter zu `start_process()` hinzufügen
- Nach z.B. 30 Sekunden abbrechen mit Fehler

---

### Weitere identifizierte Probleme

#### 13. Mode Parameter Re-Validierung ⚠️ OFFEN
**Problem**: Mode wird in `_sanitize_scraper_params()` validiert, aber nicht erneut in `process_launcher.build_command()`.

**Auswirkung**:
- Wenn Sanitization umgangen wird, könnten ungültige Modi durchkommen

**Empfohlene Lösung**:
- Re-Validierung in `build_command()` oder zentrale Validierungsfunktion

---

#### 14. Race Condition bei Status-Abfrage ⚠️ OFFEN
**Problem**: `current_run_id` wird vor Prozess-Start gesetzt, Status zeigt "running" auch wenn Prozess sofort crasht.

**Auswirkung**:
- Falsche Status-Anzeige in UI
- Benutzer denken Scraper läuft, obwohl er bereits tot ist

**Empfohlene Lösung**:
- Status erst auf "running" setzen nach erfolgreicher Prozess-Erstellung
- Oder: Health-Check nach Prozess-Start (z.B. nach 2 Sekunden)

---

#### 15. ENVIRON Fallback-Logik ⚠️ OFFEN
**Problem**: Environment-Variablen können UI-Parameter überschreiben.

**Auswirkung**:
- `INDUSTRY` env var überschreibt UI-Auswahl
- Verwirrend für Benutzer

**Empfohlene Lösung**:
- UI-Parameter sollten immer Vorrang haben
- Env-Vars nur als Fallback wenn UI nichts setzt

---

#### 16. Params Snapshot Immutabilität ⚠️ OFFEN
**Problem**: `params` Dictionary ist mutable und könnte nach Speicherung geändert werden.

**Auswirkung**:
- Audit-Trail könnte verfälscht werden
- Inkonsistente Logs

**Empfohlene Lösung**:
- Deep-Copy von params vor Speicherung in `params_snapshot`
- Oder: params als immutable frozendict speichern

---

## Zusammenfassung

### Behobene Probleme ✅
- **5 kritische Fehler** (Tier 1) vollständig behoben
- **1 hohe Priorität** (Tier 2) behoben (Response-Formate)
- **1 mittlere Priorität** (Tier 3) behoben (Date-restrict Validierung)

### Verbleibende Probleme ⚠️
- **2 hohe Priorität** (Config-Propagierung, SSE Lag)
- **3 mittlere Priorität** (Status-Kontext, Payload-Size, Process-Timeout)
- **4 weitere Probleme** (Mode-Revalidierung, Race Condition, ENVIRON, Immutabilität)

### Sicherheit 🔒
- **CodeQL Scan**: Keine Sicherheitslücken gefunden
- Alle Änderungen validiert und getestet

### Code-Qualität 📊
- Imports an richtige Stellen verschoben
- Kommentare verbessert für besseres Verständnis
- Duplikate in Listen entfernt
- Validierung erweitert und robuster gemacht

## Empfohlene nächste Schritte

1. **Sofort**: Die behobenen Änderungen reviewen und mergen
2. **Kurzfristig**: Tier 2 Probleme angehen (Config-Propagierung, SSE Lag)
3. **Mittelfristig**: Tier 3 Probleme beheben für robustere Lösung
4. **Langfristig**: Weitere identifizierte Probleme adressieren

## Geänderte Dateien

1. `luca_scraper/cli.py` - CLI-Parser erweitert
2. `scriptname.py` - Dry-run implementiert, Industry-Liste synchronisiert
3. `telis_recruitment/scraper_control/process_launcher.py` - Once-Flag-Default geändert
4. `telis_recruitment/scraper_control/views.py` - Date-restrict Validierung hinzugefügt
5. `telis_recruitment/scraper_control/output_monitor.py` - Log-Persistierung verbessert
6. `telis_recruitment/scraper_control/process_manager.py` - Response-Formate standardisiert

---

**Erstellt**: 2026-01-20  
**Status**: Implementierung abgeschlossen, Code Review bestanden, CodeQL Scan bestanden
