"""
LUCA NRW Scraper - Database Repository Layer
=============================================
CRUD-Operationen und Abfragen.

This module provides:
- SQLite-specific CRUD operations (lead_exists_sqlite, upsert_lead_sqlite, etc.)
- URL and query tracking functions
- Scraper run management
- Optional Django ORM fallbacks
- CRM status synchronization
"""

import logging
import time
from typing import Dict, Optional, Tuple

from .config import DATABASE_BACKEND
from .database import ALLOWED_LEAD_COLUMNS

logger = logging.getLogger(__name__)

# Transient error keywords that indicate retryable database errors
# Shared between Django and SQLite backends
TRANSIENT_ERROR_KEYWORDS = [
    'database is locked',
    'connection',
    'timeout',
    'deadlock',
    'temporary',
    'locked',
    'busy'
]


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
    # Define placeholder functions that raise NotImplementedError if called
    # This prevents NameError while making it clear these functions are not available
    def _not_available_in_sqlite(*args, **kwargs):
        raise NotImplementedError(
            "This function is only available when DATABASE_BACKEND is set to 'django'. "
            "Currently using SQLite backend."
        )
    
    upsert_lead = _not_available_in_sqlite
    get_lead_count = _not_available_in_sqlite
    lead_exists = _not_available_in_sqlite
    get_lead_by_id = _not_available_in_sqlite
    update_lead = _not_available_in_sqlite


# =========================
# HELPER FUNCTIONS
# =========================

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


# Field normalizations to keep DB schema compatibility
_FIELD_RENAMES = {
    "confidence": "confidence_score",
    "frische": "recency_indicator",
    "phone_source": "source_type",
}


def _sanitize_lead_data(data: Dict) -> Dict:
    """
    Drop or rename unsupported columns before writing to SQLite.

    - Renames keys defined in _FIELD_RENAMES.
    - Filters to ALLOWED_LEAD_COLUMNS to avoid 'no column named' errors.
    """
    sanitized: Dict = {}
    dropped = []

    for key, value in data.items():
        target = _FIELD_RENAMES.get(key, key)
        if target in ALLOWED_LEAD_COLUMNS:
            sanitized[target] = value
        else:
            dropped.append(key)

    if dropped and logger.isEnabledFor(logging.DEBUG):
        logger.debug("Dropping unsupported lead columns", dropped=dropped)

    return sanitized


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
    from .connection import transaction
    
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

        # Batch updates to avoid N+1 query pattern
        updates = []
        for row in rows:
            new_status = None
            if row["email"]:
                new_status = email_index.get(_normalize_email(row["email"]))
            if not new_status and row["telefon"]:
                new_status = phone_index.get(_normalize_phone(row["telefon"]))
            if new_status and new_status != row["crm_status"]:
                updates.append((new_status, row["id"]))
        
        # Execute all updates in one batch
        if updates:
            cur.executemany("UPDATE leads SET crm_status = ? WHERE id = ?", updates)
            stats["updated"] = len(updates)

    logger.debug("sync_status_to_scraper updated %d rows (checked %d)", stats["updated"], stats["checked"])
    return stats


# =========================
# SQLite-specific implementations for routing layer
# =========================

def upsert_lead_sqlite(data: Dict, max_retries: int = 3, retry_delay: float = 0.1) -> Tuple[int, bool]:
    """
    Insert or update a lead in SQLite with retry logic for handling database locks.
    
    Args:
        data: Dictionary with lead data (scraper field names)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 0.1)
        
    Returns:
        Tuple of (lead_id, created) where created is True if new lead was created
        
    Raises:
        Exception: If all retry attempts fail
    """
    from .connection import db
    
    last_exception = None
    
    for attempt in range(max_retries):
        con = None
        try:
            # Ensure only supported columns are written
            data = _sanitize_lead_data(data)

            con = db()
            cur = con.cursor()
            
            # Extract search fields
            email = data.get('email')
            telefon = data.get('telefon')
            
            normalized_email = _normalize_email(email)
            normalized_phone = _normalize_phone(telefon)
            
            # Try to find existing lead
            existing_id = None
            
            # Search by email first
            if normalized_email:
                cur.execute("SELECT id FROM leads WHERE email = ?", (email,))
                row = cur.fetchone()
                if row:
                    existing_id = row[0]
            
            # Search by phone if not found by email
            if not existing_id and telefon:
                cur.execute("SELECT id FROM leads WHERE telefon = ?", (telefon,))
                row = cur.fetchone()
                if row:
                    existing_id = row[0]
            
            if existing_id:
                # Update existing lead
                set_clauses = []
                values = []
                for key, value in data.items():
                    if key != 'id':
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if set_clauses:
                    values.append(existing_id)
                    sql = f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?"
                    cur.execute(sql, values)
                    con.commit()
                    logger.debug(f"Successfully updated lead {existing_id} in SQLite")
                
                return (existing_id, False)
            else:
                # Insert new lead
                columns = list(data.keys())
                placeholders = ['?'] * len(columns)
                values = [data[col] for col in columns]
                
                sql = f"INSERT INTO leads ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                cur.execute(sql, values)
                new_id = cur.lastrowid
                con.commit()
                logger.debug(f"Successfully created lead {new_id} in SQLite")
                
                return (new_id, True)
        
        except Exception as exc:
            last_exception = exc
            
            # Check if this is a database lock error that we should retry
            error_str = str(exc).lower()
            is_lock_error = any(keyword in error_str for keyword in TRANSIENT_ERROR_KEYWORDS)
            
            if is_lock_error and attempt < max_retries - 1:
                # Calculate exponential backoff delay
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    f"Database lock error on attempt {attempt + 1}/{max_retries} for lead save: {exc}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)
            else:
                # Either not a lock error or we're out of retries
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to save lead to SQLite after {max_retries} attempts. Last error: {exc}"
                    )
                raise
        finally:
            if con:
                try:
                    con.close()
                except Exception:
                    pass


def lead_exists_sqlite(email: Optional[str] = None, telefon: Optional[str] = None) -> bool:
    """
    Check if a lead exists in SQLite by email or phone.
    
    Args:
        email: Email address to search for
        telefon: Phone number to search for
        
    Returns:
        True if lead exists, False otherwise
    """
    from .connection import db
    
    if not email and not telefon:
        return False
    
    con = db()
    cur = con.cursor()
    
    try:
        # Check by email first
        if email:
            cur.execute("SELECT 1 FROM leads WHERE email = ?", (email,))
            if cur.fetchone():
                return True
        
        # Check by phone
        if telefon:
            cur.execute("SELECT 1 FROM leads WHERE telefon = ?", (telefon,))
            if cur.fetchone():
                return True
        
        return False
    finally:
        con.close()


def is_url_seen_sqlite(url: str, ttl_hours: int = 168) -> bool:
    """
    Check if a URL has been seen within the TTL period.
    
    Args:
        url: URL to check
        ttl_hours: Time-to-live in hours (default 168h = 7 days).
                   Set to 0 for no expiration (legacy behavior).
        
    Returns:
        True if URL was seen within TTL period, False otherwise
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        if ttl_hours <= 0:
            # Legacy behavior - no expiration
            cur.execute("SELECT 1 FROM urls_seen WHERE url = ?", (url,))
        else:
            # Check with TTL - URL is "seen" only if within TTL window
            cur.execute(
                """
                SELECT 1 FROM urls_seen 
                WHERE url = ? 
                AND ts > datetime('now', ? || ' hours')
                """,
                (url, -ttl_hours)
            )
        return bool(cur.fetchone())
    finally:
        con.close()


def mark_url_seen_sqlite(url: str, run_id: Optional[int] = None) -> None:
    """
    Mark a URL as seen in SQLite.
    
    Args:
        url: URL to mark as seen
        run_id: Optional scraper run ID
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT OR IGNORE INTO urls_seen(url, first_run_id, ts) VALUES(?, ?, datetime('now'))",
            (url, run_id)
        )
        con.commit()
    finally:
        con.close()


def is_query_done_sqlite(query: str, ttl_hours: int = 24) -> bool:
    """
    Check if a query has been done within the TTL period.
    
    Args:
        query: Search query to check
        ttl_hours: Time-to-live in hours (default 24h). 
                   Set to 0 for no expiration (legacy behavior).
        
    Returns:
        True if query was done within TTL period, False otherwise
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        if ttl_hours <= 0:
            # Legacy behavior - no expiration
            cur.execute("SELECT 1 FROM queries_done WHERE q = ?", (query,))
        else:
            # Check with TTL - query is "done" only if within TTL window
            cur.execute(
                """
                SELECT 1 FROM queries_done 
                WHERE q = ? 
                AND ts > datetime('now', ? || ' hours')
                """,
                (query, -ttl_hours)
            )
        return bool(cur.fetchone())
    finally:
        con.close()


def mark_query_done_sqlite(query: str, run_id: Optional[int] = None) -> None:
    """
    Mark a query as done in SQLite.
    
    Args:
        query: Search query to mark as done
        run_id: Optional scraper run ID
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT OR REPLACE INTO queries_done(q, last_run_id, ts) VALUES(?, ?, datetime('now'))",
            (query, run_id)
        )
        con.commit()
    finally:
        con.close()


def cleanup_expired_queries(ttl_hours: int = 48) -> int:
    """
    Remove expired query cache entries.
    
    Args:
        ttl_hours: Remove entries older than this many hours
        
    Returns:
        Number of entries removed
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        cur.execute(
            """
            DELETE FROM queries_done 
            WHERE ts < datetime('now', ? || ' hours')
            """,
            (-ttl_hours,)
        )
        deleted = cur.rowcount
        con.commit()
        logger.info(f"Cleaned up {deleted} expired query cache entries")
        return deleted
    finally:
        con.close()


def cleanup_expired_urls(ttl_hours: int = 336) -> int:
    """
    Remove expired URL cache entries.
    
    Args:
        ttl_hours: Remove entries older than this many hours (default 336h = 14 days)
        
    Returns:
        Number of entries removed
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        cur.execute(
            """
            DELETE FROM urls_seen 
            WHERE ts < datetime('now', ? || ' hours')
            """,
            (-ttl_hours,)
        )
        deleted = cur.rowcount
        con.commit()
        logger.info(f"Cleaned up {deleted} expired URL cache entries")
        return deleted
    finally:
        con.close()


def start_scraper_run_sqlite() -> int:
    """
    Start a new scraper run in SQLite.
    
    Returns:
        ID of the created scraper run
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO runs(started_at, status, links_checked, leads_new) VALUES(datetime('now'), 'running', 0, 0)"
        )
        run_id = cur.lastrowid
        con.commit()
        return run_id
    finally:
        con.close()


def finish_scraper_run_sqlite(
    run_id: int,
    links_checked: Optional[int] = None,
    leads_new: Optional[int] = None,
    status: str = "ok",
    metrics: Optional[Dict] = None
) -> None:
    """
    Finish a scraper run in SQLite.
    
    Args:
        run_id: ID of the scraper run to finish
        links_checked: Number of links checked
        leads_new: Number of new leads found
        status: Status of the run
        metrics: Optional dictionary of additional metrics (currently logged but not stored)
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        cur.execute(
            "UPDATE runs SET finished_at=datetime('now'), status=?, links_checked=?, leads_new=? WHERE id=?",
            (status, links_checked or 0, leads_new or 0, run_id)
        )
        con.commit()
        
        if metrics:
            logger.debug("Run metrics: %s", metrics)
    finally:
        con.close()


def get_lead_count_sqlite() -> int:
    """
    Get total count of leads from SQLite.
    
    Returns:
        Total number of leads
    """
    from .connection import db
    
    con = db()
    cur = con.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM leads")
        count = cur.fetchone()[0]
        return count
    finally:
        con.close()


# =========================
# EXPORTS
# =========================

# Base SQLite-specific exports
_BASE_EXPORTS = [
    'upsert_lead_sqlite',
    'lead_exists_sqlite',
    'is_url_seen_sqlite',
    'mark_url_seen_sqlite',
    'is_query_done_sqlite',
    'mark_query_done_sqlite',
    'start_scraper_run_sqlite',
    'finish_scraper_run_sqlite',
    'get_lead_count_sqlite',
    'sync_status_to_scraper',
    'cleanup_expired_queries',
    'cleanup_expired_urls',
]

# When using Django backend, also export Django adapter functions
if DATABASE_BACKEND == 'django':
    __all__ = _BASE_EXPORTS + [
        # Django backend functions
        'upsert_lead', 'get_lead_count', 'lead_exists', 
        'get_lead_by_id', 'update_lead'
    ]
else:
    __all__ = _BASE_EXPORTS
