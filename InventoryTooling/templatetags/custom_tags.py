from django import template
from django.utils.http import urlencode

# encode url di pagination result
register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.dict()
    query.update(kwargs)
    return urlencode(query)


#   cut text before specific char
@register.filter(name='cut_before')
def cut_before(value, arg):
    return value.split(arg)[0] if arg in value else value


#   cut text after specific char
@register.filter(name='cut_after')
def cut_after(value, char):
    # find position of the char
    parts = value.split(char, 1)
    return parts[1] if len(parts) > 1 else ''
