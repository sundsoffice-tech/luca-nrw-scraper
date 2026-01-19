# Einstellungen-System Implementierung

## Zusammenfassung

Das Einstellungen-Menü im TELIS CRM wurde vollständig implementiert und ist nun funktionsfähig. Alle Aspekte der Anwendung können über eine zentrale Einstellungsoberfläche konfiguriert werden.

## Was wurde implementiert

### 1. Neues App-Modul: `app_settings`

Ein dediziertes Django-App-Modul wurde erstellt, das als zentrale Anlaufstelle für alle Einstellungen dient.

**Struktur:**
```
app_settings/
├── __init__.py
├── admin.py              # Django Admin Integration
├── apps.py               # App-Konfiguration
├── models.py             # Datenmodelle
├── views.py              # View-Funktionen
├── urls.py               # URL-Routing
├── tests.py              # Unit-Tests
├── README.md             # Dokumentation
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py   # Datenbankschema
└── templates/
    └── app_settings/
        ├── dashboard.html           # Hauptseite
        ├── user_preferences.html    # Benutzereinstellungen
        ├── system_settings.html     # Systemeinstellungen
        └── integrations.html        # Integrationen
```

### 2. Datenmodelle

#### UserPreferences
- **Zweck**: Benutzerspezifische Einstellungen
- **Felder**:
  - Theme (Dark/Light)
  - Sprache (Deutsch/English)
  - E-Mail-Benachrichtigungen
  - Elemente pro Seite (10-100)
  - Standard-Lead-Ansicht (Liste/Kacheln)

#### SystemSettings
- **Zweck**: Globale Systemeinstellungen (Singleton)
- **Felder**:
  - Seitenname und URL
  - Administrator-E-Mail
  - Module aktivieren/deaktivieren (E-Mail, Scraper, KI, Landing Pages)
  - Wartungsmodus
  - Sicherheitseinstellungen (Session-Timeout, Login-Versuche)

### 3. Benutzeroberfläche

#### Einstellungs-Dashboard (`/crm/settings/`)
Zentrale Übersichtsseite mit Kacheln für alle Einstellungsbereiche:
- 👤 Benutzerprofil
- 🔧 System (nur Admin)
- 📧 E-Mail
- 📝 Brevo Integration
- 🤖 Scraper (nur Admin)
- 🧠 KI-Konfiguration (nur Admin)
- 🎨 Marke & Design (nur Admin)
- 🔌 Integrationen (nur Admin)

#### Benutzereinstellungen (`/crm/settings/user/`)
- Theme-Auswahl
- Sprachauswahl
- Benachrichtigungseinstellungen
- Anzeigeoptionen

#### Systemeinstellungen (`/crm/settings/system/`)
Nur für Administratoren:
- Allgemeine Site-Konfiguration
- Module aktivieren/deaktivieren
- Wartungsmodus
- Sicherheitseinstellungen

#### Integrationen (`/crm/settings/integrations/`)
Übersicht über externe Dienste:
- Brevo (E-Mail Marketing)
- AI Provider (OpenAI, Perplexity)
- Google Custom Search Engine
- Webhooks

### 4. Navigation

Das Menü wurde aktualisiert:
- ✅ Link zu "⚙️ Einstellungen" funktioniert
- ❌ "Bald"-Badge wurde entfernt
- ✅ Aktive Seite wird hervorgehoben

### 5. Berechtigungssystem

- **Alle Benutzer**: Zugriff auf Benutzereinstellungen und E-Mail-Konten
- **Administratoren**: Zusätzlicher Zugriff auf Systemeinstellungen, Scraper, KI, Brand Settings und Integrationen

### 6. Integration mit bestehenden Modulen

Die neue Einstellungsseite verlinkt zu bestehenden Einstellungsbereichen:

| Modul | Pfad | Beschreibung |
|-------|------|--------------|
| Mailbox | `/crm/mailbox/settings/` | E-Mail-Konten verwalten |
| Email Templates | `/email_templates:brevo-settings` | Brevo API-Schlüssel |
| Scraper Control | `/admin/scraper_control/scraperconfig/` | Scraper-Parameter |
| AI Config | `/admin/ai_config/aimodel/` | AI-Modelle und Provider |
| Pages | `/pages:brand-settings` | Brand-Farben und Logos |

### 7. Fehlerbehebungen

- **BrandSettings Model**: Fehlender `text_light_color` Field hinzugefügt
- Duplikat-Methoden in BrandSettings entfernt

### 8. Tests

Umfangreiche Test-Suite erstellt:
- Model-Tests für UserPreferences und SystemSettings
- View-Tests für alle Einstellungsseiten
- Berechtigungs-Tests (Admin vs. normale Benutzer)
- POST-Tests zum Speichern von Einstellungen

## Verwendung

### Als Benutzer

1. Im CRM-Menü auf "⚙️ Einstellungen" klicken
2. Gewünschten Einstellungsbereich auswählen
3. Einstellungen anpassen
4. "💾 Speichern" klicken

### Als Administrator

Zusätzlich zu den Benutzereinstellungen:
1. Systemeinstellungen konfigurieren
2. Module aktivieren/deaktivieren
3. Wartungsmodus steuern
4. Sicherheitsparameter anpassen

## Technische Details

### URL-Struktur
```
/crm/settings/              -> Dashboard
/crm/settings/user/         -> Benutzereinstellungen
/crm/settings/system/       -> Systemeinstellungen
/crm/settings/integrations/ -> Integrationen
```

### Template-Struktur
Alle Templates erweitern `crm/base.html` und nutzen das bestehende Dark-Theme-Design.

### Datenbankschema
```sql
-- UserPreferences (1:1 mit User)
CREATE TABLE app_settings_userpreferences (
    id BIGINT PRIMARY KEY,
    user_id INT UNIQUE,
    theme VARCHAR(20),
    language VARCHAR(10),
    email_notifications BOOLEAN,
    items_per_page INT,
    default_lead_view VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- SystemSettings (Singleton, pk=1)
CREATE TABLE app_settings_systemsettings (
    id BIGINT PRIMARY KEY,  -- Immer 1
    site_name VARCHAR(100),
    site_url VARCHAR(200),
    admin_email VARCHAR(254),
    enable_email_module BOOLEAN,
    enable_scraper BOOLEAN,
    enable_ai_features BOOLEAN,
    enable_landing_pages BOOLEAN,
    maintenance_mode BOOLEAN,
    maintenance_message TEXT,
    session_timeout_minutes INT,
    max_login_attempts INT,
    updated_at TIMESTAMP
);
```

## Nächste Schritte

Das Einstellungen-System ist vollständig implementiert und getestet. Folgende optionale Erweiterungen sind möglich:

1. **Erweiterte Benutzereinstellungen**:
   - Zeitzone-Auswahl
   - Datumsformat-Präferenzen
   - Dashboard-Widgets anpassen

2. **Erweiterte Systemeinstellungen**:
   - Backup-Konfiguration
   - Logging-Level
   - API-Rate-Limits

3. **Audit-Log**:
   - Protokollierung von Einstellungsänderungen
   - Wer hat wann was geändert

4. **Export/Import**:
   - Einstellungen exportieren
   - Einstellungen zwischen Instanzen übertragen

## Migration

```bash
# Datenbank-Migrationen anwenden
python manage.py migrate app_settings
python manage.py migrate pages  # Für text_light_color Fix

# Optional: Standard-Systemeinstellungen erstellen
python manage.py shell
>>> from app_settings.models import SystemSettings
>>> SystemSettings.get_settings()
```

## Support

Bei Fragen oder Problemen:
- Siehe `app_settings/README.md` für detaillierte Dokumentation
- Siehe `app_settings/tests.py` für Verwendungsbeispiele
- Django Admin: `/admin/app_settings/`
