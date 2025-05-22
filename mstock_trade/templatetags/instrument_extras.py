from django import template

register = template.Library()

@register.filter(name='getattr')
def getattribute(obj, attr):
    """
    Usage: {{ obj|getattr:"field_name" }}
    """
    try:
        return getattr(obj, attr)
    except Exception:
        return ''
