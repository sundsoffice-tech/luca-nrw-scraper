"""Utility functions for pages app"""
import re
import logging

logger = logging.getLogger(__name__)


def validate_asset_references(html_content: str) -> list:
    """
    Check HTML content for potentially missing asset references.
    
    Returns:
        List of warnings for missing assets
    """
    warnings = []
    
    # Find all src and href attributes
    patterns = [
        r'src=["\']([^"\']+)["\']',
        r'href=["\']([^"\']+\.(?:css|js))["\']',
    ]
    
    suspicious_paths = ['/src/', '/dist/', '/assets/', '/build/']
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        for match in matches:
            # Check for suspicious local paths
            if any(match.startswith(path) for path in suspicious_paths):
                warnings.append(f"Possibly missing file referenced: {match}")
    
    return warnings
