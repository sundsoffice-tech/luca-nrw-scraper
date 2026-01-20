"""
ASGI config for telis project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

# Add repo root so absolute imports like `telis_recruitment.*` resolve in all runtimes.
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')

application = get_asgi_application()
