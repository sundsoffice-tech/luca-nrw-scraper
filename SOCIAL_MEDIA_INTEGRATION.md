# Social Media Integration - Implementation Guide

## Overview

This document describes the comprehensive social media integration features added to the LUCA NRW Scraper landing page builder, enabling content optimization for Facebook, WhatsApp, Twitter/X, and LinkedIn.

## Features

### 1. OpenGraph Meta Tags
Full OpenGraph support with intelligent fallbacks to SEO fields:
- `og:title` - Falls back to `seo_title` or page `title`
- `og:description` - Falls back to `seo_description`
- `og:image` - Falls back to `seo_image`
- `og:type` - Configurable (default: website)
- `og:url` - Automatically set from page URL
- `og:locale` - Set to de_DE for German content

### 2. Twitter Card Support
Optimized Twitter/X card integration:
- `twitter:card` - Configurable (summary_large_image or summary)
- `twitter:title` - Falls back to OpenGraph title
- `twitter:description` - Falls back to OpenGraph description
- `twitter:image` - Falls back to OpenGraph image

### 3. Social Share Buttons
Configurable share buttons for major platforms:
- **Supported Platforms**: Facebook, Twitter/X, WhatsApp, LinkedIn
- **Positioning**: Top-left, Top-right, Bottom-left, Bottom-right, Inline
- **Responsive Design**: Mobile-optimized with auto-collapse
- **Smooth Animations**: Slide-in effects and hover states

### 4. Social Media Preview Tool
Visual preview showing how pages appear when shared:
- Facebook/WhatsApp preview
- Twitter/X preview
- LinkedIn preview
- Optimization recommendations

## Usage

### For Content Creators

#### Configuring Social Media Settings

1. **Open the Page Builder**
   - Navigate to CRM → Pages → Select your page
   - Click "Edit" to open the builder

2. **Access Social Media Settings**
   - Click the "🔗 Social Media" button in the toolbar
   - A modal will open with three tabs

3. **Meta Tags Tab**
   - Configure OpenGraph and Twitter Card settings
   - Add titles, descriptions, and image URLs
   - Recommended image size: 1200x630px (OG) or 1200x628px (Twitter)

4. **Share Buttons Tab**
   - Enable/disable share buttons
   - Choose button position
   - Select which platforms to enable

5. **Preview Tab**
   - Click "Open Social Media Preview" to see how your page will look
   - Check previews for Facebook, Twitter, and LinkedIn

#### Best Practices

**Image Recommendations:**
- OpenGraph: 1200x630px (Facebook, WhatsApp, LinkedIn)
- Twitter Card: 1200x628px
- Format: JPG or PNG
- File size: Under 1MB for fast loading

**Text Recommendations:**
- Title: 60-90 characters
- Description: 150-160 characters
- Use action-oriented language
- Include keywords naturally

**Share Button Placement:**
- **Bottom-right**: Default, least intrusive
- **Top-right**: High visibility
- **Inline**: Best for call-to-action sections

### For Developers

#### Model Fields

New fields added to `LandingPage` model:

```python
# OpenGraph fields
og_title = CharField(max_length=255, blank=True)
og_description = TextField(blank=True)
og_image = URLField(blank=True)
og_type = CharField(max_length=50, default='website')

# Twitter Card fields
twitter_card = CharField(max_length=50, default='summary_large_image')
twitter_title = CharField(max_length=255, blank=True)
twitter_description = TextField(blank=True)
twitter_image = URLField(blank=True)

# Share button settings
enable_share_buttons = BooleanField(default=False)
share_button_position = CharField(max_length=20, default='bottom-right')
share_platforms = JSONField(default=list, blank=True)
```

#### Helper Methods

```python
# Intelligent fallback methods
page.get_og_title()          # Returns og_title or seo_title or title
page.get_og_description()    # Returns og_description or seo_description
page.get_og_image()          # Returns og_image or seo_image
page.get_twitter_title()     # Returns twitter_title or og_title
page.get_share_platforms()   # Returns enabled platforms with defaults
```

#### API Endpoints

**Save social media settings:**
```python
POST /crm/pages/api/<slug>/save/
{
    "html": "...",
    "css": "...",
    "html_json": {...},
    "social_media": {
        "og_title": "My Page Title",
        "og_description": "Page description",
        "og_image": "https://example.com/image.jpg",
        "twitter_card": "summary_large_image",
        "enable_share_buttons": true,
        "share_button_position": "bottom-right",
        "share_platforms": ["facebook", "twitter", "whatsapp"]
    }
}
```

**Load social media settings:**
```python
GET /crm/pages/api/<slug>/load/
Response:
{
    "html": "...",
    "css": "...",
    "html_json": {...},
    "page": {
        "og_title": "...",
        "og_description": "...",
        "enable_share_buttons": true,
        ...
    }
}
```

#### Template Usage

**In public pages:**
```django
{% load pages_extras %}

<!-- Meta tags are automatically rendered -->
<meta property="og:title" content="{{ page.get_og_title }}">
<meta property="og:image" content="{{ page.get_og_image }}">

<!-- Share buttons (only if enabled) -->
{% if page.enable_share_buttons %}
    <!-- Buttons rendered automatically -->
{% endif %}
```

## Migration

The implementation includes migration `0012_add_social_media_fields.py`:

```bash
# Apply migration
python manage.py migrate pages
```

All new fields have default values, so existing pages are not affected.

## Testing

Comprehensive test suite included in `pages/tests.py`:

```bash
# Run all tests
python manage.py test pages.SocialMediaIntegrationTest

# Run specific test
python manage.py test pages.SocialMediaIntegrationTest.test_og_fallback_methods
```

### Test Coverage

- ✅ Model field existence
- ✅ Fallback method logic
- ✅ Meta tag rendering
- ✅ Share button rendering
- ✅ Social preview access control
- ✅ Save/load functionality
- ✅ Platform preview display

## Security

All security best practices implemented:

1. **XSS Protection**: All user-generated content in JSON-LD is escaped using `|escapejs`
2. **CSRF Protection**: All POST requests require CSRF token
3. **Access Control**: Social media settings require staff authentication
4. **Link Security**: External links use `rel="noopener noreferrer"`
5. **CodeQL Scan**: 0 security alerts

## Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Known Limitations

1. Share platforms cannot be dynamically added (limited to Facebook, Twitter/X, WhatsApp, LinkedIn)
2. Image optimization is not automatic - users must provide properly sized images
3. Preview tool shows mockups, not actual social media renders

## Future Enhancements

Potential improvements for future versions:

1. **Image Optimization**: Automatic image resizing and optimization
2. **A/B Testing**: Test different titles/images for better engagement
3. **Analytics Integration**: Track share button clicks
4. **More Platforms**: Pinterest, Reddit, Telegram
5. **Auto-generation**: AI-powered title and description suggestions
6. **Real Preview**: Integration with Facebook/Twitter preview APIs

## Support

For issues or questions:
1. Check existing tests for usage examples
2. Review code comments in views.py and models.py
3. Open an issue on GitHub with the `social-media` label

## Changelog

### v1.0.0 (2026-01-20)
- Initial implementation
- Full OpenGraph and Twitter Card support
- Share buttons for 4 major platforms
- Visual social media preview tool
- Comprehensive test coverage
- Security audit passed (0 CodeQL alerts)
