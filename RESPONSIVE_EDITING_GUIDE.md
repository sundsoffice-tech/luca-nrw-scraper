# Responsive Editing Guide

## Overview

The TELIS CRM Page Builder now supports responsive editing, allowing you to create pages that look great on desktop, tablet, and mobile devices with device-specific styling.

## Features

### 1. Device Preview Modes

The page builder includes three device preview modes accessible via toolbar buttons:

- 🖥️ **Desktop** (Default) - Full width view
- 💻 **Tablet** - 768px width (media query: max-width 992px)
- 📱 **Mobile** - 375px width (media query: max-width 480px)

### 2. Device Mode Indicator

A visual indicator at the top of the right panel shows which device mode you're currently editing:
- **Blue badge**: Desktop View
- **Cyan badge**: Tablet View  
- **Green badge**: Mobile View

### 3. Responsive Style Properties

The Style Manager now includes three new responsive sections:

#### Responsive Typography
- **Font Size (Desktop)**: Base font size for desktop devices
- **Font Size (Tablet)**: Override font size for tablets (optional - inherits desktop if not set)
- **Font Size (Mobile)**: Override font size for mobile devices (optional - inherits desktop if not set)
- **Line Height (Tablet)**: Line height for tablet devices
- **Line Height (Mobile)**: Line height for mobile devices

#### Responsive Spacing
- **Margin (Tablet)**: Margin values for tablet devices
- **Margin (Mobile)**: Margin values for mobile devices
- **Padding (Tablet)**: Padding values for tablet devices
- **Padding (Mobile)**: Padding values for mobile devices

#### Responsive Visibility
- **Display (Desktop)**: Control element visibility on desktop
- **Display (Tablet)**: Control element visibility on tablet
- **Display (Mobile)**: Control element visibility on mobile

Set display to "Hidden" to hide elements on specific devices.

## How to Use

### Step 1: Select an Element
Click on any element in the canvas to select it.

### Step 2: Choose Device Mode
Click the device button in the toolbar to switch between Desktop, Tablet, and Mobile views.

### Step 3: Apply Responsive Styles

1. **For Typography**:
   - Open the "Responsive Typography" section in the Style Manager
   - Set the base Desktop font size
   - Optionally set different sizes for Tablet and Mobile
   - If Tablet/Mobile are left as "Inherit", they will use the Desktop value

2. **For Spacing**:
   - Open the "Responsive Spacing" section
   - Adjust margins and padding for Tablet and/or Mobile
   - Desktop spacing is controlled in the "Layout" section

3. **For Visibility**:
   - Open the "Responsive Visibility" section
   - Set display properties for each device
   - Use "Hidden" to hide elements on specific devices

### Step 4: Preview Your Changes
- Switch between device modes using the toolbar buttons
- The canvas will resize to show how your page looks on each device
- The device indicator shows which mode you're currently viewing

### Step 5: Save
- Click the 💾 Save button or press Ctrl+S to save your changes
- All responsive styles are automatically saved as CSS media queries

## Technical Details

### Media Query Generation

The system uses CSS media queries to apply device-specific styles:

```css
/* Desktop (base styles) */
.element {
    font-size: 48px;
    margin: 40px;
}

/* Tablet (max-width: 992px) */
@media (max-width: 992px) {
    .element {
        font-size: 36px;
        margin: 30px;
    }
}

/* Mobile (max-width: 480px) */
@media (max-width: 480px) {
    .element {
        font-size: 24px;
        margin: 20px;
    }
}
```

### Device Breakpoints

- **Desktop**: No media query (base styles)
- **Tablet**: `@media (max-width: 992px)`
- **Mobile**: `@media (max-width: 480px)`

## Best Practices

### 1. Mobile-First Approach (Optional)
While the builder uses desktop-first by default, you can think mobile-first:
- Start with desktop design
- Reduce font sizes and spacing for tablet
- Further reduce for mobile

### 2. Test All Devices
Always preview your page in all three device modes before publishing to ensure a consistent experience.

### 3. Use "Inherit" Wisely
If a tablet or mobile value is set to "Inherit", it will use the desktop value. This is useful when you only want to change specific breakpoints.

### 4. Hide Elements Strategically
Use the visibility controls to hide elements that don't work well on smaller screens:
- Large hero images on mobile
- Complex navigation on mobile
- Excessive text blocks on mobile

### 5. Consistent Spacing
Maintain proportional spacing across devices. If desktop has 40px margin, consider 30px for tablet and 20px for mobile.

## Examples

### Example 1: Responsive Hero Section

**Desktop**:
- Font Size: 48px
- Margin: 40px

**Tablet**:
- Font Size: 36px
- Margin: 30px

**Mobile**:
- Font Size: 24px
- Margin: 20px

### Example 2: Hide Element on Mobile

**Desktop**:
- Display: Flex

**Tablet**:
- Display: Flex

**Mobile**:
- Display: Hidden

### Example 3: Responsive Button

**Desktop**:
- Font Size: 18px
- Padding: 15px 30px

**Tablet**:
- Font Size: 16px
- Padding: 12px 24px

**Mobile**:
- Font Size: 14px
- Padding: 10px 20px

## Troubleshooting

### Styles Not Applying
- Make sure you've saved the page (Ctrl+S)
- Check that the correct device mode is selected
- Verify that the property isn't set to "Inherit"

### Preview Not Updating
- Try switching between device modes
- Refresh the page if needed
- Clear browser cache

### Media Queries Not Working
- Ensure the page has been published
- Check that the CSS includes @media rules
- Verify the breakpoints match your expectations

## Support

For issues or questions about responsive editing:
1. Check this guide first
2. Review the GrapesJS documentation
3. Contact the development team

## Version History

- **v1.0** (2024-01-20): Initial implementation
  - Added responsive typography controls
  - Added responsive spacing controls
  - Added responsive visibility controls
  - Added device mode indicator
  - Added media query support
