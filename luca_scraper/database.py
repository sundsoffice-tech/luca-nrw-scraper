"""
LUCA NRW Scraper - Database Layer
==================================
SQLite Connection und Schema Management
Phase 1 der Modularisierung.

Database Backend Selection:
---------------------------
This module supports two backends:
- 'sqlite' (default): Direct SQLite connection
- 'django': Django ORM adapter

Set via SCRAPER_DB_BACKEND environment variable.
"""

import logging
import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Optional, Tuple

# Import DB_PATH and DATABASE_BACKEND from config
from .config import DB_PATH as _DB_PATH_STR, DATABASE_BACKEND

# Convert to Path object
DB_PATH = Path(_DB_PATH_STR)

# Thread-local storage for database connections
_db_local = threading.local()

# Global flag for schema initialization with thread lock
_DB_READY = False
_DB_READY_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


# =========================
# BACKEND SELECTION LOGIC
# =========================

# Conditionally import Django backend functions if 'django' backend is selected
if DATABASE_BACKEND == 'django':
    logger.info("Using Django ORM backend")
    try:
        from . import django_db
        # Import functions from django_db module
        upsert_lead = django_db.upsert_lead
        get_lead_count = django_db.get_lead_count
        lead_exists = django_db.lead_exists
        get_lead_by_id = django_db.get_lead_by_id
        update_lead = django_db.update_lead
        _DJANGO_BACKEND_AVAILABLE = True
    except ImportError as exc:
        logger.error(f"Failed to import Django backend: {exc}")
        logger.error("Django backend requires Django to be properly configured")
        _DJANGO_BACKEND_AVAILABLE = False
        raise
else:
    logger.info("Using SQLite backend")
    _DJANGO_BACKEND_AVAILABLE = False


def db() -> sqlite3.Connection:
    """
    Thread-safe database connection.
    
    Returns a connection with row factory set.
    Ensures schema is initialized on first access.
    Validates that cached connection is still open before returning it.
    
    Note: When DATABASE_BACKEND is 'django', this function raises NotImplementedError.
    Use Django ORM directly instead.
    """
    if DATABASE_BACKEND == 'django':
        raise NotImplementedError(
            "db() function is not available when using Django ORM backend. "
            "Use Django ORM directly via the Lead model."
        )
    
    global _DB_READY
    
    # Check if connection exists AND is still open/valid
    if hasattr(_db_local, "conn") and _db_local.conn is not None:
        try:
            # Test if connection is still open/valid by executing a simple query
            _db_local.conn.execute("SELECT 1")
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            # Connection is closed or broken - reset it
            _db_local.conn = None
    
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
        
        COMMIT;
        """)
        print("Successfully migrated database schema")


def _normalize_email(value: Optional[str]) -> Optional[str]:
    """Normalize emails for matching by trimming and lower-casing."""
    if not value:
        return None
    return value.strip().lower()


def _normalize_phone(value: Optional[str]) -> Optional[str]:
    """Keep only digits when normalizing phone numbers for lookup."""
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or None


def _build_crm_status_index() -> Optional[Tuple[Dict[str, str], Dict[str, str]]]:
    """Load CRM lead statuses indexed by email and phone."""
    try:
        from telis_recruitment.leads.models import Lead
    except Exception as exc:
        logger.debug("CRM models unavailable for status sync: %s", exc)
        return None

    email_index: Dict[str, str] = {}
    phone_index: Dict[str, str] = {}

    try:
        queryset = Lead.objects.filter(source=Lead.Source.SCRAPER).values("email", "telefon", "status")
    except Exception as exc:
        logger.warning("Failed to load CRM lead statuses: %s", exc)
        return None

    for row in queryset:
        status = row.get("status")
        if not status:
            continue
        normalized_email = _normalize_email(row.get("email"))
        if normalized_email:
            email_index[normalized_email] = status
        normalized_phone = _normalize_phone(row.get("telefon"))
        if normalized_phone:
            phone_index[normalized_phone] = status

    return email_index, phone_index


def sync_status_to_scraper() -> Dict[str, int]:
    """
    Synchronize CRM lead statuses back into the scraper database.

    This keeps the local SQLite DB aware of which leads were already acted upon
    so the scraper can avoid reprocessing them.
    """
    index = _build_crm_status_index()
    if not index:
        return {"checked": 0, "updated": 0}

    email_index, phone_index = index
    stats = {"checked": 0, "updated": 0}

    with transaction() as con:
        cur = con.cursor()
        cur.execute("SELECT id, email, telefon, crm_status FROM leads WHERE email IS NOT NULL OR telefon IS NOT NULL")
        rows = cur.fetchall()
        stats["checked"] = len(rows)

        for row in rows:
            new_status = None
            if row["email"]:
                new_status = email_index.get(_normalize_email(row["email"]))
            if not new_status and row["telefon"]:
                new_status = phone_index.get(_normalize_phone(row["telefon"]))
            if new_status and new_status != row["crm_status"]:
                cur.execute("UPDATE leads SET crm_status = ? WHERE id = ?", (new_status, row["id"]))
                stats["updated"] += 1

    logger.debug("sync_status_to_scraper updated %d rows (checked %d)", stats["updated"], stats["checked"])
    return stats


# Export the global ready flag for external access
# When using Django backend, also export Django adapter functions
if DATABASE_BACKEND == 'django':
    __all__ = [
        'db', 'init_db', 'transaction', 'DB_PATH', 
        'migrate_db_unique_indexes', 'sync_status_to_scraper',
        'DATABASE_BACKEND',
        # Django backend functions
        'upsert_lead', 'get_lead_count', 'lead_exists', 
        'get_lead_by_id', 'update_lead'
    ]
else:
    __all__ = [
        'db', 'init_db', 'transaction', 'DB_PATH', 
        'migrate_db_unique_indexes', 'sync_status_to_scraper',
        'DATABASE_BACKEND'
    ]
