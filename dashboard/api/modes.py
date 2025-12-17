# -*- coding: utf-8 -*-
"""
Modes API - Manages search modes for the scraper
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional


def get_current_mode(db_path: str) -> Dict[str, Any]:
    """
    Get the currently active search mode.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dictionary containing current mode configuration
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute("""
            SELECT * FROM search_modes 
            WHERE is_active = 1 
            LIMIT 1
        """)
        
        row = cur.fetchone()
        if row:
            mode = dict(row)
            if mode.get('preferred_sources'):
                try:
                    mode['preferred_sources'] = json.loads(mode['preferred_sources'])
                except:
                    mode['preferred_sources'] = []
            return mode
        
        # Default to standard mode if none active
        return get_mode_by_key(db_path, 'standard')
    finally:
        con.close()


def get_all_modes(db_path: str) -> List[Dict[str, Any]]:
    """
    Get all available search modes.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        List of all search mode configurations
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute("SELECT * FROM search_modes ORDER BY mode_key")
        
        modes = []
        for row in cur.fetchall():
            mode = dict(row)
            if mode.get('preferred_sources'):
                try:
                    mode['preferred_sources'] = json.loads(mode['preferred_sources'])
                except:
                    mode['preferred_sources'] = []
            modes.append(mode)
        
        return modes
    finally:
        con.close()


def get_mode_by_key(db_path: str, mode_key: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific search mode by key.
    
    Args:
        db_path: Path to SQLite database
        mode_key: Mode identifier (e.g., 'standard', 'aggressive')
        
    Returns:
        Mode configuration or None if not found
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute("SELECT * FROM search_modes WHERE mode_key = ?", (mode_key,))
        
        row = cur.fetchone()
        if row:
            mode = dict(row)
            if mode.get('preferred_sources'):
                try:
                    mode['preferred_sources'] = json.loads(mode['preferred_sources'])
                except:
                    mode['preferred_sources'] = []
            return mode
        
        return None
    finally:
        con.close()


def set_active_mode(db_path: str, mode_key: str) -> bool:
    """
    Set a specific mode as active (deactivates all others).
    
    Args:
        db_path: Path to SQLite database
        mode_key: Mode identifier to activate
        
    Returns:
        True if successful, False otherwise
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    try:
        # Verify mode exists
        cur.execute("SELECT mode_key FROM search_modes WHERE mode_key = ?", (mode_key,))
        if not cur.fetchone():
            return False
        
        # Deactivate all modes
        cur.execute("UPDATE search_modes SET is_active = 0")
        
        # Activate requested mode
        cur.execute("UPDATE search_modes SET is_active = 1 WHERE mode_key = ?", (mode_key,))
        
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        print(f"Error setting active mode: {e}")
        return False
    finally:
        con.close()


def get_mode_config_for_scraper(db_path: str) -> Dict[str, Any]:
    """
    Get the current mode configuration in a format suitable for the scraper.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Mode configuration with boolean values properly converted
    """
    mode = get_current_mode(db_path)
    
    return {
        'mode_key': mode.get('mode_key', 'standard'),
        'name': mode.get('name', 'Standard-Suche'),
        'deep_crawl': bool(mode.get('deep_crawl', 1)),
        'max_depth': mode.get('max_depth', 2),
        'use_ai_extraction': bool(mode.get('use_ai_extraction', 1)),
        'snippet_jackpot_only': bool(mode.get('snippet_jackpot_only', 0)),
        'query_limit': mode.get('query_limit', 15),
        'preferred_sources': mode.get('preferred_sources', []),
        'use_learned_patterns': bool(mode.get('use_learned_patterns', 0))
    }
