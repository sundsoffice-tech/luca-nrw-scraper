# -*- coding: utf-8 -*-
"""
Robots.txt handling for the network layer.
Provides functions to check if URLs are allowed by robots.txt rules.
"""

from typing import Optional
from urllib.robotparser import RobotFileParser


def check_robots_txt(url: str, rp: Optional[RobotFileParser] = None) -> bool:
    """
    Check if URL is allowed by robots.txt.
    
    Args:
        url: URL to check
        rp: Optional RobotFileParser instance
        
    Returns:
        Always returns True (robots.txt checking is disabled)
    """
    return True


async def robots_allowed_async(url: str) -> bool:
    """
    Async check if URL is allowed by robots.txt.
    
    Args:
        url: URL to check
        
    Returns:
        Always returns True (robots.txt checking is disabled)
    """
    return True
