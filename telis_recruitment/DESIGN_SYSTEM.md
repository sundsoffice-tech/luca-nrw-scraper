# TELIS Recruitment - Design System

> Zentrales Design-System für konsistentes Branding über alle Seiten der TELIS Recruitment Plattform.

## 📋 Inhaltsverzeichnis

- [Übersicht](#übersicht)
- [Installation](#installation)
- [Farben](#farben)
- [Typographie](#typographie)
- [Spacing](#spacing)
- [Buttons](#buttons)
- [Cards](#cards)
- [Formulare](#formulare)
- [Badges](#badges)
- [Best Practices](#best-practices)

## Übersicht

Das TELIS Design System ist ein zentrales, CSS-basiertes Design-System, das über CSS Custom Properties (CSS-Variablen) alle Designentscheidungen definiert. Es ermöglicht:

- ✅ Konsistentes Branding über alle Seiten
- ✅ Einfache Wartbarkeit und Updates
- ✅ Dark Mode Support
- ✅ Responsive Design
- ✅ Accessibility-First Ansatz
- ✅ Performance-optimiert

## Installation

Das Design System wird automatisch in allen Templates geladen:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/design-system.css' %}">
<link rel="stylesheet" href="{% static 'css/common.css' %}">
```

## Farben

### Primärfarben

Die Hauptfarbe der Marke ist **Cyan/Türkis** (#06b6d4).

```css
var(--color-primary)        /* #06b6d4 - Haupt-Cyan */
var(--color-primary-light)  /* #22d3ee - Helleres Cyan */
var(--color-primary-dark)   /* #0891b2 - Dunkleres Cyan */
```

**Verwendungsbeispiele:**
```html
<!-- Als Tailwind-Klasse -->
<div class="text-primary">Primary Text</div>
<div class="bg-primary">Primary Background</div>

<!-- Als CSS-Variable -->
<div style="color: var(--color-primary)">Custom Primary</div>

<!-- Als Design System Klasse -->
<div class="text-primary">Primary Text</div>
```

### Transparente Varianten

Für Overlays, Hover-Effekte und subtile Hintergründe:

```css
var(--color-primary-50)   /* 5% Transparenz */
var(--color-primary-100)  /* 10% Transparenz */
var(--color-primary-200)  /* 20% Transparenz */
var(--color-primary-300)  /* 30% Transparenz */
var(--color-primary-500)  /* 50% Transparenz */
```

### Sekundärfarben

```css
var(--color-secondary)       /* #8b5cf6 - Violett */
var(--color-secondary-light) /* #a78bfa */
var(--color-secondary-dark)  /* #7c3aed */
```

### Hintergrundfarben (Dark Theme)

```css
var(--color-bg-primary)    /* #0f172a - Haupthintergrund */
var(--color-bg-secondary)  /* #1e293b - Cards, Panels */
var(--color-bg-tertiary)   /* #334155 - Hover States */
var(--color-bg-elevated)   /* #1e293b - Modals, Dropdowns */
var(--color-bg-overlay)    /* rgba(15, 23, 42, 0.95) */
```

### Textfarben

```css
var(--color-text-primary)    /* #f1f5f9 - Haupt-Text */
var(--color-text-secondary)  /* #cbd5e1 - Sekundärer Text */
var(--color-text-tertiary)   /* #94a3b8 - Tertiärer Text */
var(--color-text-muted)      /* #64748b - Gedämpfter Text */
var(--color-text-disabled)   /* #475569 - Deaktiviert */
```

### Statusfarben

```css
/* Erfolg (Grün) */
var(--color-success)       /* #10b981 */
var(--color-success-light) /* #34d399 */
var(--color-success-dark)  /* #059669 */

/* Fehler (Rot) */
var(--color-error)         /* #ef4444 */
var(--color-error-light)   /* #f87171 */
var(--color-error-dark)    /* #dc2626 */

/* Warnung (Orange) */
var(--color-warning)       /* #f59e0b */
var(--color-warning-light) /* #fbbf24 */
var(--color-warning-dark)  /* #d97706 */

/* Info (Cyan) */
var(--color-info)          /* #06b6d4 */
var(--color-info-light)    /* #22d3ee */
var(--color-info-dark)     /* #0891b2 */
```

## Typographie

### Font Families

```css
var(--font-family-base) /* System Font Stack */
var(--font-family-mono) /* Monospace für Code */
```

### Font Sizes

| Variable | Größe | Pixel | Verwendung |
|----------|-------|-------|------------|
| `--font-size-xs` | 0.75rem | 12px | Labels, Badges |
| `--font-size-sm` | 0.875rem | 14px | Small Text |
| `--font-size-base` | 1rem | 16px | Body Text |
| `--font-size-lg` | 1.125rem | 18px | Lead Text |
| `--font-size-xl` | 1.25rem | 20px | Subtitles |
| `--font-size-2xl` | 1.5rem | 24px | Section Titles |
| `--font-size-3xl` | 1.875rem | 30px | Page Titles |
| `--font-size-4xl` | 2.25rem | 36px | Hero Titles |
| `--font-size-5xl` | 3rem | 48px | Large Headlines |

**Beispiel:**
```html
<h1 style="font-size: var(--font-size-3xl)">Page Title</h1>
<p style="font-size: var(--font-size-base)">Body text</p>
```

### Font Weights

```css
var(--font-weight-normal)    /* 400 */
var(--font-weight-medium)    /* 500 */
var(--font-weight-semibold)  /* 600 */
var(--font-weight-bold)      /* 700 */
```

### Line Heights

```css
var(--line-height-tight)    /* 1.25 - Headlines */
var(--line-height-normal)   /* 1.5 - Body Text */
var(--line-height-relaxed)  /* 1.75 - Long Form */
```

## Spacing

Konsistente Abstände basierend auf 4px Raster:

| Variable | Wert | Pixel | Verwendung |
|----------|------|-------|------------|
| `--spacing-0` | 0 | 0px | Kein Abstand |
| `--spacing-1` | 0.25rem | 4px | Minimal |
| `--spacing-2` | 0.5rem | 8px | Klein |
| `--spacing-3` | 0.75rem | 12px | Standard Klein |
| `--spacing-4` | 1rem | 16px | Standard |
| `--spacing-5` | 1.25rem | 20px | Medium |
| `--spacing-6` | 1.5rem | 24px | Standard Groß |
| `--spacing-8` | 2rem | 32px | Groß |
| `--spacing-10` | 2.5rem | 40px | Extra Groß |
| `--spacing-12` | 3rem | 48px | XXL |
| `--spacing-16` | 4rem | 64px | XXXL |
| `--spacing-20` | 5rem | 80px | Section Spacing |
| `--spacing-24` | 6rem | 96px | Large Section |

**Beispiel:**
```html
<div style="padding: var(--spacing-6); margin-bottom: var(--spacing-4)">
    Content with consistent spacing
</div>
```

## Buttons

### Basis Button

```html
<button class="btn btn-primary">Primary Button</button>
```

### Button Varianten

```html
<!-- Primary -->
<button class="btn btn-primary">Primary</button>

<!-- Secondary -->
<button class="btn btn-secondary">Secondary</button>

<!-- Success -->
<button class="btn btn-success">Success</button>

<!-- Error -->
<button class="btn btn-error">Delete</button>

<!-- Warning -->
<button class="btn btn-warning">Warning</button>

<!-- Ghost (transparent) -->
<button class="btn btn-ghost">Ghost</button>

<!-- Outline -->
<button class="btn btn-outline">Outline</button>
```

### Button Größen

```html
<!-- Extra Small -->
<button class="btn btn-primary btn-xs">XS Button</button>

<!-- Small -->
<button class="btn btn-primary btn-sm">Small Button</button>

<!-- Normal (Standard) -->
<button class="btn btn-primary">Normal Button</button>

<!-- Large -->
<button class="btn btn-primary btn-lg">Large Button</button>

<!-- Extra Large -->
<button class="btn btn-primary btn-xl">XL Button</button>
```

### Button Full Width

```html
<button class="btn btn-primary btn-block">Full Width Button</button>
```

### Button States

```html
<!-- Disabled -->
<button class="btn btn-primary" disabled>Disabled</button>

<!-- Loading (mit Icon) -->
<button class="btn btn-primary">
    <span class="mr-2">⏳</span>
    Loading...
</button>
```

## Cards

### Basis Card

```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Card Title</h3>
        <p class="card-subtitle">Card subtitle</p>
    </div>
    <div class="card-body">
        Card content goes here
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">Action</button>
    </div>
</div>
```

### Card Varianten

```html
<!-- Elevated Card (mit Schatten) -->
<div class="card card-elevated">
    Elevated card with shadow
</div>

<!-- Interactive Card (Hover-Effekt) -->
<div class="card card-interactive">
    Click me!
</div>
```

## Formulare

### Input Field

```html
<div>
    <label class="form-label" for="email">E-Mail</label>
    <input 
        type="email" 
        id="email" 
        class="form-input" 
        placeholder="name@example.com"
    >
    <p class="form-help">Wir senden niemals Spam</p>
</div>
```

### Textarea

```html
<div>
    <label class="form-label" for="message">Nachricht</label>
    <textarea 
        id="message" 
        class="form-textarea" 
        rows="4"
        placeholder="Ihre Nachricht..."
    ></textarea>
</div>
```

### Select

```html
<div>
    <label class="form-label" for="status">Status</label>
    <select id="status" class="form-select">
        <option>Aktiv</option>
        <option>Inaktiv</option>
        <option>Ausstehend</option>
    </select>
</div>
```

### Form States

```html
<!-- Error State -->
<div>
    <label class="form-label" for="error-input">E-Mail</label>
    <input 
        type="email" 
        id="error-input" 
        class="form-input form-input-error"
    >
    <p class="form-error">Bitte geben Sie eine gültige E-Mail ein</p>
</div>

<!-- Success State -->
<div>
    <label class="form-label" for="success-input">E-Mail</label>
    <input 
        type="email" 
        id="success-input" 
        class="form-input form-input-success"
    >
</div>

<!-- Disabled State -->
<input type="text" class="form-input" disabled value="Deaktiviert">
```

## Badges

```html
<!-- Primary -->
<span class="badge badge-primary">Primary</span>

<!-- Success -->
<span class="badge badge-success">Success</span>

<!-- Error -->
<span class="badge badge-error">Error</span>

<!-- Warning -->
<span class="badge badge-warning">Warning</span>

<!-- Info -->
<span class="badge badge-info">Info</span>

<!-- Secondary -->
<span class="badge badge-secondary">Secondary</span>
```

**Anwendungsbeispiele:**
```html
<!-- Status Badge -->
<span class="badge badge-success">Aktiv</span>
<span class="badge badge-error">Inaktiv</span>

<!-- Count Badge -->
<span class="badge badge-primary">42</span>

<!-- Label Badge -->
<span class="badge badge-warning">Neu</span>
```

## Utility Classes

### Text Colors

```html
<p class="text-primary">Primary text</p>
<p class="text-secondary">Secondary text</p>
<p class="text-muted">Muted text</p>
<p class="text-success">Success text</p>
<p class="text-error">Error text</p>
<p class="text-warning">Warning text</p>
```

### Background Colors

```html
<div class="bg-primary">Primary background</div>
<div class="bg-secondary">Secondary background</div>
<div class="bg-tertiary">Tertiary background</div>
```

### Border Radius

```html
<div class="rounded-sm">Small radius</div>
<div class="rounded">Base radius</div>
<div class="rounded-md">Medium radius</div>
<div class="rounded-lg">Large radius</div>
<div class="rounded-xl">Extra large radius</div>
<div class="rounded-2xl">2XL radius</div>
<div class="rounded-full">Full/Circle</div>
```

### Shadows

```html
<div class="shadow-sm">Small shadow</div>
<div class="shadow">Base shadow</div>
<div class="shadow-md">Medium shadow</div>
<div class="shadow-lg">Large shadow</div>
<div class="shadow-xl">XL shadow</div>
<div class="shadow-2xl">2XL shadow</div>
```

### Transitions

```html
<div class="transition">Standard transition</div>
<div class="transition-fast">Fast transition</div>
<div class="transition-slow">Slow transition</div>
```

## Best Practices

### 1. Verwende CSS-Variablen statt Hardcoded Values

❌ **Schlecht:**
```html
<button style="background: #06b6d4; padding: 12px 24px;">
    Click me
</button>
```

✅ **Gut:**
```html
<button class="btn btn-primary">
    Click me
</button>
```

### 2. Nutze Design System Klassen

❌ **Schlecht:**
```html
<div style="background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 24px;">
    Card content
</div>
```

✅ **Gut:**
```html
<div class="card">
    Card content
</div>
```

### 3. Konsistente Abstände

❌ **Schlecht:**
```html
<div style="margin-bottom: 13px; padding: 19px;">
    Inconsistent spacing
</div>
```

✅ **Gut:**
```html
<div style="margin-bottom: var(--spacing-3); padding: var(--spacing-5);">
    Consistent spacing
</div>
```

### 4. Semantische Button-Varianten

❌ **Schlecht:**
```html
<button class="btn btn-primary">Delete</button>
```

✅ **Gut:**
```html
<button class="btn btn-error">Delete</button>
```

### 5. Accessibility

Immer Labels für Formularfelder verwenden:

✅ **Gut:**
```html
<label class="form-label" for="username">Username</label>
<input type="text" id="username" class="form-input">
```

### 6. Kombiniere Tailwind mit Design System

Das Design System kann mit Tailwind CSS kombiniert werden:

```html
<!-- Design System Button mit Tailwind Utilities -->
<button class="btn btn-primary flex items-center gap-2">
    <span>🚀</span>
    <span>Launch</span>
</button>

<!-- Design System Card mit Tailwind Layout -->
<div class="card grid grid-cols-2 gap-4">
    <!-- Card content -->
</div>
```

## Migration Guide

### Schritt 1: Ersetze Hardcoded Colors

Suche nach Hardcoded-Farben und ersetze sie:

```bash
# Vorher
style="color: #06b6d4"
class="text-cyan-500"

# Nachher
style="color: var(--color-primary)"
class="text-primary"
```

### Schritt 2: Nutze Design System Komponenten

Ersetze Custom-Styles durch Design System Klassen:

```html
<!-- Vorher -->
<button style="background: #06b6d4; color: white; padding: 12px 24px; border-radius: 8px;">
    Submit
</button>

<!-- Nachher -->
<button class="btn btn-primary">
    Submit
</button>
```

### Schritt 3: Vereinheitliche Spacing

Nutze CSS-Variablen für konsistente Abstände:

```html
<!-- Vorher -->
<div style="padding: 20px; margin-bottom: 15px;">

<!-- Nachher -->
<div style="padding: var(--spacing-5); margin-bottom: var(--spacing-4);">
```

## Support & Feedback

Bei Fragen oder Verbesserungsvorschlägen zum Design System:

- 📧 E-Mail: design@telis.de
- 💬 Slack: #design-system
- 📝 Issues: GitHub Issues

## Version History

- **v1.0.0** (2026-01-20) - Initial Release
  - CSS Custom Properties System
  - Button Components
  - Card Components
  - Form Components
  - Badge Components
  - Utility Classes

---

**Maintained by:** TELIS Design Team  
**Last Updated:** 2026-01-20
