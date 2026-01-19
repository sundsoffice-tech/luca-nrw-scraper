# Positions-Einstellungen - Design & Information Architecture Specification

## Document Purpose
This document defines the design, information architecture (IA), navigation structure, and UX guidelines for the **Positions-Einstellungen** (Position Settings) section of the LUCA recruitment system. It serves as the foundation for implementation planning, wireframing, and development.

---

## 1. Design Principles

### 1.1 Hierarchy & Organization
- **Three-level hierarchy**: Settings → Category → Detail page
- Clear parent-child relationships with consistent visual indicators
- Logical grouping of related functionality
- Progressive disclosure: show essentials first, advanced features on demand

### 1.2 Naming Consistency
- Use consistent German terminology across all interfaces
- Standardize action verbs: "Erstellen" (Create), "Bearbeiten" (Edit), "Löschen" (Delete), "Duplizieren" (Duplicate)
- Clear section headings with descriptive labels
- Avoid technical jargon; prefer business-friendly terms

### 1.3 Navigation & Breadcrumbs
- **Breadcrumb trail**: Always show `Einstellungen > Positionen > [Current Page]`
- Breadcrumbs are clickable for quick navigation back
- Current location highlighted in sidebar navigation
- Persistent left sidebar for settings categories

### 1.4 Tabs vs. Long Scroll
- **Use tabs** for functionally distinct sections within position editing
- **Use accordion/collapse** for related subsections within a tab
- **Long scroll** acceptable for simple read-only pages or when linear flow is important
- Tab selection persists in URL hash for deep linking

### 1.5 Search & Filter
- **Global search**: Quick find positions by title, ID, or keywords
- **Faceted filters**: Status, category, location, owner, date ranges
- Filter state saved in URL parameters for bookmarking
- "Save Filter" button to create reusable saved views

### 1.6 Inline Help & Guidance
- Tooltip icons (ℹ️) next to complex fields with explanations
- Context-sensitive help links to documentation
- Placeholder text with examples for input fields
- Validation messages inline and non-intrusive
- Empty state guidance with actionable suggestions

---

## 2. Sitemap & Information Architecture

```
Einstellungen (Settings)
└── Positionen (Positions)
    ├── Übersicht (Overview)
    │   ├── List all positions with filters
    │   ├── Quick actions (Create, Duplicate, Delete)
    │   └── Saved views
    │
    ├── Position erstellen/bearbeiten (Create/Edit Position)
    │   ├── Tab: Basisdaten (Basic Data)
    │   ├── Tab: Anforderungen & Kriterien (Requirements & Criteria)
    │   ├── Tab: Workflow & Status (Workflow & Status)
    │   ├── Tab: Berechtigungen & Sichtbarkeit (Permissions & Visibility)
    │   ├── Tab: Automationen & Benachrichtigungen (Automations & Notifications)
    │   ├── Tab: Veröffentlichung/Integrationen (Publication/Integrations)
    │   ├── Tab: Anhänge/Vorlagen (Attachments/Templates)
    │   └── Tab: Historie/Protokoll (History/Log)
    │
    ├── Kategorien & Taxonomien (Categories & Taxonomies)
    │   ├── Positionskategorien (Position Categories)
    │   ├── Tags & Skills (Tags & Skills)
    │   └── Standorte (Locations)
    │
    ├── Vorlagen (Templates)
    │   ├── Positionsvorlagen (Position Templates)
    │   ├── Textbausteine (Text Snippets)
    │   └── Mehrsprachige Inhalte (Multi-language Content)
    │
    ├── Workflows (Workflows)
    │   ├── Status-Definitionen (Status Definitions)
    │   ├── Übergänge & Regeln (Transitions & Rules)
    │   └── Genehmigungsprozesse (Approval Processes)
    │
    ├── Berechtigungen & Sichtbarkeit (Permissions & Visibility)
    │   ├── Rollen & Rechte (Roles & Rights)
    │   ├── Sichtbarkeitsregeln (Visibility Rules)
    │   └── Datenschutz-Einstellungen (Privacy Settings)
    │
    ├── Automationen & Integrationen (Automations & Integrations)
    │   ├── Benachrichtigungen (Notifications)
    │   ├── Webhooks (Webhooks)
    │   ├── Veröffentlichungskanäle (Publication Channels)
    │   └── Event-Log & Retry (Event Log & Retry)
    │
    ├── Audit & Historie (Audit & History)
    │   ├── Änderungsprotokoll (Change Log)
    │   ├── Benutzeraktivitäten (User Activities)
    │   └── Versionsverlauf (Version History)
    │
    ├── Datenqualität & Validierung (Data Quality & Validation)
    │   ├── Duplikatsprüfung (Duplicate Check)
    │   ├── Validierungsregeln (Validation Rules)
    │   └── DSGVO-Compliance (GDPR Compliance)
    │
    └── Import/Export (Import/Export)
        ├── Import-Assistent (Import Wizard)
        ├── Export-Konfiguration (Export Configuration)
        └── Mapping-Vorlagen (Mapping Templates)
```

---

## 3. Detail Page Layout: Position bearbeiten (Edit Position)

### 3.1 Page Header
- **Position Title** (editable inline with auto-save indicator)
- **Status Badge** (e.g., "Entwurf", "Aktiv", "Archiviert")
- **Action Buttons**: Speichern (Save), Verwerfen (Discard), Vorschau (Preview), Duplizieren (Duplicate)
- **Last Modified**: "Zuletzt geändert: [Date] von [User]"

### 3.2 Tab Structure

#### Tab 1: Basisdaten (Basic Data)
**Purpose**: Core information about the position.

**Fields**:
- **Positionstitel** (Position Title) - Text input, required
- **Interne Bezeichnung** (Internal Name) - Text input, optional
- **Kategorie** (Category) - Dropdown, required
- **Standort(e)** (Location(s)) - Multi-select dropdown
- **Abteilung** (Department) - Dropdown
- **Beschäftigungsart** (Employment Type) - Radio buttons (Vollzeit, Teilzeit, Freelance, etc.)
- **Gehaltsspanne** (Salary Range) - Number inputs (von/bis) with currency
- **Kurzbeschreibung** (Short Description) - Textarea, max 200 chars, shown in previews
- **Vollständige Beschreibung** (Full Description) - Rich text editor (WYSIWYG)
- **Verantwortlicher** (Owner) - User picker, required

#### Tab 2: Anforderungen & Kriterien (Requirements & Criteria)
**Purpose**: Define qualifications, skills, and screening criteria.

**Sections**:
- **Muss-Kriterien** (Must-Have Criteria) - Checklist builder
  - Ausbildung (Education)
  - Berufserfahrung (Years of Experience)
  - Pflichtfähigkeiten (Required Skills) - Multi-select tags
- **Wünschenswerte Kriterien** (Nice-to-Have Criteria) - Checklist builder
  - Zusatzqualifikationen (Additional Qualifications)
  - Soft Skills
- **Automatische Bewertung** (Automatic Scoring) - Toggle on/off
  - Scoring-Gewichtung (Scoring Weights) - Sliders for each criterion

#### Tab 3: Workflow & Status (Workflow & Status)
**Purpose**: Control position lifecycle and approval process.

**Fields**:
- **Aktueller Status** (Current Status) - Readonly, badge
- **Nächster Status** (Next Status) - Dropdown with available transitions
- **Workflow-Vorlage** (Workflow Template) - Dropdown, defines allowed transitions
- **Genehmiger** (Approvers) - User/Group picker
- **Freigabe-Datum** (Approval Date) - Date picker
- **Ablaufdatum** (Expiration Date) - Date picker with auto-close toggle
- **Status-Notizen** (Status Notes) - Textarea for transition comments

#### Tab 4: Berechtigungen & Sichtbarkeit (Permissions & Visibility)
**Purpose**: Define who can see and edit this position.

**Sections**:
- **Sichtbarkeit** (Visibility)
  - Öffentlich (Public) - Radio button
  - Intern (Internal only) - Radio button
  - Eingeschränkt (Restricted) - Radio button + User/Group picker
- **Bearbeiter** (Editors)
  - Multi-select user/group picker
  - Rechte: Lesen (Read), Bearbeiten (Edit), Löschen (Delete)
- **Datenschutz** (Privacy)
  - Anonyme Bewerbung möglich (Anonymous Application) - Toggle
  - DSGVO-konforme Datenverarbeitung (GDPR-compliant processing) - Checkbox

#### Tab 5: Automationen & Benachrichtigungen (Automations & Notifications)
**Purpose**: Configure automated actions and notifications.

**Sections**:
- **E-Mail-Benachrichtigungen** (Email Notifications)
  - Bei Statusänderung (On Status Change) - Checkbox + Empfänger (Recipients)
  - Bei neuer Bewerbung (On New Application) - Checkbox + Empfänger
  - Erinnerungen (Reminders) - Checkbox + Zeitabstand (Interval)
- **Automatische Aktionen** (Automatic Actions)
  - Auto-Ablehnung nach Frist (Auto-Reject After Deadline) - Toggle + Days
  - Auto-Veröffentlichung (Auto-Publish) - Date/Time picker
- **Webhooks** (Webhooks)
  - URL-Liste (URL List) - Add/Remove webhook endpoints
  - Event-Auswahl (Event Selection) - Checkboxes for events to trigger

#### Tab 6: Veröffentlichung/Integrationen (Publication/Integrations)
**Purpose**: Configure where and how the position is published.

**Sections**:
- **Veröffentlichungskanäle** (Publication Channels)
  - Website - Checkbox + URL preview
  - Karriereseite (Career Page) - Checkbox
  - Jobbörsen (Job Boards) - Multi-select (StepStone, Indeed, LinkedIn, etc.)
- **Integration-Einstellungen** (Integration Settings)
  - API-Sync - Toggle + Last sync timestamp
  - Export-Format (Export Format) - Dropdown (JSON, XML, CSV)
- **SEO & Tracking**
  - Meta-Title - Text input
  - Meta-Description - Textarea
  - Tracking-Codes (Tracking Codes) - Textarea for analytics snippets

#### Tab 7: Anhänge/Vorlagen (Attachments/Templates)
**Purpose**: Manage documents and templates associated with the position.

**Sections**:
- **Anhänge** (Attachments)
  - File upload area (drag-and-drop)
  - List of uploaded files with name, size, date, delete action
- **Vorlagen verwenden** (Use Templates)
  - Dropdown: Positionsvorlage auswählen (Select Position Template)
  - Button: Vorlage anwenden (Apply Template) - Fills form with template data
- **Textbausteine** (Text Snippets)
  - Dropdown: Snippet auswählen (Select Snippet)
  - Button: Einfügen (Insert) - Adds to description at cursor position

#### Tab 8: Historie/Protokoll (History/Log)
**Purpose**: Audit trail and version history.

**Display**:
- **Timeline view** with entries:
  - Timestamp
  - User
  - Action (Erstellt, Geändert, Veröffentlicht, etc.)
  - Changed fields summary
  - Link to "Details anzeigen" (Show Details) - Opens modal with full diff
- **Filter**: By user, by action type, by date range
- **Export**: Button to export log as CSV/PDF

---

## 4. Overview Page: Positionen-Übersicht (Positions Overview)

### 4.1 Page Layout
- **Header**: "Positionen" + "Neue Position erstellen" button (primary action)
- **Toolbar**: Search bar, Filter button, Saved views dropdown, Export button
- **Table View**: Paginated list of positions

### 4.2 Table Columns
**Default visible columns**:
1. **Status** - Badge with color coding
2. **Titel** (Title) - Clickable link to edit page
3. **Kategorie** (Category) - Text label
4. **Standort** (Location) - Text label
5. **Verantwortlicher** (Owner) - User name + avatar
6. **Erstellt am** (Created On) - Date
7. **Aktualisiert am** (Updated On) - Date with tooltip showing who updated
8. **Aktionen** (Actions) - Dropdown with Bearbeiten (Edit), Duplizieren (Duplicate), Archivieren (Archive), Löschen (Delete)

**Optional columns** (user can add via column selector):
- Abteilung (Department)
- Gehaltsspanne (Salary Range)
- Bewerbungen (Applications Count)
- Sichtbarkeit (Visibility)

### 4.3 Filters
**Standard filters** (collapsible panel):
- **Status**: Multi-select checkboxes (Entwurf, Aktiv, Archiviert, etc.)
- **Kategorie**: Multi-select dropdown
- **Standort**: Multi-select dropdown
- **Verantwortlicher**: User picker
- **Erstellungsdatum**: Date range picker
- **Aktualisierungsdatum**: Date range picker

**Actions**:
- Button: "Filter zurücksetzen" (Reset Filters)
- Button: "Als Ansicht speichern" (Save as View) - Opens dialog to name the view

### 4.4 Bulk Actions
- **Selection**: Checkboxes on each row + "Select all" checkbox in header
- **Actions menu** (appears when ≥1 row selected):
  - Status ändern (Change Status) - Batch status update
  - Verantwortlichen ändern (Change Owner) - Batch owner reassignment
  - Export (Export) - Export selected positions as CSV/Excel
  - Löschen (Delete) - Batch delete with confirmation modal

### 4.5 Saved Views
- **Predefined views**:
  - Alle Positionen (All Positions)
  - Aktive Positionen (Active Positions)
  - Meine Positionen (My Positions)
  - Entwürfe (Drafts)
  - Abgelaufen (Expired)
- **Custom views**: User-created, saved filter combinations
- **View management**: Edit, delete, share with team

---

## 5. Taxonomies: Kategorien, Tags & Standorte

### 5.1 Positionskategorien (Position Categories)
**Purpose**: Hierarchical classification of position types.

**Structure**:
- Parent categories (e.g., "Vertrieb", "IT", "Marketing")
- Child categories (e.g., "Vertrieb" → "Account Manager", "Sales Engineer")
- Max 3 levels deep

**Fields**:
- **Name** - Text input, required
- **Parent-Kategorie** (Parent Category) - Dropdown, optional
- **Beschreibung** (Description) - Textarea
- **Icon** - Icon picker (optional)
- **Aktiv** (Active) - Toggle

**Management**:
- Drag-and-drop reordering
- Merge categories (reassign positions to new category)
- Bulk activate/deactivate

### 5.2 Tags & Skills (Tags & Skills)
**Purpose**: Flat, flexible labeling for skills, keywords, and qualifications.

**Structure**:
- No hierarchy, just flat tags
- Auto-suggest from existing tags
- Tag groups (e.g., "Technische Skills", "Soft Skills", "Zertifikate")

**Fields**:
- **Tag-Name** - Text input, required
- **Gruppe** (Group) - Dropdown, optional
- **Synonym(e)** (Synonyms) - Multi-input for alternative names
- **Verwendung** (Usage Count) - Readonly, shows # positions using this tag

**Management**:
- Merge tags (combine duplicates)
- Rename tag (updates all positions)
- Delete tag (with warning if in use)

### 5.3 Standorte (Locations)
**Purpose**: Geographic location management.

**Structure**:
- Hierarchical: Land (Country) → Region/Bundesland → Stadt (City) → Adresse (Address)
- Support for "Remote" and "Hybrid" flags

**Fields**:
- **Standortname** (Location Name) - Text input, required
- **Typ** (Type) - Dropdown (Büro, Remote, Hybrid)
- **Land** (Country) - Dropdown
- **Region/Bundesland** (Region/State) - Text input
- **Stadt** (City) - Text input
- **PLZ** (Postal Code) - Text input
- **Adresse** (Address) - Textarea
- **Google Maps Link** - URL input (auto-generates map embed)
- **Aktiv** (Active) - Toggle

**Management**:
- Geocoding integration (auto-fill lat/lon for map display)
- Merge locations (consolidate duplicate entries)
- Bulk import from CSV

---

## 6. Templates & Snippets

### 6.1 Positionsvorlagen (Position Templates)
**Purpose**: Reusable templates to speed up position creation.

**Structure**:
- Full position with all tabs pre-filled (except unique fields like title)
- Apply template copies all data to new position

**Fields**:
- **Vorlagenname** (Template Name) - Text input, required
- **Beschreibung** (Description) - Textarea
- **Kategorie** (Category) - Pre-filled
- **Alle Tabs** - Full position data structure
- **Verwendung** (Usage Count) - Readonly

**Management**:
- Create template from existing position ("Als Vorlage speichern" button)
- Edit template
- Duplicate template
- Preview template before applying

### 6.2 Textbausteine (Text Snippets Library)
**Purpose**: Reusable text blocks for descriptions, requirements, etc.

**Structure**:
- Short text blocks (e.g., benefit descriptions, company intro, legal disclaimers)
- Categorized by type (Einleitung, Aufgaben, Anforderungen, Benefits, Rechtliches)

**Fields**:
- **Snippet-Titel** (Snippet Title) - Text input, required
- **Kategorie** (Category) - Dropdown
- **Text** - Rich text editor
- **Platzhalter** (Placeholders) - Variables like {{position_title}}, {{location}}
- **Sprache** (Language) - Dropdown (DE, EN, etc.)

**Management**:
- Insert snippet into position description via button/shortcut
- Preview with placeholder substitution
- Version control for snippets

### 6.3 Mehrsprachigkeit (Multi-language Support)
**Purpose**: Manage position content in multiple languages.

**Approach**:
- Primary language: German (DE)
- Additional languages: English (EN), French (FR), etc.
- Translation workflow: Manual entry or AI-assisted translation

**Fields**:
- **Sprache** (Language) - Dropdown per field
- **Übersetzungsstatus** (Translation Status) - Badge (Vollständig, Teilweise, Fehlend)
- **Auto-Übersetzen** (Auto-Translate) - Button to use AI translation service

**Management**:
- Language switcher in position edit view
- Highlight missing translations
- Export/import translations as JSON/CSV for professional translators

---

## 7. Workflows & Permissions

### 7.1 Status-Definitionen (Status Definitions)
**Purpose**: Define lifecycle states for positions.

**Predefined statuses** (examples):
- **Entwurf** (Draft) - Initial creation, not visible
- **Zur Genehmigung** (Pending Approval) - Awaiting manager approval
- **Genehmigt** (Approved) - Ready to publish
- **Aktiv** (Active) - Published and accepting applications
- **Pausiert** (Paused) - Temporarily hidden
- **Geschlossen** (Closed) - No longer accepting applications
- **Archiviert** (Archived) - Historical record

**Fields** (per status):
- **Status-Name** - Text input, required
- **Farbe** (Color) - Color picker for badge
- **Beschreibung** (Description) - Textarea
- **Sichtbar für** (Visible To) - Dropdown (Alle, Nur intern, Nur Verantwortlicher)
- **Automatische Aktionen** (Automatic Actions) - E.g., "Archivieren nach 90 Tagen"

### 7.2 Übergänge & Regeln (Transitions & Rules)
**Purpose**: Control allowed status changes and conditions.

**Transition matrix**:
- Define which status can change to which other status
- E.g., "Entwurf" → "Zur Genehmigung" (allowed), "Aktiv" → "Entwurf" (not allowed)

**Fields** (per transition):
- **Von Status** (From Status) - Dropdown
- **Zu Status** (To Status) - Dropdown
- **Berechtigt** (Who Can Transition) - Role/User picker
- **Bedingungen** (Conditions) - E.g., "Pflichtfelder ausgefüllt"
- **Aktionen** (Actions) - E.g., "Benachrichtigung an Genehmiger senden"

**Visualization**:
- Flowchart view of workflow
- Highlight current position in workflow

### 7.3 Genehmigungsprozesse (Approval Processes)
**Purpose**: Multi-step approval before publishing.

**Structure**:
- Sequential approvals (one after another) or parallel (all must approve)
- Approval delegation (proxy approval if person unavailable)

**Fields**:
- **Genehmigungsstufe** (Approval Step) - Number
- **Genehmiger** (Approver) - User/Group picker
- **Typ** (Type) - Radio (Sequenziell, Parallel)
- **Pflicht** (Required) - Checkbox (if unchecked, can skip)
- **Zeitlimit** (Timeout) - Days until auto-escalation

**Management**:
- Visual approval timeline
- Email reminders to approvers
- History of approvals (who, when, decision)

### 7.4 Rollen & Rechte Matrix (Roles & Rights Matrix)
**Purpose**: Define permissions per role.

**Roles** (examples):
- **Admin** - Full access, all CRUD operations
- **Manager** - Create, edit, delete own positions + view all
- **Recruiter** - Create, edit own positions, view assigned
- **Leser** (Viewer) - Read-only access

**Permissions** (per role):
- Positionen erstellen (Create Positions) - Yes/No
- Positionen bearbeiten (Edit Positions) - Eigene/Alle (Own/All)
- Positionen löschen (Delete Positions) - Eigene/Alle
- Positionen veröffentlichen (Publish Positions) - Yes/No
- Einstellungen verwalten (Manage Settings) - Yes/No
- Berichte anzeigen (View Reports) - Yes/No

**Matrix view**:
- Table with roles as rows, permissions as columns
- Checkboxes for quick editing
- Export as CSV for documentation

---

## 8. Automations & Integrations

### 8.1 Benachrichtigungen (Notifications)
**Purpose**: Automated email/SMS alerts for events.

**Event types**:
- Position erstellt (Position Created)
- Position veröffentlicht (Position Published)
- Status geändert (Status Changed)
- Neue Bewerbung (New Application)
- Ablaufdatum nahe (Expiration Date Approaching)
- Genehmigung erforderlich (Approval Required)

**Configuration** (per event):
- **Empfänger** (Recipients) - User/Group picker or custom email list
- **Vorlage** (Template) - Email template with placeholders
- **Zeitpunkt** (Timing) - Sofort (Immediate) or Verzögert (Delayed)
- **Aktiv** (Active) - Toggle

**Management**:
- Test notification (send test email)
- Delivery log (success/failure)
- Retry failed notifications

### 8.2 Webhooks (Webhooks)
**Purpose**: HTTP callbacks to external systems on events.

**Event types** (same as notifications):
- Position lifecycle events
- Application events

**Configuration** (per webhook):
- **URL** - Text input, required (HTTPS enforced)
- **Events** - Multi-select checkboxes
- **HTTP-Methode** (HTTP Method) - Dropdown (POST, PUT, PATCH)
- **Header** - Key-value pairs for authentication
- **Payload-Format** (Payload Format) - Dropdown (JSON, XML)
- **Secret** - Text input for signature verification
- **Aktiv** (Active) - Toggle
- **Retry-Strategie** (Retry Strategy) - Dropdown (Exponential backoff, etc.)

**Management**:
- Test webhook (send test payload)
- Delivery log with response codes
- Retry failed webhooks manually

### 8.3 Veröffentlichung/Ziele (Publication Targets)
**Purpose**: Integrate with external job boards and career sites.

**Targets** (examples):
- StepStone
- Indeed
- LinkedIn Jobs
- Xing Jobs
- Company website (via API/RSS feed)

**Configuration** (per target):
- **Name** - Target name
- **API-Anmeldedaten** (API Credentials) - Encrypted storage
- **Mapping** - Field mapping (internal field → external field)
- **Automatische Synchronisation** (Auto-Sync) - Toggle + Interval
- **Status** - Connection status indicator (Connected, Error)

**Management**:
- Manual sync button
- Sync history with timestamps and results
- Error log with troubleshooting hints

### 8.4 Event-Log & Retry (Event Log & Retry)
**Purpose**: Audit trail for all automated actions.

**Log entries**:
- **Zeitstempel** (Timestamp)
- **Event-Typ** (Event Type) - E.g., "webhook_sent", "email_sent"
- **Ziel** (Target) - E.g., URL or email address
- **Status** - Success, Failure, Retry
- **Fehlerdetails** (Error Details) - If failed
- **Payload** - Request/response data (truncated)

**Actions**:
- Filter by event type, status, date range
- Retry failed event manually
- Export log as CSV

---

## 9. Audit & History, Data Quality

### 9.1 Änderungsprotokoll (Change Log)
**Purpose**: Track all changes to positions for compliance and debugging.

**Logged data**:
- **Zeitstempel** (Timestamp)
- **Benutzer** (User) - Who made the change
- **Aktion** (Action) - Created, Updated, Deleted, Status Changed, etc.
- **Feld** (Field) - Which field was changed
- **Alter Wert** (Old Value) - Previous value
- **Neuer Wert** (New Value) - Current value
- **IP-Adresse** (IP Address) - For security audit
- **User-Agent** - Browser/device info

**Display**:
- Timeline view (similar to Historie tab in position detail)
- Diff view for text fields (side-by-side comparison)
- Filter by user, date, action type

**Retention**:
- Configurable retention period (e.g., 2 years minimum for DSGVO)
- Archive old logs to cold storage

### 9.2 Duplikatsprüfung (Duplicate Detection)
**Purpose**: Prevent duplicate positions from being created.

**Detection criteria**:
- Exact title match
- Similar title (fuzzy matching, >80% similarity)
- Same category + location + date range overlap

**Workflow**:
- **On save**: Show warning modal if potential duplicate detected
- **List potential duplicates** with "Bearbeiten" (Edit) or "Trotzdem erstellen" (Create Anyway) options
- **Merge tool**: If duplicate confirmed, merge button combines positions

**Configuration**:
- Enable/disable duplicate detection
- Adjust similarity threshold (slider)
- Exclude certain categories from check

### 9.3 Validierungsregeln (Validation Rules)
**Purpose**: Enforce data quality standards.

**Rule types**:
- **Pflichtfelder** (Required Fields) - E.g., Title, Category, Owner
- **Format-Validierung** (Format Validation) - E.g., Email, URL, Phone
- **Bereichsprüfung** (Range Validation) - E.g., Salary min < max
- **Kreuz-Feld-Validierung** (Cross-Field Validation) - E.g., "End date must be after start date"
- **Benutzerdefinierte Regeln** (Custom Rules) - JavaScript expressions

**Configuration** (per rule):
- **Regel-Name** (Rule Name)
- **Feld** (Field) - Dropdown
- **Bedingung** (Condition) - Expression builder or code editor
- **Fehlermeldung** (Error Message) - Custom message to user
- **Schwere** (Severity) - Warning (can proceed) or Error (blocks save)
- **Aktiv** (Active) - Toggle

**Validation timing**:
- On field blur (immediate feedback)
- On save (comprehensive check)
- Batch validation (check all positions)

### 9.4 Datenschutz & DSGVO-Compliance (Privacy & GDPR Compliance)
**Purpose**: Ensure legal compliance with data protection regulations.

**Features**:
- **Datenminimierung** (Data Minimization) - Only collect necessary fields
- **Zweckbindung** (Purpose Limitation) - Clear purpose statement per position
- **Aufbewahrungsfristen** (Retention Periods) - Auto-delete positions after X days of closure
- **Anonymisierung** (Anonymization) - Remove PII from archived positions
- **Einwilligung** (Consent) - Track applicant consent for data processing
- **Auskunftsrecht** (Right of Access) - Export all data for a specific applicant
- **Löschrecht** (Right to Erasure) - Delete applicant data on request

**Configuration**:
- **Standard-Aufbewahrungsfrist** (Default Retention Period) - Days
- **Auto-Anonymisierung** (Auto-Anonymization) - Toggle
- **Datenschutzerklärung** (Privacy Policy) - Link or embedded text
- **Verantwortlicher** (Data Controller) - Contact info

**Audit**:
- Log all data access (who viewed which position when)
- DSGVO-Report (summary of compliance measures)

---

## 10. Import/Export

### 10.1 Import-Assistent (Import Wizard)
**Purpose**: Import positions from external systems or CSV files.

**Steps**:
1. **Datei hochladen** (Upload File) - Drag-and-drop CSV/Excel/JSON
2. **Datenvorschau** (Data Preview) - Show first 10 rows
3. **Feld-Mapping** (Field Mapping) - Map source columns to target fields
   - Auto-detect common fields (Title → Positionstitel)
   - Dropdown selectors for manual mapping
   - "Mapping-Vorlage speichern" (Save Mapping Template) button
4. **Validierung** (Validation) - Dry-run to check for errors
   - Show validation report (X rows valid, Y rows with errors)
   - Download error report as CSV
5. **Import starten** (Start Import) - Execute import with progress bar
6. **Zusammenfassung** (Summary) - Show imported count, skipped count, errors

**Options**:
- **Duplikate überspringen** (Skip Duplicates) - Checkbox
- **Bestehende aktualisieren** (Update Existing) - Checkbox (match by ID or unique field)
- **Standard-Werte** (Default Values) - Apply default owner, status, etc.

### 10.2 Export-Konfiguration (Export Configuration)
**Purpose**: Export positions to CSV/Excel/JSON for reporting or backup.

**Options**:
- **Format** - Dropdown (CSV, Excel, JSON, XML)
- **Felder auswählen** (Select Fields) - Checklist of all fields + "Alle" (All) checkbox
- **Filter anwenden** (Apply Filters) - Use current filter state or saved view
- **Sortierung** (Sorting) - Dropdown for sort field + order
- **Dateiname** (Filename) - Text input with timestamp variable
- **Kodierung** (Encoding) - Dropdown (UTF-8, ISO-8859-1, etc.)

**Actions**:
- Button: "Jetzt exportieren" (Export Now) - Download immediately
- Button: "Geplanter Export" (Scheduled Export) - Configure recurring exports (daily, weekly)
- Export-Historie anzeigen (Show Export History) - List of past exports with download links

### 10.3 Mapping-Vorlagen (Mapping Templates)
**Purpose**: Reusable field mapping configurations for imports.

**Structure**:
- Save mapping from import wizard
- Apply saved mapping to future imports from same source

**Fields**:
- **Vorlagenname** (Template Name)
- **Quelle** (Source) - E.g., "ATS System X"
- **Mapping** - JSON structure of field mappings
- **Transformation** - Optional JavaScript for data transformation (e.g., date format conversion)

**Management**:
- Edit template
- Duplicate template
- Delete template

---

## 11. UX Recommendations

### 11.1 Sticky Save Bar
- **Behavior**: When user makes changes to a position, a sticky bar appears at bottom of screen
- **Content**: "Nicht gespeicherte Änderungen" (Unsaved Changes) + "Speichern" (Save) + "Verwerfen" (Discard) buttons
- **Auto-save**: Optional toggle for auto-save every 30 seconds with "Wird gespeichert..." (Saving...) indicator

### 11.2 Inline Validation
- **Timing**: Validate on field blur, not on every keystroke (to avoid interruption)
- **Display**: Red border + error icon + error message below field
- **Summary**: If multiple errors, show summary at top with links to jump to error fields

### 11.3 Contextual Help
- **Tooltip icons** (ℹ️) next to labels with hover/click for explanations
- **Help sidebar**: Collapsible panel on right with context-sensitive tips for current tab
- **Links**: "Weitere Informationen" (More Info) links to full documentation
- **Video tutorials**: Embedded short videos for complex features

### 11.4 Empty States
- **When no positions exist**: Show illustration + "Erstellen Sie Ihre erste Position" (Create Your First Position) button
- **When filter returns no results**: Show "Keine Ergebnisse gefunden" (No Results Found) + "Filter zurücksetzen" (Reset Filters) button
- **Suggestions**: Provide actionable next steps, not just "No data"

### 11.5 Multi-Language UI
- **Language switcher**: In user profile or top-right corner
- **Supported languages**: German (primary), English, French
- **RTL support**: Consider future support for right-to-left languages (Arabic)
- **Translations**: Use i18n library (e.g., django-modeltranslation, react-intl)

### 11.6 Responsive Design
- **Mobile-first**: Optimize for tablet/mobile use in field
- **Breakpoints**: Desktop (>1200px), Tablet (768-1200px), Mobile (<768px)
- **Touch-friendly**: Larger buttons/inputs on mobile, swipe gestures

### 11.7 Accessibility (A11y)
- **WCAG 2.1 AA compliance**: Color contrast, keyboard navigation, screen reader support
- **Focus indicators**: Clear visible focus state for all interactive elements
- **ARIA labels**: Proper labeling for assistive technologies
- **Skip links**: "Skip to content" link for keyboard users

### 11.8 Performance
- **Lazy loading**: Load tabs and data on demand, not all at once
- **Pagination**: Limit table rows per page (default 25, options 50/100)
- **Debounced search**: Delay search API calls until user stops typing (300ms)
- **Caching**: Cache frequently accessed data (categories, users) in local storage

---

## 12. Next Steps Checklist

### Phase 1: Foundation
- [ ] **Glossar erstellen** (Create Glossary) - Define all terms and translations (DE/EN)
- [ ] **Sitemap freigeben** (Approve Sitemap) - Stakeholder review of IA structure
- [ ] **Farb- & Typografie-System** (Color & Typography System) - Finalize design tokens
- [ ] **Icon-Bibliothek** (Icon Library) - Select icon set (e.g., Heroicons, Material Icons)

### Phase 2: Design
- [ ] **Wireframes für Schlüsselseiten** (Wireframes for Key Pages)
  - [ ] Positionen-Übersicht (Overview Page)
  - [ ] Position bearbeiten - Basisdaten (Edit - Basic Data)
  - [ ] Position bearbeiten - Anforderungen (Edit - Requirements)
  - [ ] Kategorien-Management (Category Management)
  - [ ] Import-Assistent (Import Wizard)
- [ ] **Interaktive Prototypen** (Interactive Prototypes) - Figma/Sketch clickable prototypes
- [ ] **Usability-Tests** (Usability Testing) - Test with 5 recruiters, iterate on feedback

### Phase 3: Technical Specification
- [ ] **Pflichtfelder & Validierung** (Required Fields & Validation) - Document all rules
- [ ] **Rollen & Rechte Matrix** (Roles & Rights Matrix) - Finalize permissions per role
- [ ] **Datenbank-Schema** (Database Schema) - ERD for positions, categories, workflows, etc.
- [ ] **API-Spezifikation** (API Specification) - Endpoints for CRUD operations, webhooks
- [ ] **Import/Export-Spezifikation** (Import/Export Spec) - File formats, field mappings, validation rules

### Phase 4: Integration & Automation
- [ ] **Webhook-Events definieren** (Define Webhook Events) - Complete list with payload examples
- [ ] **Benachrichtigungs-Vorlagen** (Notification Templates) - Email/SMS templates for all events
- [ ] **Integrations-Partner** (Integration Partners) - Negotiate API access with job boards (StepStone, LinkedIn, etc.)
- [ ] **Retry- & Error-Handling** (Retry & Error Handling) - Document strategies for failed webhooks/syncs

### Phase 5: Compliance & Quality
- [ ] **DSGVO-Checkliste** (GDPR Checklist) - Verify all compliance measures
- [ ] **Datenqualitätsregeln** (Data Quality Rules) - Finalize validation and duplicate detection logic
- [ ] **Audit-Anforderungen** (Audit Requirements) - Define what to log, retention periods

### Phase 6: Development Readiness
- [ ] **User Stories schreiben** (Write User Stories) - Agile stories with acceptance criteria
- [ ] **Sprint-Planung** (Sprint Planning) - Break into 2-week sprints
- [ ] **Test-Szenarien** (Test Scenarios) - Manual and automated test cases
- [ ] **Dokumentation für Entwickler** (Developer Documentation) - Technical setup guide, coding standards

### Phase 7: Training & Rollout
- [ ] **Schulungsunterlagen** (Training Materials) - User guides, video tutorials
- [ ] **Pilot-Gruppe** (Pilot Group) - Beta test with small team before full rollout
- [ ] **Feedback-Kanal** (Feedback Channel) - Set up system for user feedback post-launch
- [ ] **Rollout-Plan** (Rollout Plan) - Phased rollout schedule, communication plan

---

## Appendix: Glossary

| German Term | English Term | Description |
|-------------|--------------|-------------|
| Einstellungen | Settings | Top-level configuration area |
| Positionen | Positions | Job positions/openings |
| Basisdaten | Basic Data | Core fields like title, category |
| Anforderungen | Requirements | Qualifications and criteria |
| Workflow | Workflow | Status lifecycle and approvals |
| Berechtigungen | Permissions | Access control and visibility |
| Automationen | Automations | Triggered actions and notifications |
| Veröffentlichung | Publication | Publishing to job boards |
| Anhänge | Attachments | Files associated with position |
| Historie | History | Audit log and change tracking |
| Kategorien | Categories | Hierarchical classification |
| Vorlagen | Templates | Reusable position templates |
| Textbausteine | Text Snippets | Reusable text blocks |
| Mehrsprachigkeit | Multi-language | Translation support |
| Genehmigung | Approval | Approval process |
| Duplikatsprüfung | Duplicate Check | Duplicate detection |
| Validierung | Validation | Data quality checks |
| DSGVO | GDPR | EU data protection regulation |
| Import/Export | Import/Export | Data exchange features |

---

## Document Metadata

- **Version**: 1.0
- **Date**: 2026-01-19
- **Author**: LUCA Product Team
- **Status**: Draft for Review
- **Next Review**: After stakeholder feedback

---

**End of Document**
