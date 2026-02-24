from django import template
register = template.Library()

@register.filter
def letter(n):
    try:
        return 'ABCDEFGHIJ'[int(n) - 1]
    except:
        return n
