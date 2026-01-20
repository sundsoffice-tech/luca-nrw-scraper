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

# CSS properties allowed in style attributes (remove potentially dangerous ones)
ALLOWED_CSS_PROPERTIES = [
    # Colors
    'color', 'background', 'background-color',
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

# Allowed attributes for landing pages (more restrictive on iframe)
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
    # Iframe with restricted attributes (no arbitrary src for security)
    # Note: iframes are a security risk - consider removing if not needed
    'iframe': ['width', 'height', 'frameborder', 'allowfullscreen'],
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
    
    # Note: bleach.linkify has compatibility issues with newer versions
    # Skipping linkify for now - the clean() method already handles href sanitization
    
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
    
    import re
    
    # Remove potentially dangerous CSS patterns (case-insensitive, whitespace-tolerant)
    dangerous_patterns = [
        r'javascript\s*:',  # javascript: URLs
        r'expression\s*\(',  # IE CSS expressions
        r'behavior\s*:',  # IE CSS behaviors
        r'-moz-binding\s*:',  # Mozilla binding
        r'@import',  # CSS imports
        r'vbscript\s*:',  # VBScript URLs
        r'data\s*:\s*text\s*/\s*html',  # Data URLs with HTML
    ]
    
    cleaned = css_content
    for pattern in dangerous_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Basic validation: CSS should not contain script tags or other HTML
    if re.search(r'<script', cleaned, re.IGNORECASE):
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
