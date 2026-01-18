"""
LUCA NRW Scraper - Database Layer
==================================
SQLite Connection und Schema Management
Phase 1 der Modularisierung.
"""

import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

# Import DB_PATH from config
from .config import DB_PATH as _DB_PATH_STR

# Convert to Path object
DB_PATH = Path(_DB_PATH_STR)

# Thread-local storage for database connections
_db_local = threading.local()

# Global flag for schema initialization with thread lock
_DB_READY = False
_DB_READY_LOCK = threading.Lock()


def db() -> sqlite3.Connection:
    """
    Thread-safe database connection.
    
    Returns a connection with row factory set.
    Ensures schema is initialized on first access.
    """
    global _DB_READY
    
    if not hasattr(_db_local, "conn") or _db_local.conn is None:
        _db_local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _db_local.conn.row_factory = sqlite3.Row
    
    # Initialize schema if not already done (thread-safe)
    if not _DB_READY:
        with _DB_READY_LOCK:
            # Double-check pattern to avoid multiple initializations
            if not _DB_READY:
                _ensure_schema(_db_local.conn)
                
                # Dashboard schema initialization removed - migrated to Django CRM
                # See docs/FLASK_TO_DJANGO_MIGRATION.md for migration details
                
                _DB_READY = True
    
    return _db_local.conn


def init_db():
    """
    Explicit database initializer.
    
    Opens connection, ensures schema exists, then closes.
    Kept for backward compatibility.
    """
    con = db()
    con.close()
    # Reset the thread-local connection
    if hasattr(_db_local, "conn"):
        _db_local.conn = None


@contextmanager
def transaction():
    """
    Context manager for database transactions.
    
    Usage:
        with transaction() as conn:
            conn.execute("INSERT INTO ...")
    
    Commits on success, rolls back on exception.
    """
    conn = db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _ensure_schema(con: sqlite3.Connection) -> None:
    """
    Ensures all tables exist with correct schema.
    Idempotent - safe to call multiple times.
    
    Creates tables:
    - leads: Main lead/contact storage
    - runs: Scraper run tracking
    - queries_done: Query history
    - urls_seen: URL deduplication
    - telefonbuch_cache: Phone lookup cache
    """
    cur = con.cursor()
    
    # Create base tables
    cur.executescript("""
    PRAGMA journal_mode = WAL;

    CREATE TABLE IF NOT EXISTS leads(
      id INTEGER PRIMARY KEY,
      name TEXT,
      rolle TEXT,
      email TEXT,
      telefon TEXT,
      quelle TEXT,
      score INT,
      tags TEXT,
      region TEXT,
      role_guess TEXT,
      lead_type TEXT,
      salary_hint TEXT,
      commission_hint TEXT,
      opening_line TEXT,
      ssl_insecure TEXT,
      company_name TEXT,
      company_size TEXT,
      hiring_volume TEXT,
      industry TEXT,
      recency_indicator TEXT,
      location_specific TEXT,
      confidence_score INT,
      last_updated TEXT,
      data_quality INT,
      phone_type TEXT,
      whatsapp_link TEXT,
      private_address TEXT,
      social_profile_url TEXT,
      ai_category TEXT,
      ai_summary TEXT
      -- neue Spalten werden unten per ALTER TABLE nachgezogen
    );

    CREATE TABLE IF NOT EXISTS runs(
      id INTEGER PRIMARY KEY,
      started_at TEXT,
      finished_at TEXT,
      status TEXT,
      links_checked INTEGER,
      leads_new INTEGER
    );

    CREATE TABLE IF NOT EXISTS queries_done(
      q TEXT PRIMARY KEY,
      last_run_id INTEGER,
      ts TEXT
    );

    CREATE TABLE IF NOT EXISTS urls_seen(
      url TEXT PRIMARY KEY,
      first_run_id INTEGER,
      ts TEXT
    );

    CREATE TABLE IF NOT EXISTS telefonbuch_cache(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      city TEXT NOT NULL,
      query_hash TEXT UNIQUE,
      results_json TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    con.commit()

    # Add missing columns to leads table
    cur.execute("PRAGMA table_info(leads)")
    existing_cols = {row[1] for row in cur.fetchall()}

    # Phone and WhatsApp columns
    if "phone_type" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN phone_type TEXT")
    if "whatsapp_link" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN whatsapp_link TEXT")
    
    # Lead type column
    try:
        cur.execute("ALTER TABLE leads ADD COLUMN lead_type TEXT")
    except Exception:
        pass  # Already exists
    
    # Additional contact columns
    if "private_address" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN private_address TEXT")
    if "social_profile_url" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN social_profile_url TEXT")
    
    # AI enrichment columns
    if "ai_category" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN ai_category TEXT")
    if "ai_summary" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN ai_summary TEXT")
    
    # Candidate-specific columns
    if "experience_years" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN experience_years INTEGER")
    if "skills" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN skills TEXT")  # JSON array
    if "availability" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN availability TEXT")
    if "current_status" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN current_status TEXT")
    if "industries" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN industries TEXT")  # JSON array
    if "location" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN location TEXT")
    if "profile_text" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN profile_text TEXT")
    
    # New candidate-focused columns
    if "candidate_status" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN candidate_status TEXT")
    if "mobility" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN mobility TEXT")
    if "industries_experience" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN industries_experience TEXT")
    if "source_type" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN source_type TEXT")
    if "profile_url" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN profile_url TEXT")
    if "cv_url" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN cv_url TEXT")
    if "contact_preference" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN contact_preference TEXT")
    if "last_activity" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN last_activity TEXT")
    if "name_validated" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN name_validated INTEGER")
    
    con.commit()

    # Create unique indexes (partial - only when values present)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_email
        ON leads(email) WHERE email IS NOT NULL AND email <> ''
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_tel
        ON leads(telefon) WHERE telefon IS NOT NULL AND telefon <> ''
    """)
    con.commit()


def migrate_db_unique_indexes():
    """
    Fallback migration for very old schemas with hard UNIQUE constraints.
    Only run if inserts continue to fail.
    
    This recreates the leads table without UNIQUE constraints.
    """
    con = db()
    cur = con.cursor()
    
    try:
        # Test if we can insert with duplicate handling
        cur.execute(
            "INSERT OR IGNORE INTO leads (name,email,telefon) VALUES (?,?,?)",
            ("_probe_", "", "")
        )
        con.commit()
    except Exception:
        # Need to migrate - recreate table
        cur.executescript("""
        BEGIN TRANSACTION;
        CREATE TABLE leads_new(
          id INTEGER PRIMARY KEY,
          name TEXT, rolle TEXT, email TEXT, telefon TEXT, quelle TEXT,
          score INT, tags TEXT, region TEXT, role_guess TEXT, salary_hint TEXT,
          commission_hint TEXT, opening_line TEXT, ssl_insecure TEXT,
          company_name TEXT, company_size TEXT, hiring_volume TEXT, industry TEXT,
          recency_indicator TEXT, location_specific TEXT, confidence_score INT,
          last_updated TEXT, data_quality INT, phone_type TEXT, whatsapp_link TEXT,
          private_address TEXT, social_profile_url TEXT, ai_category TEXT,
          ai_summary TEXT, lead_type TEXT, experience_years INTEGER, skills TEXT,
          availability TEXT, current_status TEXT, industries TEXT, location TEXT,
          profile_text TEXT, candidate_status TEXT, mobility TEXT,
          industries_experience TEXT, source_type TEXT, profile_url TEXT,
          cv_url TEXT, contact_preference TEXT, last_activity TEXT,
          name_validated INTEGER
        );
        INSERT INTO leads_new SELECT * FROM leads;
        DROP TABLE leads;
        ALTER TABLE leads_new RENAME TO leads;
        
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_email
        ON leads(email) WHERE email IS NOT NULL AND email <> '';
        
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_tel
        ON leads(telefon) WHERE telefon IS NOT NULL AND telefon <> '';
        
        COMMIT;
        """)
        print("Successfully migrated database schema")


# Export the global ready flag for external access
__all__ = ['db', 'init_db', 'transaction', 'DB_PATH', 'migrate_db_unique_indexes']
