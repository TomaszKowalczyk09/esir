from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def get_item(d, key):
    try:
        return d.get(key)
    except Exception:
        return None


def _format_opis_inline(text):
    rendered = escape(text)
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"\*(.+?)\*", r"<em>\1</em>", rendered)
    rendered = re.sub(r"__(.+?)__", r"<u>\1</u>", rendered)
    return rendered


@register.filter
def format_opis(value):
    if not value:
        return ""

    lines = str(value).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    html = []
    in_list = False
    paragraph_buffer = []

    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            html.append(f"<p>{'<br>'.join(paragraph_buffer)}</p>")
            paragraph_buffer = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            if in_list:
                html.append("</ul>")
                in_list = False
            continue

        list_match = re.match(r"^[-*•]\s+(.+)$", line)
        if list_match:
            flush_paragraph()
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{_format_opis_inline(list_match.group(1))}</li>")
            continue

        if in_list:
            html.append("</ul>")
            in_list = False
        paragraph_buffer.append(_format_opis_inline(line))

    flush_paragraph()
    if in_list:
        html.append("</ul>")

    return mark_safe("".join(html))
