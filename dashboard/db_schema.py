# -*- coding: utf-8 -*-
"""
Database schema extensions for the dashboard.
Adds tables for API cost tracking and search mode configuration.
"""

import sqlite3
from typing import Optional


def ensure_dashboard_schema(con: sqlite3.Connection) -> None:
    """
    Ensure dashboard-specific tables exist in the database.
    
    Args:
        con: SQLite connection object
    """
    cur = con.cursor()
    
    # API Costs tracking table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            provider TEXT NOT NULL,
            endpoint TEXT,
            tokens_input INTEGER DEFAULT 0,
            tokens_output INTEGER DEFAULT 0,
            cost_eur REAL DEFAULT 0.0,
            run_id INTEGER,
            model TEXT,
            metadata TEXT
        )
    """)
    
    # Create index for faster queries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_costs_timestamp 
        ON api_costs(timestamp DESC)
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_costs_provider 
        ON api_costs(provider, timestamp DESC)
    """)
    
    # Daily costs view
    cur.execute("""
        CREATE VIEW IF NOT EXISTS daily_costs AS
        SELECT 
            DATE(timestamp) as date,
            provider,
            SUM(tokens_input) as total_tokens_in,
            SUM(tokens_output) as total_tokens_out,
            SUM(cost_eur) as total_cost
        FROM api_costs
        GROUP BY DATE(timestamp), provider
    """)
    
    # Search modes configuration table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS search_modes (
            mode_key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            deep_crawl INTEGER DEFAULT 1,
            max_depth INTEGER DEFAULT 2,
            use_ai_extraction INTEGER DEFAULT 1,
            snippet_jackpot_only INTEGER DEFAULT 0,
            query_limit INTEGER DEFAULT 15,
            preferred_sources TEXT,
            use_learned_patterns INTEGER DEFAULT 0,
            config_json TEXT,
            is_active INTEGER DEFAULT 0
        )
    """)
    
    # Dashboard settings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            value_type TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Scheduler configuration table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduler_config (
            id INTEGER PRIMARY KEY,
            enabled BOOLEAN DEFAULT FALSE,
            interval_hours REAL DEFAULT 2.0,
            pause_start_hour INTEGER DEFAULT 23,
            pause_end_hour INTEGER DEFAULT 6,
            pause_weekends BOOLEAN DEFAULT FALSE,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add status column to leads table if it doesn't exist
    # First check if leads table exists
    cur.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='leads'
    """)
    
    if cur.fetchone():
        # Table exists, check if status column exists
        cur.execute("PRAGMA table_info(leads)")
        columns = [row[1] for row in cur.fetchall()]
        
        if 'status' not in columns:
            # Column doesn't exist, add it
            cur.execute("""
                ALTER TABLE leads ADD COLUMN status TEXT DEFAULT 'new'
            """)
    
    con.commit()


def initialize_default_search_modes(con: sqlite3.Connection) -> None:
    """
    Initialize default search modes if they don't exist.
    
    Args:
        con: SQLite connection object
    """
    import json
    cur = con.cursor()
    
    # Check if modes already exist
    cur.execute("SELECT COUNT(*) FROM search_modes")
    if cur.fetchone()[0] > 0:
        return  # Already initialized
    
    default_modes = [
        {
            'mode_key': 'standard',
            'name': 'Standard-Suche',
            'description': 'Ausgewogene Suche mit moderatem API-Verbrauch',
            'deep_crawl': 1,
            'max_depth': 2,
            'use_ai_extraction': 1,
            'snippet_jackpot_only': 0,
            'query_limit': 15,
            'preferred_sources': None,
            'use_learned_patterns': 0,
            'is_active': 1
        },
        {
            'mode_key': 'headhunter',
            'name': 'Headhunter-Modus',
            'description': 'Fokus auf LinkedIn/Xing und Recruiter-Themen',
            'deep_crawl': 1,
            'max_depth': 3,
            'use_ai_extraction': 1,
            'snippet_jackpot_only': 0,
            'query_limit': 20,
            'preferred_sources': json.dumps(['linkedin.com', 'xing.com']),
            'use_learned_patterns': 0,
            'is_active': 0
        },
        {
            'mode_key': 'aggressive',
            'name': 'Aggressive Suche',
            'description': 'Maximale Tiefe und alle Quellen - hoher API-Verbrauch',
            'deep_crawl': 1,
            'max_depth': 5,
            'use_ai_extraction': 1,
            'snippet_jackpot_only': 0,
            'query_limit': 30,
            'preferred_sources': None,
            'use_learned_patterns': 0,
            'is_active': 0
        },
        {
            'mode_key': 'snippet_only',
            'name': 'Nur Snippet-Scan',
            'description': 'Schneller Scan ohne Deep-Crawl - minimaler API-Verbrauch',
            'deep_crawl': 0,
            'max_depth': 0,
            'use_ai_extraction': 0,
            'snippet_jackpot_only': 1,
            'query_limit': 50,
            'preferred_sources': None,
            'use_learned_patterns': 0,
            'is_active': 0
        },
        {
            'mode_key': 'learning',
            'name': 'Lern-Modus',
            'description': 'AI-optimierte Queries basierend auf bisherigen Erfolgen',
            'deep_crawl': 1,
            'max_depth': 2,
            'use_ai_extraction': 1,
            'snippet_jackpot_only': 0,
            'query_limit': 15,
            'preferred_sources': None,
            'use_learned_patterns': 1,
            'is_active': 0
        }
    ]
    
    for mode in default_modes:
        cur.execute("""
            INSERT INTO search_modes 
            (mode_key, name, description, deep_crawl, max_depth, use_ai_extraction,
             snippet_jackpot_only, query_limit, preferred_sources, use_learned_patterns, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mode['mode_key'], mode['name'], mode['description'],
            mode['deep_crawl'], mode['max_depth'], mode['use_ai_extraction'],
            mode['snippet_jackpot_only'], mode['query_limit'],
            mode['preferred_sources'], mode['use_learned_patterns'],
            mode['is_active']
        ))
    
    con.commit()


def initialize_default_settings(con: sqlite3.Connection) -> None:
    """
    Initialize default dashboard settings if they don't exist.
    
    Args:
        con: SQLite connection object
    """
    cur = con.cursor()
    
    # Check if settings already exist
    cur.execute("SELECT COUNT(*) FROM dashboard_settings")
    if cur.fetchone()[0] > 0:
        return  # Already initialized
    
    default_settings = [
        ('budget_limit_eur', '1000', 'number'),
        ('industry_filter', '[]', 'json'),
        ('region_filter', 'NRW', 'string'),
        ('blacklist_domains', '', 'text'),
        ('whitelist_domains', '', 'text'),
        ('min_confidence_score', '0.3', 'number')
    ]
    
    for key, value, value_type in default_settings:
        cur.execute("""
            INSERT INTO dashboard_settings (key, value, value_type)
            VALUES (?, ?, ?)
        """, (key, value, value_type))
    
    con.commit()


# OpenAI Pricing (as of December 2024)
# TODO: Move to database table or config file for easier updates
# Update these values when OpenAI changes pricing
OPENAI_PRICING = {
    'gpt-4o': {'input': 0.0025, 'output': 0.01},  # per 1K tokens
    'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
    'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015}
}


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Calculate the cost in EUR for OpenAI API usage.
    
    Args:
        model: Model name (e.g., 'gpt-4o-mini')
        tokens_in: Number of input tokens
        tokens_out: Number of output tokens
    
    Returns:
        Cost in EUR rounded to 4 decimal places
    """
    pricing = OPENAI_PRICING.get(model, OPENAI_PRICING['gpt-4o-mini'])
    cost = (tokens_in / 1000 * pricing['input']) + (tokens_out / 1000 * pricing['output'])
    return round(cost, 4)


def track_api_cost(
    con: sqlite3.Connection,
    provider: str,
    tokens_input: int,
    tokens_output: int,
    model: str = 'gpt-4o-mini',
    endpoint: Optional[str] = None,
    run_id: Optional[int] = None,
    metadata: Optional[str] = None
) -> None:
    """
    Track API cost in the database.
    
    Args:
        con: SQLite connection object
        provider: Provider name (e.g., 'openai', 'google_cse')
        tokens_input: Number of input tokens
        tokens_output: Number of output tokens
        model: Model name for cost calculation
        endpoint: API endpoint used
        run_id: Associated run ID
        metadata: Additional metadata as JSON string
    """
    cost = calculate_cost(model, tokens_input, tokens_output)
    
    cur = con.cursor()
    cur.execute("""
        INSERT INTO api_costs 
        (provider, endpoint, tokens_input, tokens_output, cost_eur, run_id, model, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (provider, endpoint, tokens_input, tokens_output, cost, run_id, model, metadata))
    
    con.commit()


def save_performance_settings(settings: dict) -> None:
    """
    Save performance settings to database.
    
    Args:
        settings: Dictionary containing performance settings
    """
    import json
    from pathlib import Path
    
    # Determine DB_PATH
    db_path = Path(__file__).parent.parent / 'scraper.db'
    
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    
    cur.execute("""
        INSERT OR REPLACE INTO dashboard_settings (key, value, value_type, updated_at)
        VALUES ('performance_settings', ?, 'json', CURRENT_TIMESTAMP)
    """, (json.dumps(settings),))
    
    con.commit()
    con.close()


def load_performance_settings() -> dict:
    """
    Load performance settings from database.
    
    Returns:
        Dictionary containing performance settings, or defaults if not found
    """
    import json
    from pathlib import Path
    
    # Determine DB_PATH
    db_path = Path(__file__).parent.parent / 'scraper.db'
    
    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        cur.execute("SELECT value FROM dashboard_settings WHERE key = 'performance_settings'")
        row = cur.fetchone()
        con.close()
        if row:
            return json.loads(row[0])
    except Exception:
        pass
    
    # Return defaults
    return {
        'mode': 'balanced',
        'cpu_limit': 80,
        'ram_limit': 85,
        'auto_throttle': True,
        'auto_pause': True,
        'night_mode': False,
        'custom': {
            'threads': 4,
            'async_limit': 35,
            'batch_size': 20,
            'request_delay': 2.5
        },
        'current_multiplier': 1.0
    }
