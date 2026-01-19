# 🚀 QUICKSTART - In 20 Minuten zu deinen ersten Leads

**Ziel:** Du installierst LUCA, startest das System, führst einen Testlauf durch und siehst deine ersten 10 Leads im CRM.

**Zeit:** 20-30 Minuten

---

## Schritt 1: Installation (5 Minuten)

### Option A: Docker (Empfohlen) 🐳

```bash
# Repository klonen
git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
cd luca-nrw-scraper

# Umgebung konfigurieren
cp .env.example .env

# Docker starten
docker-compose up -d

# Admin-User erstellen
docker-compose exec web python manage.py createsuperuser
```

### Option B: Manuell (Linux/Mac)

```bash
# Repository klonen
git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
cd luca-nrw-scraper

# Installation durchführen
./install.sh

# Virtual Environment aktivieren
source venv/bin/activate

# Server starten
cd telis_recruitment
python manage.py runserver
```

### Option C: Manuell (Windows)

```cmd
# Repository klonen
git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
cd luca-nrw-scraper

# Installation durchführen
install.bat

# Virtual Environment aktivieren
venv\Scripts\activate.bat

# Server starten
cd telis_recruitment
python manage.py runserver
```

✅ **Checkpoint:** Du solltest jetzt auf http://localhost:8000/crm/ zugreifen können.

---

## Schritt 2: Erststart & Login (2 Minuten)

1. **Öffne deinen Browser:** http://localhost:8000/crm/
2. **Login:** Verwende die Admin-Credentials, die du gerade erstellt hast
3. **Dashboard:** Du siehst das Dashboard mit 0 Leads (noch leer, das ändern wir gleich!)

✅ **Checkpoint:** Dashboard lädt ohne Fehler, KPIs zeigen alle 0.

---

## Schritt 3: API-Keys eintragen (5 Minuten)

### Minimalkonfiguration (nur für Test)

Für einen **ersten Testlauf OHNE Kosten** brauchst du **keine** API-Keys! Der Scraper funktioniert mit kostenlosen Quellen.

### Optional: OpenAI für bessere Ergebnisse

Falls du bessere Lead-Qualität möchtest (empfohlen für Produktiveinsatz):

1. **OpenAI API Key holen:**
   - Gehe zu https://platform.openai.com/api-keys
   - Erstelle einen neuen Key
   - Kopiere den Key

2. **Key in .env eintragen:**

   Öffne die `.env` Datei im Hauptverzeichnis:
   
   ```bash
   # Docker
   nano .env
   
   # Manuell
   cd /pfad/zu/luca-nrw-scraper
   nano .env
   ```

   Füge hinzu:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Server neu starten:**
   ```bash
   # Docker
   docker-compose restart web
   
   # Manuell
   # Drücke Ctrl+C im Terminal und starte neu:
   python manage.py runserver
   ```

✅ **Checkpoint:** Du kannst auch ohne API-Keys weitermachen!

---

## Schritt 4: Testlauf durchführen (5 Minuten)

Jetzt starten wir einen **minimalen Testlauf** mit dem "Safe Mode" Profil.

### Im CRM starten (Empfohlen)

1. **Gehe zu:** http://localhost:8000/crm/scraper/
2. **Klicke auf:** "Scraper starten"
3. **Einstellungen:**
   - **Modus:** Once (einmalig)
   - **Industry:** recruiter
   - **Queries per Industry:** 6 (Safe Mode)
   - **Date Restrict:** d30 (letzte 30 Tage)

4. **Klicke:** "Start Scraper"
5. **Beobachte:** Live-Logs erscheinen automatisch

### Alternativ: Command-Line

```bash
# Aktiviere Virtual Environment
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate.bat  # Windows

# Führe Testlauf aus
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30
```

**Was passiert jetzt?**
- Der Scraper durchsucht Google nach NRW-Vertriebskontakten
- Er extrahiert E-Mails, Telefonnummern, Namen
- Er bewertet und speichert die Leads in der Datenbank
- **Dauer:** 3-5 Minuten für 6 Queries

✅ **Checkpoint:** Scraper läuft, Logs zeigen "Processing...", keine Fehler.

---

## Schritt 5: Leads im CRM ansehen (2 Minuten)

1. **Gehe zurück zum Dashboard:** http://localhost:8000/crm/
2. **Refresh die Seite** (F5)
3. **Sieh dir die KPIs an:**
   - Gesamtleads: ~10-30 (abhängig von aktuellen Suchergebnissen)
   - Neue Leads (24h): Die gerade gescrapten Leads
   - Top Leads: Die besten bewerteten Kontakte

4. **Klicke auf "Alle Leads anzeigen"**
5. **Filter & Export:**
   - Filtere nach Score > 70
   - Sortiere nach Datum
   - Exportiere als CSV für Test

**Was du sehen solltest:**
```
Name           | E-Mail              | Telefon        | Score | Tags
---------------|---------------------|----------------|-------|--------
Max Mustermann | max@beispiel.de     | +49 171 123... | 85    | Vertrieb
...            | ...                 | ...            | ...   | ...
```

✅ **Checkpoint:** Du siehst mindestens 5-10 Leads mit Namen, E-Mail, Telefon.

---

## Schritt 6: Nächste Schritte 🎯

Glückwunsch! 🎉 Du hast LUCA erfolgreich gestartet und deine ersten Leads gescrapt.

### Sofort verfügbar (keine weitere Konfiguration):

1. **Mehr Leads scrapen:**
   - Erhöhe `--qpi` auf 12 (Balanced Mode)
   - Probiere andere Industries: `--industry talent_hunt`

2. **Lead-Management:**
   - Filtern, Sortieren, Suchen im CRM
   - Status ändern (Neu → Kontaktiert → Qualifiziert)
   - Bulk-Aktionen (mehrere Leads gleichzeitig bearbeiten)

3. **Export für dein Team:**
   - CSV/Excel Export mit Filtern
   - Übergabe an CRM oder Telefonisten

### Für Fortgeschrittene (optional):

4. **Skalierung:**
   - [Deployment Guide](DEPLOYMENT.md) - Produktiveinsatz (Railway, Render, Hetzner)
   - [Configuration Profiles](CONFIGURATION_PROFILES.md) - Safe/Balanced/Aggressive Modi
   - Automatisierte Runs (Cron/Scheduler)

5. **Stabilität & Qualität:**
   - [Lead Validation](../LEAD_VALIDATION_GUIDE.md) - Qualitätsfilter anpassen
   - [Troubleshooting](TROUBLESHOOTING.md) - Probleme lösen
   - Google Custom Search API für mehr Queries (optional)

6. **Features:**
   - Landing Page Builder nutzen (GrapesJS)
   - Brevo Email-Integration für Automation
   - AI-Features aktivieren (GPT-4, Perplexity)

---

## 🆘 Probleme?

| Problem | Lösung |
|---------|--------|
| **0 Leads nach Scraper-Run** | [→ Troubleshooting: 0 Leads](TROUBLESHOOTING.md#ich-bekomme-0-leads) |
| **"Port already in use"** | [→ Installation Guide](INSTALLATION.md#port-8000-already-in-use) |
| **CRM zeigt nichts an** | [→ Troubleshooting: CRM Issues](TROUBLESHOOTING.md#crm-zeigt-nichts-an) |
| **403 Errors / Blockaden** | [→ Troubleshooting: Blockaden](TROUBLESHOOTING.md#zu-viele-403blockaden) |

**Detaillierte Hilfe:** [Troubleshooting Guide](TROUBLESHOOTING.md)

---

## 📊 Erwartete Ergebnisse

Nach diesem Quickstart solltest du haben:

✅ Funktionstüchtiges LUCA CRM System  
✅ 5-30 gescrapte Leads in der Datenbank  
✅ Verständnis für den grundlegenden Workflow  
✅ Basis für Skalierung & Produktiveinsatz  

**Typische Zahlen für Safe Mode (QPI=6):**
- **Laufzeit:** 3-5 Minuten
- **Leads:** 10-30 (abhängig von Suchergebnissen)
- **Kosten:** €0 (ohne API-Keys)
- **API Calls:** 0 (nur kostenlose Quellen)

**Nächster Schritt:** [Configuration Profiles](CONFIGURATION_PROFILES.md) - Optimiere deine Scraper-Einstellungen!

---

**Feedback?** [GitHub Issues](https://github.com/sundsoffice-tech/luca-nrw-scraper/issues) | **Support?** [README.md](../README.md)
