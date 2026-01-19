"""
Robots.txt handling and checking.
"""

from typing import Optional
from urllib.robotparser import RobotFileParser


def check_robots_txt(url: str, rp: Optional[RobotFileParser] = None) -> bool:
    """
    Check if URL is allowed by robots.txt.
    
    Currently returns True (permissive mode).
    
    Args:
        url: URL to check
        rp: Optional RobotFileParser instance
        
    Returns:
        True if allowed
    """
    return True


async def robots_allowed_async(url: str) -> bool:
    """
    Async version of robots.txt check.
    
    Currently returns True (permissive mode).
    
    Args:
        url: URL to check
        
    Returns:
        True if allowed
    """
    return True
