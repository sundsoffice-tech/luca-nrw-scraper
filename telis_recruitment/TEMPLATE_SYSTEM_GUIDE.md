# Flexibles Layout- & Template-System

## Übersicht

Das flexible Template-System ermöglicht die schnelle Erstellung von anpassbaren Seiten mit vorgefertigten Layouts. Jede Vorlage ist vollständig anpassbar und zwingt Nutzer nicht in starre Strukturen.

## Verfügbare Layout-Kategorien

### 1. Landingpage (`landing`)
**Beschreibung:** Vollständig anpassbare Landingpage mit Hero, Features, Testimonials und CTA

**Sektionen:**
- Hero Section (Hauptbereich mit Überschrift und CTA)
- Features (Grid mit Feature-Karten)
- Testimonials (optional)
- Call-to-Action (optional)

**Anpassbarkeit:**
- Flexible Grid-Layouts
- Frei anpassbare Farben und Schriften
- Vollständig editierbare Inhalte
- Hinzufügen/Entfernen von Sektionen

**Layout-Konfiguration:**
```json
{
  "sections": ["hero", "features", "testimonials", "cta"],
  "customizable": true,
  "flexible_grid": true
}
```

**Verwendung:**
```python
# Via Management Command
python manage.py seed_layout_templates

# Via API
POST /pages/templates/<template_id>/apply/
{
  "slug": "neue-seite",
  "title": "Meine Landingpage"
}

# Via Code
from pages.models import PageTemplate, LandingPage
template = PageTemplate.objects.get(slug='moderne-landingpage')
page = LandingPage.objects.create(slug='meine-seite', title='Meine Seite')
page.html_json = template.html_json
page.css = template.css
page.save()
```

---

### 2. Kontaktseite (`contact`)
**Beschreibung:** Flexibles Kontaktformular mit Kontaktinformationen und Karte

**Sektionen:**
- Header (Überschrift und Beschreibung)
- Kontaktformular (Name, E-Mail, Nachricht)
- Kontaktinformationen (E-Mail, Telefon, Adresse)
- Karte (optional)

**Anpassbarkeit:**
- Formularfelder hinzufügen/entfernen
- Validierungsregeln anpassen
- Integration mit Brevo/E-Mail
- Custom Styling

**Layout-Konfiguration:**
```json
{
  "sections": ["header", "form", "info", "map"],
  "form_integration": true,
  "customizable": true
}
```

**Formular-Integration:**
```html
<!-- Das Formular kann mit Brevo oder eigenem Backend verbunden werden -->
<form class="contact-form" method="POST" action="/pages/submit/">
  <input type="text" name="name" required>
  <input type="email" name="email" required>
  <textarea name="message" required></textarea>
  <button type="submit">Senden</button>
</form>
```

---

### 3. Verkaufsseite (`sales`)
**Beschreibung:** Überzeugende Verkaufsseite mit Produktvorteilen und CTAs

**Sektionen:**
- Hero (Produktbeschreibung und Haupt-CTA)
- Benefits (Vorteile Grid)
- Testimonials (Kundenbewertungen)
- Pricing (Preistabelle)
- FAQ (Häufige Fragen)
- Final CTA (Abschluss-Call-to-Action)

**Anpassbarkeit:**
- Conversion-optimierte Layouts
- A/B-Testing freundlich
- Dynamische Preisgestaltung
- Flexible Benefit-Darstellung

**Layout-Konfiguration:**
```json
{
  "sections": ["hero", "benefits", "testimonials", "pricing", "faq", "cta"],
  "conversion_optimized": true,
  "customizable": true
}
```

**Conversion-Features:**
- Prominent CTAs (Call-to-Action Buttons)
- Social Proof (Kundenbewertungen)
- Urgency-Elemente (zeitlich begrenzte Angebote)
- Trust-Badges

---

### 4. Infoseite (`info`)
**Beschreibung:** Flexible Infoseite für Inhalte, Dokumentation und Anleitungen

**Sektionen:**
- Header (Überschrift)
- Sidebar Navigation (Sticky Navigation)
- Hauptinhalt (Artikel mit Überschriften, Listen, etc.)
- Verwandte Inhalte (optional)

**Anpassbarkeit:**
- Dokumentations-freundlich
- Inhaltsverzeichnis automatisch
- Code-Highlighting Support
- Multi-Level Navigation

**Layout-Konfiguration:**
```json
{
  "sections": ["header", "sidebar", "content", "related"],
  "documentation_friendly": true,
  "customizable": true
}
```

**Content-Struktur:**
```html
<section class="info-content">
  <aside class="sidebar">
    <!-- Sticky Navigation -->
  </aside>
  <article class="main-content">
    <!-- Hauptinhalt -->
  </article>
</section>
```

---

## API Endpoints

### Template-Auswahl
```
GET /pages/templates/
→ Liste aller Templates gruppiert nach Kategorie

GET /pages/templates/category/<category>/
→ Templates einer bestimmten Kategorie
  Kategorien: landing, contact, sales, info

GET /pages/templates/<template_id>/config/
→ Layout-Konfiguration eines Templates
```

### Template-Anwendung
```
POST /pages/templates/<template_id>/apply/
Body: {
  "slug": "neue-seite",
  "title": "Meine Seite"
}
→ Wendet Template auf neue oder existierende Seite an
```

### Beispiel-Request
```javascript
// Template anwenden
fetch('/pages/templates/1/apply/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken
  },
  body: JSON.stringify({
    slug: 'meine-verkaufsseite',
    title: 'Meine Verkaufsseite'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    window.location.href = data.page_url;
  }
});

// Template-Konfiguration abrufen
fetch('/pages/templates/1/config/')
  .then(response => response.json())
  .then(data => {
    console.log('Layout Config:', data.template.layout_config);
    console.log('Sections:', data.template.layout_config.sections);
  });
```

---

## Management Commands

### Templates initialisieren
```bash
python manage.py seed_layout_templates
```

Dieser Befehl erstellt alle vier Layout-Templates:
- ✓ Moderne Landingpage (landing)
- ✓ Kontaktseite (contact)
- ✓ Verkaufsseite (sales)
- ✓ Infoseite (info)

---

## Workflow: Von Template zu fertiger Seite

### 1. Template auswählen
```python
from pages.models import PageTemplate

# Alle Templates anzeigen
templates = PageTemplate.objects.filter(is_active=True)
for t in templates:
    print(f"{t.name} ({t.get_category_display()})")

# Spezifisches Template wählen
template = PageTemplate.objects.get(slug='moderne-landingpage')
```

### 2. Neue Seite erstellen
```python
from pages.models import LandingPage

page = LandingPage.objects.create(
    slug='meine-landingpage',
    title='Meine Landingpage',
    status='draft',
    created_by=request.user
)
```

### 3. Template anwenden
```python
# Template-Inhalt kopieren
page.html_json = template.html_json
page.css = template.css
page.save()

# Usage Count erhöhen
template.usage_count += 1
template.save()
```

### 4. Im Builder anpassen
```
URL: /pages/builder/meine-landingpage/
```

Im GrapesJS Builder können alle Elemente frei angepasst werden:
- Text ändern
- Farben anpassen
- Bilder ersetzen
- Sektionen hinzufügen/entfernen
- Layout umstrukturieren

### 5. Veröffentlichen
```python
page.status = 'published'
page.save()
```

Öffentliche URL: `/p/meine-landingpage/`

---

## Anpassung von Templates

### Template-Inhalt ändern
Templates sind **nicht starr**. Jeder Teil kann im Builder angepasst werden:

1. **Texte:** Direkt im Builder editierbar
2. **Farben:** Per Style-Panel anpassbar
3. **Layout:** Drag & Drop Umstrukturierung
4. **Sektionen:** Hinzufügen/Entfernen/Duplizieren
5. **Komponenten:** Aus Block-Library hinzufügen

### Eigene Templates erstellen
```python
from pages.models import PageTemplate

# Neues Template erstellen
template = PageTemplate.objects.create(
    name='Mein Custom Template',
    slug='mein-custom-template',
    category='landing',  # oder contact, sales, info
    description='Meine Beschreibung',
    html_json={
        'components': [
            {
                'tagName': 'section',
                'components': [...]
            }
        ]
    },
    css='...',
    layout_config={
        'sections': ['hero', 'features'],
        'customizable': True
    }
)
```

### Template aus bestehender Seite
```python
from pages.models import LandingPage, PageTemplate

# Seite als Template speichern
page = LandingPage.objects.get(slug='meine-seite')

template = PageTemplate.objects.create(
    name='Template von ' + page.title,
    slug='template-' + page.slug,
    category='landing',
    html_json=page.html_json,
    css=page.css,
    layout_config={
        'customizable': True
    }
)
```

---

## Best Practices

### 1. Semantische Kategorien
Wählen Sie die richtige Kategorie für Ihr Template:
- `landing` → Haupt-Landingpages mit Fokus auf Conversion
- `contact` → Kontakt- und Anfrageseiten
- `sales` → Produkt- und Verkaufsseiten
- `info` → Content-, Dokumentations- und Infoseiten

### 2. Layout-Konfiguration nutzen
```json
{
  "sections": ["header", "content", "footer"],
  "customizable": true,
  "flexible_grid": true,
  "form_integration": true,
  "documentation_friendly": false,
  "conversion_optimized": true
}
```

### 3. Data-Attribute für Sektionen
```html
<section class="hero" data-section="hero">
  <!-- Macht Sektionen identifizierbar und anpassbar -->
</section>
```

### 4. Responsive Design
Alle Templates sind standardmäßig responsive:
```css
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
```

### 5. Performance
- CSS im `<head>`
- JavaScript am Ende des `<body>`
- Bilder lazy-loading
- Minimale externe Dependencies

---

## Troubleshooting

### Template wird nicht angezeigt
```python
# Template aktivieren
template = PageTemplate.objects.get(slug='mein-template')
template.is_active = True
template.save()
```

### Migration ausführen
```bash
python manage.py migrate pages
```

### Templates neu generieren
```bash
python manage.py seed_layout_templates
```

---

## Technische Details

### Datenbank-Modell
```python
class PageTemplate(models.Model):
    name = CharField(max_length=100)
    slug = SlugField(unique=True)
    category = CharField(choices=CATEGORIES)
    description = TextField(blank=True)
    html_json = JSONField(default=dict)
    css = TextField(blank=True)
    layout_config = JSONField(default=dict, blank=True)
    usage_count = IntegerField(default=0)
    is_active = BooleanField(default=True)
```

### GrapesJS Format
Templates verwenden das GrapesJS Component Format:
```json
{
  "components": [
    {
      "tagName": "section",
      "attributes": {"class": "hero"},
      "components": [
        {
          "tagName": "h1",
          "components": [
            {"type": "textnode", "content": "Titel"}
          ]
        }
      ]
    }
  ]
}
```

---

## Support & Weiterentwicklung

### Neue Template-Kategorie hinzufügen
1. In `models.py` CATEGORIES erweitern
2. Migration erstellen: `python manage.py makemigrations`
3. Migration ausführen: `python manage.py migrate`
4. Template in `seed_layout_templates.py` hinzufügen

### Feature Requests
Neue Layout-Typen und Features können jederzeit hinzugefügt werden. Das System ist designed für maximale Flexibilität.
