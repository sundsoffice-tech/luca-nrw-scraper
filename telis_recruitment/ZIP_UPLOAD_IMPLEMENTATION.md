# ZIP-Upload Implementation für Multipage-Projekte

## Übersicht

Diese Implementation ermöglicht das Hochladen von kompletten HTML/CSS/JS-Projekten als ZIP-Dateien, die automatisch in das Landing Page System importiert werden.

## Implementierte Features

### 1. Project Model (`pages/models.py`)
- **Container für Multipage-Projekte** (Websites, Spiele, Web-Apps)
- Felder:
  - `name`: Projektname
  - `slug`: URL-freundlicher Identifier
  - `project_type`: Typ (website, game, app, landing)
  - `description`: Projektbeschreibung
  - `static_path`: Pfad zu statischen Dateien
  - `main_page`: Referenz zur Hauptseite (index.html)
  - `navigation`: JSON-Struktur für Navigation
  - `is_deployed`: Deployment-Status
  - `deployed_url`: URL der deployed Version
  - Timestamps und Benutzer-Tracking

### 2. LandingPage Erweiterung
- Neues Feld `project`: ForeignKey zu Project
- Ermöglicht Zuordnung von einzelnen Seiten zu Projekten

### 3. ZIP-Upload Funktionalität

#### Upload View (`upload_project`)
- **Sicherheit:**
  - Maximale Dateigröße: 50MB
  - Erlaubte Dateitypen: .html, .css, .js, .jpg, .png, .svg, .woff, etc.
  - Path-Traversal-Schutz beim Entpacken
  - CSRF-Protection
  - Staff-only Zugriff

- **Funktionsweise:**
  1. ZIP-Datei hochladen
  2. Validierung (Größe, Dateitypen)
  3. Extraktion nach `MEDIA_ROOT/projects/{project_slug}/`
  4. Scannen nach HTML-Dateien
  5. Erstellen eines Project-Objekts
  6. Erstellen einer LandingPage pro HTML-Datei
  7. Verlinkung aller Seiten zum Project
  8. Setzen von index.html als Hauptseite

### 4. Quick-Create UI

#### Interface (`quick_create.html`)
Tabbed-Interface mit 4 Tabs:

1. **Code einfügen**: HTML/CSS/JS direkt eingeben
2. **ZIP hochladen**: Drag & Drop für ZIP-Dateien
3. **Template wählen**: Aus vorhandenen Templates wählen
4. **KI-Prompt**: Placeholder für zukünftige KI-Integration

Features:
- Drag & Drop für ZIP-Dateien
- Upload-Progress-Anzeige
- File-Info-Display
- Responsive Design

### 5. Projektverwaltung

#### Project List (`project_list.html`)
- Grid-Ansicht aller Projekte
- Anzeige von:
  - Projektname und Typ
  - Anzahl der Seiten
  - Deployment-Status
  - Erstellungsdatum und Ersteller
- Aktionen: Details anzeigen, Löschen

#### Project Detail (`project_detail.html`)
- Detaillierte Projektinformationen
- Liste aller zugehörigen Seiten
- Hauptseiten-Anzeige
- Statistiken (Seitenanzahl, Erstellungsdatum, etc.)
- Aktionen: Bearbeiten, Löschen

#### Project Delete
- Löscht Projekt und alle zugehörigen Seiten
- Entfernt auch die Dateien vom Server
- Cascade-Delete für alle verlinkten Objekte

### 6. URL-Routing

Neue Routes in `pages/urls.py`:
```python
path('quick-create/', views.quick_create, name='quick-create')
path('upload-project/', views.upload_project, name='upload-project')
path('projects/', views.project_list, name='project-list')
path('projects/<slug:slug>/', views.project_detail, name='project-detail')
path('projects/<slug:slug>/delete/', views.project_delete, name='project-delete')
```

### 7. Admin Integration

#### Project Admin
- Liste: Name, Slug, Typ, Seitenanzahl, Ersteller, Datum
- Filter: Projekttyp, Deployment-Status, Ersteller
- Inline: Zugehörige LandingPages
- Custom Actions: Projekt-Detail-Link

### 8. Migration

Migration `0009_project_landingpage_project.py`:
- Erstellt Project-Tabelle
- Fügt project-ForeignKey zu LandingPage hinzu

## Sicherheit

### Implementierte Sicherheitsmaßnahmen:

1. **CSRF-Protection**: Alle POST-Endpoints
2. **Staff-only Zugriff**: Alle neuen Views
3. **Dateitypvalidierung**: Whitelist erlaubter Dateitypen
4. **Größenlimit**: 50MB Maximum
5. **Path-Traversal-Schutz**: Normalisierung und Validierung der Pfade
6. **XSS-Schutz**: escapejs-Filter in Templates
7. **Input-Validierung**: Slug-Generierung und -Validierung

### Code Quality:

- ✅ Keine CodeQL-Warnungen
- ✅ Code-Review bestanden
- ✅ Import-Struktur optimiert
- ✅ N+1-Query-Problem behoben (Annotation statt Loop)
- ✅ Python-Syntax validiert

## Verwendung

### ZIP-Upload:
1. Navigiere zu `/pages/quick-create/`
2. Wähle Tab "ZIP hochladen"
3. Gib Projektname, Typ und Beschreibung ein
4. Drag & Drop oder wähle ZIP-Datei aus
5. Klicke "Projekt hochladen"
6. System extrahiert, erstellt Seiten und leitet zu Projektdetails weiter

### Projektverwaltung:
1. Navigiere zu `/pages/projects/`
2. Siehe Liste aller Projekte
3. Klicke auf "Details" für detaillierte Ansicht
4. Bearbeite einzelne Seiten über den Builder
5. Lösche Projekte bei Bedarf

## Technische Details

### Dateistruktur:
```
MEDIA_ROOT/
  projects/
    {project-slug}/
      index.html
      css/
      js/
      images/
      ...
```

### Datenbank-Schema:

**Project**:
- id, name, slug, project_type, description
- static_path, main_page_id, navigation
- created_at, updated_at, created_by_id
- is_deployed, deployed_url

**LandingPage** (erweitert):
- ...existing fields...
- project_id (ForeignKey zu Project)

## Zukünftige Erweiterungen

- [ ] Code-Editor für direkte HTML/CSS/JS-Eingabe
- [ ] KI-Integration für automatische Landing Page Generierung
- [ ] Export-Funktion für Projekte
- [ ] Versionierung für Projekte
- [ ] Deployment-Integration
- [ ] Template-Erstellung aus bestehenden Projekten

## Testing

Empfohlene Testszenarien:
1. ZIP-Upload mit verschiedenen Projekttypen
2. Upload von großen Dateien (>50MB) sollte abgelehnt werden
3. Upload mit nicht erlaubten Dateitypen
4. Upload mit path-traversal-Versuchen
5. Projekt-Löschung und Verifizierung der Cascade-Delete
6. UI-Testing aller Tabs in Quick-Create
7. Performance-Testing bei vielen Projekten

## Support

Bei Fragen oder Problemen:
- Siehe Admin-Interface unter `/admin/pages/project/`
- Logs prüfen für Error-Messages
- Migration ausführen: `python manage.py migrate pages`
