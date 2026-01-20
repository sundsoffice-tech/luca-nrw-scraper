import re

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

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
