"""
Security utilities for sanitizing HTML and CSS content to prevent XSS attacks.
"""
import bleach
from bleach.css_sanitizer import CSSSanitizer
from django.utils.safestring import mark_safe


# Allowed HTML tags for email content (based on common email clients)
ALLOWED_EMAIL_TAGS = [
    # Text formatting
    'p', 'br', 'hr', 'div', 'span', 'blockquote', 'pre', 'code',
    # Headers
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # Lists
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    # Tables
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
    # Links and media
    'a', 'img',
    # Text styling
    'b', 'i', 'u', 's', 'em', 'strong', 'small', 'mark', 'del', 'ins', 'sub', 'sup',
]

# Allowed HTML attributes for email content
ALLOWED_EMAIL_ATTRIBUTES = {
    '*': ['class', 'id', 'style', 'title', 'dir', 'lang'],
    'a': ['href', 'target', 'rel', 'name'],
    'img': ['src', 'alt', 'width', 'height', 'align', 'border'],
    'table': ['border', 'cellpadding', 'cellspacing', 'width'],
    'td': ['colspan', 'rowspan', 'align', 'valign'],
    'th': ['colspan', 'rowspan', 'align', 'valign'],
}

# CSS properties allowed in style attributes
ALLOWED_CSS_PROPERTIES = [
    # Colors
    'color', 'background', 'background-color', 'background-image',
    # Text
    'font-family', 'font-size', 'font-weight', 'font-style', 'text-align',
    'text-decoration', 'line-height', 'letter-spacing', 'word-spacing',
    # Spacing
    'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
    'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
    # Sizing
    'width', 'height', 'min-width', 'min-height', 'max-width', 'max-height',
    # Border
    'border', 'border-top', 'border-right', 'border-bottom', 'border-left',
    'border-width', 'border-style', 'border-color', 'border-radius',
    # Display
    'display', 'float', 'clear', 'vertical-align',
]

# Allowed HTML tags for landing pages (more permissive for page builder)
ALLOWED_PAGE_TAGS = ALLOWED_EMAIL_TAGS + [
    'article', 'section', 'nav', 'aside', 'header', 'footer', 'main',
    'figure', 'figcaption', 'video', 'audio', 'source', 'iframe',
    'form', 'input', 'textarea', 'button', 'select', 'option', 'label',
]

# Allowed attributes for landing pages
ALLOWED_PAGE_ATTRIBUTES = {
    **ALLOWED_EMAIL_ATTRIBUTES,
    '*': ALLOWED_EMAIL_ATTRIBUTES['*'] + ['data-*', 'aria-*'],
    'form': ['action', 'method', 'enctype', 'data-landing-form'],
    'input': ['type', 'name', 'value', 'placeholder', 'required', 'pattern', 'min', 'max'],
    'textarea': ['name', 'rows', 'cols', 'placeholder', 'required'],
    'button': ['type', 'name', 'value'],
    'select': ['name', 'multiple', 'required'],
    'option': ['value', 'selected'],
    'label': ['for'],
    'video': ['src', 'controls', 'autoplay', 'loop', 'muted', 'poster', 'width', 'height'],
    'audio': ['src', 'controls', 'autoplay', 'loop'],
    'source': ['src', 'type'],
    'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen'],
}


def sanitize_email_html(html_content):
    """
    Sanitize HTML content from emails to prevent XSS while preserving formatting.
    
    Args:
        html_content: Raw HTML content from email
        
    Returns:
        Sanitized HTML safe for rendering
    """
    if not html_content:
        return ""
    
    css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)
    
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_EMAIL_TAGS,
        attributes=ALLOWED_EMAIL_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True,  # Remove disallowed tags instead of escaping them
        strip_comments=True,
    )
    
    # Additional security: ensure all links open in new tab and have noopener
    cleaned = bleach.linkify(
        cleaned,
        callbacks=[lambda attrs, new: attrs if attrs.get('href', '').startswith('mailto:') else {**attrs, 'target': '_blank', 'rel': 'noopener noreferrer'}],
        skip_tags=['pre', 'code'],
    )
    
    return mark_safe(cleaned)


def sanitize_page_html(html_content):
    """
    Sanitize HTML content for landing pages created with page builder.
    More permissive than email sanitization to support page builder features.
    
    Args:
        html_content: Raw HTML content from page builder
        
    Returns:
        Sanitized HTML safe for rendering
    """
    if not html_content:
        return ""
    
    css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)
    
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_PAGE_TAGS,
        attributes=ALLOWED_PAGE_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True,
        strip_comments=True,
    )
    
    return mark_safe(cleaned)


def sanitize_css(css_content):
    """
    Sanitize CSS content to prevent CSS-based XSS attacks.
    
    Args:
        css_content: Raw CSS content
        
    Returns:
        Sanitized CSS safe for rendering
    """
    if not css_content:
        return ""
    
    # Remove potentially dangerous CSS patterns
    dangerous_patterns = [
        'javascript:',
        'expression(',
        'behavior:',
        '-moz-binding:',
        '@import',
        'vbscript:',
        'data:text/html',
    ]
    
    cleaned = css_content
    for pattern in dangerous_patterns:
        cleaned = cleaned.replace(pattern, '')
    
    # Basic validation: CSS should not contain script tags or other HTML
    if '<script' in cleaned.lower() or 'javascript:' in cleaned.lower():
        return ""
    
    return mark_safe(cleaned)


def sanitize_quoted_content(html_content):
    """
    Sanitize quoted email content for reply forms.
    Uses same rules as email sanitization but adds blockquote styling.
    
    Args:
        html_content: Raw HTML content to be quoted
        
    Returns:
        Sanitized HTML safe for rendering in reply form
    """
    return sanitize_email_html(html_content)
