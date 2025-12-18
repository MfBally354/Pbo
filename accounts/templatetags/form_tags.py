from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """
    Filter untuk menambahkan class Tailwind ke field form.
    Jika field ada error, otomatis menambahkan class border-red-500.
    
    Usage:
    {{ form.username|add_class:"mt-1 w-full px-4 py-2 border rounded-xl focus:ring-2 focus:ring-orange-400" }}
    """
    classes = css
    if field.errors:
        # tambahkan class khusus jika error
        classes += " border-red-500 ring-red-300"
    return field.as_widget(attrs={"class": classes})
