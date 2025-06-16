import re
from django import template
from django.urls import reverse
from django.utils.html import format_html

register = template.Library()

@register.filter
def linkify_mentions(content,request):
    pattern = r'@(\w+)'

    def replace_mention(match):
        username = match.group(1)
        url = reverse('profile', kwargs={'slug': username})  # ou username se você usar username direto
        if 'search' in request.path:
            return format_html('<a href="{}" class="font-bold text-cyan-800 hover:text-cyan-900">@{}</a>', url, username)
        else:
            return format_html('<a href="{}" class="text-cyan-500 hover:text-cyan-600">@{}</a>', url, username)

    return re.sub(pattern, replace_mention, content)
