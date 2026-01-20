# Form Builder - Formular-Builder

## Übersicht

Der Form Builder ist ein visueller Drag-and-Drop-Editor zum Erstellen benutzerdefinierter Formulare für das LUCA CRM-System. Mit diesem Tool können Sie dynamische Formulare erstellen, konfigurieren und in Ihre Lead-Generierung integrieren.

## Features

### ✨ Hauptfunktionen

- **Visueller Drag-and-Drop-Editor**: Intuitive Benutzeroberfläche zum Erstellen von Formularen
- **Flexible Feldtypen**: 
  - 📝 Text Input (Einzeiliger Text)
  - 📧 Email Input (mit Validierung)
  - 📞 Phone Input (Telefonnummer)
  - 📄 Text Area (Mehrzeiliger Text)
  - ▼ Dropdown (Auswahlliste)
  - ☑️ Checkbox (Ja/Nein-Option)
  - 🔘 Radio Buttons (Einzelauswahl)
  - 📎 File Upload (Datei-Upload)
  - 📅 Date Picker (Datumsauswahl)
  - 🔢 Number Input (Zahleneingabe)

- **Feldkonfiguration**:
  - Feldbezeichnung anpassen
  - Platzhaltertext definieren
  - Hilfetext hinzufügen
  - Pflichtfelder markieren
  - Validierungsregeln festlegen
  - Feldbreite anpassen (Vollbreite, Halb, Drittel)

- **Backend-Integration**:
  - Automatische Lead-Erstellung aus Formular-Submissions
  - E-Mail-Benachrichtigungen bei neuen Einreichungen
  - Speicherung aller Submissions mit Metadaten
  - API-Endpunkte für externe Integrationen

## Verwendung

### 1. Formular erstellen

1. Navigieren Sie zu **CRM → Form Builder**
2. Klicken Sie auf **"➕ Create New Form"**
3. Geben Sie einen Namen und eine Beschreibung ein
4. Klicken Sie auf **"Create Form"**

### 2. Felder hinzufügen

1. Im Form Builder werden links die verfügbaren Feldtypen angezeigt
2. Klicken Sie auf einen Feldtyp, um ihn zum Formular hinzuzufügen
3. Das Feld erscheint in der Mitte im Formular-Canvas
4. Klicken Sie auf ein Feld, um seine Eigenschaften rechts zu bearbeiten

### 3. Felder konfigurieren

Im Properties-Panel können Sie folgende Einstellungen vornehmen:

- **Label**: Beschriftung des Feldes
- **Field Name**: Interner Name für Backend-Verarbeitung
- **Placeholder**: Platzhaltertext
- **Help Text**: Hilfetext unter dem Feld
- **Options**: Optionen für Dropdown/Radio/Checkbox (falls zutreffend)
- **Required**: Pflichtfeld-Status
- **Width**: Feldbreite (full, half, third)

### 4. Formular speichern

Klicken Sie auf **"💾 Save Form"**, um Ihre Änderungen zu speichern.

### 5. Formular testen

Klicken Sie auf **"👁️ Preview"**, um das Formular zu testen. Im Preview-Modus können Sie sehen, wie das Formular für Benutzer aussieht.

### 6. Formular veröffentlichen

1. Gehen Sie zu den Formular-Einstellungen (⚙️ Settings)
2. Ändern Sie den Status auf **"Published"**
3. Optional: Konfigurieren Sie Integrationen
4. Speichern Sie die Einstellungen

## Backend-Integration

### Lead-Erstellung

Wenn **"Save to Leads"** aktiviert ist, wird automatisch ein Lead-Datensatz erstellt:

```python
# Automatisch erstellte Felder
{
    'name': form_data.get('name'),
    'email': form_data.get('email'),
    'telefon': form_data.get('phone'),
    'source': 'form',
    'form_name': form.name
}
```

### E-Mail-Benachrichtigungen

Aktivieren Sie **"Send email notification"** und geben Sie eine E-Mail-Adresse an, um bei jeder Submission benachrichtigt zu werden.

### API-Endpunkte

#### Formular-Submission (Öffentlich)

```bash
POST /crm/forms/api/<slug>/submit/
Content-Type: application/json

{
    "name": "Max Mustermann",
    "email": "max@example.com",
    "phone": "+49123456789",
    "message": "Kontaktanfrage"
}
```

Antwort:
```json
{
    "success": true,
    "message": "Thank you for your submission!",
    "redirect_url": ""
}
```

#### Felder abrufen

```bash
GET /crm/forms/api/<slug>/fields/
```

## Formular einbetten

### iFrame

```html
<iframe 
    src="http://your-domain.com/crm/forms/<slug>/preview/" 
    width="100%" 
    height="600" 
    frameborder="0">
</iframe>
```

### Direkt-Link

```
http://your-domain.com/crm/forms/<slug>/preview/
```

## Submissions verwalten

1. Navigieren Sie zu **CRM → Form Builder**
2. Klicken Sie auf das Formular
3. Klicken Sie auf **"📊 Submissions"**
4. Hier sehen Sie alle eingereichten Formulare mit:
   - Datum und Uhrzeit
   - Vorschau der Daten
   - Lead-Status (falls erstellt)
   - IP-Adresse und User Agent

## Best Practices

### Formular-Design

- ✅ Verwenden Sie klare, prägnante Feldbezeichnungen
- ✅ Fügen Sie Hilfetext für komplexe Felder hinzu
- ✅ Markieren Sie Pflichtfelder deutlich
- ✅ Gruppieren Sie zusammengehörige Felder
- ✅ Verwenden Sie sinnvolle Feldbreiten

### Performance

- ✅ Begrenzen Sie die Anzahl der Felder auf das Notwendige
- ✅ Verwenden Sie Validierung, um unnötige Submissions zu vermeiden
- ✅ Testen Sie Formulare vor der Veröffentlichung

### Sicherheit

- ✅ Alle Formulare sind CSRF-geschützt
- ✅ Eingaben werden validiert
- ✅ Submissions werden mit IP-Adresse geloggt
- ✅ Nur authentifizierte Benutzer können Formulare erstellen/bearbeiten

## Technische Details

### Modelle

- **Form**: Hauptformular mit Konfiguration
- **FormField**: Einzelnes Formularfeld mit Eigenschaften
- **FormSubmission**: Gespeicherte Formular-Einreichung

### Dateien

- `forms/models.py`: Django-Modelle
- `forms/views.py`: View-Logik
- `forms/urls.py`: URL-Routen
- `forms/admin.py`: Django-Admin-Integration
- `forms/templates/forms/`: HTML-Templates

### Datenbank-Migrations

```bash
python manage.py makemigrations forms
python manage.py migrate forms
```

## Fehlerbehebung

### Formular wird nicht gespeichert

- Überprüfen Sie die Browser-Konsole auf JavaScript-Fehler
- Stellen Sie sicher, dass Sie angemeldet sind
- Überprüfen Sie die Django-Logs

### Felder werden nicht angezeigt

- Klicken Sie auf "Speichern" nach dem Hinzufügen von Feldern
- Aktualisieren Sie die Seite
- Überprüfen Sie die Browser-Konsole

### Submissions erscheinen nicht

- Überprüfen Sie, ob das Formular auf "Published" gesetzt ist
- Prüfen Sie die Django-Logs für Fehler
- Stellen Sie sicher, dass CSRF-Token korrekt ist

## Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Dokumentation
2. Prüfen Sie die Django-Logs
3. Erstellen Sie ein GitHub-Issue

## Changelog

### Version 1.0.0 (2026-01-20)
- ✨ Initiale Implementierung
- 🎨 Visueller Drag-and-Drop-Editor
- 📝 10 Feldtypen unterstützt
- 🔗 Lead-Integration
- 📧 E-Mail-Benachrichtigungen
- 🔒 Sicherheitsfeatures
