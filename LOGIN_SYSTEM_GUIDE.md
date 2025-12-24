# Human-in-the-Loop Login System

## Übersicht

Das Login-System ermöglicht es dem Scraper, automatisch zu erkennen, wenn ein Portal einen Login erfordert, und den Benutzer aufzufordern, sich manuell einzuloggen. Die Session-Cookies werden dann gespeichert und für zukünftige Anfragen wiederverwendet.

## Features

- ✅ **Automatische Login-Erkennung**: Erkennt Login-Anforderungen anhand von Status-Codes (403, 401, 429), Text-Patterns und URL-Patterns
- ✅ **Browser-basierter Login**: Öffnet Browser für manuellen Login (Selenium oder Standard-Browser)
- ✅ **Session-Speicherung**: Speichert Cookies in SQLite-Datenbank mit 7-Tage-Ablauf
- ✅ **Session-Wiederverwendung**: Verwendet gespeicherte Cookies automatisch
- ✅ **Portal-spezifisch**: Unterstützt verschiedene Portale (LinkedIn, XING, Indeed, Kleinanzeigen, etc.)
- ✅ **Dashboard-Integration**: Zeigt aktive/abgelaufene Sessions im Dashboard an
- ✅ **CLI-Verwaltung**: Kommandozeilen-Tools zum Verwalten von Sessions

## Unterstützte Portale

- **kleinanzeigen.de** - Kleinanzeigen Stellengesuche
- **linkedin.com** - LinkedIn Profile
- **xing.com** - XING Profile
- **indeed.com/indeed.de** - Indeed Jobs
- **facebook.com** - Facebook
- **stepstone.de** - Stepstone Jobs
- **monster.de** - Monster Jobs
- **quoka.de** - Quoka
- **markt.de** - Markt.de

## Installation

Selenium ist optional, aber empfohlen für bessere Cookie-Extraktion:

```bash
pip install selenium>=4.0.0
```

## Verwendung

### 1. Automatische Login-Erkennung während des Scrapings

Der Scraper erkennt automatisch, wenn ein Login erforderlich ist:

```bash
python scriptname.py --once --industry candidates
```

Wenn ein Login erforderlich ist, erscheint:

```
============================================================
🔐 LOGIN ERFORDERLICH
============================================================
Portal: LINKEDIN
URL: https://www.linkedin.com/login
------------------------------------------------------------
🌐 Öffne Chrome Browser...
👉 Bitte logge dich ein und drücke ENTER wenn fertig.
------------------------------------------------------------

⏳ Drücke ENTER wenn du eingeloggt bist...
```

### 2. Manuelles Einloggen vor dem Scraping

Logge dich manuell bei einem Portal ein:

```bash
# LinkedIn
python scriptname.py --login linkedin

# XING
python scriptname.py --login xing

# Kleinanzeigen
python scriptname.py --login kleinanzeigen
```

### 3. Sessions anzeigen

Zeige alle gespeicherten Sessions:

```bash
python scriptname.py --list-sessions
```

Ausgabe:
```
✅ linkedin: 2025-12-23 14:30:00
✅ xing: 2025-12-23 15:45:00
❌ facebook: 2025-12-20 10:00:00  (abgelaufen)
```

### 4. Sessions löschen

Lösche alle gespeicherten Sessions:

```bash
python scriptname.py --clear-sessions
```

### 5. Dashboard anzeigen

Das Dashboard zeigt den Status aller Login-Sessions:

```bash
python dashboard.py
```

Ausgabe:
```
🔐 LOGIN SESSIONS
-----------------------------------------------------------------
  ✅ linkedin            Login: 2025-12-23  Expires: 2025-12-30
  ✅ xing                Login: 2025-12-23  Expires: 2025-12-30
  ❌ facebook            Login: 2025-12-20  Expires: 2025-12-27
```

## Wie es funktioniert

### Login-Erkennung

Das System erkennt Login-Anforderungen durch:

1. **Status-Codes**: 401 (Unauthorized), 403 (Forbidden), 429 (Too Many Requests)
2. **Text-Patterns** (case-insensitive):
   - "bitte anmelden", "bitte einloggen"
   - "login required", "please log in"
   - "captcha", "sind sie ein roboter"
   - "access denied", "zugang verweigert"
   - "unusual traffic", "too many requests"
3. **URL-Patterns**: URLs die "login", "signin", "anmelden", "einloggen" enthalten

### Session-Speicherung

Sessions werden in zwei Orten gespeichert:

1. **SQLite-Datenbank** (`scraper.db`, Tabelle `login_sessions`):
   - Portal-Name
   - Cookies (JSON)
   - User-Agent
   - Login-Zeitstempel
   - Ablaufdatum (7 Tage)
   - Gültigkeitsflag

2. **JSON-Backup-Dateien** (`sessions/` Verzeichnis):
   - `{portal}_cookies.json` für jedes Portal
   - Enthält Cookies, User-Agent und Zeitstempel

### Browser-Integration

**Mit Selenium** (empfohlen):
- Öffnet Chrome mit speziellen Optionen
- Benutzer loggt sich manuell ein
- Cookies werden automatisch extrahiert
- Browser wird geschlossen

**Ohne Selenium** (Fallback):
- Öffnet Standard-Browser
- Benutzer loggt sich manuell ein
- Optional: Cookies können manuell eingefügt werden (JSON-Format)
- Session wird als "versucht" markiert

## Programmatische Verwendung

### In eigenem Code verwenden

```python
from login_handler import LoginHandler, get_login_handler, check_and_handle_login

# Login-Handler initialisieren
handler = get_login_handler()

# Login-Anforderung prüfen
response_text = "..."
status_code = 403
url = "https://www.linkedin.com/in/profile"

if handler.detect_login_required(response_text, status_code, url):
    portal = handler.get_portal_from_url(url)
    
    # Prüfe ob gültige Session existiert
    if handler.has_valid_session(portal):
        cookies = handler.get_session_cookies(portal)
        # Verwende Cookies für Request
    else:
        # Fordere manuellen Login an
        cookies = handler.request_manual_login(portal, url)
```

### Mit fetch_with_login_check

Der Scraper enthält eine Helper-Funktion:

```python
# In scriptname.py
response = await fetch_with_login_check(url, headers=headers)
```

Diese Funktion:
1. Lädt gespeicherte Cookies falls vorhanden
2. Führt Request aus
3. Prüft Response auf Login-Anforderungen
4. Loggt Warnung wenn Login erforderlich ist

## Sicherheit

- ✅ **Sensitive Daten geschützt**: `sessions/` Verzeichnis ist in `.gitignore`
- ✅ **Lokale Speicherung**: Cookies werden nur lokal gespeichert
- ✅ **Keine Third-Party**: Keine Daten werden an Dritte gesendet
- ✅ **Automatische Ablaufdaten**: Sessions laufen nach 7 Tagen ab
- ✅ **CodeQL geprüft**: Keine Sicherheitslücken gefunden

## Troubleshooting

### Selenium funktioniert nicht

**Problem**: "Selenium-Fehler: ..."

**Lösung**:
1. Installiere Selenium: `pip install selenium>=4.0.0`
2. Installiere ChromeDriver (wird automatisch von Selenium verwaltet)
3. Falls weiterhin Probleme: System verwendet automatisch Fallback auf Standard-Browser

### Cookies werden nicht gespeichert

**Problem**: "❌ Keine Cookies gefunden"

**Lösung**:
1. Stelle sicher, dass du dich erfolgreich eingeloggt hast
2. Warte bis die Seite vollständig geladen ist
3. Drücke erst dann ENTER
4. Bei Fallback-Browser: Kopiere Cookies manuell aus DevTools

### Session abgelaufen

**Problem**: "Login erforderlich" trotz gespeicherter Session

**Lösung**:
1. Sessions laufen nach 7 Tagen ab
2. Portal könnte Session serverseitig ungültig gemacht haben
3. Führe neuen Login durch: `python scriptname.py --login {portal}`

### Portal wird nicht erkannt

**Problem**: "Portal: UNKNOWN"

**Lösung**:
1. Portal ist noch nicht in der Liste
2. Füge Portal zu `PORTAL_LOGIN_URLS` in `login_handler.py` hinzu
3. Füge Domain zu `portal_domains` in `get_portal_from_url()` hinzu

## Erweiterung

### Neues Portal hinzufügen

In `login_handler.py`:

```python
# Portal-spezifische Login-URLs
PORTAL_LOGIN_URLS = {
    # ... existing portals ...
    "neuportal": "https://www.neuportal.de/login",
}

# In get_portal_from_url()
portal_domains = {
    # ... existing domains ...
    "neuportal.de": "neuportal",
}
```

### Neue Login-Patterns hinzufügen

In `login_handler.py`:

```python
LOGIN_INDICATORS = [
    # ... existing patterns ...
    "neues pattern hier",
    "another pattern",
]
```

## API-Referenz

### LoginHandler

**Konstruktor**:
```python
handler = LoginHandler(db_path="scraper.db")
```

**Methoden**:
- `detect_login_required(response_text, status_code, url)` - Erkennt Login-Anforderung
- `get_portal_from_url(url)` - Ermittelt Portal-Name aus URL
- `has_valid_session(portal)` - Prüft ob gültige Session existiert
- `get_session_cookies(portal)` - Lädt gespeicherte Cookies
- `save_session(portal, cookies, user_agent)` - Speichert Session
- `invalidate_session(portal)` - Markiert Session als ungültig
- `request_manual_login(portal, url)` - Fordert manuellen Login an
- `get_all_sessions()` - Gibt alle Sessions zurück

### Globale Funktionen

- `get_login_handler()` - Gibt Singleton-Instanz zurück
- `check_and_handle_login(response_text, status_code, url)` - Prüft und handelt Login

## Beispiele

### Beispiel 1: Alle LinkedIn-Profile einer Liste scrapen

```bash
# 1. Login bei LinkedIn
python scriptname.py --login linkedin

# 2. Scraper starten
python scriptname.py --once --industry candidates
```

### Beispiel 2: Sessions vor großem Scraping-Lauf vorbereiten

```bash
# Login bei allen relevanten Portalen
python scriptname.py --login linkedin
python scriptname.py --login xing
python scriptname.py --login kleinanzeigen

# Sessions anzeigen
python scriptname.py --list-sessions

# Scraping starten
python scriptname.py --once --industry all
```

### Beispiel 3: Sessions nach Scraping-Problemen zurücksetzen

```bash
# Alte Sessions löschen
python scriptname.py --clear-sessions

# Neu einloggen
python scriptname.py --login linkedin

# Erneut versuchen
python scriptname.py --once --industry candidates
```

## Lizenz

Teil des luca-nrw-scraper Projekts.
