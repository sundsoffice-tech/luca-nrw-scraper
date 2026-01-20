"""Template filters for email_templates app with security sanitization."""

import json
from django import template
from django.utils.safestring import mark_safe
from ...mailbox.utils.security import sanitize_email_html

register = template.Library()


@register.filter(is_safe=True)
def sanitize_email_template(value):
    """
    Sanitize email template HTML content to prevent XSS attacks.
    Usage: {{ template.html_content|sanitize_email_template }}
    """
    return sanitize_email_html(value)


@register.filter(is_safe=True)
def json_encode(value):
    """
    Safely encode Python data as JSON for use in JavaScript.
    Only use this for data structures, not user-generated content.
    Usage: {{ data|json_encode }}
    """
    # Validate that value is a safe data structure (dict, list, etc.)
    # Do not use this for arbitrary user input
    if value is None:
        return mark_safe('null')
    
    if not isinstance(value, (dict, list, tuple, str, int, float, bool)):
        # Reject unsafe types
        raise ValueError(f"json_encode only accepts basic Python types, got {type(value)}")
    
    return mark_safe(json.dumps(value))
