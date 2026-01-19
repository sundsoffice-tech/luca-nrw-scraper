# Landing Page Builder Upgrade - Teil 1 Implementation Summary

## Überblick
Dieser Teil des Landing Page Builder Upgrades implementiert die neuen Models und Asset-Management Funktionalität gemäß der Spezifikation.

## Implementierte Änderungen

### 1. PageAsset Model Updates

**Neue Felder:**
- `landing_page`: ForeignKey zu LandingPage (optional)
- `asset_type`: CharField mit Choices ('image', 'video', 'document')
- `mime_type`: CharField für MIME-Type

**Umbenennungen:**
- `filename` → `name`
- `uploaded_at` → `created_at`

**Feldtyp-Änderungen:**
- `file`: ImageField → FileField mit neuem upload_to Pfad
- `file_size`: PositiveIntegerField → IntegerField
- `width`, `height`: PositiveIntegerField → IntegerField

**Neue Methode:**
- `@property url`: Gibt die URL des Assets zurück

### 2. BrandSettings Model Updates

**Singleton Pattern:**
- `save()` Methode überschrieben: setzt immer `pk=1`
- `@classmethod get_settings()`: Holt oder erstellt die einzige Instanz

**Neue Felder:**
- `updated_at`: DateTimeField (auto_now=True)

**Umbenennungen:**
- `email` → `contact_email`
- `phone` → `contact_phone`
- `generate_css_variables()` → `get_css_variables()`

**Entfernte Felder:**
- `base_font_size`
- `twitter_url`
- `youtube_url`
- `address`
- `terms_url`

**Geänderte Defaults:**
- `primary_color`: '#007bff' → '#6366f1'
- `secondary_color`: '#6c757d' → '#06b6d4'
- `accent_color`: '#28a745' → '#22c55e'
- `text_color`: '#212529' → '#1f2937'
- `body_font`: 'Open Sans' → 'Inter'
- `company_name`: '' → 'LUCA'

**Vereinfachte Methode:**
- `get_css_variables()`: Gibt jetzt eine kompakte CSS-Variable Zeichenkette zurück

### 3. PageTemplate Model Updates

**Neue Felder:**
- `slug`: SlugField (unique)
- `description`: TextField

**Umbenennungen:**
- `gjs_data` → `html_json`
- `html_content` → `html`
- `css_content` → `css`

**Feldtyp-Änderungen:**
- `usage_count`: PositiveIntegerField → IntegerField
- `thumbnail`: Jetzt nicht mehr required (blank=True)

**Geänderte Choices:**
- CATEGORY_CHOICES reduziert auf: 'lead_gen', 'product', 'coming_soon', 'thank_you'
- Category Labels auf Deutsch aktualisiert

**Meta Änderungen:**
- `ordering`: ['-usage_count', 'name'] → ['category', 'name']

### 4. Views Updates

**upload_asset():**
- Verwendet neue PageAsset Felder
- Setzt `landing_page_id`, `asset_type`, `mime_type`
- Nutzt PIL für Bildabmessungen
- Vereinfachte Rückgabe

**list_assets():**
- Filtert nach `asset_type='image'`
- Unterstützt Filterung nach `landing_page_id` (mit NULL-Assets)
- Vereinfachtes Rückgabeformat

**brand_settings_view() (ehemals brand_settings):**
- Nutzt `BrandSettings.get_settings()` statt get_or_create
- Verarbeitet alle Felder aus dem Formular
- Verwendet Django messages für Feedback

**get_brand_css():**
- Nutzt `get_css_variables()` statt `generate_css_variables()`

**apply_template():**
- Verwendet neue PageTemplate Felder (`html`, `css`, `html_json`)

### 5. URLs Updates

**Geänderte Pfade:**
- `assets/upload/` → `api/assets/upload/` (name: 'upload-asset')
- `assets/` → `api/assets/` (name: 'list-assets')
- `brand-settings/` → `brand/` (name: 'brand-settings')

### 6. Admin Updates

**PageAssetAdmin:**
- Zeigt neue Felder: `asset_type`, `landing_page`, `mime_type`
- Aktualisierte list_display und fieldsets

**BrandSettingsAdmin:**
- Deutsche Feldset-Überschriften
- Entfernte nicht mehr vorhandene Felder
- Singleton-Logik beibehalten

**PageTemplateAdmin:**
- Fügt `slug` und `description` hinzu
- Nutzt `prepopulated_fields` für slug
- Aktualisierte search_fields

### 7. Template Updates

**brand_settings.html:**
- Aktualisiert Feldnamen: `contact_email`, `contact_phone`
- Entfernt: Twitter, YouTube, Address, Terms URL, Base Font Size
- Grid-Layouts angepasst

### 8. Migration

**Datei:** `0006_update_models_to_match_spec.py`

Die Migration beinhaltet:
- Alle PageAsset Änderungen (Felder, Umbenennungen, Typen)
- Alle BrandSettings Änderungen (Felder, Defaults, Umbenennungen)
- Alle PageTemplate Änderungen (Felder, Umbenennungen, Meta)

## Deployment-Schritte

1. Code auf Server deployen
2. Migration ausführen:
   ```bash
   cd telis_recruitment
   python manage.py migrate pages
   ```
3. Static files neu sammeln (falls nötig):
   ```bash
   python manage.py collectstatic --noinput
   ```

## Testing

Nach dem Deployment testen:

1. **Brand Settings:**
   - Navigiere zu `/crm/pages/brand/`
   - Teste alle Farbauswähler
   - Teste Logo-Uploads
   - Speichere und verifiziere

2. **Asset Manager:**
   - Upload von Bildern über `/crm/pages/api/assets/upload/`
   - Liste Assets über `/crm/pages/api/assets/`
   - Verknüpfe Assets mit Landing Pages

3. **Templates:**
   - Erstelle PageTemplate mit Slug
   - Wende Template auf neue Page an
   - Verifiziere Feldnamen

## Bekannte Einschränkungen

- Migration wurde manuell erstellt (nicht via makemigrations)
- Funktioniert nur mit Django/SQLite oder anderen kompatiblen Datenbanken
- Keine Daten-Migration für existierende Instanzen

## Nächste Schritte (Teil 2)

Für Teil 2 des Upgrades könnten folgende Features hinzugefügt werden:
- Erweiterte Template-Verwaltung
- Asset-Kategorisierung und Suche
- Bulk-Asset-Upload
- Brand Settings Export/Import
- Template-Preview-Funktion
