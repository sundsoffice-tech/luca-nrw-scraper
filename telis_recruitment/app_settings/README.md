# App Settings Module

Zentrale Einstellungsverwaltung für die TELIS CRM-Anwendung.

## Übersicht

Das `app_settings` Modul bietet eine einheitliche Schnittstelle zur Verwaltung aller Anwendungseinstellungen:

- **Benutzereinstellungen**: Persönliche Präferenzen für jeden Benutzer
- **Systemeinstellungen**: Globale Konfigurationen (nur für Administratoren)
- **Integrationen**: Übersicht über externe Dienste und APIs

## Modelle

### UserPreferences

Benutzerspezifische Einstellungen mit One-to-One Beziehung zum User-Modell.

**Felder:**
- `theme`: Dark/Light Mode
- `language`: Deutsch/English
- `email_notifications`: E-Mail-Benachrichtigungen ein/aus
- `items_per_page`: Anzahl Elemente pro Seite (10-100)
- `default_lead_view`: Standard-Ansicht für Leads (Liste/Kacheln)

### SystemSettings

Globale Systemeinstellungen (Singleton-Modell).

**Felder:**
- `site_name`: Name der Anwendung
- `site_url`: URL der Installation
- `admin_email`: Administrator-E-Mail
- `enable_email_module`: E-Mail-Modul aktivieren
- `enable_scraper`: Scraper aktivieren
- `enable_ai_features`: KI-Funktionen aktivieren
- `enable_landing_pages`: Landing Pages aktivieren
- `maintenance_mode`: Wartungsmodus
- `maintenance_message`: Nachricht im Wartungsmodus
- `session_timeout_minutes`: Sitzungszeitlimit in Minuten
- `max_login_attempts`: Maximale Login-Versuche

## Views

### settings_dashboard
Hauptseite der Einstellungen mit Übersicht aller Kategorien.
- **URL**: `/crm/settings/`
- **Template**: `app_settings/dashboard.html`
- **Berechtigung**: Login erforderlich

### user_preferences_view
Benutzereinstellungen bearbeiten.
- **URL**: `/crm/settings/user/`
- **Template**: `app_settings/user_preferences.html`
- **Berechtigung**: Login erforderlich
- **POST**: Speichert Benutzereinstellungen

### system_settings_view
Systemeinstellungen bearbeiten (nur Admins).
- **URL**: `/crm/settings/system/`
- **Template**: `app_settings/system_settings.html`
- **Berechtigung**: Admin-Gruppe erforderlich
- **POST**: Speichert Systemeinstellungen

### integrations_view
Übersicht über Integrationen (nur Admins).
- **URL**: `/crm/settings/integrations/`
- **Template**: `app_settings/integrations.html`
- **Berechtigung**: Admin-Gruppe erforderlich

## URLs

```python
app_name = 'app_settings'

urlpatterns = [
    path('', views.settings_dashboard, name='dashboard'),
    path('user/', views.user_preferences_view, name='user-preferences'),
    path('system/', views.system_settings_view, name='system-settings'),
    path('integrations/', views.integrations_view, name='integrations'),
]
```

## Verwendung

### In Templates

```django
{% url 'app_settings:dashboard' %}
{% url 'app_settings:user-preferences' %}
{% url 'app_settings:system-settings' %}
```

### In Python

```python
from app_settings.models import UserPreferences, SystemSettings

# Benutzereinstellungen abrufen oder erstellen
prefs, created = UserPreferences.objects.get_or_create(user=request.user)

# Systemeinstellungen abrufen (Singleton)
settings = SystemSettings.get_settings()
```

## Integration

Das Modul ist in das CRM-Menü unter "⚙️ Einstellungen" integriert und bietet Links zu:

- Brand Settings (pages app)
- E-Mail-Konten (mailbox app)
- Brevo Integration (email_templates app)
- Scraper-Konfiguration (scraper_control app)
- AI-Konfiguration (ai_config app)

## Tests

Umfangreiche Tests sind in `tests.py` verfügbar:

```bash
python manage.py test app_settings
```

## Migration

```bash
python manage.py migrate app_settings
```

## Admin

Beide Modelle sind im Django Admin registriert:
- `/admin/app_settings/userpreferences/`
- `/admin/app_settings/systemsettings/`
