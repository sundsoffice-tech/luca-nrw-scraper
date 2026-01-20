# Editor-Stabilität & Zukunftssicherheit Implementation

## Übersicht

Diese Implementierung adressiert die Anforderungen für eine zukunftssichere und skalierbare Builder-Architektur:

1. ✅ **Saubere Trennung von Daten, Layout und Logik**
2. ✅ **Undo/Redo-System**
3. ✅ **Versionierung**
4. ✅ **Sichere Speicherung aller Änderungen**

## Architektur-Änderungen

### 1. Unified Version Control System

#### Neue Modelle

**ChangeLog** (`telis_recruitment/pages/models.py`)
- Unified change tracking für alle Content-Änderungen
- Transaction grouping (mehrere Änderungen in einer logischen Operation)
- Content integrity verification (SHA256 hashing)
- Snapshot/Release support
- Delta storage capability

```python
class ChangeLog(models.Model):
    landing_page = ForeignKey('LandingPage')
    transaction_id = UUIDField()  # Gruppiert zusammenhängende Änderungen
    change_type = CharField(CHANGE_TYPE_CHOICES)
    target_path = CharField()  # Betroffene Datei/Komponente
    version = PositiveIntegerField()
    
    # Content storage
    content_before = TextField()  # Für Undo
    content_after = TextField()   # Für Redo
    content_hash = CharField()     # SHA256 für Integrität
    
    # Metadata & Tagging
    note = CharField()
    tags = JSONField()
    is_snapshot = BooleanField()
    snapshot_name = CharField()
```

**UndoRedoStack** (`telis_recruitment/pages/models.py`)
- Per-User, per-Page Undo/Redo stacks
- Session-based state management
- Separate undo und redo stacks

```python
class UndoRedoStack(models.Model):
    landing_page = ForeignKey('LandingPage')
    user = ForeignKey(User)
    session_key = CharField()
    
    # Stack state
    undo_stack = JSONField()  # Liste von transaction IDs
    redo_stack = JSONField()  # Liste von transaction IDs
    current_version = PositiveIntegerField()
    max_version = PositiveIntegerField()
```

**VersionSnapshot** (`telis_recruitment/pages/models.py`)
- Named snapshots für wichtige Versionen
- Semantic versioning support
- Release management

```python
class VersionSnapshot(models.Model):
    landing_page = ForeignKey('LandingPage')
    name = CharField()  # z.B. "v1.0.0", "Backup vor Redesign"
    snapshot_type = CharField(SNAPSHOT_TYPE_CHOICES)
    changelog_version = ForeignKey(ChangeLog)
    
    # Semantic versioning
    semver_major = PositiveIntegerField()
    semver_minor = PositiveIntegerField()
    semver_patch = PositiveIntegerField()
```

### 2. Service Layer

#### ChangeLogService (`telis_recruitment/pages/services/changelog_service.py`)

Hauptfunktionen:
- `create_change()` - Einzelne Änderung erfassen
- `create_transaction()` - Multiple Änderungen als Transaction
- `get_versions()` - Version History abrufen
- `restore_version()` - Zu Version zurückkehren
- `create_snapshot()` - Snapshot/Release erstellen
- Content integrity verification

#### UndoRedoService (`telis_recruitment/pages/services/changelog_service.py`)

Hauptfunktionen:
- `undo()` - Letzte Transaction rückgängig machen
- `redo()` - Rückgängig gemachte Transaction wiederherstellen
- `push_transaction()` - Neue Transaction auf Stack
- `get_stack_state()` - Aktueller Stack-Status

### 3. API Endpoints

Neue API Endpoints in `telis_recruitment/pages/views_changelog.py`:

#### Undo/Redo
- `POST /api/<slug>/undo/` - Undo letzte Änderung
- `POST /api/<slug>/redo/` - Redo letzte rückgängig gemachte Änderung
- `GET /api/<slug>/undo-redo/state/` - Aktueller Undo/Redo Status

#### Changelog
- `GET /api/<slug>/changelog/history/` - Version History
- `GET /api/<slug>/changelog/<version>/` - Details zu Version
- `POST /api/<slug>/changelog/restore/` - Zu Version zurückkehren

#### Snapshots
- `GET /api/<slug>/snapshots/` - Liste alle Snapshots
- `POST /api/<slug>/snapshots/create/` - Neuen Snapshot erstellen
- `POST /api/<slug>/snapshots/<id>/restore/` - Zu Snapshot zurückkehren

### 4. Daten/Logic/Layout Separation

#### Vorher
```
models.py (30+ Klassen, gemischt)
├── Content Models (html, css)
├── Metadata Models (SEO, hosting)
├── Version Models (PageVersion, FileVersion)
└── Settings Models
```

#### Nachher
```
models/
├── changelog.py (ChangeLog, UndoRedoStack, VersionSnapshot)
└── [weitere Aufteilungen möglich]

services/
├── changelog_service.py (Version control logic)
├── editor_service.py (File editing logic)
├── version_service.py (Legacy, wird ersetzt)
└── [weitere services]

views/
├── views.py (Main builder views)
├── views_editor.py (Editor views)
├── views_changelog.py (NEW: Changelog/Undo/Redo views)
└── [weitere views]
```

## Vorteile der neuen Architektur

### 1. Unified Version Control
- **Ein System** statt zwei (PageVersion + FileVersion)
- Transaction grouping für atomare Multi-File Änderungen
- Content integrity durch SHA256 hashing
- Efficient storage durch Delta-Support (vorbereitet)

### 2. Echtes Undo/Redo
- **Stack-basiert** statt point-in-time restoration
- Per-User, per-Session isolation
- Separate Undo/Redo stacks
- Keyboard shortcuts ready (Ctrl+Z, Ctrl+Y)

### 3. Snapshot/Release Management
- Named snapshots für wichtige Versionen
- Semantic versioning support
- Tag-System für Kategorisierung
- Release workflows ready

### 4. Security & Integrity
- SHA256 hashing für Content verification
- Transaction-based changes (ACID properties)
- Comprehensive audit trail
- User tracking für alle Änderungen

### 5. Scalability
- Indexes für Performance
- Version cleanup (MAX_VERSIONS_PER_PAGE = 100)
- Delta storage vorbereitet
- Transaction grouping reduziert DB load

## Migration Path

### Phase 1: Neue Modelle ✅
- ChangeLog, UndoRedoStack, VersionSnapshot hinzugefügt
- Migrationen erstellt

### Phase 2: Service Layer ✅
- ChangeLogService implementiert
- UndoRedoService implementiert
- API Endpoints erstellt

### Phase 3: Integration (TODO)
- [ ] Builder UI Undo/Redo buttons
- [ ] Keyboard shortcuts (Ctrl+Z, Ctrl+Y)
- [ ] Version History UI
- [ ] Snapshot Management UI

### Phase 4: Migration von Alt zu Neu (TODO)
- [ ] Migrate PageVersion → ChangeLog
- [ ] Migrate FileVersion → ChangeLog
- [ ] Update existing editor_service to use ChangeLogService
- [ ] Deprecate old version models

### Phase 5: Testing (TODO)
- [ ] Unit tests für ChangeLogService
- [ ] Unit tests für UndoRedoService
- [ ] Integration tests
- [ ] Performance tests

## Verwendung

### Transaction mit mehreren Änderungen

```python
from pages.services.changelog_service import ChangeLogService

service = ChangeLogService(landing_page)

# Mehrere Änderungen in einer Transaction
transaction_id, changelogs = service.create_transaction(
    changes=[
        {
            'change_type': 'file_edit',
            'target_path': 'css/style.css',
            'content_before': old_css,
            'content_after': new_css,
        },
        {
            'change_type': 'file_edit',
            'target_path': 'js/script.js',
            'content_before': old_js,
            'content_after': new_js,
        }
    ],
    user=request.user,
    note='Updated styling and scripts'
)
```

### Undo/Redo

```python
from pages.services.changelog_service import UndoRedoService

service = UndoRedoService(landing_page, user, session_key)

# Undo
result = service.undo()
if result:
    # Apply changes from result['changes']
    pass

# Redo
result = service.redo()
if result:
    # Apply changes from result['changes']
    pass

# Check state
state = service.get_stack_state()
# {
#     'can_undo': True,
#     'can_redo': False,
#     'current_version': 42,
#     'undo_count': 5,
#     'redo_count': 0
# }
```

### Snapshots erstellen

```python
from pages.services.changelog_service import ChangeLogService

service = ChangeLogService(landing_page)

# Release snapshot
snapshot = service.create_snapshot(
    name='Release 1.0.0',
    snapshot_type='release',
    description='First stable release',
    user=request.user,
    semver=(1, 0, 0, '')  # Major, Minor, Patch, Prerelease
)

# Backup snapshot
snapshot = service.create_snapshot(
    name='Backup before redesign',
    snapshot_type='backup',
    description='Backup before major redesign',
    user=request.user,
    tags=['important', 'redesign']
)
```

## API Beispiele

### Undo

```bash
curl -X POST http://localhost:8000/crm/pages/api/my-page/undo/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..."
```

Response:
```json
{
  "success": true,
  "message": "Changes undone",
  "data": {
    "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
    "changes": [
      {
        "target_path": "css/style.css",
        "content": "...",
        "change_type": "file_edit"
      }
    ],
    "can_undo": true,
    "can_redo": true
  }
}
```

### Changelog History

```bash
curl http://localhost:8000/crm/pages/api/my-page/changelog/history/?limit=10 \
  -H "Cookie: sessionid=..."
```

Response:
```json
{
  "success": true,
  "data": {
    "changelogs": [
      {
        "version": 42,
        "change_type": "file_edit",
        "target_path": "css/style.css",
        "note": "Updated header styling",
        "tags": [],
        "is_snapshot": false,
        "transaction_id": "...",
        "created_by": "admin",
        "created_at": "2026-01-20T22:00:00Z",
        "metadata": {}
      }
    ],
    "count": 10
  }
}
```

### Create Snapshot

```bash
curl -X POST http://localhost:8000/crm/pages/api/my-page/snapshots/create/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{
    "name": "Release 1.0.0",
    "snapshot_type": "release",
    "description": "First stable release",
    "semver": {
      "major": 1,
      "minor": 0,
      "patch": 0
    }
  }'
```

## Sicherheit

### Content Integrity
- SHA256 hashing für alle content_after Felder
- `verify_integrity()` Methode für Validierung
- Automatische Hash-Generierung beim Speichern

### Access Control
- Alle Endpoints staff_member_required
- User tracking für alle Änderungen
- Session-based isolation für Undo/Redo

### Transaction Safety
- Django `@transaction.atomic` für alle write operations
- ACID properties für Multi-Change transactions
- Rollback bei Fehlern

## Performance

### Indexes
```python
class ChangeLog:
    class Meta:
        indexes = [
            Index(fields=['landing_page', '-version']),
            Index(fields=['transaction_id']),
            Index(fields=['landing_page', 'is_snapshot']),
            Index(fields=['created_at']),
        ]
```

### Cleanup
- Automatisches Cleanup alter Versionen
- `MAX_VERSIONS_PER_PAGE = 100` (konfigurierbar)
- Snapshots werden nie gelöscht

### Future Optimizations
- Delta storage statt full content (vorbereitet)
- Content compression
- Async cleanup tasks

## Zusammenfassung

Die neue Architektur bietet:

✅ **Unified Version Control** - Ein System für alle Changes  
✅ **Echtes Undo/Redo** - Stack-basiert mit Session-Isolation  
✅ **Snapshot Management** - Named versions mit semantic versioning  
✅ **Content Integrity** - SHA256 hashing  
✅ **Transaction Grouping** - Atomare Multi-Change operations  
✅ **Comprehensive Audit Trail** - Vollständige Change History  
✅ **Scalable Architecture** - Indexes, cleanup, delta-ready  
✅ **Secure** - Access control, integrity checks, ACID transactions  

Die Implementierung ist backward-kompatibel und kann schrittweise eingeführt werden.
