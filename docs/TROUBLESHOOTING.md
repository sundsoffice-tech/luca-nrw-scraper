# 🆘 Troubleshooting Guide

Dieser Guide hilft dir, häufige Probleme **nach Symptomen** zu lösen - nicht nach Technik. Finde dein Problem und folge der Lösung.

---

## 🔍 Schnell-Navigation

| Symptom | Kategorie |
|---------|-----------|
| [Ich bekomme 0 Leads](#ich-bekomme-0-leads) | 🎯 Leads & Daten |
| [Zu wenige Leads (< 10)](#zu-wenige-leads-10) | 🎯 Leads & Daten |
| [Login/Session klappt nicht](#loginsession-klappt-nicht) | 🔐 Authentifizierung |
| [Zu viele 403/Blockaden](#zu-viele-403blockaden) | 🚫 Rate Limits |
| [CRM zeigt nichts an](#crm-zeigt-nichts-an) | 💻 CRM/UI |
| [Scraper läuft, aber speichert nicht](#scraper-läuft-aber-speichert-nicht) | 💾 Datenbank |
| [Port already in use](#port-already-in-use) | 🔌 Server |
| [Static Files not loading](#static-files-not-loading) | 🎨 Frontend |
| [Docker Container fails](#docker-container-fails) | 🐳 Docker |
| [API-Kosten explodieren](#api-kosten-explodieren) | 💰 Kosten |

---

## 🎯 Leads & Daten

### Ich bekomme 0 Leads

**Symptome:**
- Scraper läuft durch ohne Fehler
- Dashboard zeigt 0 Leads
- Keine Einträge in der Datenbank

#### Ursache 1: Keine Suchergebnisse gefunden

**Check:**
```bash
# Schaue in die Logs
docker-compose logs -f web  # Docker
# oder schaue im Terminal wo der Scraper läuft

# Suche nach:
# "No results found" oder "0 URLs fetched"
```

**Lösung:**
```bash
# 1. Date Restrict erweitern (mehr Zeitraum)
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d90

# 2. Andere Industry testen
python scriptname.py --once --industry talent_hunt --qpi 8

# 3. QPI erhöhen (mehr Queries)
python scriptname.py --once --industry recruiter --qpi 12
```

#### Ursache 2: Alle Leads werden gefiltert

**Check:**
```bash
# Schaue nach Rejection Stats
python scriptname.py --show-stats

# Oder in den Logs nach:
# "Rejected: invalid_name" oder "Rejected: no_contact"
```

**Lösung:**
```bash
# Option 1: Validierung temporär lockern (für Test)
# Edit scriptname.py oder in der .env:
LEAD_VALIDATION_STRICT=False

# Option 2: Minimum Score senken
python scriptname.py --once --industry recruiter --qpi 12 --min-score 50
```

#### Ursache 3: Datenbank-Pfad falsch

**Check:**
```bash
# Prüfe ob Datenbank existiert
ls -la telis_recruitment/db.sqlite3

# Prüfe Permissions
ls -la telis_recruitment/db.sqlite3
# Sollte schreibbar sein
```

**Lösung:**
```bash
# Datenbank neu initialisieren
cd telis_recruitment
python manage.py migrate

# Oder für Docker:
docker-compose exec web python manage.py migrate
```

#### Ursache 4: Blocked by Websites

**Check:**
```bash
# In Logs nach 403, 429, 503 Errors suchen
# "HTTP 403" oder "blocked" oder "rate limit"
```

**Lösung:**
- Siehe [Zu viele 403/Blockaden](#zu-viele-403blockaden)

---

### Zu wenige Leads (< 10)

**Symptome:**
- Scraper läuft erfolgreich
- Nur 1-5 Leads werden gespeichert
- Erwartet wurden 10-30+ Leads

#### Lösung 1: QPI erhöhen

```bash
# Von Safe Mode (6) zu Balanced Mode (12)
python scriptname.py --once --industry recruiter --qpi 12 --daterestrict d60
```

#### Lösung 2: Date Restrict erweitern

```bash
# Mehr Zeitraum = mehr potenzielle Ergebnisse
python scriptname.py --once --industry recruiter --qpi 12 --daterestrict d90
```

#### Lösung 3: Mehrere Industries kombinieren

```bash
# Parallel mehrere Industries scrapen
python scriptname.py --once --industry recruiter --qpi 10 &
python scriptname.py --once --industry talent_hunt --qpi 8 &
wait
```

#### Lösung 4: Google Custom Search API nutzen

**Vorteil:** Mehr Queries möglich (100 Queries/Tag gratis)

```bash
# 1. API Key holen
# Gehe zu: https://developers.google.com/custom-search/v1/introduction
# Erstelle API Key und Custom Search Engine ID

# 2. In .env eintragen
GOOGLE_API_KEY=your-key-here
GOOGLE_CSE_ID=your-cse-id-here

# 3. Scraper nutzt automatisch Google CSE wenn verfügbar
python scriptname.py --once --industry recruiter --qpi 20
```

---

## 🔐 Authentifizierung

### Login/Session klappt nicht

**Symptome:**
- "Invalid credentials" beim Login
- Nach Login sofort wieder auf Login-Seite
- Session expired Meldungen

#### Ursache 1: Falscher Admin User

**Lösung:**
```bash
# Docker
docker-compose exec web python manage.py createsuperuser

# Manuell
cd telis_recruitment
python manage.py createsuperuser

# Folge den Prompts und erstelle neuen User
```

#### Ursache 2: SECRET_KEY fehlt oder falsch

**Check:**
```bash
# Prüfe .env Datei
cat .env | grep SECRET_KEY

# Sollte NICHT leer sein und nicht "change-me" enthalten
```

**Lösung:**
```bash
# Neuen SECRET_KEY generieren
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Output kopieren und in .env eintragen:
SECRET_KEY=dein-neuer-generierter-key-hier

# Server neu starten
docker-compose restart web  # Docker
# oder Ctrl+C und python manage.py runserver für manuell
```

#### Ursache 3: CSRF Token Probleme

**Check:**
```bash
# In Browser Console (F12) nach CSRF errors suchen
```

**Lösung:**
```bash
# In .env: CSRF_TRUSTED_ORIGINS setzen
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Für Produktion mit Domain:
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Server neu starten
```

#### Ursache 4: Browser Cache

**Lösung:**
```
1. Öffne Browser Dev Tools (F12)
2. Rechtsklick auf Reload Button
3. Wähle "Empty Cache and Hard Reload"
4. Oder: Private/Incognito Fenster verwenden
```

---

## 🚫 Rate Limits & Blockaden

### Zu viele 403/Blockaden

**Symptome:**
- Viele "HTTP 403 Forbidden" in Logs
- "Access Denied" oder "blocked" Meldungen
- Scraper stoppt vorzeitig
- < 20% Success Rate

#### Ursache 1: Zu viele Requests zu schnell

**Lösung 1: QPI reduzieren**
```bash
# Von Aggressive (20) zu Balanced (12)
python scriptname.py --once --industry recruiter --qpi 12 --daterestrict d60
```

**Lösung 2: Delay erhöhen**

Edit `scriptname.py` (temporär für Test):
```python
# Suche nach: DELAY_BETWEEN_REQUESTS
# Ändere von 1-2 zu 3-5 Sekunden
DELAY_BETWEEN_REQUESTS = 3  # oder 5
```

**Lösung 3: Nur zu Off-Peak Zeiten scrapen**
```bash
# Nachts oder früh morgens (weniger Competition)
# z.B. Cron Job um 4 Uhr morgens
0 4 * * * cd /path/to/luca && python scriptname.py --once --qpi 12
```

#### Ursache 2: IP-Adresse geblockt

**Lösung 1: Proxy verwenden**

```bash
# In .env:
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=https://your-proxy:port

# Oder Command-Line:
export HTTP_PROXY=http://your-proxy:port
python scriptname.py --once --industry recruiter --qpi 12
```

**Lösung 2: VPN nutzen**
- Aktiviere VPN
- Wechsle Server-Standort
- Führe Scraper erneut aus

**Lösung 3: IP rotieren lassen**
- Warte 24 Stunden
- Oder: Nutze dynamische IP (Router neu starten)

#### Ursache 3: User-Agent geblockt

Der Scraper rotiert User-Agents automatisch, aber falls Problem besteht:

```python
# Check in scriptname.py:
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    # Sind mehrere definiert?
]
```

---

## 💻 CRM & UI

### CRM zeigt nichts an

**Symptome:**
- Dashboard lädt, aber zeigt 0 Leads
- Leads sollten vorhanden sein
- Oder: Dashboard lädt gar nicht

#### Ursache 1: Keine Leads in Datenbank

**Check:**
```bash
# Docker
docker-compose exec web python manage.py shell
>>> from crm.models import Lead
>>> Lead.objects.count()
# Sollte > 0 sein wenn Leads vorhanden

# Manuell
cd telis_recruitment
python manage.py shell
>>> from crm.models import Lead
>>> Lead.objects.count()
```

**Lösung:**
- Wenn 0: Siehe [Ich bekomme 0 Leads](#ich-bekomme-0-leads)
- Wenn > 0: Ursache 2 oder 3

#### Ursache 2: Falsche Datenbank wird gelesen

**Check:**
```bash
# Prüfe DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Sollte sein:
DATABASE_URL=sqlite:///db.sqlite3
```

**Lösung:**
```bash
# Falls falsch, korrigiere in .env:
DATABASE_URL=sqlite:///db.sqlite3

# Server neu starten
docker-compose restart web  # Docker
# oder Ctrl+C und python manage.py runserver
```

#### Ursache 3: Static Files nicht geladen

**Symptome:**
- Dashboard lädt, aber ohne Styling
- Nur Text sichtbar, kein Design

**Lösung:**
```bash
# Docker
docker-compose exec web python manage.py collectstatic --noinput

# Manuell
cd telis_recruitment
python manage.py collectstatic --noinput

# Server neu starten
```

#### Ursache 4: JavaScript Fehler

**Check:**
```
1. Öffne Browser Dev Tools (F12)
2. Gehe zum "Console" Tab
3. Suche nach roten Fehlermeldungen
```

**Häufige Fehler & Lösungen:**

**Fehler:** "Failed to load resource: 404"
```bash
# Static files fehlen
python manage.py collectstatic --noinput
```

**Fehler:** "CSRF token missing"
```bash
# Siehe: Login/Session klappt nicht
```

---

## 💾 Datenbank

### Scraper läuft, aber speichert nicht

**Symptome:**
- Scraper zeigt "Processing..." und "Found leads"
- Aber: Datenbank bleibt leer
- Keine Fehler sichtbar

#### Ursache 1: Datenbank-Permissions

**Check:**
```bash
# Prüfe ob db.sqlite3 existiert und schreibbar ist
ls -la telis_recruitment/db.sqlite3

# Sollte nicht read-only sein
# Sollte dem User gehören, der den Server startet
```

**Lösung:**
```bash
# Permissions korrigieren
chmod 644 telis_recruitment/db.sqlite3
chown $USER:$USER telis_recruitment/db.sqlite3

# Für Docker: Container user muss schreiben können
docker-compose exec web chown -R app:app /app/telis_recruitment/db.sqlite3
```

#### Ursache 2: Falscher Datenbank-Pfad

**Check:**
```bash
# Im Scraper: Prüfe Database Path
grep "DB_PATH" scriptname.py

# Sollte auf telis_recruitment/db.sqlite3 zeigen
```

**Lösung:**

Edit `scriptname.py` (falls nötig):
```python
# Suche nach DB_PATH Definition
DB_PATH = "telis_recruitment/db.sqlite3"  # Korrekter Pfad
```

#### Ursache 3: Transactions nicht committed

**Check:**
```bash
# In Logs nach "rollback" oder "transaction error" suchen
```

**Lösung:**
```bash
# Datenbank neu initialisieren (ACHTUNG: Löscht Daten!)
rm telis_recruitment/db.sqlite3
cd telis_recruitment
python manage.py migrate
```

#### Ursache 4: Duplikate werden ignoriert

**Das ist eigentlich gewünschtes Verhalten!**

Der Scraper ignoriert Duplikate basierend auf:
- E-Mail
- Telefonnummer
- URL

**Check ob es wirklich neue Leads sind:**
```bash
# Im CRM: Suche nach E-Mail oder Telefon
# Oder in DB:
cd telis_recruitment
python manage.py shell
>>> from crm.models import Lead
>>> Lead.objects.filter(email="test@example.com").exists()
```

---

## 🔌 Server & Installation

### Port already in use

**Symptome:**
- `Error: That port is already in use.`
- Server startet nicht

**Lösung 1: Port 8000 freigeben**

```bash
# Linux/Mac: Process finden und killen
lsof -ti:8000 | xargs kill -9

# Windows: Process finden
netstat -ano | findstr :8000
# Dann killen mit PID:
taskkill /PID <PID> /F
```

**Lösung 2: Anderen Port verwenden**

```bash
# Docker: Edit docker-compose.yml
ports:
  - "8080:8000"  # Statt 8000:8000

# Manuell
python manage.py runserver 0.0.0.0:8080
```

### Static Files not loading

**Symptome:**
- CSS/JS Files nicht gefunden
- Seite sieht "kaputt" aus
- 404 Fehler für /static/...

**Lösung:**
```bash
# Docker
docker-compose exec web python manage.py collectstatic --noinput --clear

# Manuell
cd telis_recruitment
python manage.py collectstatic --noinput --clear

# Prüfe STATIC_ROOT in .env:
STATIC_ROOT=staticfiles

# Server neu starten
```

---

## 🐳 Docker

### Docker Container fails

**Symptome:**
- `docker-compose up` startet, aber Container stoppt sofort
- Exit code > 0

**Check Logs:**
```bash
docker-compose logs web
# Oder für alle Services:
docker-compose logs
```

**Häufige Ursachen & Lösungen:**

#### Ursache 1: .env fehlt oder SECRET_KEY fehlt

```bash
# Check ob .env existiert
ls -la .env

# Falls nicht:
cp .env.example .env
nano .env
# SECRET_KEY setzen (siehe oben)

# Container neu starten
docker-compose up -d
```

#### Ursache 2: Dependencies nicht installiert

```bash
# Rebuild mit --no-cache
docker-compose up -d --build --no-cache
```

#### Ursache 3: Port Conflict

```bash
# Prüfe ob Port 8000 belegt ist
lsof -ti:8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Falls ja: Siehe "Port already in use"
```

#### Ursache 4: Volume Permissions

```bash
# Remove volumes und neu starten
docker-compose down -v
docker-compose up -d

# Oder: Permissions im Container fixen
docker-compose exec web chown -R app:app /app
```

---

## 💰 Kosten

### API-Kosten explodieren

**Symptome:**
- OpenAI/Perplexity Kosten unerwartet hoch
- Mehr als €1 pro Tag
- Viele API Calls in Logs

#### Lösung 1: AI-Enrichment temporär deaktivieren

```bash
# In .env: API Keys leer lassen
OPENAI_API_KEY=
PERPLEXITY_API_KEY=

# Scraper funktioniert weiterhin (ohne AI-Features)
# Server neu starten
```

#### Lösung 2: QPI reduzieren

```bash
# Weniger Queries = weniger Leads = weniger API Calls
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30
```

#### Lösung 3: Weniger häufige Runs

```bash
# Statt täglich: nur 2-3x pro Woche
# Oder: nur bei Bedarf manuell triggern
```

#### Lösung 4: Budget Limits setzen

```
1. Gehe zu OpenAI Dashboard: https://platform.openai.com/account/limits
2. Setze "Hard limit" z.B. auf $10/month
3. Setze "Soft limit" z.B. auf $5/month (Email-Warnung)
```

#### Lösung 5: Günstigeres Modell verwenden

Falls du AI-Config anpassen kannst:
```python
# Statt GPT-4:
model = "gpt-3.5-turbo"  # Deutlich günstiger

# Oder:
model = "gpt-4o-mini"  # Neues günstiges Modell
```

---

## 🔧 Erweiterte Diagnose

### Debug-Modus aktivieren

Für detaillierte Logs:

```bash
# In .env:
DEBUG=True
LOG_LEVEL=DEBUG

# Server neu starten
# ACHTUNG: Nur für Development! In Production: DEBUG=False
```

### Datenbank-Inspektion

```bash
# Shell öffnen
cd telis_recruitment
python manage.py shell

# Leads anzeigen
>>> from crm.models import Lead
>>> leads = Lead.objects.all()
>>> for lead in leads[:5]:
...     print(f"{lead.name} - {lead.email} - Score: {lead.score}")

# Scraper Stats
>>> Lead.objects.count()
>>> Lead.objects.filter(score__gte=80).count()
```

### Scraper Test-Run

Minimaler Test ohne CRM:

```bash
# Standalone Test
python -c "
import sqlite3
con = sqlite3.connect('telis_recruitment/db.sqlite3')
cur = con.cursor()
cur.execute('SELECT COUNT(*) FROM crm_lead')
print(f'Total Leads: {cur.fetchone()[0]}')
con.close()
"
```

---

## 📚 Weiterführende Hilfe

Wenn dein Problem hier nicht gelöst wurde:

1. **GitHub Issues durchsuchen:**
   - https://github.com/sundsoffice-tech/luca-nrw-scraper/issues
   - Vielleicht hatte jemand das gleiche Problem

2. **Neues Issue erstellen:**
   - Beschreibe das Problem
   - Inkludiere: Logs, OS, Installation-Methode
   - Inkludiere: Was du bereits versucht hast

3. **Dokumentation lesen:**
   - [Installation Guide](INSTALLATION.md)
   - [Deployment Guide](DEPLOYMENT.md)
   - [Configuration Profiles](CONFIGURATION_PROFILES.md)

4. **Community fragen:**
   - GitHub Discussions
   - Stack Overflow (Tag: luca-nrw-scraper)

---

## 🎯 Checkliste: Gesundes System

Nutze diese Checkliste um sicherzustellen, dass alles funktioniert:

```
✅ Server startet ohne Fehler
✅ CRM Dashboard lädt korrekt
✅ Login funktioniert
✅ Scraper läuft und findet Leads (> 10)
✅ Leads werden in DB gespeichert
✅ CRM zeigt Leads an
✅ Export funktioniert (CSV/Excel)
✅ < 10% Error Rate beim Scrapen
✅ API-Kosten im Budget
✅ Logs zeigen keine kritischen Fehler
```

Wenn alle Punkte ✅ sind: System ist healthy! 🎉

---

**Noch Fragen?** [GitHub Issues](https://github.com/sundsoffice-tech/luca-nrw-scraper/issues) | [README.md](../README.md)
