import re

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

from ..utils.security import sanitize_email_html, sanitize_quoted_content

register = template.Library()


@register.filter(is_safe=True)
def highlight(value, term):
    if not term:
        return value
    try:
        escaped_value = conditional_escape(value)
    except Exception:
        escaped_value = value
    escaped_term = re.escape(term)
    pattern = re.compile(escaped_term, re.IGNORECASE)

    def repl(match):
        return format_html('<mark>{}</mark>', match.group(0))

    highlighted = pattern.sub(repl, str(escaped_value))
    return mark_safe(highlighted)


@register.filter(is_safe=True)
def sanitize_email(value):
    """
    Sanitize email HTML content to prevent XSS attacks.
    Usage: {{ email.body_html|sanitize_email }}
    """
    return sanitize_email_html(value)


@register.filter(is_safe=True)
def sanitize_quoted(value):
    """
    Sanitize quoted email content for reply forms.
    Usage: {{ quoted_content|sanitize_quoted }}
    """
    return sanitize_quoted_content(value)
