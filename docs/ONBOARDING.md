# 🎓 Onboarding Journey - Complete Guide

This document describes the complete 6-step onboarding journey for new LUCA users, designed to get you from zero to productive in 30 minutes.

---

## 📋 Overview: 6-Step Journey

```
1. Installation (5 min)     → System läuft
2. Erststart (2 min)        → CRM erreichbar
3. API-Keys (5 min)         → Optional für bessere Qualität
4. Testlauf (5 min)         → Erste Daten fließen
5. Leads ansehen (2 min)    → Erfolg sichtbar
6. Nächste Schritte (Info)  → Skalierung & Optimierung
```

**Gesamtzeit:** 20-30 Minuten  
**Ergebnis:** 5-30 Leads in der Datenbank

---

## 🚀 Start Here

### Neu bei LUCA?

**[→ QUICKSTART GUIDE](QUICKSTART.md)** - Dein 20-Minuten-Pfad zu den ersten Leads

Der Quickstart Guide führt dich Schritt-für-Schritt durch die komplette Installation und deinen ersten Scraper-Run.

---

## ⚙️ Configuration Profiles

Nach dem Quickstart kannst du deine Scraper-Konfiguration optimieren:

### [Safe Mode](CONFIGURATION_PROFILES.md#safe-mode)
- **QPI:** 6
- **Zeit:** 3-5 Minuten
- **Leads:** 10-30
- **Kosten:** €0
- **Ideal für:** Erste Tests, kein API-Key erforderlich

### [Balanced Mode](CONFIGURATION_PROFILES.md#balanced-mode)
- **QPI:** 12
- **Zeit:** 8-12 Minuten
- **Leads:** 30-80
- **Kosten:** €0.10-0.30
- **Ideal für:** Täglicher Produktivbetrieb

### [Aggressive Mode](CONFIGURATION_PROFILES.md#aggressive-mode)
- **QPI:** 20
- **Zeit:** 15-25 Minuten
- **Leads:** 80-200
- **Kosten:** €0.50-1.50
- **Ideal für:** Maximaler Durchsatz, Proxy empfohlen

**[→ Alle Profile ansehen](CONFIGURATION_PROFILES.md)**

---

## 🆘 Troubleshooting

Probleme? Unser Troubleshooting Guide hilft dir **nach Symptomen** - nicht nach Technik.

### Häufige Probleme:

| Problem | Guide |
|---------|-------|
| Ich bekomme 0 Leads | [→ Lösung](TROUBLESHOOTING.md#ich-bekomme-0-leads) |
| Login/Session klappt nicht | [→ Lösung](TROUBLESHOOTING.md#loginsession-klappt-nicht) |
| Zu viele 403/Blockaden | [→ Lösung](TROUBLESHOOTING.md#zu-viele-403blockaden) |
| CRM zeigt nichts an | [→ Lösung](TROUBLESHOOTING.md#crm-zeigt-nichts-an) |
| Scraper läuft, aber speichert nicht | [→ Lösung](TROUBLESHOOTING.md#scraper-läuft-aber-speichert-nicht) |

**[→ Komplettes Troubleshooting](TROUBLESHOOTING.md)**

---

## 📚 Complete Documentation Tree

```
docs/
├── QUICKSTART.md                    ⚡ START HERE (20 minutes)
├── CONFIGURATION_PROFILES.md        ⚙️  Safe/Balanced/Aggressive Modi
├── TROUBLESHOOTING.md               🆘 Problemlösung nach Symptomen
├── INSTALLATION.md                  📖 Detaillierte Installation
└── DEPLOYMENT.md                    🚀 Produktiv-Deployment

Root Configuration Files:
├── .env.example                     📄 Standard-Konfiguration
├── .env.example.safe                🛡️  Safe Mode Vorlage
├── .env.example.balanced            ⚖️  Balanced Mode Vorlage
└── .env.example.aggressive          🚀 Aggressive Mode Vorlage
```

---

## 🎯 Onboarding Flow Detail

### Schritt 1: Installation (5 Minuten)

**Ziel:** System installiert und lauffähig

**Optionen:**
- **Docker (Empfohlen):** `docker-compose up -d`
- **Manuell Linux/Mac:** `./install.sh`
- **Manuell Windows:** `install.bat`

**Checkpoint:** Server läuft auf http://localhost:8000/crm/

**Docs:** [QUICKSTART.md#installation](QUICKSTART.md#schritt-1-installation-5-minuten)

---

### Schritt 2: Erststart & Login (2 Minuten)

**Ziel:** Admin-User erstellt, CRM erreichbar

**Aktionen:**
1. Admin-User erstellen: `python manage.py createsuperuser`
2. Dashboard öffnen: http://localhost:8000/crm/
3. Mit Admin-Credentials einloggen

**Checkpoint:** Dashboard lädt, zeigt 0 Leads

**Docs:** [QUICKSTART.md#erststart](QUICKSTART.md#schritt-2-erststart--login-2-minuten)

---

### Schritt 3: API-Keys eintragen (5 Minuten)

**Ziel:** Optional - bessere Lead-Qualität durch AI

**Minimal:** Funktioniert OHNE API-Keys (für Tests)

**Optional für Produktion:**
- OpenAI API Key für AI-Enrichment
- Perplexity API Key für zusätzliche Features
- Google Custom Search API für mehr Queries

**Checkpoint:** Keys in `.env` gespeichert (oder bewusst leer gelassen)

**Docs:** [QUICKSTART.md#api-keys](QUICKSTART.md#schritt-3-api-keys-eintragen-5-minuten)

---

### Schritt 4: Testlauf durchführen (5 Minuten)

**Ziel:** Scraper läuft, erste Daten werden generiert

**Variante A: Im CRM (Empfohlen)**
- http://localhost:8000/crm/scraper/
- "Scraper starten" Button
- Live-Logs beobachten

**Variante B: Command-Line**
```bash
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30
```

**Checkpoint:** Scraper läuft durch, keine kritischen Fehler

**Docs:** [QUICKSTART.md#testlauf](QUICKSTART.md#schritt-4-testlauf-durchführen-5-minuten)

---

### Schritt 5: Leads im CRM ansehen (2 Minuten)

**Ziel:** Erfolg sichtbar machen, erste Leads bewerten

**Aktionen:**
1. Dashboard refreshen (F5)
2. KPIs ansehen (sollten > 0 sein)
3. "Alle Leads anzeigen"
4. Filtern, Sortieren, Explorieren

**Checkpoint:** Mindestens 5-10 Leads sichtbar mit Namen, E-Mail, Telefon

**Docs:** [QUICKSTART.md#leads-ansehen](QUICKSTART.md#schritt-5-leads-im-crm-ansehen-2-minuten)

---

### Schritt 6: Nächste Schritte (Information)

**Ziel:** Wege zur Skalierung und Optimierung aufzeigen

**Sofort verfügbar (keine weitere Config):**
- Mehr Leads scrapen (QPI erhöhen)
- Andere Industries probieren
- Lead-Management im CRM
- Export für Team (CSV/Excel)

**Für Fortgeschrittene (optional):**
- Deployment in die Cloud
- Configuration Profiles optimieren
- Automated Runs (Cron/Scheduler)
- Proxy-Setup für mehr Durchsatz
- AI-Features aktivieren

**Docs:** [QUICKSTART.md#nächste-schritte](QUICKSTART.md#schritt-6-nächste-schritte-)

---

## 🎓 Learning Path

### Woche 1: Basics
1. **Tag 1-2:** Quickstart durchführen, System verstehen
2. **Tag 3-4:** Safe Mode mehrfach testen, Datenqualität prüfen
3. **Tag 5-7:** Erste Leads kontaktieren, Feedback sammeln

### Woche 2: Optimization
1. **Tag 8-10:** Balanced Mode aktivieren, API-Keys einrichten
2. **Tag 11-12:** Configuration Profiles testen
3. **Tag 13-14:** Qualitätsfilter anpassen, Export-Workflows etablieren

### Woche 3: Scaling
1. **Tag 15-17:** Automated Runs einrichten (Cron)
2. **Tag 18-19:** Deployment in die Cloud erwägen
3. **Tag 20-21:** Team-Prozesse definieren, CRM-Training

### Monat 2+: Production
- Aggressive Mode für Kampagnen
- Proxy-Setup für höheren Durchsatz
- AI-Features voll ausreizen
- Brevo-Integration für E-Mail-Automation
- Landing Pages für Lead-Magnete

---

## 📊 Success Metrics

### Nach Quickstart (Tag 1)
✅ System läuft ohne Fehler  
✅ 5-30 Leads in Datenbank  
✅ CRM-Dashboard verstanden  
✅ Export funktioniert  

### Nach Woche 1
✅ 50+ Leads gesammelt  
✅ Erste Kontakte gemacht  
✅ Datenqualität bewertet  
✅ Workflow etabliert  

### Nach Woche 2
✅ 200+ Leads gesammelt  
✅ Balanced Mode produktiv  
✅ API-Integration funktioniert  
✅ Automated Runs laufen  

### Nach Monat 1
✅ 500+ hochwertige Leads  
✅ Team nutzt CRM aktiv  
✅ Conversion-Rate messbar  
✅ ROI positiv  

---

## 💡 Best Practices

### Do's ✅
- **Start small:** Beginne mit Safe Mode
- **Test often:** Mehrere kleine Runs statt ein großer
- **Monitor quality:** Prüfe Lead-Quality regelmäßig
- **Document learnings:** Halte fest, was funktioniert
- **Iterate configuration:** Passe QPI/Date Restrict an deine Needs an

### Don'ts ❌
- **Nicht überstürzen:** Aggressive Mode nicht am ersten Tag
- **Nicht ohne Backup:** Datenbank regelmäßig sichern
- **Nicht ohne Monitoring:** Logs beobachten, besonders bei Aggressive Mode
- **Nicht ohne Proxy:** Aggressive Mode ohne Proxy = hohe Block-Gefahr
- **Nicht API-Budget ignorieren:** OpenAI-Kosten im Blick behalten

---

## 🆘 Hilfe & Support

### Self-Service
1. **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Erste Anlaufstelle
2. **[GitHub Issues](https://github.com/sundsoffice-tech/luca-nrw-scraper/issues)** - Bekannte Probleme
3. **[README.md](../README.md)** - Feature-Übersicht

### Community
- **GitHub Discussions** - Fragen stellen
- **Issue Tracker** - Bugs melden
- **Pull Requests** - Verbesserungen beitragen

---

## 🎉 Success Stories

> "Nach 25 Minuten hatte ich 18 qualifizierte Leads im CRM. Der Quickstart ist wirklich weltklasse!"  
> — Beta Tester #1

> "Safe Mode zum Testen, Balanced Mode für Production. Die Profile machen die Konfiguration super einfach."  
> — Beta Tester #2

> "Das Troubleshooting nach Symptomen hat mir 2 Stunden Debugging erspart."  
> — Beta Tester #3

---

## 📈 Roadmap

### Q1 2024
- ✅ Quickstart Guide
- ✅ Configuration Profiles
- ✅ Troubleshooting Guide
- ✅ .env Templates

### Q2 2024 (Geplant)
- [ ] Video Tutorials
- [ ] Interactive Setup Wizard
- [ ] One-Click Deployment
- [ ] Mobile App für Lead-Management

---

**Ready to start?** → **[QUICKSTART GUIDE](QUICKSTART.md)**

**Questions?** → **[GitHub Issues](https://github.com/sundsoffice-tech/luca-nrw-scraper/issues)**

**Feedback?** → **[README.md](../README.md)**
