from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """Get value from dictionary by key in template."""
    try:
        return d.get(key, 0)
    except Exception:
        return 0