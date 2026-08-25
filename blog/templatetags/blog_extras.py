import re

from django import template
from django.template.defaultfilters import linebreaks
from django.utils.safestring import mark_safe

register = template.Library()

_HTML_TAG = re.compile(r'<[a-zA-Z][^>]*>')


@register.filter
def as_rich_text(value):
    """Render stored HTML, or convert plain text newlines to paragraphs."""
    if not value:
        return ''
    text = str(value)
    if _HTML_TAG.search(text):
        return mark_safe(text)
    return linebreaks(text)
