"""
Context processors for making variables available in all templates.
"""

from django.conf import settings


def version_context(request):
    """
    Add application version to template context.
    
    Makes APP_VERSION available in all templates for displaying in UI.
    """
    return {
        'APP_VERSION': settings.APP_VERSION,
    }


def tinymce_api_key(request):
    """
    Add TinyMCE API key to template context.
    
    Makes TINYMCE_API_KEY available in all templates for TinyMCE initialization.
    """
    return {
        'TINYMCE_API_KEY': settings.TINYMCE_API_KEY
    }
