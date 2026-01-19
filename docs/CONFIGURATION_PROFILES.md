# ⚙️ Scraper Configuration Profiles

Dieser Guide zeigt dir drei vorkonfigurierte Profile für unterschiedliche Anwendungsfälle. Wähle das Profil, das zu deinem Usecase passt.

---

## 📋 Übersicht der Profile

| Profil | QPI | Date Restrict | Runtime | Leads | Kosten | Empfohlen für |
|--------|-----|---------------|---------|-------|--------|---------------|
| **Safe Mode** | 6 | d30 | 3-5 min | 10-30 | €0 | Erste Tests, keine API-Keys |
| **Balanced Mode** | 12 | d60 | 8-12 min | 30-80 | €0-0.20 | Standard-Betrieb, tägliche Runs |
| **Aggressive Mode** | 20 | d90 | 15-25 min | 80-200 | €0.50-1.00 | Voller Durchsatz, mit Proxy empfohlen |

---

## 🛡️ Safe Mode (Starter & Test)

**Ideal für:**
- 🎯 Erste Tests ohne Risiko
- 🆓 Keine API-Keys erforderlich
- 🧪 Verständnis für den Workflow
- 📊 Kleine Lead-Mengen für Qualitätschecks

### Konfiguration

#### .env Datei

**Option 1: Vorkonfigurierte Vorlage nutzen (Empfohlen)**
```bash
# Kopiere die Safe Mode Vorlage
cp .env.example.safe .env

# Bearbeite nur SECRET_KEY (erforderlich)
nano .env
```

**Option 2: Manuell konfigurieren**
```bash
# Minimal Configuration (Safe Mode)
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Scraper Settings
SCRAPER_MODE=once
SCRAPER_QPI=6
SCRAPER_DATE_RESTRICT=d30
SCRAPER_DEFAULT_INDUSTRY=recruiter

# Optional (nicht erforderlich für Safe Mode)
OPENAI_API_KEY=
PERPLEXITY_API_KEY=
```

#### Command-Line
```bash
# Docker
docker-compose --profile scraper up scraper

# Manuell
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30
```

#### Im CRM
1. Gehe zu: http://localhost:8000/crm/scraper/
2. Einstellungen:
   - **Modus:** Once
   - **Industry:** recruiter
   - **QPI:** 6
   - **Date Restrict:** d30
3. Klicke "Start Scraper"

### Erwartete Ergebnisse

```
⏱️  Laufzeit:        3-5 Minuten
📊 Leads:            10-30
💰 Kosten:           €0
🔍 Queries:          6
🌐 API Calls:        0 (ohne OpenAI)
📈 Lead Quality:     Mittel (ohne AI-Enrichment)
⚠️  Rate Limits:     Sehr niedrig
🔒 Block-Risiko:     Minimal
```

### Best Practices

✅ **Gut für:**
- Ersten Durchlauf zum Testen
- Verständnis der Datenstruktur
- Überprüfung der CRM-Integration
- Setup-Validierung

❌ **Nicht gut für:**
- Produktiveinsatz mit hohem Volumen
- Schnelle Lead-Generierung
- Vollständige Marktabdeckung

---

## ⚖️ Balanced Mode (Standard-Betrieb)

**Ideal für:**
- 🏢 Täglicher Produktivbetrieb
- 📈 Gute Balance zwischen Qualität und Quantität
- 💰 Geringe bis moderate Kosten
- 🔄 Regelmäßige, planbare Runs

### Konfiguration

#### .env Datei

**Option 1: Vorkonfigurierte Vorlage nutzen (Empfohlen)**
```bash
# Kopiere die Balanced Mode Vorlage
cp .env.example.balanced .env

# Bearbeite die Werte:
# - SECRET_KEY (erforderlich)
# - OPENAI_API_KEY (empfohlen)
# - ALLOWED_HOSTS (für Produktion)
nano .env
```

**Option 2: Manuell konfigurieren**
```bash
# Balanced Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Scraper Settings
SCRAPER_MODE=once
SCRAPER_QPI=12
SCRAPER_DATE_RESTRICT=d60
SCRAPER_DEFAULT_INDUSTRY=recruiter

# Optional: AI für bessere Lead-Qualität
OPENAI_API_KEY=sk-your-key-here
PERPLEXITY_API_KEY=pplx-your-key-here
```

#### Command-Line
```bash
# Docker
docker-compose --profile scraper up scraper

# Manuell
python scriptname.py --once --industry recruiter --qpi 12 --daterestrict d60
```

#### Im CRM
1. Gehe zu: http://localhost:8000/crm/scraper/
2. Einstellungen:
   - **Modus:** Once
   - **Industry:** recruiter
   - **QPI:** 12
   - **Date Restrict:** d60
3. Klicke "Start Scraper"

### Erwartete Ergebnisse

```
⏱️  Laufzeit:        8-12 Minuten
📊 Leads:            30-80
💰 Kosten:           €0.10-0.30 (mit OpenAI)
🔍 Queries:          12
🌐 API Calls:        ~30-80 (für AI-Enrichment)
📈 Lead Quality:     Hoch (mit AI)
⚠️  Rate Limits:     Moderat
🔒 Block-Risiko:     Gering
```

### Best Practices

✅ **Empfohlene Frequenz:**
- 1x täglich (z.B. morgens 6 Uhr)
- 2-3x pro Woche für geringeren Durchsatz
- Automatisiert via Cron oder Scheduler

✅ **Optimierungen:**
```bash
# Mehrere Industries parallel
python scriptname.py --once --industry recruiter --qpi 12 &
python scriptname.py --once --industry talent_hunt --qpi 8 &
wait

# Mit zusätzlichen Filtern
python scriptname.py --once --industry recruiter --qpi 12 --daterestrict d60 --min-score 70
```

✅ **Monitoring:**
- Überwache Lead-Quality über CRM-Dashboard
- Prüfe API-Kosten wöchentlich
- Adjustiere QPI basierend auf Results

---

## 🚀 Aggressive Mode (Maximaler Durchsatz)

**Ideal für:**
- 💪 Maximale Lead-Generierung
- 🎯 Schnelle Marktabdeckung
- 🔄 One-Time Campaigns
- 🌐 Mit Proxy-Infrastruktur

### ⚠️ Wichtige Voraussetzungen

Bevor du Aggressive Mode nutzt:

1. **Proxy oder VPN empfohlen:**
   - Reduziert Block-Risiko
   - Verteilt Requests auf mehrere IPs
   - Siehe: [Proxy Setup Guide](../PROXY_FIX_SUMMARY.md)

2. **API-Keys konfiguriert:**
   - OpenAI für AI-Enrichment
   - Google Custom Search API (optional, für mehr Queries)

3. **Monitoring aktiv:**
   - Live-Logs überwachen
   - Error-Rate beobachten
   - Bei >20% 403s: Pause einlegen

### Konfiguration

#### .env Datei

**Option 1: Vorkonfigurierte Vorlage nutzen (Empfohlen)**
```bash
# Kopiere die Aggressive Mode Vorlage
cp .env.example.aggressive .env

# Bearbeite die Werte (alle erforderlich!):
# - SECRET_KEY
# - OPENAI_API_KEY (erforderlich für Aggressive)
# - HTTP_PROXY / HTTPS_PROXY (dringend empfohlen)
# - ALLOWED_HOSTS (für Produktion)
nano .env
```

**Option 2: Manuell konfigurieren**
```bash
# Aggressive Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Scraper Settings
SCRAPER_MODE=once
SCRAPER_QPI=20
SCRAPER_DATE_RESTRICT=d90
SCRAPER_DEFAULT_INDUSTRY=recruiter

# Required: AI APIs
OPENAI_API_KEY=sk-your-key-here
PERPLEXITY_API_KEY=pplx-your-key-here

# Optional: Google CSE für mehr Queries
GOOGLE_API_KEY=your-google-key
GOOGLE_CSE_ID=your-cse-id

# Optional: Proxy Configuration (siehe Proxy Guide)
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=https://your-proxy:port
```

#### Command-Line
```bash
# Mit allen Features
python scriptname.py --once --industry recruiter --qpi 20 --daterestrict d90

# Mehrere Industries gleichzeitig
python scriptname.py --once --industry recruiter --qpi 20 --daterestrict d90 &
python scriptname.py --once --industry talent_hunt --qpi 15 --daterestrict d90 &
python scriptname.py --once --industry callcenter --qpi 10 --daterestrict d90 &
wait
```

#### Im CRM
1. Gehe zu: http://localhost:8000/crm/scraper/
2. Einstellungen:
   - **Modus:** Once
   - **Industry:** recruiter
   - **QPI:** 20
   - **Date Restrict:** d90
3. Klicke "Start Scraper"
4. **Wichtig:** Überwache die Live-Logs!

### Erwartete Ergebnisse

```
⏱️  Laufzeit:        15-25 Minuten
📊 Leads:            80-200
💰 Kosten:           €0.50-1.50 (mit OpenAI)
🔍 Queries:          20+
🌐 API Calls:        ~100-200 (für AI-Enrichment)
📈 Lead Quality:     Sehr hoch (mit AI)
⚠️  Rate Limits:     Hoch
🔒 Block-Risiko:     Mittel-Hoch (ohne Proxy)
```

### Best Practices

✅ **Vorbereitung:**
- Proxy/VPN aktivieren
- API-Keys validieren
- Monitoring Dashboard öffnen
- Zeitfenster planen (nicht zu Spitzenzeiten)

✅ **Während des Runs:**
- Live-Logs beobachten
- Bei >20% Fehlerrate: Pause (Ctrl+C)
- Bei Blocks: Proxy wechseln oder Delay erhöhen

✅ **Nach dem Run:**
- Lead-Quality prüfen (Score-Verteilung)
- Duplikate entfernen (automatisch)
- API-Kosten tracken
- Lessons learned dokumentieren

❌ **Nicht empfohlen:**
- Ohne Proxy/VPN auf Heimnetzwerk
- Mehrfach täglich (Block-Risiko!)
- Ohne Monitoring
- Ohne API-Budget

---

## 🔧 Custom Configuration

Du kannst auch eigene Profile erstellen:

### Eigenes Profil definieren

```bash
# Beispiel: "Weekend Warrior" - Samstags großer Run
SCRAPER_QPI=15
SCRAPER_DATE_RESTRICT=d45
SCRAPER_DEFAULT_INDUSTRY=recruiter

# Beispiel: "Nightly Crawl" - Nachts moderate Runs
SCRAPER_QPI=10
SCRAPER_DATE_RESTRICT=d30
SCRAPER_DEFAULT_INDUSTRY=talent_hunt
```

### Parameter-Referenz

| Parameter | Werte | Beschreibung |
|-----------|-------|--------------|
| `SCRAPER_MODE` | `once`, `continuous` | Einmaliger Run vs. Dauerbetrieb |
| `SCRAPER_QPI` | 1-30 | Queries per Industry (höher = mehr Leads) |
| `SCRAPER_DATE_RESTRICT` | `d7`, `d30`, `d60`, `d90` | Zeitfenster für Suchergebnisse |
| `SCRAPER_DEFAULT_INDUSTRY` | `recruiter`, `talent_hunt`, `callcenter` | Ziel-Industry |

### Industries verfügbar

```bash
# B2B Vertriebskontakte
--industry recruiter

# Aktive Jobsuchende im Sales
--industry talent_hunt

# Callcenter & Telemarketing
--industry callcenter

# Construction Industry
--industry construction

# Medical Industry
--industry medical

# Food & Beverage
--industry food
```

---

## 📊 Performance-Vergleich

### Lead-Quality nach Profil

```
Safe Mode:       ⭐⭐⭐☆☆ (Mittel, ohne AI)
Balanced Mode:   ⭐⭐⭐⭐☆ (Hoch, mit AI)
Aggressive Mode: ⭐⭐⭐⭐⭐ (Sehr hoch, mit AI + Volume)
```

### Kosten-Nutzen-Analyse

```
Safe Mode:       Cost/Lead: €0      (kein AI, keine API)
Balanced Mode:   Cost/Lead: €0.005  (50 Leads für €0.25)
Aggressive Mode: Cost/Lead: €0.008  (150 Leads für €1.20)
```

### Block-Risiko

```
Safe Mode:       🟢 Sehr gering (6 Queries)
Balanced Mode:   🟡 Gering (12 Queries, moderate Frequenz)
Aggressive Mode: 🔴 Mittel-Hoch (20+ Queries, Proxy empfohlen)
```

---

## 🆘 Troubleshooting

### "Zu wenige Leads" (< 10 bei Balanced)

```bash
# Check 1: Date Restrict erweitern
SCRAPER_DATE_RESTRICT=d90

# Check 2: QPI erhöhen
SCRAPER_QPI=15

# Check 3: Andere Industry testen
--industry talent_hunt
```

### "Zu viele 403 Errors"

```bash
# Lösung 1: QPI reduzieren
SCRAPER_QPI=8

# Lösung 2: Delay erhöhen (im Script)
# Edit scriptname.py: DELAY_BETWEEN_REQUESTS = 3

# Lösung 3: Proxy aktivieren
HTTP_PROXY=http://your-proxy:port
```

### "API-Kosten zu hoch"

```bash
# Lösung 1: AI-Enrichment deaktivieren
OPENAI_API_KEY=  # leer lassen

# Lösung 2: QPI reduzieren
SCRAPER_QPI=6

# Lösung 3: Weniger häufige Runs
# z.B. nur 2x pro Woche statt täglich
```

**Mehr Hilfe:** [Troubleshooting Guide](TROUBLESHOOTING.md)

---

## 📚 Weiterführende Dokumentation

- **[Quickstart Guide](QUICKSTART.md)** - Erste Schritte in 20 Minuten
- **[Installation Guide](INSTALLATION.md)** - Detaillierte Setup-Anleitung
- **[Deployment Guide](DEPLOYMENT.md)** - Produktiv-Deployment
- **[Troubleshooting](TROUBLESHOOTING.md)** - Problemlösungen

---

**Feedback?** [GitHub Issues](https://github.com/sundsoffice-tech/luca-nrw-scraper/issues) | **Fragen?** [README.md](../README.md)
