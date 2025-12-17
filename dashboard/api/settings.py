# -*- coding: utf-8 -*-
"""
Settings API - Manages dashboard settings
"""

import sqlite3
import json
from typing import Dict, Any, Optional


def get_all_settings(db_path: str) -> Dict[str, Any]:
    """
    Get all dashboard settings.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dictionary of all settings
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute("SELECT key, value, value_type FROM dashboard_settings")
        
        settings = {}
        for row in cur.fetchall():
            key = row['key']
            value = row['value']
            value_type = row['value_type']
            
            # Convert value based on type
            if value_type == 'number':
                settings[key] = float(value) if '.' in value else int(value)
            elif value_type == 'json':
                try:
                    settings[key] = json.loads(value)
                except:
                    settings[key] = []
            else:
                settings[key] = value
        
        return settings
    finally:
        con.close()


def get_setting(db_path: str, key: str) -> Optional[Any]:
    """
    Get a specific setting value.
    
    Args:
        db_path: Path to SQLite database
        key: Setting key
        
    Returns:
        Setting value or None if not found
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute("""
            SELECT value, value_type FROM dashboard_settings 
            WHERE key = ?
        """, (key,))
        
        row = cur.fetchone()
        if not row:
            return None
        
        value = row['value']
        value_type = row['value_type']
        
        # Convert value based on type
        if value_type == 'number':
            return float(value) if '.' in value else int(value)
        elif value_type == 'json':
            try:
                return json.loads(value)
            except:
                return []
        else:
            return value
    finally:
        con.close()


def update_setting(db_path: str, key: str, value: Any) -> bool:
    """
    Update a setting value.
    
    Args:
        db_path: Path to SQLite database
        key: Setting key
        value: New value
        
    Returns:
        True if successful, False otherwise
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    try:
        # Convert value to string based on type
        if isinstance(value, (list, dict)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
        
        cur.execute("""
            UPDATE dashboard_settings 
            SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = ?
        """, (value_str, key))
        
        con.commit()
        return cur.rowcount > 0
    except Exception as e:
        con.rollback()
        print(f"Error updating setting {key}: {e}")
        return False
    finally:
        con.close()


def update_settings_bulk(db_path: str, settings: Dict[str, Any]) -> Dict[str, bool]:
    """
    Update multiple settings at once.
    
    Args:
        db_path: Path to SQLite database
        settings: Dictionary of settings to update
        
    Returns:
        Dictionary mapping keys to success status
    """
    results = {}
    for key, value in settings.items():
        results[key] = update_setting(db_path, key, value)
    return results


# Setting definitions with metadata
SETTING_DEFINITIONS = {
    'budget_limit_eur': {
        'type': 'number',
        'label': 'Monatliches Budget (EUR)',
        'default': 1000,
        'min': 0,
        'max': 10000,
        'step': 10
    },
    'industry_filter': {
        'type': 'multiselect',
        'label': 'Branchen-Filter',
        'options': ['recruiter', 'sales', 'vertrieb', 'handel', 'industrie', 'dienstleistung']
    },
    'region_filter': {
        'type': 'select',
        'label': 'Region',
        'options': ['NRW', 'DE', 'DACH', 'EU']
    },
    'blacklist_domains': {
        'type': 'textarea',
        'label': 'Domain-Blacklist (eine pro Zeile)',
        'placeholder': 'domain1.com\ndomain2.de'
    },
    'whitelist_domains': {
        'type': 'textarea',
        'label': 'Domain-Whitelist (eine pro Zeile)',
        'placeholder': 'domain1.com\ndomain2.de'
    },
    'min_confidence_score': {
        'type': 'range',
        'label': 'Minimaler Confidence-Score',
        'default': 0.3,
        'min': 0,
        'max': 1,
        'step': 0.1
    }
}


def get_setting_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Get metadata about available settings.
    
    Returns:
        Dictionary of setting definitions
    """
    return SETTING_DEFINITIONS
