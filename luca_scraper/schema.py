"""
LUCA NRW Scraper - Database Schema Management
==============================================
Schema-Definitionen und Migrationen.

This module provides:
- Schema initialization and table creation
- Column migrations for the leads table
- Index creation and management
- Schema migration utilities
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


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
      ai_summary TEXT,
      crm_status TEXT
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
    if "crm_status" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN crm_status TEXT")
    
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
    
    # Performance indexes for common queries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_lead_type
        ON leads(lead_type) WHERE lead_type IS NOT NULL
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_quality_score
        ON leads(score) WHERE score IS NOT NULL
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_type_status
        ON leads(lead_type, crm_status) WHERE lead_type IS NOT NULL
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_last_updated
        ON leads(last_updated) WHERE last_updated IS NOT NULL
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_confidence
        ON leads(confidence_score) WHERE confidence_score IS NOT NULL
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_data_quality
        ON leads(data_quality) WHERE data_quality IS NOT NULL
    """)
    
    con.commit()


def migrate_db_unique_indexes():
    """
    Fallback migration for very old schemas with hard UNIQUE constraints.
    Only run if inserts continue to fail.
    
    This recreates the leads table without UNIQUE constraints.
    """
    from .connection import db
    
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
          ai_summary TEXT, crm_status TEXT, lead_type TEXT, experience_years INTEGER, skills TEXT,
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
        
        -- Performance indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_leads_lead_type
        ON leads(lead_type) WHERE lead_type IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_leads_quality_score
        ON leads(score) WHERE score IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_leads_type_status
        ON leads(lead_type, crm_status) WHERE lead_type IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_leads_last_updated
        ON leads(last_updated) WHERE last_updated IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_leads_confidence
        ON leads(confidence_score) WHERE confidence_score IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_leads_data_quality
        ON leads(data_quality) WHERE data_quality IS NOT NULL;
        
        COMMIT;
        """)
        print("Successfully migrated database schema")


__all__ = [
    '_ensure_schema',
    'migrate_db_unique_indexes',
]
