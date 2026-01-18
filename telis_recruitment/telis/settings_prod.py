"""
Production settings for LUCA Command Center (Django CRM)
Inherits from base settings.py and overrides for production security.
"""

import os
from .settings import *

# ======================
# SECURITY SETTINGS
# ======================

# SECURITY WARNING: DEBUG must be False in production!
DEBUG = False

# ALLOWED_HOSTS must be configured for production
ALLOWED_HOSTS = [
    host.strip() 
    for host in os.getenv('ALLOWED_HOSTS', '').split(',') 
    if host.strip()
]

# CSRF Protection - add your domains
CSRF_TRUSTED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') 
    if origin.strip()
]

# ======================
# HTTPS/SSL SECURITY
# ======================

# Redirect all HTTP requests to HTTPS (only enable with SSL certificate)
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'

# Use secure cookies (only enable with SSL certificate)
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'

# HTTP Strict Transport Security (HSTS)
# Tells browsers to only use HTTPS (set to 31536000 for 1 year in production with SSL)
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0

# Additional security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ======================
# STATIC FILES (Whitenoise)
# ======================

# Whitenoise for serving static files in production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be after SecurityMiddleware
] + [m for m in MIDDLEWARE if m not in [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]]

# Whitenoise storage backend with compression and caching
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ======================
# LOGGING
# ======================

# Production logging to console (works with Docker/PaaS)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# ======================
# MEDIA FILES
# ======================

MEDIA_URL = '/media/'
# Handle Path/string compatibility
_media_root = os.getenv('MEDIA_ROOT')
MEDIA_ROOT = Path(_media_root) if _media_root else BASE_DIR / 'media'

# ======================
# ADMIN SETTINGS
# ======================

# Admin site header customization
ADMIN_SITE_HEADER = "LUCA Command Center - Production"
