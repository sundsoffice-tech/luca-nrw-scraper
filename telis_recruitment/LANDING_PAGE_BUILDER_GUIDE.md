# Landing Page Builder - Complete Feature Documentation

## Overview
The Landing Page Builder has been completely upgraded with a professional GrapesJS-based interface, including 35+ pre-built blocks, asset management, brand settings, and template system.

---

## 🎯 Key Features

### 1. Full GrapesJS Editor UI
- **3-Panel Layout**: Left (Blocks & Assets), Center (Canvas), Right (Styles & Layers)
- **Top Toolbar**: Save, Undo/Redo, Device Preview, Publish
- **Device Preview**: Desktop 🖥️, Tablet 💻, Mobile 📱
- **Auto-Save**: Every 60 seconds
- **Dark Theme**: Professional dark UI optimized for long editing sessions

### 2. Asset Manager 🖼️
Upload and manage images directly in the builder:
- **Drag & Drop Upload**: Upload multiple images at once
- **Automatic Metadata**: Width, height, file size extracted automatically
- **Folder Organization**: Organize assets in folders
- **Alt Text for SEO**: Add alt text for better SEO
- **Click to Copy URL**: Easy integration into pages

**API Endpoints:**
```
POST   /pages/assets/upload/           - Upload new asset
GET    /pages/assets/                  - List all assets
DELETE /pages/assets/<id>/delete/      - Delete asset
```

### 3. Brand Settings 🎨
Global brand configuration for consistent styling:

**Colors:**
- Primary Color
- Secondary Color
- Accent Color
- Text Color
- Background Color

**Typography:**
- Heading Font (Inter, Poppins, Roboto, Montserrat, Lato)
- Body Font (Open Sans, Roboto, Lato, Source Sans Pro, Inter)
- Base Font Size (12-24px)

**Branding:**
- Logo (Light version)
- Logo Dark (Dark version)
- Favicon

**Social Media:**
- Facebook, Instagram, LinkedIn, Twitter, YouTube URLs

**Contact Information:**
- Company Name, Email, Phone, Address

**Legal Links:**
- Privacy Policy, Imprint, Terms of Service URLs

**CSS Variables Generation:**
Brand settings automatically generate CSS custom properties:
```css
:root {
    --brand-primary: #007bff;
    --brand-secondary: #6c757d;
    --brand-accent: #28a745;
    --brand-text: #212529;
    --brand-background: #ffffff;
    --font-heading: 'Inter', sans-serif;
    --font-body: 'Open Sans', sans-serif;
    --font-size-base: 16px;
}
```

**Access:**
```
GET/POST /pages/brand-settings/         - View/Edit settings
GET      /pages/brand-settings/css/     - Get CSS variables
```

### 4. Template System 📄
Pre-built professional templates for quick start:

**Categories:**
- Lead Generation
- Product
- Service
- Event
- Coming Soon
- Thank You

**Features:**
- Visual thumbnail preview
- Usage counter
- One-click application to new pages
- Category-based organization

**Access:**
```
GET  /pages/templates/                    - Browse templates
POST /pages/templates/<id>/apply/         - Apply to page
```

---

## 📦 35+ Pre-Built Blocks

### Layout Blocks (6)
1. **Section** - Full-width container
2. **2 Column Grid** - 50/50 split
3. **3 Column Grid** - 33/33/33 split
4. **4 Column Grid** - 25/25/25/25 split
5. **Divider** - Horizontal line
6. **Spacer** - Vertical spacing

### Basic Blocks (7)
1. **Heading** - H1-H6 with brand fonts
2. **Paragraph** - Text content
3. **Image** - Responsive images
4. **Button** - Call-to-action button
5. **Link** - Hyperlink
6. **List** - Unordered/ordered lists
7. **Quote** - Blockquote/testimonial

### Form Blocks (7)
1. **Form Container** - Form wrapper
2. **Input Field** - Text input
3. **Textarea** - Multi-line text
4. **Select** - Dropdown menu
5. **Checkbox** - Single checkbox
6. **Radio Buttons** - Radio group
7. **Submit Button** - Form submission

### LUCA Custom Sections (11)
Professional, ready-to-use sections:

1. **🎯 Hero Section (Centered)**
   - Large headline with gradient background
   - Subheadline and CTA button
   - Perfect for landing pages

2. **🎯 Hero Section (Split)**
   - Left: Text + CTA
   - Right: Image/Video
   - Modern split-screen design

3. **📊 Stats Counter**
   - 4 animated statistic boxes
   - Icons, numbers, and labels
   - Perfect for showcasing achievements

4. **⭐ Testimonials Grid**
   - 3 testimonial cards
   - Photo, name, position, quote
   - 5-star rating display

5. **💰 Pricing Table**
   - 3 pricing tiers (Basic, Pro, Enterprise)
   - Highlighted "Recommended" tier
   - Feature lists and CTA buttons

6. **❓ FAQ Accordion**
   - Expandable question/answer pairs
   - Smooth animations
   - Plus/minus icons

7. **📞 CTA Section**
   - Eye-catching call-to-action
   - Gradient background
   - Large CTA button

8. **🏆 Features Grid**
   - 6 feature cards
   - Icon + title + description
   - Responsive grid layout

9. **📧 Lead Form (Advanced)**
   - Professional multi-field form
   - First/last name, email, phone, message
   - GDPR checkbox
   - Styled submit button

10. **⏰ Countdown Timer**
    - Days, hours, minutes, seconds
    - Configurable target date
    - Multiple design styles

11. **🦶 Footer**
    - Logo and company info
    - Navigation links
    - Social media icons
    - Copyright and legal links

### Advanced Blocks (4)
1. **🗺️ Google Maps** - Embedded map
2. **🎥 Video Embed** - YouTube/Vimeo
3. **👥 Social Icons** - Social media links
4. **📦 Icon Box** - Icon + text card

---

## 🚀 Usage Guide

### Creating a New Page

1. **From Template (Recommended):**
   ```
   Navigate to: /pages/templates/
   → Select template
   → Enter slug and title
   → Click "Create Page"
   → Start editing in builder
   ```

2. **From Scratch:**
   ```
   Django Admin → Landing Pages → Add Landing Page
   → Enter title and slug
   → Save
   → Click "Edit in Builder"
   ```

### Editing a Page

1. **Access Builder:**
   ```
   Navigate to: /pages/builder/<slug>/
   ```

2. **Add Blocks:**
   - Browse blocks in left panel
   - Click or drag block to canvas
   - Blocks are organized by category

3. **Customize Styles:**
   - Select element on canvas
   - Edit properties in right panel:
     - Colors (background, text, border)
     - Layout (width, height, margin, padding)
     - Typography (font, size, weight)
     - Decorations (border radius, shadow)

4. **Manage Assets:**
   - Click "Upload" in Assets panel
   - Select images to upload
   - Click asset to copy URL
   - Paste URL in image src

5. **Device Preview:**
   - Click device icons in toolbar
   - Preview on Desktop 🖥️, Tablet 💻, Mobile 📱

6. **Save & Publish:**
   - Auto-saves every 60 seconds
   - Manual save: Click "💾 Save" or Ctrl+S
   - Publish: Click "🚀 Publish" button

### Configuring Brand Settings

1. **Access Settings:**
   ```
   Navigate to: /pages/brand-settings/
   ```

2. **Configure:**
   - Set brand colors
   - Choose fonts
   - Upload logo and favicon
   - Add social media links
   - Enter contact information
   - Set legal URLs

3. **Apply:**
   - Click "💾 Save Settings"
   - CSS variables automatically generated
   - All pages use brand settings via `var(--brand-primary)` etc.

### Using Brand Variables in Custom CSS

```css
.my-button {
    background-color: var(--brand-primary);
    color: var(--brand-background);
    font-family: var(--font-body);
    font-size: var(--font-size-base);
}
```

---

## 🔧 Technical Details

### File Structure
```
pages/
├── models.py                      # Updated models
├── views.py                       # New views for assets/brand/templates
├── urls.py                        # New URL routes
├── admin.py                       # Admin for new models
├── static/pages/
│   ├── js/
│   │   └── blocks/
│   │       ├── index.js           # Block loader
│   │       ├── layout.js          # Layout blocks
│   │       ├── basic.js           # Basic blocks
│   │       ├── forms.js           # Form blocks
│   │       ├── luca-custom.js     # LUCA custom sections
│   │       └── advanced.js        # Advanced blocks
│   └── css/
│       └── builder.css            # Builder UI styles
├── templates/pages/
│   ├── builder.html               # NEW: Complete builder UI
│   ├── brand_settings.html        # NEW: Brand settings page
│   └── select_template.html       # NEW: Template selection
└── migrations/
    └── 0004_pageasset_brandsettings_pagetemplate.py
```

### New Models

**PageAsset:**
- Stores uploaded images/media
- Tracks dimensions, file size, metadata
- Folder organization

**BrandSettings:**
- Global brand configuration
- Generates CSS variables
- Single instance (singleton pattern)

**PageTemplate:**
- Pre-built page templates
- Tracks usage count
- Category-based organization

### Dependencies Added
```
Pillow>=10.0.0  # For image processing
```

---

## 🎨 Styling Guidelines

### Using Brand Colors
Always use CSS variables for brand colors:
```html
<div style="background: var(--brand-primary); color: var(--brand-background);">
    Content
</div>
```

### Using Brand Fonts
```html
<h1 style="font-family: var(--font-heading);">Heading</h1>
<p style="font-family: var(--font-body);">Body text</p>
```

### Responsive Design
All blocks are mobile-first and responsive:
- Desktop: Full width
- Tablet: Adjusted layout
- Mobile: Single column

---

## 🔐 Security Features

- **CSRF Protection**: All POST endpoints protected
- **File Type Validation**: Only images allowed in asset manager
- **Size Validation**: File size limits enforced
- **Staff Only**: Builder accessible only to staff members
- **Image Processing**: Automatic dimension extraction with Pillow

---

## 📊 Admin Interface

New admin sections:
1. **Page Assets** - View/manage uploaded assets
2. **Brand Settings** - Configure global brand (single instance)
3. **Page Templates** - Manage templates

Enhanced Landing Page admin:
- Direct links to Builder, Upload Manager, Domain Settings
- Status and hosting badges
- Publish/unpublish actions

---

## 🚨 Known Limitations

1. **Template Preview**: Preview feature not yet implemented
2. **Publish Endpoint**: Publish button shows alert (needs endpoint)
3. **Animation**: Countdown timer and stats counter need JavaScript
4. **FAQ Accordion**: Needs JavaScript for expand/collapse
5. **Image Field Migration**: Requires `Pillow` installed before running migrations

---

## 🔄 Migration Steps

1. **Install Pillow:**
   ```bash
   pip install Pillow>=10.0.0
   ```

2. **Run Migrations:**
   ```bash
   python manage.py migrate pages
   ```

3. **Create Brand Settings:**
   ```bash
   python manage.py shell
   >>> from pages.models import BrandSettings
   >>> BrandSettings.objects.create()
   ```

4. **Access Builder:**
   ```
   Navigate to: /pages/builder/<slug>/
   ```

---

## 📚 Additional Resources

- **GrapesJS Documentation**: https://grapesjs.com/docs/
- **CSS Custom Properties**: https://developer.mozilla.org/en-US/docs/Web/CSS/--*
- **Responsive Design**: Use media queries for fine-tuning

---

## ✅ Checklist for Production

- [ ] Run migrations
- [ ] Install Pillow dependency
- [ ] Create Brand Settings instance
- [ ] Configure MEDIA_URL and MEDIA_ROOT
- [ ] Set up static file serving
- [ ] Test asset uploads
- [ ] Test brand settings
- [ ] Create initial templates
- [ ] Configure Brevo for forms
- [ ] Add publish endpoint
- [ ] Test responsive design
- [ ] Run security checks

---

## 🤝 Support

For questions or issues, contact the development team.

**Version**: 2.0.0  
**Last Updated**: 2024-01-19
