# -*- coding: utf-8 -*-
"""
Database query operations module.
Contains all data access functions for queries, URLs, leads, and runs.
"""

import json
import re
import sqlite3
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from luca_scraper.database.connection import db, get_learning_engine
from luca_scraper.database.models import migrate_db_unique_indexes

# Import validation functions
from lead_validation import (
    validate_lead_before_insert,
    normalize_phone_number,
    extract_person_name,
    validate_lead_name,
    increment_rejection_stat,
    get_rejection_stats,
    reset_rejection_stats,
)
from learning_engine import is_mobile_number, is_job_posting

# Try to import phonebook enrichment
try:
    from phonebook_lookup import enrich_lead_with_phonebook, BAD_NAMES
except ImportError:
    enrich_lead_with_phonebook = None
    # Fallback BAD_NAMES if phonebook module not available
    BAD_NAMES = ["_probe_", "", None, "Unknown Candidate", "Keine Fixkosten"]


def _log(level: str, msg: str, **ctx):
    """Simple logging function to avoid circular import with scriptname."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    line = f"[{ts}] [{level.upper():7}] {msg}{ctx_str}"
    print(line, flush=True)

# Lead fields for database insertion
LEAD_FIELDS = [
    "name","rolle","email","telefon","quelle","score","tags","region",
    "role_guess","lead_type","salary_hint","commission_hint","opening_line","ssl_insecure",
    "company_name","company_size","hiring_volume","industry",
    "recency_indicator","location_specific","confidence_score","last_updated",
    "data_quality","phone_type","whatsapp_link","private_address","social_profile_url",
    "ai_category","ai_summary",
    # New candidate-focused fields
    "candidate_status","experience_years","availability","mobility","skills",
    "industries_experience","source_type","profile_url","cv_url",
    "contact_preference","last_activity","name_validated"
]

# URL deduplication cache
_seen_urls_cache: set[str] = set()


def _normalize_for_dedupe(u: str) -> str:
    """
    Normalize URL for deduplication by removing tracking parameters and fragments.
    
    Args:
        u: URL to normalize
        
    Returns:
        Normalized URL string
    """
    try:
        pu = urllib.parse.urlparse(u)

        # Query normalisieren – Tracking & Paginierung raus
        q = urllib.parse.parse_qsl(pu.query, keep_blank_values=False)
        q = [
            (k, v) for (k, v) in q
            if not (
                k.lower().startswith(("utm_",))                       # utm_*
                or k.lower() in {"gclid", "fbclid", "mc_eid", "page"} # + page-Param raus
            )
        ]
        new_q = urllib.parse.urlencode(q, doseq=True)

        # Pfad normalisieren: Fragment weg, trailing slash schlucken
        path = pu.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        pu = pu._replace(query=new_q, fragment="", path=path)
        return urllib.parse.urlunparse(pu)
    except Exception:
        return u


def is_query_done(q: str) -> bool:
    """
    Check if a query has already been executed.
    
    Args:
        q: Query string to check
        
    Returns:
        True if query was already done, False otherwise
    """
    con = db(); cur = con.cursor()
    cur.execute("SELECT 1 FROM queries_done WHERE q=?", (q,))
    hit = cur.fetchone()
    con.close()
    return bool(hit)


def mark_query_done(q: str, run_id: int):
    """
    Mark a query as completed in the database.
    
    Args:
        q: Query string that was executed
        run_id: Run ID this query belongs to
    """
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO queries_done(q,last_run_id,ts) VALUES(?,?,datetime('now'))",
        (q, run_id)
    )
    con.commit(); con.close()


def mark_url_seen(url: str, run_id: int):
    """
    Mark a URL as seen/visited in the database and cache.
    
    Args:
        url: URL that was visited
        run_id: Run ID this URL was seen in
    """
    global _seen_urls_cache
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO urls_seen(url,first_run_id,ts) VALUES(?,?,datetime('now'))",
        (url, run_id)
    )
    con.commit(); con.close()
    _seen_urls_cache.add(_normalize_for_dedupe(url))


def url_seen(url: str) -> bool:
    """
    Check if URL was already seen/visited (checks cache first, then DB).
    
    Args:
        url: URL to check
        
    Returns:
        True if URL was seen before, False otherwise
    """
    norm = _normalize_for_dedupe(url)
    if norm in _seen_urls_cache:
        return True
    con = db(); cur = con.cursor()
    cur.execute("SELECT 1 FROM urls_seen WHERE url=?", (url,))
    hit = cur.fetchone()
    con.close()
    if hit:
        _seen_urls_cache.add(norm)
    return bool(hit)


def _url_seen_fast(url: str) -> bool:
    """
    Fast URL seen check using only the in-memory cache (no DB access).
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is in cache, False otherwise
    """
    return _normalize_for_dedupe(url) in _seen_urls_cache


# Import phone functions from extraction module to avoid duplication
# Note: normalize_phone and validate_phone are defined in luca_scraper/extraction/phone.py
from luca_scraper.extraction.phone import normalize_phone, validate_phone


def _validate_name_heuristic(name: str) -> Tuple[bool, int, str]:
    """Fallback-Heuristik für Namensvalidierung ohne KI."""
    if not name or len(name.strip()) < 3:
        return False, 0, "Name zu kurz"
    
    name_lower = name.lower().strip()
    
    # Blacklist
    blacklist = [
        "gmbh", "ag", "kg", "ug", "ltd", "inc",
        "team", "vertrieb", "sales", "info", "kontakt",
        "ansprechpartner", "unknown", "n/a", "k.a.",
        "firma", "unternehmen", "company", "abteilung",
    ]
    if any(b in name_lower for b in blacklist):
        return False, 90, f"Blacklist-Wort gefunden"
    
    # Muss mindestens 2 Wörter haben
    words = name.split()
    if len(words) < 2:
        return False, 70, "Nur ein Wort"
    
    # Keine Zahlen
    if re.search(r'\d', name):
        return False, 85, "Enthält Zahlen"
    
    return True, 75, "Heuristik: wahrscheinlich echter Name"


def insert_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Führt INSERT OR IGNORE aus. Zieht Schema automatisch nach (fehlende Spalten).
    Phone hardfilter: Re-validates phone before insert to ensure no invalid phones slip through.
    STRICT RULE: Only mobile numbers allowed - landline numbers are rejected.
    NEW: Uses lead_validation module for comprehensive quality filtering.
    
    Args:
        leads: List of lead dictionaries to insert
        
    Returns:
        List of successfully inserted leads
    """
    if not leads:
        return []

    con = db(); cur = con.cursor()

    cols = ",".join(LEAD_FIELDS)
    placeholders = ",".join(["?"] * len(LEAD_FIELDS))
    sql = f"INSERT OR IGNORE INTO leads ({cols}) VALUES ({placeholders})"

    new_rows = []
    learning_engine = get_learning_engine()
    
    try:
        for r in leads:
            # STEP 1: Apply comprehensive validation from lead_validation module
            is_valid, reason = validate_lead_before_insert(r)
            if not is_valid:
                _log("debug", "Lead abgelehnt", reason=reason, url=r.get('quelle'))
                increment_rejection_stat(reason)
                continue
            
            # STEP 2: Normalize phone number to international format
            phone = r.get('telefon')
            if phone:
                normalized = normalize_phone_number(phone)
                if normalized:
                    r['telefon'] = normalized
            
            # STEP 2.5: Reverse phonebook lookup for leads with phone but no/invalid name
            # This enriches leads where we have a phone number but the name is missing or invalid
            if enrich_lead_with_phonebook is not None:
                current_name = r.get('name', '')
                # Use shared bad names list from phonebook_lookup module
                needs_enrichment = (
                    not current_name or 
                    current_name in BAD_NAMES or 
                    len(current_name) < 3 or
                    not any(c.isalpha() for c in current_name)
                )
                
                if needs_enrichment and r.get('telefon'):
                    try:
                        r = enrich_lead_with_phonebook(r)
                        if r.get('name'):
                            _log("info", "Lead enriched via reverse phonebook", 
                                phone=r.get('telefon', '')[:8]+"...", name=r['name'])
                    except Exception as e:
                        _log("warn", "Phonebook reverse lookup failed", error=str(e))
            
            # STEP 3: Extract real person name from raw text
            name = r.get('name')
            if name:
                extracted_name = extract_person_name(name)
                if extracted_name:
                    r['name'] = extracted_name
                    
                    # Validate extracted name again
                    if not validate_lead_name(extracted_name):
                        _log("debug", "Lead abgelehnt nach Name-Extraktion", name=extracted_name)
                        increment_rejection_stat("Ungültiger Name nach Extraktion")
                        continue
            
            # STEP 4: Additional validation using existing logic for backwards compatibility
            source_url = r.get("quelle", "")
            
            # Check for job postings
            if is_job_posting(url=source_url, title=r.get("name", ""), 
                             snippet=r.get("opening_line", ""), content=r.get("tags", "")):
                _log("debug", "Lead dropped at insert (job posting)", url=source_url)
                increment_rejection_stat("Job posting detected")
                continue
            
            # Validate name with heuristics
            name = (r.get("name") or "").strip()
            if name:
                is_real, confidence, reason_heuristic = _validate_name_heuristic(name)
                if not is_real:
                    _log("debug", "Lead dropped at insert (invalid name heuristic)", name=name, reason=reason_heuristic, url=source_url)
                    increment_rejection_stat(f"Invalid name: {reason_heuristic}")
                    continue
                r["name_validated"] = 1  # Mark as validated
            else:
                _log("debug", "Lead dropped at insert (no name)", url=source_url)
                increment_rejection_stat("No name")
                continue
            
            # Phone validation - already done by validate_lead_before_insert, but double-check
            phone = (r.get("telefon") or "").strip()
            if phone:
                is_valid_phone, phone_type = validate_phone(phone)
                if not is_valid_phone:
                    _log("debug", "Lead dropped at insert (invalid phone secondary check)", phone=phone, url=source_url)
                    increment_rejection_stat("Invalid phone (secondary)")
                    continue
                
                # Ensure it's a mobile number
                normalized_phone = normalize_phone(phone)
                if not is_mobile_number(normalized_phone):
                    _log("debug", "Lead dropped at insert (not mobile number)", phone=phone, url=source_url)
                    increment_rejection_stat("Not mobile number")
                    continue
                
                r["phone_type"] = "mobile"
            else:
                _log("debug", "Lead dropped at insert (no phone)", url=source_url)
                increment_rejection_stat("No phone")
                continue
            vals = [
                r.get("name",""),
                r.get("rolle",""),
                r.get("email",""),
                r.get("telefon",""),
                r.get("quelle",""),
                r.get("score",0),
                r.get("tags",""),
                r.get("region",""),
                r.get("role_guess",""),
                r.get("lead_type",""),
                r.get("salary_hint",""),
                r.get("commission_hint",""),
                r.get("opening_line",""),
                r.get("ssl_insecure","no"),
                r.get("company_name",""),
                r.get("company_size","unbekannt"),
                r.get("hiring_volume","niedrig"),
                r.get("industry","unbekannt"),
                r.get("recency_indicator","unbekannt"),
                r.get("location_specific",""),
                r.get("confidence_score",0),
                r.get("last_updated",""),
                r.get("data_quality",0),
                r.get("phone_type",""),
                r.get("whatsapp_link",""),
                r.get("private_address",""),
                r.get("social_profile_url",""),
                r.get("ai_category",""),
                r.get("ai_summary",""),
                # New candidate fields
                r.get("candidate_status",""),
                r.get("experience_years",0),
                r.get("availability",""),
                r.get("mobility",""),
                r.get("skills",""),
                r.get("industries_experience",""),
                r.get("source_type",""),
                r.get("profile_url",""),
                r.get("cv_url",""),
                r.get("contact_preference",""),
                r.get("last_activity",""),
                r.get("name_validated",0)
            ]
            cur.execute(sql, vals)
            if cur.rowcount > 0:
                new_rows.append(r)
                # Learn from successful lead (with mobile number)
                if learning_engine:
                    try:
                        # Get the query context from metadata if available
                        query_context = r.get("_query_context", "")
                        learning_engine.learn_from_success(r, query=query_context)
                    except Exception as e:
                        # Don't fail lead insertion if learning fails
                        _log("debug", "Learning failed", error=str(e))
        con.commit()
    except sqlite3.OperationalError as e:
        # Fallback: sehr alte DB migrieren (harte UNIQUE/fehlende Spalten)
        con.rollback(); con.close()
        migrate_db_unique_indexes()
        con = db(); cur = con.cursor()
        for r in leads:
            vals = [
                r.get("name",""),
                r.get("rolle",""),
                r.get("email",""),
                r.get("telefon",""),
                r.get("quelle",""),
                r.get("score",0),
                r.get("tags",""),
                r.get("region",""),
                r.get("role_guess",""),
                r.get("lead_type",""),
                r.get("salary_hint",""),
                r.get("commission_hint",""),
                r.get("opening_line",""),
                r.get("ssl_insecure","no"),
                r.get("company_name",""),
                r.get("company_size","unbekannt"),
                r.get("hiring_volume","niedrig"),
                r.get("industry","unbekannt"),
                r.get("recency_indicator","unbekannt"),
                r.get("location_specific",""),
                r.get("confidence_score",0),
                r.get("last_updated",""),
                r.get("data_quality",0),
                r.get("phone_type",""),
                r.get("whatsapp_link",""),
                r.get("private_address",""),
                r.get("social_profile_url",""),
                r.get("ai_category",""),
                r.get("ai_summary",""),
                # New candidate fields
                r.get("candidate_status",""),
                r.get("experience_years",0),
                r.get("availability",""),
                r.get("mobility",""),
                r.get("skills",""),
                r.get("industries_experience",""),
                r.get("source_type",""),
                r.get("profile_url",""),
                r.get("cv_url",""),
                r.get("contact_preference",""),
                r.get("last_activity",""),
                r.get("name_validated",0)
            ]
            cur.execute(sql, vals)
            if cur.rowcount > 0:
                new_rows.append(r)
        con.commit()
    finally:
        con.close()

    return new_rows


def start_run() -> int:
    """
    Start a new scraper run and return its ID.
    
    Returns:
        Run ID of the newly created run
    """
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT INTO runs(started_at,status,links_checked,leads_new) VALUES(datetime('now'),'running',0,0)"
    )
    run_id = cur.lastrowid
    con.commit(); con.close()
    return run_id


def finish_run(run_id: int, links_checked: Optional[int] = None, leads_new: Optional[int] = None, status: str = "ok", metrics: Optional[Dict[str, int]] = None):
    """
    Mark a run as finished and update its metrics.
    
    Args:
        run_id: ID of the run to finish
        links_checked: Number of links checked during run
        leads_new: Number of new leads found during run
        status: Final status of the run (default: "ok")
        metrics: Optional additional metrics to log
    """
    con = db(); cur = con.cursor()
    cur.execute(
        "UPDATE runs SET finished_at=datetime('now'), status=?, links_checked=?, leads_new=? WHERE id=?",
        (status, links_checked or 0, leads_new or 0, run_id)
    )
    con.commit(); con.close()
    if metrics:
        _log("info", "Run metrics", **metrics)
    
    # Log lead rejection statistics
    log_rejection_stats()


def log_rejection_stats():
    """Log statistics about rejected leads at the end of a run."""
    stats = get_rejection_stats()
    total_rejected = sum(stats.values())
    
    if total_rejected > 0:
        _log("info", "Lead-Filter Statistik", 
            total_rejected=total_rejected,
            rejected_phone=stats['invalid_phone'],
            rejected_source=stats['blocked_source'],
            rejected_name=stats['invalid_name'],
            rejected_type=stats['wrong_type'])
    
    # Reset statistics for next run
    reset_rejection_stats()
