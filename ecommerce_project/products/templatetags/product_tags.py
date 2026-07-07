from django import template
from django.templatetags.static import static

register = template.Library()


@register.filter
def image_url(obj):
    if obj and obj.image:
        return obj.image.url
    return static('images/placeholder.svg')
