from django import template

register = template.Library()

@register.filter
def times(number):
    return range(1, number + 1)


@register.filter
def to(number):
    try:
        return range(1, int(number) + 1)
    except (ValueError, TypeError):
        return []