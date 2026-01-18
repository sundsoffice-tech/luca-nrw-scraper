# -*- coding: utf-8 -*-
"""
Database schema and migration module.
Contains all CREATE TABLE statements and schema migrations.
"""

import sqlite3


def _ensure_schema(con: sqlite3.Connection) -> None:
    """
    Stellt sicher, dass alle Tabellen existieren, fehlende Spalten nachgezogen
    und Indizes korrekt angelegt sind. Idempotent.
    
    Args:
        con: SQLite database connection
    """
    cur = con.cursor()
    # Basis-Tabellen
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

    # Fehlende Spalten in leads nachziehen (z. B. nach Update)
    cur.execute("PRAGMA table_info(leads)")
    existing_cols = {row[1] for row in cur.fetchall()}  # 2. Feld = Spaltenname

    # phone_type / whatsapp_link sicherstellen
    if "phone_type" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN phone_type TEXT")
    if "whatsapp_link" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN whatsapp_link TEXT")
    try:
        cur.execute("ALTER TABLE leads ADD COLUMN lead_type TEXT")
    except Exception:
        pass
    if "private_address" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN private_address TEXT")
    if "social_profile_url" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN social_profile_url TEXT")
    if "ai_category" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN ai_category TEXT")
    if "ai_summary" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN ai_summary TEXT")
    
    # Candidate-specific columns (existing)
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
        cur.execute("ALTER TABLE leads ADD COLUMN candidate_status TEXT")  # aktiv_suchend, passiv_offen, etc.
    if "mobility" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN mobility TEXT")  # remote, hybrid, vor_ort, reisebereit
    if "industries_experience" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN industries_experience TEXT")  # JSON array
    if "source_type" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN source_type TEXT")  # Detailed source type
    if "profile_url" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN profile_url TEXT")  # Social media profile
    if "cv_url" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN cv_url TEXT")  # CV/Resume PDF URL
    if "contact_preference" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN contact_preference TEXT")  # whatsapp, telefon, email, telegram
    if "last_activity" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN last_activity TEXT")  # When candidate was last active
    if "name_validated" not in existing_cols:
        cur.execute("ALTER TABLE leads ADD COLUMN name_validated INTEGER")  # 1 = AI-validated real name
    con.commit()

    # Indizes (partielle UNIQUE nur wenn Werte vorhanden)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_email
        ON leads(email) WHERE email IS NOT NULL AND email <> ''
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_tel
        ON leads(telefon) WHERE telefon IS NOT NULL AND telefon <> ''
    """)
    con.commit()


def init_db():
    """
    Explicit database initializer (makes internally the same as db()).
    """
    from luca_scraper.database.connection import db
    con = db()
    con.close()


def migrate_db_unique_indexes():
    """
    Fallback für sehr alte Schemas mit harten UNIQUE-Constraints.
    Nur ausführen, wenn Einfügen weiterhin scheitert.
    """
    from luca_scraper.database.connection import db
    
    con = db(); cur = con.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO leads (name,email,telefon) VALUES (?,?,?)",
                    ("_probe_", "", ""))
        con.commit()
    except Exception:
        cur.executescript("""
        BEGIN TRANSACTION;
        CREATE TABLE leads_new(
          id INTEGER PRIMARY KEY,
          name TEXT, rolle TEXT, email TEXT, telefon TEXT, quelle TEXT,
          score INT, tags TEXT, region TEXT, role_guess TEXT, salary_hint TEXT,
          commission_hint TEXT, opening_line TEXT, ssl_insecure TEXT,
          company_name TEXT, company_size TEXT, hiring_volume TEXT, industry TEXT,
          recency_indicator TEXT, location_specific TEXT, confidence_score INT,
          last_updated TEXT, data_quality INT,
          phone_type TEXT, whatsapp_link TEXT,
          lead_type TEXT,
          private_address TEXT, social_profile_url TEXT,
          experience_years INTEGER, skills TEXT, availability TEXT,
          current_status TEXT, industries TEXT, location TEXT, profile_text TEXT
        );

        INSERT INTO leads_new (
          id,name,rolle,email,telefon,quelle,score,tags,region,role_guess,salary_hint,
          commission_hint,opening_line,ssl_insecure,company_name,company_size,hiring_volume,
          industry,recency_indicator,location_specific,confidence_score,last_updated,data_quality,
          phone_type,whatsapp_link,lead_type,private_address,social_profile_url,
          experience_years,skills,availability,current_status,industries,location,profile_text
        )
        SELECT
          id,name,rolle,email,telefon,quelle,score,tags,region,role_guess,salary_hint,
          commission_hint,opening_line,ssl_insecure,company_name,company_size,hiring_volume,
          industry,recency_indicator,location_specific,confidence_score,last_updated,data_quality,
          '' AS phone_type, '' AS whatsapp_link, '' AS lead_type,
          '' AS private_address, '' AS social_profile_url,
          NULL AS experience_years, '' AS skills, '' AS availability,
          '' AS current_status, '' AS industries, '' AS location, '' AS profile_text
        FROM leads;

        DROP TABLE leads;
        ALTER TABLE leads_new RENAME TO leads;
        COMMIT;
        """)
        con.commit()
        # Indizes nachziehen
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_email
            ON leads(email) WHERE email IS NOT NULL AND email <> ''
        """)
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_tel
            ON leads(telefon) WHERE telefon IS NOT NULL AND telefon <> ''
        """)
        con.commit()
    finally:
        con.close()
