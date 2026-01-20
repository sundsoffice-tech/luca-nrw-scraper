# Pages App - Landing Page Builder

## Overview

The `pages` Django app provides a no-code landing page builder using GrapesJS, integrated into the TELIS CRM system. It enables staff members to create, edit, and publish landing pages without writing code, while automatically capturing form submissions and syncing leads to Brevo.

## Features

- **GrapesJS Builder**: Visual drag-and-drop page builder with live preview
- **Responsive Editing**: Device-specific styles for Desktop, Tablet, and Mobile (NEW!)
- **Custom LUCA Blocks**: Pre-built components (Lead Form, Stats Counter, Testimonials)
- **Version History**: Auto-save with undo/redo capability
- **SEO Optimization**: Built-in meta tags, title, and description fields
- **Form Integration**: Automatic lead capture with Brevo sync
- **UTM Tracking**: Full campaign tracking support
- **Public Rendering**: Published pages served at `/p/<slug>/`

## Architecture

### Models

1. **LandingPage**: Main model for landing pages
   - Stores GrapesJS JSON, rendered HTML/CSS
   - Status (draft/published), SEO fields
   - Brevo integration settings

2. **PageVersion**: Version history for undo/redo
   - Each save creates a new version
   - Linked to user who made changes

3. **PageComponent**: Reusable components library
   - Pre-built blocks (Hero, Form, Stats, Testimonials)
   - Can be inserted into any landing page

4. **PageSubmission**: Form submission records
   - Links to Lead model
   - Captures UTM parameters and technical metadata

### URL Structure

**Builder Interface (Staff Only):**
- `/crm/pages/` - List all landing pages
- `/crm/pages/builder/<slug>/` - Edit page in GrapesJS
- `/crm/pages/api/<slug>/load/` - Load page data
- `/crm/pages/api/<slug>/save/` - Save page data

**Public Pages:**
- `/p/<slug>/` - View published landing page
- `/p/<slug>/submit/` - Form submission endpoint (AJAX)

## Usage

### Creating a New Landing Page

1. Go to Django Admin or `/crm/pages/`
2. Click "New Page" or create via admin
3. Set slug, title, and status
4. Click "Edit in Builder" to open GrapesJS
5. Drag and drop components to build your page
6. Use custom LUCA blocks from the sidebar:
   - **Lead Form**: Captures name, email, phone with Brevo opt-in
   - **Stats Counter**: Display key metrics
   - **Testimonials**: Customer testimonials grid
7. Save manually or rely on auto-save (every 30 seconds)
8. Set status to "Published" to make it live

### Custom Blocks

Custom blocks are defined in `/pages/static/pages/js/custom-blocks.js`. To add new blocks:

```javascript
grapesjs.BlockManager.add('my-block', {
    label: 'My Block',
    category: 'LUCA Custom',
    content: `
        <div class="my-custom-block">
            <!-- Your HTML here -->
        </div>
    `
});
```

### Form Submission

Forms must have the `data-landing-form` attribute to be auto-handled:

```html
<form data-landing-form>
    <input type="text" name="name" required />
    <input type="email" name="email" required />
    <input type="tel" name="phone" />
    <button type="submit">Submit</button>
</form>
```

The public page template automatically:
1. Captures form data on submit
2. Sends AJAX request to `/p/<slug>/submit/`
3. Extracts UTM parameters from URL
4. Creates/links Lead record
5. Syncs to Brevo with configured list ID

### Brevo Integration

Landing pages can specify a `brevo_list_id` to add form submissions to a specific Brevo list:

1. Set `brevo_list_id` in the LandingPage admin
2. Ensure `BREVO_API_KEY` is configured in settings
3. On form submission, lead is automatically synced to Brevo

The integration reuses the existing Brevo service in `leads/services/brevo.py`.

### Responsive Editing

**NEW!** The builder now supports device-specific styling for Desktop, Tablet, and Mobile:

1. **Switch Device Modes**: Use the toolbar buttons (🖥️ Desktop, 💻 Tablet, 📱 Mobile)
2. **Device Indicator**: Visual badge shows current editing mode (color-coded)
3. **Responsive Properties**:
   - **Typography**: Font sizes and line heights per device
   - **Spacing**: Margins and padding per device
   - **Visibility**: Show/hide elements on specific devices

**Example Workflow**:
1. Select an element in the canvas
2. Set Desktop font size to 48px in "Responsive Typography"
3. Set Tablet font size to 36px
4. Set Mobile font size to 24px
5. Switch device modes to preview changes
6. Save - CSS media queries are automatically generated

For detailed instructions, see [RESPONSIVE_EDITING_GUIDE.md](/RESPONSIVE_EDITING_GUIDE.md).

### Migration from Existing Landing

The initial migration (`0002_seed_landing_page.py`) imports the original `/landing/index.html` as a published page at `/p/home/` and creates seed components. This ensures continuity while providing the ability to edit the page in GrapesJS.

## Admin Interface

### LandingPage Admin

- **List View**: Shows title, slug, status, publish date, builder/preview links
- **Actions**:
  - Publish selected pages
  - Unpublish selected pages
  - Duplicate selected pages
- **Filters**: Status, created date, published date

### PageComponent Admin

- **List View**: Shows name, category, slug, active status
- **Filters**: Category, active status, created date
- Fully editable to add new reusable components

### PageSubmission Admin

- **List View**: Shows landing page, lead, submission date, UTM data
- **Filters**: Landing page, UTM source/medium/campaign, date hierarchy
- Read-only (submissions are records, not editable)
- Links to associated Lead record

## Development

### Adding Custom Blocks

1. Edit `/pages/static/pages/js/custom-blocks.js`
2. Add new block definition following the existing pattern
3. Refresh builder page to see new blocks

### Extending Models

If you need to add fields:

```bash
# Add field to models.py
python manage.py makemigrations pages
python manage.py migrate pages
```

### Testing

```python
from pages.models import LandingPage, PageSubmission
from leads.models import Lead

# Create a test page
page = LandingPage.objects.create(
    slug='test',
    title='Test Page',
    status='published',
    html='<h1>Test</h1>',
    css='h1 { color: red; }'
)

# Test form submission
submission = PageSubmission.objects.create(
    landing_page=page,
    data={'name': 'Test User', 'email': 'test@example.com'},
    utm_source='google',
    utm_campaign='test'
)
```

## Security

- Builder interface requires `@staff_member_required`
- Form submission endpoint uses `@csrf_exempt` (AJAX only)
- Client IP and User-Agent are captured for tracking
- Submissions are read-only in admin to preserve records

## Future Enhancements

- A/B testing support
- Analytics integration (Google Analytics, etc.)
- Email template builder (similar to landing pages)
- More custom blocks (FAQ, Pricing Table, Video, etc.)
- Drag-and-drop component ordering in admin
- Multi-language support

## Troubleshooting

**Builder doesn't load:**
- Check browser console for JavaScript errors
- Ensure GrapesJS CDN is accessible
- Verify CSRF token is present

**Form submissions not working:**
- Check that form has `data-landing-form` attribute
- Verify page status is "published"
- Check browser network tab for AJAX errors
- Review server logs for backend errors

**Brevo sync failing:**
- Verify `BREVO_API_KEY` in settings
- Check Brevo list ID is valid
- Review logs for Brevo API errors
- Ensure lead has email address

## Support

For issues or questions, contact the development team or refer to the main TELIS CRM documentation.
