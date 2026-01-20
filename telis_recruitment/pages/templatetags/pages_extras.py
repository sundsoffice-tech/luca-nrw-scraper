"""Template filters for pages app with security sanitization."""

from django import template
from ...mailbox.utils.security import sanitize_page_html, sanitize_css

register = template.Library()


@register.filter(is_safe=True)
def sanitize_page(value):
    """
    Sanitize landing page HTML content to prevent XSS attacks.
    Usage: {{ page.html|sanitize_page }}
    """
    return sanitize_page_html(value)


@register.filter(is_safe=True)
def sanitize_page_css(value):
    """
    Sanitize CSS content to prevent CSS-based XSS attacks.
    Usage: {{ page.css|sanitize_page_css }}
    """
    return sanitize_css(value)
