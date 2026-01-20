# SEO-Optimierung - Feature Documentation

## Übersicht

Die SEO-Optimierung erweitert den Landing Page Builder mit umfassenden Funktionen zur Suchmaschinenoptimierung. Diese Funktionen helfen dabei, die Sichtbarkeit und das Ranking deiner Landing Pages in Suchmaschinen zu verbessern.

## Features

### 1. Erweiterte SEO-Metadaten

#### Meta-Tags
- **SEO Title**: Optimierter Titel für Suchmaschinen (30-60 Zeichen empfohlen)
- **Meta Description**: Kurze Beschreibung der Seite (120-160 Zeichen empfohlen)
- **Keywords**: Komma-getrennte Keywords für bessere Auffindbarkeit
- **Canonical URL**: Vermeidet Duplicate Content durch eindeutige URL-Angabe
- **Robots Meta**: Steuert Indexierung durch Suchmaschinen

#### Open Graph (Facebook/Social Media)
- **OG Title**: Titel beim Teilen auf Social Media
- **OG Description**: Beschreibung beim Teilen
- **OG Image**: Vorschaubild (mindestens 1200x630px empfohlen)
- **OG Type**: Art des Inhalts (website, article, product)

#### Twitter Card
- **Card Type**: Art der Twitter-Vorschau (summary_large_image, summary, etc.)
- **Twitter Site**: @username deines Unternehmens
- **Twitter Creator**: @username des Content-Erstellers

### 2. URL-Slug-Verwaltung

Der Slug ist der URL-freundliche Teil deiner Seiten-URL.

**Funktionen:**
- Slug bearbeiten mit Echtzeit-Vorschau
- Automatische Validierung auf Eindeutigkeit
- Slug-Format-Prüfung (nur Kleinbuchstaben, Zahlen, Bindestriche)
- URL-Vorschau vor dem Speichern

**Best Practices:**
- Verwende Bindestriche statt Unterstriche
- Halte Slugs kurz und aussagekräftig
- Verwende relevante Keywords
- Vermeide Zahlen am Anfang

### 3. Automatische Sitemap-Generierung

Die Sitemap hilft Suchmaschinen, alle deine Seiten zu finden und zu indexieren.

**Zugriff:**
- Sitemap XML: `/sitemap.xml`
- Robots.txt: `/robots.txt`

**Features:**
- Automatische Generierung für alle veröffentlichten Seiten
- Konfigurierbare Priorität (0.0 - 1.0)
- Änderungsfrequenz (daily, weekly, monthly, yearly)
- Automatisches Last-Modified-Datum

**Konfiguration pro Seite:**
- **Sitemap Priority**: Relative Wichtigkeit der Seite (0.5 Standard)
- **Change Frequency**: Wie oft sich die Seite ändert

### 4. SEO-Analyse-Tool

Das Analyse-Tool überprüft deine Seite auf SEO-Best-Practices und gibt einen Score.

**Analysierte Faktoren:**

#### Title-Optimierung
- ✓ Title vorhanden
- ✓ Länge optimal (30-60 Zeichen)
- ⚠️ Zu kurz (< 30 Zeichen)
- ⚠️ Zu lang (> 60 Zeichen)

#### Description-Optimierung
- ✓ Description vorhanden
- ✓ Länge optimal (120-160 Zeichen)
- ⚠️ Zu kurz (< 120 Zeichen)
- ⚠️ Zu lang (> 160 Zeichen)

#### Überschriften-Struktur
- ✓ Genau ein H1-Tag
- ✓ H2-Tags vorhanden
- ⚠️ Kein H1-Tag
- ⚠️ Mehrere H1-Tags

#### Bilder-Optimierung
- ✓ Alle Bilder haben Alt-Text
- ⚠️ Bilder ohne Alt-Text gefunden

#### Link-Analyse
- ✓ Interne und externe Links vorhanden
- ⚠️ Externe Links ohne rel="noopener"

#### Content-Länge
- ✓ Ausreichend Content (> 300 Wörter)
- ⚠️ Content zu kurz (< 300 Wörter)

**Bewertungssystem:**
- **A (90-100)**: Ausgezeichnet
- **B (80-89)**: Gut
- **C (70-79)**: Befriedigend
- **D (60-69)**: Verbesserungswürdig
- **F (< 60)**: Mangelhaft

### 5. Builder UI Integration

Das SEO-Panel ist direkt im Page Builder integriert.

#### Tabs im SEO-Panel

**1. Editor Tab**
- SEO-Metadaten bearbeiten
- Slug-Editor mit Live-Vorschau
- Zeichenzähler mit Status-Indikatoren
- Erweiterte Einstellungen (ausklappbar)

**2. Analysis Tab**
- SEO-Score mit visueller Darstellung
- Analyse-Button
- Detaillierte Probleme, Warnungen und Vorschläge
- Kategorisierte Checkliste

**3. Preview Tab**
- **Google-Vorschau**: So erscheint deine Seite in den Suchergebnissen
- **Facebook-Vorschau**: So sieht die Vorschau beim Teilen aus
- **Twitter-Vorschau**: So erscheint der Twitter Card

#### Bedienung

1. **SEO-Panel öffnen**: Klicke auf das SEO-Icon im Builder
2. **Metadaten eingeben**: Fülle Title, Description, etc. aus
3. **Echtzeit-Feedback**: Zeichenzähler zeigen optimale Längen
4. **Analyse ausführen**: Klicke auf "Analyze Page" für SEO-Score
5. **Vorschau prüfen**: Wechsle zum Preview-Tab
6. **Speichern**: Klicke auf "Save SEO Settings"

## Installation & Setup

### Voraussetzungen

```bash
# Python-Pakete
beautifulsoup4>=4.12.0

# Bereits installiert im Projekt
Django>=4.2
djangorestframework>=3.14.0
```

### Migration ausführen

```bash
cd telis_recruitment
python manage.py migrate pages
```

### Statische Dateien sammeln

```bash
python manage.py collectstatic --noinput
```

## API-Referenz

### SEO-Analyse

**Endpoint:** `GET /crm/pages/api/<slug>/seo/analyze/`

**Response:**
```json
{
  "success": true,
  "analysis": {
    "score": 85,
    "grade": "B",
    "issues": [],
    "warnings": ["Meta description is too short"],
    "suggestions": ["Consider adding H2 headings"],
    "details": {
      "title": {
        "text": "My Page Title",
        "length": 45,
        "optimal": true
      },
      "description": {
        "text": "Short desc",
        "length": 10,
        "optimal": false
      }
    }
  }
}
```

### SEO-Update

**Endpoint:** `POST /crm/pages/api/<slug>/seo/update/`

**Request Body:**
```json
{
  "seo_title": "Optimized Title",
  "seo_description": "Detailed description...",
  "seo_keywords": "keyword1, keyword2, keyword3",
  "canonical_url": "https://example.com/page",
  "robots_meta": "index, follow",
  "og_title": "Social Media Title",
  "og_description": "Social media description",
  "og_image": "https://example.com/image.jpg",
  "og_type": "website",
  "twitter_card": "summary_large_image",
  "sitemap_priority": 0.8,
  "sitemap_changefreq": "weekly"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SEO settings updated successfully"
}
```

### Slug-Update

**Endpoint:** `POST /crm/pages/api/<slug>/slug/update/`

**Request Body:**
```json
{
  "new_slug": "updated-page-slug"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Slug updated successfully",
  "old_slug": "old-page-slug",
  "new_slug": "updated-page-slug",
  "new_url": "/p/updated-page-slug/"
}
```

## Best Practices

### Title-Optimierung

1. **Länge**: 30-60 Zeichen
2. **Keywords**: Wichtigste Keywords am Anfang
3. **Unique**: Jede Seite braucht einen einzigartigen Title
4. **Markenname**: Optional am Ende hinzufügen
5. **Lesbarkeit**: Für Menschen, nicht nur für Suchmaschinen

**Beispiele:**
- ✓ "Premium CRM-Software für KMUs | TELIS"
- ✓ "Lead Generation Tools - Mehr Kunden gewinnen"
- ✗ "Home" (zu kurz, nicht beschreibend)
- ✗ "Beste CRM Software für kleine und mittlere Unternehmen in Deutschland 2024" (zu lang)

### Description-Optimierung

1. **Länge**: 120-160 Zeichen
2. **Call-to-Action**: Füge eine Handlungsaufforderung hinzu
3. **Keywords**: Verwende relevante Keywords natürlich
4. **Unique**: Jede Seite braucht eine einzigartige Description
5. **Nutzen**: Zeige den Mehrwert für den Nutzer

**Beispiele:**
- ✓ "Automatisiere deine Lead-Generierung mit TELIS CRM. Spare Zeit, gewinne mehr Kunden. Jetzt kostenlos testen!"
- ✗ "CRM Software" (zu kurz, kein Mehrwert)

### Open Graph Images

1. **Größe**: Mindestens 1200x630px (optimal 1200x630px)
2. **Format**: JPG oder PNG
3. **Dateigröße**: Unter 8MB
4. **Content**: Zeige Logo, Produkt oder Key Visual
5. **Text**: Große, lesbare Überschriften (wenn Text im Bild)

### URL-Slugs

1. **Kurz & prägnant**: 3-5 Wörter
2. **Keywords**: Verwende relevante Keywords
3. **Bindestriche**: Verwende `-` statt `_`
4. **Kleinschreibung**: Nur Kleinbuchstaben
5. **Keine Sonderzeichen**: Nur a-z, 0-9, und `-`

**Beispiele:**
- ✓ "crm-software-kmu"
- ✓ "preise"
- ✓ "kontakt"
- ✗ "Über_Uns" (Großbuchstaben, Unterstriche)
- ✗ "seite-1234" (nicht beschreibend)

## Troubleshooting

### Sitemap nicht erreichbar

**Problem:** `/sitemap.xml` gibt 404 zurück

**Lösung:**
1. Prüfe, ob die URL in `telis/urls.py` eingetragen ist
2. Starte den Server neu: `python manage.py runserver`
3. Prüfe, ob veröffentlichte Seiten existieren

### SEO-Score zu niedrig

**Häufige Probleme:**
- Title oder Description fehlen
- Kein H1-Tag vorhanden
- Bilder ohne Alt-Text
- Content zu kurz

**Lösung:**
1. Gehe zum "Analysis"-Tab
2. Prüfe die angezeigten Issues und Warnings
3. Behebe die Probleme im Editor
4. Analysiere erneut

### Slug-Update schlägt fehl

**Problem:** "Slug already exists"

**Lösung:**
Der gewünschte Slug wird bereits von einer anderen Seite verwendet. Wähle einen anderen, eindeutigen Slug.

### Preview zeigt falsches Bild

**Problem:** Facebook/Twitter Preview zeigt nicht das richtige Bild

**Lösung:**
1. Prüfe, ob die Bild-URL korrekt ist
2. Stelle sicher, dass das Bild öffentlich erreichbar ist
3. Cache von Facebook leeren: [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
4. Cache von Twitter leeren: [Twitter Card Validator](https://cards-dev.twitter.com/validator)

## Weiterführende Ressourcen

### SEO-Grundlagen
- [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [Moz Beginner's Guide to SEO](https://moz.com/beginners-guide-to-seo)

### Open Graph
- [Open Graph Protocol](https://ogp.me/)
- [Facebook Sharing Best Practices](https://developers.facebook.com/docs/sharing/best-practices)

### Twitter Cards
- [Twitter Cards Documentation](https://developer.twitter.com/en/docs/twitter-for-websites/cards/overview/abouts-cards)

### Sitemap
- [Sitemap Protocol](https://www.sitemaps.org/protocol.html)
- [Google Sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)

## Changelog

### Version 1.0.0 (2026-01-20)

**Neue Features:**
- ✨ SEO-Panel im Page Builder
- ✨ Automatische Sitemap-Generierung
- ✨ SEO-Analyse-Tool mit Scoring
- ✨ Open Graph und Twitter Card Unterstützung
- ✨ URL-Slug-Editor
- ✨ Google/Facebook/Twitter Previews
- ✨ Echtzeit-Zeichenzähler

**Technisch:**
- Migration 0012_add_seo_enhancements
- Neue API-Endpoints für SEO-Funktionen
- SEOAnalyzer Service
- Sitemap Generator Service

## Support

Bei Fragen oder Problemen:
1. Prüfe diese Dokumentation
2. Schaue in die API-Referenz
3. Kontaktiere das Entwicklungsteam

---

**Hinweis:** Diese Dokumentation beschreibt die SEO-Features ab Version 2.4.0 des LUCA NRW Scrapers.
