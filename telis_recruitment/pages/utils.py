"""Utility functions for pages app"""
import re
import logging

logger = logging.getLogger(__name__)


def validate_asset_references(html_content: str) -> list:
    """
    Prüft HTML-Content auf potentiell fehlende Asset-Referenzen.
    
    Returns:
        Liste von Warnungen für fehlende Assets
    """
    warnings = []
    
    # Finde alle src und href Attribute
    patterns = [
        r'src=["\']([^"\']+)["\']',
        r'href=["\']([^"\']+\.(?:css|js))["\']',
    ]
    
    suspicious_paths = ['/src/', '/dist/', '/assets/', '/build/']
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        for match in matches:
            # Prüfe auf verdächtige lokale Pfade
            if any(match.startswith(path) for path in suspicious_paths):
                warnings.append(f"Möglicherweise fehlende Datei referenziert: {match}")
    
    return warnings
