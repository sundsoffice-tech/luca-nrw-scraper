# -*- coding: utf-8 -*-
"""
Database connection management module.
Provides lazy singleton pattern for database connections.
"""

import os
import sqlite3
from typing import Optional, Dict, Any

from luca_scraper.config import DB_PATH
from learning_engine import LearningEngine

# Global state
_DB_READY = False
_LEARNING_ENGINE: Optional[LearningEngine] = None


def db():
    """
    Returns a SQLite connection with row factory enabled.
    Uses lazy singleton pattern for schema initialization.
    
    Returns:
        sqlite3.Connection: Database connection with row factory
    """
    from luca_scraper.database.models import _ensure_schema
    
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    global _DB_READY, _LEARNING_ENGINE
    if not _DB_READY:
        _ensure_schema(con)
        # Initialize dashboard schema
        try:
            from dashboard.db_schema import ensure_dashboard_schema, initialize_default_search_modes, initialize_default_settings
            ensure_dashboard_schema(con)
            initialize_default_search_modes(con)
            initialize_default_settings(con)
        except ImportError as e:
            # Dashboard module not available - this is expected if dashboard deps not installed
            import sys
            if '--verbose' in sys.argv or os.getenv('DEBUG'):
                print(f"Note: Dashboard module not available: {e}")
        except Exception as e:
            # Log other errors but don't fail
            print(f"Warning: Could not initialize dashboard schema: {e}")
        _DB_READY = True
    # Initialize learning engine on first DB access
    if _LEARNING_ENGINE is None:
        _LEARNING_ENGINE = LearningEngine(DB_PATH)
    return con


def get_learning_engine() -> Optional[LearningEngine]:
    """
    Get the global learning engine instance.
    
    Returns:
        Optional[LearningEngine]: The learning engine instance or None
    """
    global _LEARNING_ENGINE
    if _LEARNING_ENGINE is None:
        _LEARNING_ENGINE = LearningEngine(DB_PATH)
    return _LEARNING_ENGINE


def init_mode(mode: str) -> Dict[str, Any]:
    """
    Initialize the operating mode and apply its configuration.
    
    IMPORTANT: This function must be called during startup before any async operations begin,
    as it modifies global configuration variables.
    
    Args:
        mode: Mode name (standard, learning, aggressive, snippet_only)
    
    Returns:
        Mode configuration dictionary
    """
    from luca_scraper.config import MODE_CONFIGS
    
    global _LEARNING_ENGINE
    
    config = MODE_CONFIGS.get(mode, MODE_CONFIGS["standard"])
    
    # Note: ACTIVE_MODE_CONFIG and ASYNC_LIMIT are set in scriptname.py
    # This function is called from scriptname.py which handles those globals
    
    # Initialize learning engine if learning mode is enabled
    if config.get("learning_enabled"):
        if _LEARNING_ENGINE is None:
            _LEARNING_ENGINE = LearningEngine(DB_PATH)
        print(f"[INFO] Learning-Modus aktiviert")
    
    print(f"[INFO] Betriebsmodus initialisiert: {mode} - {config.get('description')}")
    
    return config
