# Brevo Email Integration - Dokumentation

## Übersicht

Diese Integration ermöglicht die automatische Email-Marketing-Verwaltung über Brevo (ehemals Sendinblue) für das TELIS Recruitment System.

## Features

✅ **Automatische Kontaktsynchronisierung**: Neue Landing Page Leads werden automatisch zu Brevo synchronisiert
✅ **Welcome Email**: Automatischer Versand einer Welcome-Email nach Opt-In
✅ **Webhook-Tracking**: Verfolgung von Email Opens, Clicks, Bounces und Unsubscribes
✅ **Auto-Status-Updates**: Hard Bounces markieren Leads automatisch als INVALID
✅ **Graceful Degradation**: System funktioniert auch ohne Brevo-Konfiguration
✅ **Django Signals**: Entkoppelte Integration via post_save Signal

## Einrichtung

### 1. Brevo Account & API Key

1. Registriere dich bei [Brevo](https://www.brevo.com/)
2. Gehe zu **Transactional > Settings > SMTP & API**
3. Erstelle einen neuen API Key
4. Kopiere den API Key

### 2. Brevo Listen erstellen

1. Gehe zu **Contacts > Lists**
2. Erstelle zwei Listen:
   - **Default List** (z.B. "All Leads") - Notiere die List-ID
   - **Landing Page List** (z.B. "Landing Page Leads") - Notiere die List-ID

### 3. Email Template erstellen

1. Gehe zu **Transactional > Templates**
2. Erstelle ein neues Template für die Welcome Email
3. Verwende folgende Platzhalter im Template:
   - `{{ params.VORNAME }}` - Vorname des Leads
   - `{{ params.NACHNAME }}` - Nachname des Leads
   - `{{ params.NAME }}` - Vollständiger Name
4. Notiere die Template-ID

### 4. Umgebungsvariablen konfigurieren

Füge folgende Variablen zu deiner `.env` Datei hinzu:

```bash
# Brevo (Sendinblue) Email Marketing
BREVO_API_KEY=xkeysib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-yyyyyy
BREVO_DEFAULT_LIST_ID=1
BREVO_LANDING_PAGE_LIST_ID=2
BREVO_WELCOME_TEMPLATE_ID=1
```

### 5. Requirements installieren

```bash
pip install -r requirements.txt
```

Dies installiert `sib-api-v3-sdk>=7.6.0` für die Brevo API Integration.

### 6. Webhook konfigurieren

1. Gehe zu **Transactional > Settings > Webhooks**
2. Erstelle einen neuen Webhook mit folgenden Einstellungen:
   - **URL**: `https://your-domain.com/api/webhooks/brevo/`
   - **Events**: Wähle folgende Events aus:
     - ✅ Email opened
     - ✅ Email clicked
     - ✅ Hard bounce
     - ✅ Unsubscribe

## Verwendung

### Automatische Integration

Die Integration erfolgt automatisch:

1. **Opt-In über Landing Page**:
   ```bash
   curl -X POST http://localhost:8000/api/opt-in/ \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Max Mustermann",
       "email": "max@example.com",
       "telefon": "0123456789"
     }'
   ```

2. **Automatische Aktionen**:
   - Lead wird in Datenbank erstellt
   - Kontakt wird zu Brevo synchronisiert
   - Welcome Email wird automatisch gesendet
   - Email-Counter wird erhöht

### Webhook Events

Wenn ein Empfänger mit der Email interagiert, sendet Brevo Webhooks:

- **Email Opened**: `email_opens` Counter wird erhöht
- **Link Clicked**: `email_clicks` Counter wird erhöht
- **Hard Bounce**: Lead Status wird auf `INVALID` gesetzt
- **Unsubscribe**: Interest Level wird auf 0 gesetzt

## API Dokumentation

### Brevo Service (`leads/services/brevo.py`)

#### `get_brevo_config()`
Gibt die Brevo API Configuration zurück.

**Returns**: `Configuration` object oder `None` wenn nicht konfiguriert

#### `create_or_update_contact(email, attributes, list_ids=None)`
Erstellt oder aktualisiert einen Kontakt in Brevo.

**Parameter**:
- `email` (str): E-Mail-Adresse
- `attributes` (dict): Kontakt-Attribute (VORNAME, NACHNAME, etc.)
- `list_ids` (list, optional): Liste von Brevo List-IDs

**Returns**: `bool` - True bei Erfolg, False bei Fehler

**Beispiel**:
```python
from leads.services.brevo import create_or_update_contact

success = create_or_update_contact(
    email='max@example.com',
    attributes={
        'VORNAME': 'Max',
        'NACHNAME': 'Mustermann',
        'TELEFON': '0123456789',
        'FIRMA': 'Test GmbH',
        'QUELLE': 'landing_page',
        'QUALITY_SCORE': 85
    },
    list_ids=[1, 2]
)
```

#### `send_transactional_email(to_email, to_name, template_id, params=None)`
Sendet eine transaktionale Email über Brevo Template.

**Parameter**:
- `to_email` (str): Empfänger E-Mail
- `to_name` (str): Empfänger Name
- `template_id` (int): Brevo Template ID
- `params` (dict, optional): Template-Parameter

**Returns**: `str` - Message-ID bei Erfolg, None bei Fehler

**Beispiel**:
```python
from leads.services.brevo import send_transactional_email

message_id = send_transactional_email(
    to_email='max@example.com',
    to_name='Max Mustermann',
    template_id=1,
    params={
        'VORNAME': 'Max',
        'NACHNAME': 'Mustermann',
        'NAME': 'Max Mustermann'
    }
)
```

#### `send_welcome_email(lead)`
Sendet Welcome-Email an neuen Landing Page Lead.

**Parameter**:
- `lead`: Lead Model-Instanz

**Returns**: `str` - Message-ID bei Erfolg, None bei Fehler

**Beispiel**:
```python
from leads.models import Lead
from leads.services.brevo import send_welcome_email

lead = Lead.objects.get(id=1)
message_id = send_welcome_email(lead)
```

#### `sync_lead_to_brevo(lead)`
Synchronisiert einen Lead zu Brevo.

**Parameter**:
- `lead`: Lead Model-Instanz

**Returns**: `bool` - True bei Erfolg, False bei Fehler

**Beispiel**:
```python
from leads.models import Lead
from leads.services.brevo import sync_lead_to_brevo

lead = Lead.objects.get(id=1)
success = sync_lead_to_brevo(lead)
```

### Webhook Endpoint

**Endpoint**: `POST /api/webhooks/brevo/`

**Request Body**:
```json
{
  "event": "opened",
  "email": "max@example.com"
}
```

**Response**:
```json
{
  "status": "ok",
  "event": "opened"
}
```

**Supported Events**:
- `opened` - Email wurde geöffnet
- `click` - Link wurde geklickt
- `hard_bounce` - Email unzustellbar
- `unsubscribed` - Abgemeldet

## Testing

Die Integration enthält umfassende Tests:

```bash
cd telis_recruitment
python manage.py test leads.tests.BrevoIntegrationTest
python manage.py test leads.tests.BrevoWebhookTest
```

### Test Cases

1. **Graceful Degradation**: System funktioniert ohne Brevo SDK
2. **Signal Integration**: Lead-Erstellung triggert Brevo-Sync
3. **Webhook Events**: Alle Events werden korrekt verarbeitet
4. **Error Handling**: Fehler werden korrekt geloggt

## Troubleshooting

### Problem: "sib-api-v3-sdk nicht installiert"

**Lösung**:
```bash
pip install sib-api-v3-sdk>=7.6.0
```

### Problem: "BREVO_API_KEY nicht konfiguriert"

**Lösung**: Stelle sicher, dass `BREVO_API_KEY` in der `.env` Datei gesetzt ist.

### Problem: Welcome Email wird nicht gesendet

**Mögliche Ursachen**:
1. `BREVO_WELCOME_TEMPLATE_ID` nicht konfiguriert
2. Template-ID existiert nicht in Brevo
3. API Key ist ungültig
4. Lead hat keine Email-Adresse

**Debug**:
```bash
# Prüfe Logs
tail -f logs/django.log | grep Brevo
```

### Problem: Webhook funktioniert nicht

**Mögliche Ursachen**:
1. Webhook URL ist nicht erreichbar
2. CSRF-Token wird überprüft (sollte nicht, da `@csrf_exempt`)
3. Lead mit dieser Email existiert nicht

**Test Webhook lokal**:
```bash
curl -X POST http://localhost:8000/api/webhooks/brevo/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "opened",
    "email": "test@example.com"
  }'
```

## Sicherheit

✅ **API Key**: Wird über Umgebungsvariable verwaltet, nie im Code
✅ **CSRF Exempt**: Webhook Endpoint ist CSRF-exempt (Brevo hat keine CSRF-Tokens)
✅ **Error Handling**: Alle Exceptions werden geloggt, keine sensitiven Daten in Responses
✅ **Input Validation**: Email-Adressen werden validiert
✅ **SQL Injection**: Django ORM schützt automatisch

## Monitoring

### Logs überwachen

```bash
# Alle Brevo-bezogenen Logs
grep "Brevo" logs/django.log

# Erfolgreiche Emails
grep "Brevo: Email gesendet" logs/django.log

# Fehler
grep "Brevo.*Fehler" logs/django.log
```

### Metriken

Die Integration trackt folgende Metriken im Lead Model:
- `email_sent_count` - Anzahl gesendeter Emails
- `email_opens` - Anzahl Email-Öffnungen
- `email_clicks` - Anzahl Link-Klicks
- `last_email_at` - Zeitstempel der letzten Email

## Best Practices

1. **Template Testing**: Teste Email-Templates vor Produktions-Deployment
2. **List Management**: Halte Listen sauber und segmentiert
3. **Monitoring**: Überwache Bounce-Raten und Email-Performance
4. **Rate Limits**: Brevo hat API Rate Limits - achte auf Bulk-Operationen
5. **GDPR Compliance**: Stelle sicher, dass Opt-Ins dokumentiert sind

## Support

Bei Fragen oder Problemen:
1. Prüfe die Logs: `grep "Brevo" logs/django.log`
2. Teste API-Zugriff: `python manage.py shell` und teste Funktionen
3. Prüfe Brevo Dashboard für Email-Status
4. Kontaktiere Brevo Support bei API-Problemen

## Weitere Ressourcen

- [Brevo API Dokumentation](https://developers.brevo.com/)
- [sib-api-v3-sdk GitHub](https://github.com/sendinblue/APIv3-python-library)
- [Django Signals Dokumentation](https://docs.djangoproject.com/en/4.2/topics/signals/)
