from django import template
from django.core.paginator import Paginator

register = template.Library()

SERVICE_PARAMS = {'scope'}

@register.simple_tag(takes_context=True)
def change_params(context, **kwargs):
    query = context['request'].GET.copy()

    sid = context.get("sid")

    if sid:
        query["sid"] = sid

    for i in SERVICE_PARAMS:
        query.pop(i, None)

    for key, value in kwargs.items():
        query[key] = value
    
    return query.urlencode()

@register.simple_tag
def get_proper_elided_page_range(page_obj, on_each_side=2, on_ends=1):

    return page_obj.paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=on_each_side,
        on_ends=on_ends)
    

@register.filter
def is_num(value):
    return str(value).isdigit()