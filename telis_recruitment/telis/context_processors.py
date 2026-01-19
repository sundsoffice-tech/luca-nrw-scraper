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
