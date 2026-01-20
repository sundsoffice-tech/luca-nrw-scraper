# Flexible Layout & Template System - Visual Overview

## 🎨 Template Categories

### 1. Landingpage (Landing Page)
**Purpose:** Main landing pages with focus on conversion  
**Category:** `landing`  
**Template:** `moderne-landingpage`

```
┌─────────────────────────────────────┐
│         HERO SECTION                │
│  ┌──────────────────────────┐      │
│  │   Headline                │      │
│  │   Subtitle                │      │
│  │   [Call to Action]        │      │
│  └──────────────────────────┘      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│      FEATURES SECTION               │
│  ┌────┐  ┌────┐  ┌────┐            │
│  │ F1 │  │ F2 │  │ F3 │            │
│  └────┘  └────┘  └────┘            │
└─────────────────────────────────────┘
```

**Key Features:**
- ✅ Hero section with CTA
- ✅ Features grid (3-column)
- ✅ Fully customizable colors
- ✅ Gradient backgrounds
- ✅ Responsive design

**Use Cases:**
- Product launches
- Service offerings
- Event promotions
- App downloads

---

### 2. Kontaktseite (Contact Page)
**Purpose:** Contact and inquiry pages  
**Category:** `contact`  
**Template:** `kontaktseite`

```
┌─────────────────────────────────────┐
│         HEADER                      │
│  "Kontaktieren Sie uns"             │
└─────────────────────────────────────┘
┌──────────────────┬──────────────────┐
│  CONTACT FORM    │  CONTACT INFO    │
│  ┌────────────┐  │  📧 Email        │
│  │ Name       │  │  📞 Phone        │
│  │ Email      │  │  📍 Address      │
│  │ Message    │  │                  │
│  │ [Submit]   │  │                  │
│  └────────────┘  │                  │
└──────────────────┴──────────────────┘
```

**Key Features:**
- ✅ Responsive contact form
- ✅ Contact information sidebar
- ✅ Form validation ready
- ✅ Email integration support
- ✅ Map integration optional

**Use Cases:**
- Support inquiries
- Sales contacts
- General information
- Appointment booking

---

### 3. Verkaufsseite (Sales Page)
**Purpose:** Product and sales pages  
**Category:** `sales`  
**Template:** `verkaufsseite`

```
┌─────────────────────────────────────┐
│      SALES HERO                     │
│  "Das perfekte Produkt"             │
│  [Jetzt kaufen]                     │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│      BENEFITS                       │
│  ┌──┐  ┌──┐  ┌──┐                  │
│  │✓1│  │✓2│  │✓3│                  │
│  └──┘  └──┘  └──┘                  │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│      PRICING                        │
│  ┌──────────────┐                   │
│  │    99€       │                   │
│  │ [Bestellen]  │                   │
│  └──────────────┘                   │
└─────────────────────────────────────┘
```

**Key Features:**
- ✅ Conversion-optimized layout
- ✅ Benefits showcase
- ✅ Pricing section
- ✅ Multiple CTAs
- ✅ Trust elements

**Use Cases:**
- Product sales
- Service packages
- Subscription offers
- Digital products

---

### 4. Infoseite (Info Page)
**Purpose:** Content, documentation, and guides  
**Category:** `info`  
**Template:** `infoseite`

```
┌─────────────────────────────────────┐
│         HEADER                      │
│  "Informationen"                    │
└─────────────────────────────────────┘
┌────────┬────────────────────────────┐
│ SIDE   │  MAIN CONTENT              │
│ BAR    │  ┌──────────────────┐      │
│ Nav 1  │  │ ## Heading       │      │
│ Nav 2  │  │ Content text...  │      │
│ Nav 3  │  │                  │      │
│        │  │ ### Subheading   │      │
│        │  │ More content...  │      │
│        │  └──────────────────┘      │
└────────┴────────────────────────────┘
```

**Key Features:**
- ✅ Sidebar navigation (sticky)
- ✅ Article layout
- ✅ Documentation-friendly
- ✅ Code highlighting support
- ✅ Multi-level structure

**Use Cases:**
- Documentation pages
- Help centers
- Knowledge base
- Guides and tutorials

---

## 🚀 Quick Start

### 1. Install Templates
```bash
cd telis_recruitment
python manage.py migrate
python manage.py seed_layout_templates
```

### 2. Use via API
```javascript
// Get templates by category
fetch('/pages/templates/category/landing/')
  .then(r => r.json())
  .then(data => console.log(data.templates));

// Apply template
fetch('/pages/templates/1/apply/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    slug: 'my-page',
    title: 'My Page'
  })
});
```

### 3. Customize in Builder
1. Navigate to `/pages/builder/my-page/`
2. Edit in GrapesJS visual builder
3. Save and publish

---

## 📊 Template Comparison

| Feature | Landing | Contact | Sales | Info |
|---------|---------|---------|-------|------|
| Hero Section | ✅ | ✅ | ✅ | ✅ |
| Form Integration | ❌ | ✅ | ❌ | ❌ |
| Benefits Grid | ✅ | ❌ | ✅ | ❌ |
| Pricing Section | ❌ | ❌ | ✅ | ❌ |
| Sidebar Nav | ❌ | ❌ | ❌ | ✅ |
| Content Layout | Simple | 2-Column | Complex | Article |
| Best For | Marketing | Support | E-Commerce | Docs |

---

## 🎯 Layout Configuration

Each template includes a `layout_config` field:

```json
{
  "sections": ["hero", "features", "cta"],
  "customizable": true,
  "flexible_grid": true,
  "form_integration": false,
  "conversion_optimized": false,
  "documentation_friendly": false
}
```

This config helps you:
- ✅ Understand template structure
- ✅ Identify available sections
- ✅ Choose right template for use case
- ✅ Extend templates programmatically

---

## 🔧 Customization Levels

### Level 1: Content Only
- Change text, images, colors in builder
- No coding required

### Level 2: Layout Adjustment
- Add/remove sections
- Reorder components
- Use block library

### Level 3: CSS Customization
- Custom styles in builder
- Brand-specific theming
- Advanced animations

### Level 4: Template Creation
- Create from scratch
- Save as new template
- Share with team

---

## 📱 Responsive Design

All templates are mobile-first and responsive:

```css
/* Desktop */
@media (min-width: 1024px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}

/* Tablet */
@media (max-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

/* Mobile */
@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
}
```

---

## 🎨 Color Schemes

### Landing Page
- Primary: `#667eea` (Purple)
- Background: Gradient purple

### Contact Page
- Primary: `#667eea` (Purple)
- Background: `#f8f9fa` (Light gray)

### Sales Page
- Primary: `#f5576c` (Pink)
- Background: Gradient pink

### Info Page
- Primary: `#667eea` (Purple)
- Sidebar: `#f8f9fa` (Light gray)

All colors fully customizable via builder!

---

## 📈 Usage Statistics

Templates track usage automatically:

```python
template = PageTemplate.objects.get(slug='moderne-landingpage')
print(f"Used {template.usage_count} times")
```

Popular templates appear first in selection UI.

---

## 🔗 Integration Points

### Form Integration (Contact)
```html
<form method="POST" action="/pages/submit/">
  <!-- Auto-routes to lead system -->
</form>
```

### Brevo Integration
```python
page.brevo_list_id = 123
page.save()
# Form submissions sync to Brevo
```

### Domain Hosting
All templates support:
- Internal hosting
- STRATO domains
- Custom domains

---

## 📚 Documentation

Full guide: `TEMPLATE_SYSTEM_GUIDE.md`

Topics covered:
- API endpoints
- Management commands
- Template creation
- Customization guide
- Best practices
- Troubleshooting

---

## ✨ Future Enhancements

Planned features:
- [ ] More template categories
- [ ] Template marketplace
- [ ] A/B testing support
- [ ] Analytics integration
- [ ] Template versioning
- [ ] Collaborative editing
- [ ] Template export/import
- [ ] Preview mode

---

## 🤝 Support

Questions? Check:
1. `TEMPLATE_SYSTEM_GUIDE.md` - Full documentation
2. Admin interface - `/admin/pages/pagetemplate/`
3. API endpoints - `/pages/templates/`

---

**Made with ❤️ for flexible, user-friendly page building**
