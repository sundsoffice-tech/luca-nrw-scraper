# Analytics & Tracking Integration

## Übersicht

Das TELIS CRM System verfügt nun über eine integrierte Analytics- und Tracking-Funktionalität, die es Administratoren ermöglicht, externe Tracking-Codes (Google Analytics, Meta Pixel, etc.) einzubinden und grundlegende Statistiken direkt im Backend anzuzeigen.

## Features

### 1. Tracking-Code-Integration

#### Unterstützte Tracking-Dienste:
- **Google Analytics (GA4 & Universal Analytics)**: Automatische Integration über Measurement ID
- **Meta Pixel (Facebook Pixel)**: Facebook/Instagram Conversion-Tracking
- **Benutzerdefinierte Tracking-Codes**: Unterstützung für Matomo, Plausible, oder andere Analytics-Dienste

#### Konfiguration:
1. Navigieren Sie zu **Einstellungen → Systemeinstellungen**
2. Scrollen Sie zum Abschnitt **"Analytics & Tracking"**
3. Aktivieren Sie **"Analytics aktivieren"**
4. Geben Sie Ihre Tracking-IDs ein:
   - **Google Analytics ID**: z.B. `G-XXXXXXXXXX` (GA4) oder `UA-XXXXXXXXX-X` (Universal Analytics)
   - **Meta Pixel ID**: z.B. `123456789012345` (nur Zahlen)
   - **Benutzerdefinierter Code**: Fügen Sie beliebige JavaScript-Tracking-Snippets ein
5. Klicken Sie auf **"Speichern"**

### 2. Analytics Dashboard

#### Zugriff:
- Klicken Sie in der Seitenleiste auf **📊 Analytics**
- Oder navigieren Sie direkt zu `/settings/analytics/`

#### Verfügbare Metriken:

##### Hauptmetriken (KPIs):
- **Gesamt-Seitenaufrufe**: Anzahl aller Seitenaufrufe im gewählten Zeitraum
- **Eindeutige Besucher**: Anzahl einzigartiger Sessions
- **Gesamt-Events**: Anzahl getrackte Benutzerinteraktionen

##### Zeitraumfilter:
- 7 Tage
- 30 Tage (Standard)
- 90 Tage

##### Visualisierungen:
1. **Seitenaufrufe über Zeit** (Liniendiagramm)
   - Zeigt tägliche Seitenaufrufe
   - Trend-Analyse über den gewählten Zeitraum

2. **Events nach Kategorie** (Doughnut-Diagramm)
   - Verteilung der Event-Kategorien
   - Kategorien: Navigation, Interaktion, Conversion, Fehler, Engagement

3. **Top Seiten**
   - Die 10 meistbesuchten Seiten
   - Zeigt Pfad und Anzahl der Aufrufe

4. **Top Events**
   - Die 10 häufigsten Events
   - Gruppiert nach Kategorie, Aktion und Label

5. **Benutzeraktivität**
   - Top 10 aktivste Benutzer
   - Anzahl der Seitenaufrufe pro Benutzer

6. **Neueste Seitenaufrufe**
   - Live-Feed der letzten 20 Seitenaufrufe
   - Zeigt Pfad, Benutzer und Zeitstempel

### 3. Datenerfassung

#### Automatisches Tracking:
Das System trackt automatisch:
- Seitenaufrufe (PageView)
  - URL-Pfad
  - Seitentitel
  - HTTP-Methode (GET, POST, etc.)
  - Referrer
  - User-Agent
  - IP-Adresse (anonymisiert)
  - Session-ID
  - Eingeloggter Benutzer (falls vorhanden)

#### Manuelle Event-Erfassung:
Events können programmatisch über die AnalyticsEvent-Modell erfasst werden:

```python
from app_settings.models import AnalyticsEvent

# Event erfassen
AnalyticsEvent.objects.create(
    user=request.user,
    session_key=request.session.session_key,
    category='conversion',
    action='lead_created',
    label='Import-Funktion',
    value=1.0,
    page_path=request.path,
    metadata={'source': 'csv_import'}
)
```

### 4. Admin-Bereich

#### Zugriff auf Rohdaten:
Administratoren können im Django-Admin auf die Rohdaten zugreifen:

1. **PageView-Einträge**: `/admin/app_settings/pageview/`
   - Filterable nach Datum, Methode, Benutzer
   - Durchsuchbar nach Pfad, IP-Adresse, Benutzer
   - Nur-Lese-Zugriff (Tracking-Daten werden nicht manuell geändert)

2. **AnalyticsEvent-Einträge**: `/admin/app_settings/analyticsevent/`
   - Filterable nach Kategorie, Aktion, Datum
   - Durchsuchbar nach Aktion, Label, Pfad
   - Nur-Lese-Zugriff

### 5. Datenschutz

#### DSGVO-Konformität:
- **Opt-In**: Analytics muss explizit aktiviert werden
- **Cookie-Consent**: Das System verfügt bereits über ein Cookie-Consent-Banner
- **IP-Anonymisierung**: IP-Adressen können anonymisiert gespeichert werden
- **Datenminimierung**: Es werden nur notwendige Daten erfasst

#### Best Practices:
1. Informieren Sie Nutzer in der Datenschutzerklärung über Analytics
2. Implementieren Sie Cookie-Consent vor dem Laden externer Tracking-Scripts
3. Erwägen Sie regelmäßiges Löschen alter Analytics-Daten
4. Nutzen Sie anonymisierte IP-Adressen für externe Dienste

### 6. Tracking-Code-Vorlagen

#### Google Analytics 4 (GA4):
```
Measurement ID: G-XXXXXXXXXX
```
Das System fügt automatisch den offiziellen GA4-Code ein.

#### Meta Pixel:
```
Pixel ID: 123456789012345
```
Das System fügt automatisch den Meta Pixel Base Code ein.

#### Matomo (Selbst-gehostet):
```html
<!-- Matomo -->
<script>
  var _paq = window._paq = window._paq || [];
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="//ihre-matomo-url.de/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '1']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<!-- End Matomo Code -->
```

#### Plausible Analytics:
```html
<script defer data-domain="ihre-domain.de" src="https://plausible.io/js/script.js"></script>
```

## API-Dokumentik

### Context Processor

Der `tracking_codes` Context Processor macht folgende Variablen in allen Templates verfügbar:
- `analytics_enabled`: Boolean - Gibt an, ob Analytics aktiviert ist
- `google_analytics_id`: String - Google Analytics Measurement ID
- `meta_pixel_id`: String - Meta Pixel ID
- `custom_tracking_code`: String - Benutzerdefinierter Tracking-Code

### Template Integration

Tracking-Codes werden automatisch in alle Seiten eingefügt via:
```django
{% include 'includes/tracking_codes.html' %}
```

Dieser Include ist bereits in `templates/base.html` und `templates/crm/base.html` eingebunden.

## Wartung & Optimierung

### Datenbank-Bereinigung

Um alte Analytics-Daten zu löschen (z.B. älter als 90 Tage):

```python
from datetime import timedelta
from django.utils import timezone
from app_settings.models import PageView, AnalyticsEvent

cutoff_date = timezone.now() - timedelta(days=90)
PageView.objects.filter(timestamp__lt=cutoff_date).delete()
AnalyticsEvent.objects.filter(timestamp__lt=cutoff_date).delete()
```

### Performance-Optimierung

Die Analytics-Modelle verfügen über optimierte Indizes:
- `timestamp` + `path` (PageView)
- `session_key` + `timestamp` (PageView)
- `timestamp` + `category` (AnalyticsEvent)
- `action` + `timestamp` (AnalyticsEvent)

Für große Datenmengen (> 100.000 Einträge) erwägen Sie:
1. Regelmäßige Archivierung alter Daten
2. Aggregierung auf Tagesbasis
3. Verwendung eines dedizierten Analytics-Backends

## Troubleshooting

### Tracking-Codes werden nicht geladen
1. Überprüfen Sie, ob **"Analytics aktivieren"** aktiviert ist
2. Leeren Sie den Browser-Cache
3. Überprüfen Sie die Browser-Konsole auf Fehler
4. Stellen Sie sicher, dass Ad-Blocker deaktiviert sind

### Dashboard zeigt keine Daten
1. Stellen Sie sicher, dass die Migration durchgeführt wurde: `python manage.py migrate`
2. Überprüfen Sie, ob Daten vorhanden sind: PageView.objects.count()
3. Wählen Sie einen längeren Zeitraum (90 Tage)

### Externe Tracking-Dienste funktionieren nicht
1. Überprüfen Sie die korrekte Schreibweise der IDs
2. Verifizieren Sie in den Browser-Developer-Tools, dass Scripts geladen werden
3. Konsultieren Sie die Dokumentation des jeweiligen Dienstes

## Weitere Entwicklung

Mögliche Erweiterungen:
- [ ] Event-Tracking über JavaScript-API
- [ ] Conversion-Funnel-Tracking
- [ ] A/B-Testing-Integration
- [ ] Echtzeit-Dashboards mit WebSockets
- [ ] Export-Funktionen (CSV, Excel, PDF)
- [ ] Custom Reports und Dashboards
- [ ] Integration mit CRM-Events (Lead-Erstellung, E-Mail-Öffnungen, etc.)

## Support

Bei Fragen oder Problemen:
1. Konsultieren Sie diese Dokumentation
2. Überprüfen Sie die Logs: `python manage.py runserver` (Development)
3. Erstellen Sie ein Issue auf GitHub
