from django import template

register = template.Library()

@register.filter(name="multiply")
def multiply(value, arg):
    """Multiplica o value pelo argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name="divide")
def divide(value, arg):
    """Divide o value pelo argumento"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0

@register.filter(name="subtract")
def subtract(value, arg):
    """Subtrai o argumento do value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
