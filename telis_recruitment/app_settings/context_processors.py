"""
Context processors for app_settings app.
Makes settings and tracking codes available in all templates.
"""

from .models import SystemSettings


def tracking_codes(request):
    """
    Add tracking codes to template context if analytics is enabled.
    """
    try:
        settings = SystemSettings.get_settings()
        
        if settings.enable_analytics:
            return {
                'analytics_enabled': True,
                'google_analytics_id': settings.google_analytics_id,
                'meta_pixel_id': settings.meta_pixel_id,
                'custom_tracking_code': settings.custom_tracking_code,
            }
    except Exception:
        # Fail silently if settings don't exist yet (e.g., during migrations)
        pass
    
    return {
        'analytics_enabled': False,
        'google_analytics_id': '',
        'meta_pixel_id': '',
        'custom_tracking_code': '',
    }
