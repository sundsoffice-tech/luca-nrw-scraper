# -*- coding: utf-8 -*-
"""
Leads-Scraper (NRW Vertrieb/Callcenter/D2D) — robust + inkrementell + UI

Features:
- Suche: Google CSE (Key/CX-Rotation, Backoff, Pagination) + Fallback Bing + Seed-URLs
- Fetch: Retries, SSL-Verify mit Fallback (Flag), robots tolerant (Cache)
- Filter: Harter Domain-Block (News/Behörden/Verbände), Pfad-Whitelist, Content-Validation tolerant
- Extraktion: OpenAI (JSON) oder Regex (E-Mail/Tel/WhatsApp/wa.me + Namensheuristik); Kleinanzeigen-Extractor
- Scoring: Kontakt-/Branchen-Signale, starker WhatsApp/Telefon/E-Mail-Boost, URL-Hints, dynamischer Schwellenwert
- Enrichment: Firma/Größe/Branche/Region/Frische + Confidence/DataQuality realistisch
- Persistenz: SQLite (runs, queries_done, urls_seen, leads) => keine Doppelten, Wiederaufnahme
- Export: CSV/XLSX (append nur neue Leads)
- Depth: Interne Tiefe + Sitemap-Hints
- UI: Flask (Start/Stop/Force/Reset/Seen-Reset/Queries-Reset + Live-Logs via SSE)
"""

# Stdlib
import argparse
import asyncio
import csv
import json
import os
import queue
import random
import re
import sqlite3
import sys
import threading
import time
import traceback
import urllib.parse
import pandas
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from flask import Response, render_template_string


# Third-party
from curl_cffi.requests import AsyncSession
import tldextract
import urllib3
from bs4 import BeautifulSoup
from bs4.element import Comment
try:
    from duckduckgo_search import DDGS
    HAVE_DDG = True
except ImportError:
    HAVE_DDG = False
from dotenv import load_dotenv
from urllib.robotparser import RobotFileParser
from stream2_extraction_layer.open_data_resolver import resolve_company_domain
from stream2_extraction_layer.extraction_enhanced import (
    extract_name_enhanced,
    extract_role_with_context,
)

# =========================
# NRW Städte für städtebasierte Suche
# =========================
NRW_CITIES = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", 
    "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster", 
    "Gelsenkirchen", "Aachen", "Mönchengladbach"
]

# --- Globales Query-Set (wird in __main__ gesetzt) ---
QUERIES: List[str] = []

# === Export-Felder (CSV/XLSX) ===
ENH_FIELDS = [
    "name","rolle","email","telefon","quelle","score","tags","region",
    "role_guess","lead_type","salary_hint","commission_hint","opening_line",
    "ssl_insecure","company_name","company_size","hiring_volume",
    "industry","recency_indicator","location_specific",
    "confidence_score","last_updated","data_quality",
    "phone_type","whatsapp_link","private_address","social_profile_url"
]

def export_xlsx(filename: str, rows=None):
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM leads")
    data = cur.fetchall()
    con.close()
    if not data:
        return
    df = pd.DataFrame(data, columns=data[0].keys())
    df.to_excel(filename, index=False)


# Warnungen zu unsicherem SSL dämpfen (bewusstes Fallback via Flag)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================
# Konfiguration & Globals
# =========================

load_dotenv(override=True)

USER_AGENT = "Mozilla/5.0 (compatible; VertriebFinder/2.3; +https://example.com)"
DEFAULT_CSV = "vertrieb_kontakte.csv"
DEFAULT_XLSX = "vertrieb_kontakte.xlsx"
DB_PATH = os.getenv("SCRAPER_DB", "scraper.db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GCS_API_KEY    = os.getenv("GCS_API_KEY", "")
GCS_CX_RAW     = os.getenv("GCS_CX", "")
BING_API_KEY   = os.getenv("BING_API_KEY", "")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "25"))

POOL_SIZE = int(os.getenv("POOL_SIZE", "12"))  # (historisch; wird in Async-Version nicht mehr genutzt)

ALLOW_PDF = (os.getenv("ALLOW_PDF", "0") == "1")
ALLOW_INSECURE_SSL = (os.getenv("ALLOW_INSECURE_SSL", "1") == "1")

# Neue Async-ENV
ASYNC_LIMIT = int(os.getenv("ASYNC_LIMIT", "50"))          # globale max. gleichzeitige Requests
ASYNC_PER_HOST = int(os.getenv("ASYNC_PER_HOST", "4"))     # pro Host
HTTP2_ENABLED = (os.getenv("HTTP2", "1") == "1")
USE_TOR = False

NRW_CITIES = ["Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster"]

ENABLE_KLEINANZEIGEN = (os.getenv("ENABLE_KLEINANZEIGEN", "1") == "1")
KLEINANZEIGEN_MAX_RESULTS = int(os.getenv("KLEINANZEIGEN_MAX_RESULTS", "20"))

# === Rotation: Proxies & User-Agents ===
def _env_list(val: str, sep: str) -> list[str]:
    return [x.strip() for x in (val or "").split(sep) if x.strip()]

PROXY_POOL = _env_list(os.getenv("PROXY_POOL", ""), ",")  # "http://user:pass@ip1:port, http://ip2:port"
UA_POOL_ENV = _env_list(os.getenv("UA_POOL", ""), "|")

# Realistische Desktop-UAs (falls UA_POOL leer)
UA_POOL_DEFAULT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/121.0.0.0 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]
UA_POOL = UA_POOL_ENV if UA_POOL_ENV else UA_POOL_DEFAULT


# Basis-MinScore aus .env; wird pro Query-Runde dynamisch angepasst
MIN_SCORE_ENV = int(os.getenv("MIN_SCORE", "40"))

MAX_PER_DOMAIN = int(os.getenv("MAX_PER_DOMAIN", "5"))
INTERNAL_DEPTH_PER_DOMAIN = int(os.getenv("INTERNAL_DEPTH_PER_DOMAIN", "10"))

SLEEP_BETWEEN_QUERIES = float(os.getenv("SLEEP_BETWEEN_QUERIES", "1.6"))
SEED_FORCE = (os.getenv("SEED_FORCE", "0") == "1")

# -------------- Logging --------------
def log(level:str, msg:str, **ctx):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    line = f"[{ts}] [{level.upper():7}] {msg}{ctx_str}"
    print(line, flush=True)
    if UILOGQ is not None:
        try: UILOGQ.put_nowait(line)
        except Exception: pass

def die(msg, **ctx):
    log("fatal", msg, **ctx); sys.exit(1)

# -------------- UI State --------------
UILOGQ: Optional[queue.Queue] = None
RUN_FLAG = {"running": False, "force": False}

# -------------- Dataclass CFG --------------
@dataclass
class ScraperConfig:
    min_score: int = MIN_SCORE_ENV
    max_results_per_domain: int = MAX_PER_DOMAIN
    request_timeout: int = HTTP_TIMEOUT
    allow_pdf: bool = ALLOW_PDF
    allow_insecure_ssl: bool = ALLOW_INSECURE_SSL
    pool_size: int = POOL_SIZE
    internal_depth_per_domain: int = INTERNAL_DEPTH_PER_DOMAIN

CFG = ScraperConfig()

# =========================
# DB-Layer (SQLite)
# =========================

_DB_READY = False  # einmaliges Schema-Setup pro Prozess

LEAD_FIELDS = [
    "name","rolle","email","telefon","quelle","score","tags","region",
    "role_guess","lead_type","salary_hint","commission_hint","opening_line","ssl_insecure",
    "company_name","company_size","hiring_volume","industry",
    "recency_indicator","location_specific","confidence_score","last_updated",
    "data_quality","phone_type","whatsapp_link","private_address","social_profile_url"
]

def _ensure_schema(con: sqlite3.Connection) -> None:
    """
    Stellt sicher, dass alle Tabellen existieren, fehlende Spalten nachgezogen
    und Indizes korrekt angelegt sind. Idempotent.
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
      social_profile_url TEXT
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

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    global _DB_READY
    if not _DB_READY:
        _ensure_schema(con)
        _DB_READY = True
    return con

def init_db():
    # bleibt als expliziter Initialisierer erhalten (macht intern dasselbe)
    con = db()
    con.close()

def migrate_db_unique_indexes():
    """
    Fallback für sehr alte Schemas mit harten UNIQUE-Constraints.
    Nur ausführen, wenn Einfügen weiterhin scheitert.
    """
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
          private_address TEXT, social_profile_url TEXT
        );

        INSERT INTO leads_new (
          id,name,rolle,email,telefon,quelle,score,tags,region,role_guess,salary_hint,
          commission_hint,opening_line,ssl_insecure,company_name,company_size,hiring_volume,
          industry,recency_indicator,location_specific,confidence_score,last_updated,data_quality,
          phone_type,whatsapp_link,lead_type,private_address,social_profile_url
        )
        SELECT
          id,name,rolle,email,telefon,quelle,score,tags,region,role_guess,salary_hint,
          commission_hint,opening_line,ssl_insecure,company_name,company_size,hiring_volume,
          industry,recency_indicator,location_specific,confidence_score,last_updated,data_quality,
          '' AS phone_type, '' AS whatsapp_link, '' AS lead_type,
          '' AS private_address, '' AS social_profile_url
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

def is_query_done(q: str) -> bool:
    con = db(); cur = con.cursor()
    cur.execute("SELECT 1 FROM queries_done WHERE q=?", (q,))
    hit = cur.fetchone()
    con.close()
    return bool(hit)

def mark_query_done(q: str, run_id: int):
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO queries_done(q,last_run_id,ts) VALUES(?,?,datetime('now'))",
        (q, run_id)
    )
    con.commit(); con.close()

def mark_url_seen(url: str, run_id: int):
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO urls_seen(url,first_run_id,ts) VALUES(?,?,datetime('now'))",
        (url, run_id)
    )
    con.commit(); con.close()

def url_seen(url: str) -> bool:
    con = db(); cur = con.cursor()
    cur.execute("SELECT 1 FROM urls_seen WHERE url=?", (url,))
    hit = cur.fetchone()
    con.close()
    return bool(hit)

def insert_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Führt INSERT OR IGNORE aus. Zieht Schema automatisch nach (fehlende Spalten).
    """
    if not leads:
        return []

    con = db(); cur = con.cursor()

    cols = ",".join(LEAD_FIELDS)
    placeholders = ",".join(["?"] * len(LEAD_FIELDS))
    sql = f"INSERT OR IGNORE INTO leads ({cols}) VALUES ({placeholders})"

    new_rows = []
    try:
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
                r.get("social_profile_url","")
            ]
            cur.execute(sql, vals)
            if cur.rowcount > 0:
                new_rows.append(r)
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
                r.get("social_profile_url","")
            ]
            cur.execute(sql, vals)
            if cur.rowcount > 0:
                new_rows.append(r)
        con.commit()
    finally:
        con.close()

    return new_rows

def start_run() -> int:
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT INTO runs(started_at,status,links_checked,leads_new) VALUES(datetime('now'),'running',0,0)"
    )
    run_id = cur.lastrowid
    con.commit(); con.close()
    return run_id

def finish_run(run_id: int, links_checked: int, leads_new: int, status: str = "ok"):
    con = db(); cur = con.cursor()
    cur.execute(
        "UPDATE runs SET finished_at=datetime('now'), status=?, links_checked=?, leads_new=? WHERE id=?",
        (status, links_checked, leads_new, run_id)
    )
    con.commit(); con.close()

def reset_history():
    con = db(); cur = con.cursor()
    a = cur.execute("SELECT COUNT(*) FROM queries_done").fetchone()[0]
    b = cur.execute("SELECT COUNT(*) FROM urls_seen").fetchone()[0]
    cur.execute("DELETE FROM queries_done")
    cur.execute("DELETE FROM urls_seen")
    con.commit(); con.close()
    return a, b


# =========================
# HTTP/SSL/robots — ASYNC
# =========================

# Content-Guards (konfigurierbar)
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(3 * 1024 * 1024)))  # 3 MB
BINARY_CT_PREFIXES = ("image/", "video/", "audio/")
DENY_CT_EXACT = {
    "application/octet-stream",
    "application/x-msdownload",
}
PDF_CT = "application/pdf"

# Circuit-Breaker pro Host
_HOST_STATE: Dict[str, Dict[str, Any]] = {}  # {host: {"penalty_until": float, "failures": int}}
# URLs, die wegen 429/403 in die zweite Welle sollen
CB_BASE_PENALTY = int(os.getenv("CB_BASE_PENALTY", "90"))  # Sekunden
CB_MAX_PENALTY  = int(os.getenv("CB_MAX_PENALTY", "900"))

_RETRY_URLS: list[str] = []

def _host_from(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""

def _penalize_host(host: str):
    st = _HOST_STATE.setdefault(host, {"penalty_until": 0.0, "failures": 0})
    st["failures"] = min(st["failures"] + 1, 10)
    penalty = min(CB_BASE_PENALTY * (2 ** (st["failures"] - 1)), CB_MAX_PENALTY)
    st["penalty_until"] = time.time() + penalty
    log("warn", "Circuit-Breaker: Host penalized", host=host, failures=st["failures"], penalty_s=penalty)

def _host_allowed(host: str) -> bool:
    st = _HOST_STATE.get(host)
    if not st:
        return True
    if time.time() >= st.get("penalty_until", 0.0):
        st["failures"] = 0
        st["penalty_until"] = 0.0
        return True
    return False

# Globale Async-Client-Fabrik + Rate-Limiter
_CLIENT_SECURE: Optional[AsyncSession] = None
_CLIENT_INSECURE: Optional[AsyncSession] = None

async def get_client(secure: bool = True) -> AsyncSession:
    global _CLIENT_SECURE, _CLIENT_INSECURE
    proxy_cfg = {"http://": "socks5://127.0.0.1:9050", "https://": "socks5://127.0.0.1:9050"} if USE_TOR else None
    if secure:
        if _CLIENT_SECURE is None:
            _CLIENT_SECURE = AsyncSession(
                impersonate="chrome120",
                headers={"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
                verify=True,
                timeout=HTTP_TIMEOUT,
                proxies=proxy_cfg,
            )
        return _CLIENT_SECURE
    else:
        if _CLIENT_INSECURE is None:
            _CLIENT_INSECURE = AsyncSession(
                impersonate="chrome120",
                headers={"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
                verify=False,
                timeout=HTTP_TIMEOUT,
                proxies=proxy_cfg,
            )
        return _CLIENT_INSECURE
    
def _make_client(secure: bool, ua: str, proxy_url: Optional[str], force_http1: bool, timeout_s: int):
    if USE_TOR:
        proxy_url = "socks5://127.0.0.1:9050"
    headers = {
        "User-Agent": ua or USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    proxies = {"http://": proxy_url, "https://": proxy_url} if proxy_url else None
    return AsyncSession(
        impersonate="chrome120",
        headers=headers,
        verify=True if secure else False,
        timeout=timeout_s,
        proxies=proxies,
    )



# robots.txt Cache mit TTL
_ROBOTS_CACHE_TTL = int(os.getenv("ROBOTS_CACHE_TTL", "21600"))  # 6h
_ROBOTS_CACHE: Dict[str, Tuple[RobotFileParser, float]] = {}     # {base: (rp, ts)}

def _acceptable_by_headers(hdrs: Dict[str, str]) -> Tuple[bool, str]:
    ct = (hdrs.get("Content-Type", "") or "").lower().split(";")[0].strip()
    if any(ct.startswith(p) for p in BINARY_CT_PREFIXES) or ct in DENY_CT_EXACT:
        return False, f"content-type={ct}"
    if (PDF_CT in ct) and (not CFG.allow_pdf):
        return False, "pdf-not-allowed"
    try:
        cl = int(hdrs.get("Content-Length", "0"))
        if cl > 0 and cl > MAX_CONTENT_LENGTH:
            return False, f"too-large:{cl}"
    except Exception:
        pass
    return True, ct or "unknown"

# Letzten HTTP-Status pro URL merken
_LAST_STATUS: Dict[str, int] = {}

async def http_get_async(url, headers=None, params=None, timeout=HTTP_TIMEOUT):
    """
    GET mit optionalem HEAD-Preflight, Proxys/UA-Rotation, HTTP/2→1.1 Fallback
    Verbesserungen:
      - HEAD-Preflight: 405/501 nicht „bestrafen“ (kein erneutes HEAD), aber bei 405 Host sanft penalizen.
      - Host-Penalty zusätzlich bei 503/504 (Rate drosseln, spätere Retries wahrscheinlicher).
    """
    # --- Rotation wählen ---
    ua = random.choice(UA_POOL) if UA_POOL else USER_AGENT
    proxy = random.choice(PROXY_POOL) if PROXY_POOL else None

    # Eingehende Header mergen (UA aus Rotation hat Vorrang)
    headers = {**(headers or {})}
    headers["User-Agent"] = ua

    host = _host_from(url)
    if not _host_allowed(host):
        log("warn", "Circuit-Breaker: host muted (skip)", url=url, host=host)
        return None

    base_to = max(5, min(timeout, 45))
    eff_timeout = base_to + random.uniform(0.0, 1.25)

    # 1) HEAD-Preflight (secure, HTTP/2/1 je nach Param) – optional
    r_head = None
    try:
        async with _make_client(True, ua, proxy, force_http1=False, timeout_s=eff_timeout) as client_head:
            r_head = await client_head.head(url, headers=headers, params=params, allow_redirects=True, timeout=eff_timeout)
            if r_head is not None:
                # Wenn HEAD 405/501 → kein erneutes HEAD versuchen (spart Roundtrips).
                # Zusätzlich: bei 405 sanfte Host-Penalty (viele Sites blocken HEAD hart).
                if r_head.status_code == 405:
                    _penalize_host(host)
                    log("info", "HEAD 405: host penalized, continue with GET", url=url)
                if r_head.status_code in (405, 501):
                    pass  # einfach mit GET fortfahren

                elif r_head.status_code in (200, 204):
                    ok, reason = _acceptable_by_headers(r_head.headers or {})
                    if not ok:
                        log("info", "Head-preflight: skipped by headers", url=url, reason=reason)
                        return None
    except Exception:
        # Preflight ist optional – still & silent
        r_head = None

    async def _do_get(secure: bool, force_http1: bool) -> Optional[Any]:
        async with _make_client(secure, ua, proxy, force_http1, eff_timeout) as cl:
            return await cl.get(url, headers=headers, params=params, timeout=eff_timeout, allow_redirects=True)

    # 2) Primär GET (secure, HTTP/2 erlaubt)
    try:
        r = await _do_get(secure=True, force_http1=False)
        if r.status_code == 200:
            ok, reason = _acceptable_by_headers(r.headers or {})
            if not ok:
                log("info", "GET: skipped by headers", url=url, reason=reason)
                return None
            setattr(r, "insecure_ssl", False)
            return r
        if r.status_code in (429, 403, 503, 504):
            _penalize_host(host)
            if url not in _RETRY_URLS:
                _RETRY_URLS.append(url)
            log("warn", f"{r.status_code} received", url=url)
            return r
    except Exception:
        # 2a) Retry als HTTP/1.1
        try:
            r = await _do_get(secure=True, force_http1=True)
            if r.status_code == 200:
                ok, reason = _acceptable_by_headers(r.headers or {})
                if not ok:
                    return None
                setattr(r, "insecure_ssl", False)
                return r
            if r.status_code in (429, 403, 503, 504):
                _penalize_host(host)
                if url not in _RETRY_URLS:
                    _RETRY_URLS.append(url)
                log("warn", f"{r.status_code} received (HTTP/1.1 retry)", url=url)
                return r
        except Exception:
            pass

    # 3) SSL-Fallback (unsicher), erst HTTP/2, dann HTTP/1.1
    if CFG.allow_insecure_ssl:
        try:
            r2 = await _do_get(secure=False, force_http1=False)
            if r2.status_code == 200:
                ok, reason = _acceptable_by_headers(r2.headers or {})
                if not ok:
                    return None
                setattr(r2, "insecure_ssl", True)
                log("warn", "SSL Fallback ohne Verify genutzt", url=url)
                return r2
            if r2.status_code in (429, 403, 503, 504):
                _penalize_host(host)
                if url not in _RETRY_URLS:
                    _RETRY_URLS.append(url)
                log("warn", f"{r2.status_code} received (insecure TLS)", url=url)
                return r2
        except Exception:
            try:
                r2 = await _do_get(secure=False, force_http1=True)
                if r2.status_code == 200:
                    ok, reason = _acceptable_by_headers(r2.headers or {})
                    if not ok:
                        return None
                    setattr(r2, "insecure_ssl", True)
                    log("warn", "SSL Fallback (HTTP/1.1) genutzt", url=url)
                    return r2
                if r2.status_code in (429, 403, 503, 504):
                    _penalize_host(host)
                    if url not in _RETRY_URLS:
                        _RETRY_URLS.append(url)
                    log("warn", f"{r2.status_code} received (insecure TLS, HTTP/1.1)", url=url)
                    return r2
            except Exception:
                pass

    log("error", "HTTP GET endgültig gescheitert", url=url)
    return None


async def fetch_response_async(url: str, headers=None, params=None, timeout=HTTP_TIMEOUT):
    r = await http_get_async(url, headers=headers, params=params, timeout=timeout)
    if r is None:
        _LAST_STATUS[url] = -1
        return None
    status = getattr(r, "status_code", 0)
    if status != 200:
        _LAST_STATUS[url] = status
        log("warn", "Nicht-200 beim Abruf – skip", url=url, status=status)
        return None
    _LAST_STATUS[url] = 200
    return r

async def robots_allowed_async(url: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        rp_ts = _ROBOTS_CACHE.get(base)

        need_refresh = True
        if rp_ts:
            rp, ts = rp_ts
            if time.time() - ts < _ROBOTS_CACHE_TTL:
                need_refresh = False

        if need_refresh:
            robots_url = urllib.parse.urljoin(base, "/robots.txt")
            r = await http_get_async(robots_url, timeout=10)
            rp = RobotFileParser()
            if r and r.status_code == 200 and r.text:
                rp.parse(r.text.splitlines())
            else:
                _ROBOTS_CACHE[base] = (rp, time.time())
                log("warn", "robots.txt Fetch fehlgeschlagen – konservativ erlauben", url=url)
                return True
            _ROBOTS_CACHE[base] = (rp, time.time())

        allowed = _ROBOTS_CACHE[base][0].can_fetch(USER_AGENT, url)
        log("debug", "robots.txt geprüft", url=url, allowed=allowed)
        return allowed
    except Exception as e:
        log("warn", "robots.txt Prüfung fehlgeschlagen – konservativ erlauben", url=url, error=str(e))
        return True

# =========================
# Suche (modular)
# =========================

def _normalize_cx(s: str) -> str:
    if not s: return ""
    try:
        p = urllib.parse.urlparse(s)
        if p.query:
            q = urllib.parse.parse_qs(p.query)
            val = q.get("cx", [""])[0].strip()
            if val: return val
    except Exception:
        pass
    return s.strip()

def _jitter(a=0.2,b=0.8): return a + random.random()*(b-a)

GCS_CX = _normalize_cx(GCS_CX_RAW)
# Multi-Key/CX Rotation + Limits
GCS_KEYS = [k.strip() for k in os.getenv("GCS_KEYS","").split(",") if k.strip()] or ([GCS_API_KEY] if GCS_API_KEY else [])
GCS_CXS  = [_normalize_cx(x) for x in os.getenv("GCS_CXS","").split(",") if _normalize_cx(x)] or ([GCS_CX] if GCS_CX else [])
MAX_GOOGLE_PAGES = int(os.getenv("MAX_GOOGLE_PAGES","12"))  # höherer Default

# ======= SUCHE: Branchen & Query-Baukasten (modular) =======
REGION = '(NRW OR "Nordrhein-Westfalen" OR Düsseldorf OR Köln OR Essen OR Dortmund OR Bochum OR Duisburg OR Mönchengladbach)'
CONTACT = '(kontakt OR impressum OR ansprechpartner OR "e-mail" OR email OR telefon OR whatsapp)'
SALES   = '(vertrieb OR d2d OR "call center" OR telesales OR outbound OR verkauf OR sales)'

# Kurze, treffsichere Query-Sets je Branche
INDUSTRY_QUERIES: dict[str, list[str]] = {
    "candidates": [
        # Kleinanzeigen (Privatpersonen)
        'site:kleinanzeigen.de/s-gesuche "vertrieb" "NRW" -gewerblich',
        'site:kleinanzeigen.de "ich suche job" "vertrieb" "NRW"',
        'site:markt.de "stellengesuche" "vertrieb"',

        # Messenger Gruppen (Offene Einladungslinks)
        'site:t.me/joinchat "vertrieb" "gruppe"',
        'site:chat.whatsapp.com "jobs" "nrw"',
        'site:chat.whatsapp.com "vertriebler"',

        # Social Media (Public Profiles via Search)
        'site:linkedin.com/in/ "open to work" "sales" "nrw" -intitle:Login',
        'site:facebook.com/groups "stellengesuche" "vertrieb" "handynummer"',
        'site:instagram.com "suche job" "vertrieb" "dm me"',

        # Lebensläufe / Portfolios
        'filetype:pdf "lebenslauf" "vertrieb" "nrw" -site:xing.com -site:linkedin.com',
    ],
}

# NEU: Recruiter-spezifische Queries für Vertriebler-Rekrutierung
RECRUITER_QUERIES = {
    'recruiter': [
        'site:kleinanzeigen.de/s-stellengesuche/ "vertrieb" NRW',
        'site:kleinanzeigen.de/s-stellengesuche/ "verkäufer" NRW',
        'site:kleinanzeigen.de "suche arbeit" "vertrieb" NRW',
        'site:markt.de/stellengesuche/ "vertrieb" NRW',
    ]
}


# Fallback für "alle" Branchen – Reihenfolge
INDUSTRY_ORDER = ["nrw","social","solar","telekom","versicherung","bau","ecom","household"]

def build_queries(
    selected_industry: Optional[str] = None,
    per_industry_limit: int = 2
) -> List[str]:
    """
    Erweiterte Query-Builder mit Recruiter-Support und städtebasierter LinkedIn-Suche.
    
    Logik:
    1. Falls selected_industry == 'recruiter': RECRUITER_QUERIES + dynamische LinkedIn-Queries pro Stadt
    2. Falls selected_industry == 'all': Recruiter ZUERST (inkl. LinkedIn-Queries), dann alle Branchen
    3. Falls normale Branche: Nur diese Branche
    
    Args:
        selected_industry: 'recruiter' | 'all' | 'solar' | 'telekom' | etc.
        per_industry_limit: Queries pro Branche/Set (Default: 2)
    
    Returns:
        Liste von Query-Strings für diesen Run
    """
    out: List[str] = []
    limit = max(1, per_industry_limit)

    def _generate_linkedin_city_queries() -> List[str]:
        """
        Generiert dynamisch LinkedIn-Queries für jede Stadt in NRW_CITIES.
        Zwei Varianten pro Stadt:
          a) "open to work" + "vertrieb" + Stadt
          b) "vertrieb" + E-Mail-Provider + Stadt
        """
        linkedin_queries: List[str] = []
        for city in NRW_CITIES:
            linkedin_queries.append(f'site:linkedin.com/in/ "open to work" "vertrieb" {city}')
            linkedin_queries.append(f'site:linkedin.com/in/ "vertrieb" ("@gmail.com" OR "@gmx.de" OR "@web.de") {city}')
        return linkedin_queries

    linkedin_city_qs = _generate_linkedin_city_queries()
    recruiter_all_qs: List[str] = list(RECRUITER_QUERIES.get('recruiter', [])) + linkedin_city_qs

    # FALL 1: Recruiter-Mode (reine Vertriebler-Suche)
    if selected_industry and selected_industry.lower() == 'recruiter':
        recruiter_limit = limit
        if per_industry_limit <= 2:
            recruiter_limit = len(recruiter_all_qs)
            log('info', f"Recruiter-Mode: Limit auf {recruiter_limit} erhoeht (Geo-Fencing fuer {len(NRW_CITIES)} Staedte).")
        log('info', f"Recruiter-Mode: lade {len(recruiter_all_qs)} Queries, Limit: {recruiter_limit}")
        return recruiter_all_qs[:recruiter_limit]

    # FALL 2: Standard Industrie (solar, telekom, etc.)
    if selected_industry and selected_industry.lower() != 'all':
        qs = INDUSTRY_QUERIES.get(selected_industry.lower(), [])
        if qs:
            log('info', f"Branche '{selected_industry}': lade {len(qs)} Queries, Limit: {limit}")
            return qs[:limit]
        else:
            log('warn', f"Branche '{selected_industry}' nicht gefunden, verwende 'all'")
            selected_industry = 'all'
    
    # FALL 3: 'all' = Recruiter ZUERST (inkl. LinkedIn-Stadt-Queries), dann alle Branchen
    if selected_industry == 'all' or selected_industry is None:
        recruiter_count = min(len(recruiter_all_qs), limit)
        out.extend(recruiter_all_qs[:recruiter_count])
        
        # Dann nacheinander alle Standard-Branchen nach INDUSTRY_ORDER
        industry_count = 0
        for key in INDUSTRY_ORDER:
            qs = INDUSTRY_QUERIES.get(key, [])
            if qs:
                out.extend(qs[:limit])
                industry_count += len(qs[:limit])
        
        log('info', f"All-Mode: {len(out)} Queries geladen (Recruiter: {recruiter_count} inkl. {len(linkedin_city_qs)} LinkedIn-Stadt-Queries, Branchen: {industry_count})")
    
    return out



# ---- Domain-/Pfad-Filter (erweitert) ----
DENY_DOMAINS = {
  "google.com","maps.google.com","mapy.google.com","business.site",
  "twitter.com","x.com","tiktok.com","youtube.com","youtu.be"
}

SOCIAL_HOSTS = {
    "facebook.com","m.facebook.com",
    "instagram.com","www.instagram.com",
    "t.me","telegram.me",
    "whatsapp.com","chat.whatsapp.com",
}

ALLOW_PATH_HINTS = (
  "kontakt","impressum","karriere","jobs","stellen","bewerben","team","ansprechpartner",
  "callcenter","telesales","outbound","vertrieb","verkauf","sales","d2d","door-to-door","haustuer","haustür"
)

NEG_PATH_HINTS = (
  "/datenschutz", "/privacy", "/agb", "/terms", "/bedingungen",
  "/login", "/signin", "/signup", "/account", "/cart", "/warenkorb", "/checkout", "/search",
  "/newsletter",
  "/gleichstellungsstelle",
  "/grundsicherung",
  "/rathaus/",
  "/verwaltung/",
  "/soziales-gesundheit-wohnen-und-recht",
  "/seminare",
  "/seminarprogramm",
  "/events",
  "/veranstaltungen",
)

def is_denied(url: str) -> bool:
    p = urllib.parse.urlparse(url)
    host = (p.netloc or "").lower()
    # Normalisieren: www./m. abschneiden
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("m."):
        host = host[2:]

    if host in SOCIAL_HOSTS:
        return False

    # Harte Domain-Blockliste (bestehend)
    for d in DENY_DOMAINS:
        d = d.lower()
        if host == d or host.endswith("." + d):
            return True

    # Bestehende Heuristiken
    if host.startswith(("uni-", "cdu-", "stadtwerke-")):
        return True
    if host in {"ruhr-uni-bochum.de"}:
        return True

    # NEU: NRW-Rauschen — IHK/HWK/Bildung
    if host.endswith(".ihk.de") or host.startswith(("ihk-", "hwk-")):
        return True
    if any(k in host for k in (
        "schule", "berufskolleg", "weiterbildung", "bildungszentrum",
        "akademie", "bbw-", "bfw-", "leb-"
    )):
        return True

    # NEU: Jobportale/Aggregatoren (ziehen Budget, liefern selten direkte tel/mail/wa)
    PORTAL_HOST_HINTS = (
        "stepstone", "indeed", "monster", "jobware", "stellenanzeigen",
        "jobvector", "yourfirm", "metajob", "stellenangebotevertrieb",
        "jobanzeiger", "jobboerse.arbeitsagentur", "meinestadt"
    )
    if any(h in host for h in PORTAL_HOST_HINTS):
        return True

    return False


def path_ok(url: str) -> bool:
    p = urllib.parse.urlparse(url)
    path = (p.path or "").lower()
    q    = (p.query or "").lower()
    frag = (p.fragment or "").lower()
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host in SOCIAL_HOSTS:
        return True
    if host.endswith("kleinanzeigen.de") or host.endswith("ebay-kleinanzeigen.de"):
        return True
    if any(bad in path for bad in NEG_PATH_HINTS):
        return False
    positive = any(h in path for h in ALLOW_PATH_HINTS) \
               or any(h in q for h in ALLOW_PATH_HINTS) \
               or any(h in frag for h in ALLOW_PATH_HINTS)
    is_rootish = (path in ("", "/"))
    return positive or is_rootish

def _normalize_for_dedupe(u: str) -> str:
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


UrlLike = Union[str, Dict[str, Any]]


def _extract_url(item: UrlLike) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("url", "")
    return ""


from typing import List
import re, urllib.parse

def prioritize_urls(urls: List[str]) -> List[str]:
    """
    Priorisiert typische Kontaktseiten deutlich höher als Karriere/Jobs/Datenschutz.
    - Additives Scoring (nicht nur erstes Pattern)
    - Starke Upvotes: /kontakt, /impressum
    - Downvotes: /karriere, /jobs, /stellen, /datenschutz, /privacy, /agb
    - Leichte Bevorzugung kurzer/oberflächlicher Pfade; Abwertung bei Paginierung/Fragmenten
    """
    # --- POSITIVE & NEGATIVE Schlüsselwörter ---
    # Hinweis: additive Bewertung; ein Pfad kann mehrere Treffer bekommen.
    PRIORITY_PATTERNS = [
        (r'/kontakt(?:/|$)',                    +40),
        (r'/kontaktformular(?:/|$)',            +32),
        (r'/impressum(?:/|$)',                  +35),
        (r'/team(?:/|$)',                       +12),
        (r'/ueber-uns|/über-uns|/unternehmen',  +10),
        # NEU: Jobseeker-Signale boosten
        (r'/karriere(?:/|$)',                   +18),
        (r'/jobs?(?:/|$)',                      +18),
        (r'/stellen(?:/|$)',                    +16),
        (r'/bewerb|/lebenslauf|/cv|/profil',    +24),
    ]

    PENALTY_PATTERNS = [
        (r'/datenschutz|/privacy|/policy',      -40),
        (r'/agb|/terms|/bedingungen',           -16),
        (r'/login|/signin|/signup|/account',    -70),
        (r'/cart|/warenkorb|/checkout|/search', -70),
        (r'/blog/|/news/',                      -30),
    ]


    def _score(u: str) -> int:
        s = 50
        path = urllib.parse.urlparse(u).path or "/"
        low = u.lower()

        # Positive Muster: additiv werten
        for pat, pts in PRIORITY_PATTERNS:
            if re.search(pat, low, re.I):
                s += pts

        # Negative Muster: additiv abwerten
        for pat, pts in PENALTY_PATTERNS:
            if re.search(pat, low, re.I):
                s += pts

        # Query-Hints (selten, aber wenn vorhanden → leicht positiv)
        if re.search(r'(\?|#).*(kontakt|impressum)', low, re.I):
            s += 12

        # Pfad-Länge / -Tiefe: kurze, flache Pfade bevorzugen
        depth = max(0, path.count('/') - 1)
        s += max(0, 20 - len(path))           # kürzerer Pfad = besser
        s += max(0, 10 - 5*depth)             # weniger Unterverzeichnisse = besser

        # Rauschfilter / Paginierung / Fragmente
        if len(u) > 220:                      # sehr lange URLs wirken oft „Rauschen“
            s -= 40
        if re.search(r'(\?|&)page=\d{1,3}\b', low):
            s -= 25
        if re.search(r'/page/\d{1,3}\b', low):
            s -= 25
        if '#' in u:                          # Anker/Kommentare/Blogfragmente
            s -= 10

        return s

    # Dedupe (auf Basis deiner Normalisierung) + Scoring + Sortierung
    normed, seen = [], set()
    for u in urls:
        nu = _normalize_for_dedupe(u)
        if nu in seen:
            continue
        seen.add(nu)
        normed.append(nu)

    scored = [(u, _score(u)) for u in normed]
    scored.sort(key=lambda x: (-x[1], x[0]))
    return [u for u, _ in scored]


async def google_cse_search_async(q: str, max_results: int = 60, date_restrict: Optional[str] = None) -> Tuple[List[Dict[str, str]], bool]:
    if not (GCS_KEYS and GCS_CXS):
        log("debug","Google CSE nicht konfiguriert – übersprungen"); return [], False

    def _preview(txt: Optional[str]) -> str:
        if not txt: return ""
        # HTML-Tags & übermäßige Whitespaces entfernen, dann hart bei 200 cutten
        txt = re.sub(r"<[^>]+>", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt[:200]

    url = "https://www.googleapis.com/customsearch/v1"
    results: List[Dict[str, str]] = []
    page_no, key_i, cx_i = 0, 0, 0
    had_429 = False
    page_cap = int(os.getenv("MAX_GOOGLE_PAGES","12"))
    while len(results) < max_results and page_no < page_cap:
        params = {
            "key": GCS_KEYS[key_i], "cx": GCS_CXS[cx_i], "q": q,
            "num": min(10, max_results - len(results)),
            "start": 1 + page_no*10, "lr":"lang_de", "safe":"off",
        }
        if date_restrict:
            params["dateRestrict"] = date_restrict

        r = await http_get_async(url, headers=None, params=params, timeout=HTTP_TIMEOUT)
        if not r:
            key_i = (key_i + 1) % max(1,len(GCS_KEYS))
            cx_i  = (cx_i  + 1) % max(1,len(GCS_CXS))
            sleep_s = 4 + int(4*_jitter())
            await asyncio.sleep(sleep_s)
            continue

        if r.status_code == 429:
            had_429 = True
            key_i = (key_i + 1) % max(1,len(GCS_KEYS))
            cx_i  = (cx_i  + 1) % max(1,len(GCS_CXS))
            sleep_s = 6 + int(6*_jitter())
            log("warn","Google 429 – rotiere Key/CX & backoff", sleep=sleep_s)
            await asyncio.sleep(sleep_s)
            continue

        if r.status_code != 200:
            log("error","Google CSE Status != 200", status=r.status_code, body=_preview(r.text))
            break

        try:
            data = r.json()
        except Exception:
            log("error","Google CSE JSON-Parsing fehlgeschlagen", text=_preview(r.text))
            break

        items = data.get("items", []) or []
        batch = [
            {
                "url": it.get("link"),
                "title": it.get("title", "") or "",
                "snippet": it.get("snippet", "") or "",
            }
            for it in items
            if it.get("link")
        ]
        results.extend(batch)
        log("info","Google CSE Batch", q=q, batch=len(batch), total=len(results), page_no=page_no)

        if not batch: break
        page_no += 1
        await asyncio.sleep(0.5 + _jitter(0,0.6))

    uniq_items: List[Dict[str, str]] = []
    seen = set()
    for entry in results:
        raw_url = entry.get("url", "")
        if not raw_url:
            continue
        nu = _normalize_for_dedupe(raw_url)
        if nu in seen: continue
        seen.add(nu)
        if is_denied(nu): continue
        if not path_ok(nu): continue
        uniq_items.append({
            "url": nu,
            "title": entry.get("title", "") or "",
            "snippet": entry.get("snippet", "") or "",
        })
    if uniq_items:
        ordered = prioritize_urls([item["url"] for item in uniq_items])
        order_map = {u: i for i, u in enumerate(ordered)}
        uniq_items.sort(key=lambda item: order_map.get(item["url"], len(order_map)))
    return uniq_items, had_429


async def duckduckgo_search_async(q: str, max_results: int = 30) -> List[Dict[str, str]]:
    if not HAVE_DDG:
        log("warn", "duckduckgo_search nicht installiert – Fallback übersprungen", q=q)
        return []

    def _search_sync():
        with DDGS() as ddgs:
            return list(ddgs.text(q, region="de-de", safesearch="off", max_results=max_results))

    try:
        results = await asyncio.to_thread(_search_sync)
    except Exception as e:
        log("warn", "DuckDuckGo-Suche fehlgeschlagen", q=q, error=str(e))
        return []

    items: List[Dict[str, str]] = []
    seen = set()
    for entry in results or []:
        href = entry.get("href")
        if not href:
            continue
        nu = _normalize_for_dedupe(href)
        if nu in seen:
            continue
        seen.add(nu)
        if is_denied(nu):
            continue
        if not path_ok(nu):
            continue
        items.append({
            "url": nu,
            "title": entry.get("title", "") or "",
            "snippet": entry.get("body", "") or "",
        })

    if items:
        ordered = prioritize_urls([item["url"] for item in items])
        order_map = {u: i for i, u in enumerate(ordered)}
        items.sort(key=lambda item: order_map.get(item["url"], len(order_map)))
    log("info", "DuckDuckGo Treffer", q=q, count=len(items))
    return items


def _ka_keywords_from_query(q: str) -> str:
    if not q:
        return ""
    cleaned = re.sub(r"site:[^\s]+", " ", q, flags=re.I)
    cleaned = re.sub(r"[()\"']", " ", cleaned)
    cleaned = re.sub(r"\b(OR|AND)\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:120]


async def kleinanzeigen_search_async(q: str, max_results: int = KLEINANZEIGEN_MAX_RESULTS) -> List[Dict[str, str]]:
    if (not ENABLE_KLEINANZEIGEN) or max_results <= 0:
        return []

    keywords = _ka_keywords_from_query(q)
    if not keywords:
        return []

    url = "https://www.kleinanzeigen.de/s-suchanfrage.html"
    try:
        r = await http_get_async(url, params={"keywords": keywords}, timeout=HTTP_TIMEOUT)
    except Exception as e:
        log("warn", "Kleinanzeigen-Suche fehlgeschlagen", q=keywords, err=str(e))
        return []
    if not r:
        return []
    if r.status_code != 200:
        log("warn", "Kleinanzeigen Status != 200", status=r.status_code, q=keywords)
        return []

    html = r.text or ""
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, str]] = []
    for art in soup.select("li.ad-listitem article.aditem"):
        href = art.get("data-href") or ""
        if not href:
            a_tag = art.find("a", href=True)
            if a_tag:
                href = a_tag.get("href", "")
        if not href:
            continue
        full = urllib.parse.urljoin("https://www.kleinanzeigen.de", href)
        title_el = art.select_one("h2 a")
        desc_el = art.select_one(".aditem-main--middle--description")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        snippet = desc_el.get_text(" ", strip=True) if desc_el else ""
        items.append({"url": full, "title": title, "snippet": snippet})
        if len(items) >= max_results:
            break

    uniq: List[Dict[str, str]] = []
    seen = set()
    for entry in items:
        u = _extract_url(entry)
        if not u:
            continue
        nu = _normalize_for_dedupe(u)
        if nu in seen:
            continue
        seen.add(nu)
        if is_denied(nu):
            continue
        uniq.append({**entry, "url": nu})

    if uniq:
        log("info", "Kleinanzeigen Treffer", q=keywords, count=len(uniq))
    return uniq


# =========================
# Regex/Scoring/Enrichment
# =========================

EMAIL_RE   = re.compile(r'\b(?!noreply|no-reply|donotreply)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}\b', re.I)
PHONE_RE   = re.compile(r'(?:\+49|0049|0)\s?(?:\(?\d{2,5}\)?[\s\/\-]?)?\d(?:[\s\/\-]?\d){5,10}')
MOBILE_RE  = re.compile(r'(?:\+49|0049|0)\s*1[5-7]\d(?:[\s\/\-]?\d){6,10}')
SALES_RE   = re.compile(r'\b(vertrieb|vertriebs|sales|account\s*manager|key\s*account|business\s*development|au?endienst|aussendienst|handelsvertreter|telesales|call\s*center|outbound|haust?r|d2d)\b', re.I)
LOW_PAY_HINT   = re.compile(r'\b(12[,\.]?\d{0,2}|13[,\.]?\d{0,2})\s*€\s*/?\s*h|\b(Mindestlohn|Fixum\s+ab\s+\d{1,2}\s*€)\b', re.I)
PROVISION_HINT = re.compile(r'\b(Provisionsbasis|nur\s*Provision|hohe\s*Provision(en)?|Leistungsprovision)\b', re.I)
D2D_HINT       = re.compile(r'\b(Door[-\s]?to[-\s]?door|Haustür|Kaltakquise|D2D)\b', re.I)
CALLCENTER_HINT= re.compile(r'\b(Call\s*Center|Telesales|Outbound|Inhouse-?Sales)\b', re.I)
B2C_HINT       = re.compile(
    r'\b(?:B2C|Privatkunden|Haushalte|Endkunden|Privatperson(?:en)?|'
    r'verschuld\w*|schuldenhilfe|schuldnerberatung|schuldner|'
    r'inkasso(?:[-\s]?f(?:ä|ae)lle?)?)\b',
    re.I,
)
JOBSEEKER_RE  = re.compile(r'\b(jobsuche|stellensuche|arbeitslos|lebenslauf|bewerb(ung)?|cv|portfolio|offen\s*f(?:ür|uer)\s*neues)\b', re.I)
CANDIDATE_TEXT_RE = re.compile(r'(?is)\b(ich\s+suche|suche\s+job|biete\s+mich|arbeitslos|stellengesuch|open\s+to\s+work)\b')
EMPLOYER_TEXT_RE  = re.compile(r'(?is)\b(wir\s+suchen|wir\s+stellen\s+ein|deine\s+aufgaben|unser\s+angebot|jetzt\s+bewerben)\b')
RECRUITER_RE  = re.compile(r'\b(recruit(er|ing)?|hr|human\s*resources|personalvermittlung|headhunter|wir\s*suchen|join\s*our\s*team)\b', re.I)


WHATSAPP_RE    = re.compile(r'(?i)\b(WhatsApp|Whats\s*App)[:\s]*\+?\d[\d \-()]{6,}\b')
WA_LINK_RE     = re.compile(r'(?:https?://)?(?:wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+|chat\.whatsapp\.com/[A-Za-z0-9]+)', re.I)
WHATS_RE       = re.compile(r'(?:\+?\d{2,3}\s?)?(?:\(?0\)?\s?)?\d{2,4}[\s\-]?\d{3,}.*?(?:whatsapp|wa\.me|api\.whatsapp)', re.I)
WHATSAPP_PHRASE_RE = re.compile(
    r'(?i)(meldet\s+euch\s+per\s+whatsapp|schreib(?:t)?\s+mir\s+(?:per|bei)\s+whatsapp|per\s+whatsapp\s+melden)'
)
TELEGRAM_LINK_RE = re.compile(r'(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_/-]+', re.I)

CITY_RE        = re.compile(r'\b(NRW|Nordrhein[-\s]?Westfalen|Düsseldorf|Köln|Essen|Dortmund|Mönchengladbach|Bochum|Wuppertal|Bonn)\b', re.I)
NAME_RE        = re.compile(r'\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+){0,2})\b')
# --- Kontext-Fenster für Heuristiken (Sales/Jobseeker) ---
# Sales-Fenster: erkennt Vertriebs-/Akquise-Kontext im Umfeld von Text
SALES_WINDOW = re.compile(
    r'(?is).{0,400}(vertrieb|verkauf|sales|akquise|außendienst|aussendienst|'
    r'call\s*center|telefonverkauf|door\s*to\s*door|d2d|provision).{0,400}'
)

# Jobseeker-Fenster: erkennt Lebenslauf/Bewerbung/Jobsuche-Kontext
JOBSEEKER_WINDOW = re.compile(
    r'(?is).{0,400}(jobsuche|stellensuche|arbeitslos|bewerb(?:ung)?|lebenslauf|'
    r'cv|portfolio|offen\s*f(?:ür|uer)\s*neues|profil).{0,400}'
)

CANDIDATE_KEYWORDS = [
    "suche job",
    "biete mich an",
    "open to work",
    "neue herausforderung",
    "gesuch",
    "lebenslauf",
]

IGNORE_KEYWORDS = [
    "wir suchen",
    "stellenanzeige",
    "gmbh",
    "hr manager",
    "karriere bei uns",
]


NEGATIVE_HINT  = re.compile(r'\b(Behörde|Amt|Universität|Karriereportal|Blog|Ratgeber|Software|SaaS|Bank|Versicherung)\b', re.I)
WHATSAPP_INLINE= re.compile(r'\+?\d[\d ()\-]{6,}\s*(?:WhatsApp|WA)', re.I)
PERSON_PREFIX  = re.compile(r'\b(Herr|Frau|Hr\.|Fr\.)\s+[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)?')
JOBSEEKER_WINDOW = re.compile(
    r'(?is).{0,400}(jobsuche|stellensuche|arbeitslos|bewerb(ung)?|lebenslauf|cv|portfolio|offen\s*f(?:ür|uer)\s*neues).{0,400}'
)
INDUSTRY_PATTERNS = {
    "energie":      r'\b(Energie|Strom|Gas|Ökostrom|Versorger|Photovoltaik|PV|Solar|Wärmepumpe)\b',
    "telekom":      r'\b(Telekommunikation|Telefonie|Internet|DSL|Mobilfunk|Glasfaser|Telekom)\b',
    "versicherung": r'\b(Versicherung(en)?|Versicherungsmakler|Bausparen|Finanzberatung|Finanzen)\b',
    "bau":          r'\b(Bau|Handwerk|Sanierung|Fenster|Türen|Dämm|Energieberatung)\b',
    "ecommerce":    r'\b(E-?Commerce|Onlineshop|Bestellhotline|Kundengewinnung)\b',
    "household":    r'\b(Vorwerk|Kobold|Staubsauger|Haushaltswaren)\b'
}

CONTACT_HINTS = [
    "kontakt", "ansprechpartner", "e-mail", "email", "mail",
    "telefon", "tel", "tel.", "whatsapp", "telegram", "anruf", "hotline"
]

INDUSTRY_HINTS = [
    "solar", "photovoltaik", "pv", "energie", "energieberatung", "strom", "gas",
    "glasfaser", "telekom", "telekommunikation", "dsl", "mobilfunk", "internet",
    "vorwerk", "kobold", "staubsauger", "haushaltswaren",
    "fenster", "türen", "tueren", "dämm", "daemm", "wärmepumpe", "waermepumpe",
    "versicherung", "versicherungen", "bausparen", "immobilien", "makler",
    "onlineshop", "e-commerce", "shop", "kundengewinnung"
]

BAD_MAILBOXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "info", "kontakt", "contact", "office", "service", "support",
    "bewerbung", "recruiting", "karriere", "jobs", "hr", "humanresources",
    "talent", "people", "personal", "datenschutz", "privacy"
}

PORTAL_DOMAINS = {
    "heyjobs.co", "heyjobs.de", "stepstone.de", "indeed.com", "monster.de",
    "arbeitsagentur.de", "softgarden.io", "talents.studysmarter.de",
    "join.com", "jobware.de", "hays.de", "randstad.de", "adecco.de"
}

GENERIC_BOXES = {"sales", "vertrieb", "verkauf", "marketing", "kundenservice", "hotline"}

def etld1(host: str) -> str:
    if not host:
        return ""
    ex = tldextract.extract(host)
    dom = getattr(ex, "top_domain_under_public_suffix", None) or ex.registered_domain
    return dom.lower() if dom else host.lower()


def _dedup_run(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Entdoppelt pro Run anhand (eTLD+1 der Quelle, normalisierte E-Mail, normalisierte Tel).
    Spart sinnlose DB-Inserts/Exports.
    """
    seen: set[Tuple[str, str, str]] = set()
    out: List[Dict[str, Any]] = []
    for r in rows:
        try:
            dom = etld1(urllib.parse.urlparse(r.get("quelle","")).netloc)
        except Exception:
            dom = ""
        e = (r.get("email") or "").strip().lower()
        t = re.sub(r'\D','', r.get("telefon") or "")
        key = (dom, e, t)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def same_org_domain(page_url: str, email_domain: str) -> bool:
    try:
        host = urllib.parse.urlparse(page_url).netloc
        return etld1(host) == etld1(email_domain)
    except Exception:
        return False

_OBFUSCATION_PATTERNS = [
    (r'\s*(\[\s*at\s*\]|\(\s*at\s*\)|\{\s*at\s*\}|\s+at\s+|\s+ät\s+)\s*', '@'),
    (r'\s*(\[\s*dot\s*\]|\(\s*dot\s*\)|\{\s*dot\s*\}|\s+dot\s+|\s+punkt\s*|\s*\.\s*)\s*', '.'),
    (r'\s*(ät|@t)\s*', '@'),   # zusätzliche Varianten
]

def deobfuscate_text_for_emails(text: str) -> str:
    s = text
    for pat, rep in _OBFUSCATION_PATTERNS:
        s = re.sub(pat, rep, s, flags=re.I)
    return s

def email_quality(email: str, page_url: str) -> str:
    if not email:
        return "reject"
    low = email.strip().lower()
    local, _, domain = low.partition("@")
    if any(domain.endswith(p) for p in PORTAL_DOMAINS):
        return "reject"
    if local in BAD_MAILBOXES:
        return "reject"
    if page_url and not same_org_domain(page_url, domain):
        if domain in {"gmail.com", "outlook.com", "hotmail.com", "gmx.de", "web.de"}:
            return "weak"
        return "reject"
    if re.match(r'^[a-z]\.?[a-z]+(\.[a-z]+)?$', local) or re.match(r'^[a-z]+[._-][a-z]+$', local):
        return "personal"
    if local in GENERIC_BOXES:
        return "team"
    return "generic"

def normalize_email(e: str) -> str:
    if not e:
        return ""
    e = e.strip().lower()
    local, _, domain = e.partition("@")
    if domain == "gmail.com":
        local = local.split("+", 1)[0].replace(".", "")
    return f"{local}@{domain}"

def extract_company_name(title_text:str)->str:
    if not title_text: return ""
    m = re.split(r'[-–|•·:]', title_text)
    base = m[0].strip() if m else title_text.strip()
    if re.search(r'\b(Job|Karriere|Kontakt|Impressum)\b', base, re.I): return ""
    return base[:120]

def detect_company_size(text:str)->str:
    patterns = {
        "klein":  r'\b(1-10|klein|Inhaber|Familienunternehmen)\b',
        "mittel": r'\b(11-50|50-250|Mittelstand|[1-9]\d?\s*Mitarbeiter)\b',
        "groß":   r'\b(250\+|Konzern|Tochtergesellschaft|international|[2-9]\d{2,}\s*Mitarbeiter)\b'
    }
    for size, pat in patterns.items():
        if re.search(pat, text, re.I): return size
    return "unbekannt"

def detect_industry(text:str)->str:
    for k, pat in INDUSTRY_PATTERNS.items():
        if re.search(pat, text, re.I): return k
    return "unbekannt"

def detect_recency(html:str)->str:
    if re.search(r'\b(2025|2024)\-(0[1-9]|1[0-2])\-(0[1-9]|[12]\d|3[01])\b', html): return "aktuell"
    if re.search(r'\b(0?[1-9]|[12]\d|3[01])\.(0?[1-9]|1[0-2])\.(2024|2025)\b', html): return "aktuell"
    if re.search(r'\b(ab\s*sofort|sofort|zum\s*nächsten?\s*möglichen\s*termin)\b', html, re.I): return "sofort"
    return "unbekannt"

def estimate_hiring_volume(text:str)->str:
    if re.search(r'\b(mehrere|Teams|Team-?Erweiterung|Verstärkung|wir wachsen)\b', text, re.I): return "hoch"
    if len(re.findall(r'\b(Stelle|Stellen|Job)\b', text, re.I)) > 1: return "mittel"
    return "niedrig"

ADDRESS_RE = re.compile(
    r'\b([A-ZÄÖÜ][\wÄÖÜäöüß\-\.\s]{2,40}?(?:straße|str\.|weg|platz|allee|gasse|ring|ufer|chaussee|damm|steig|pfad|stieg|promenade)\s*\d+[a-zA-Z]?(?:\s*,\s*)?(?:\d{5}\s+[A-ZÄÖÜ][\wÄÖÜäöüß\-\.\s]{2,40})?)',
    re.I
)
ADDRESS_RE_ALT = re.compile(
    r'\b(\d{5}\s+[A-ZÄÖÜ][\wÄÖÜäöüß\-\.\s]{2,40}\s*,?\s*[A-ZÄÖÜ][\wÄÖÜäöüß\-\.\s]{2,40}?(?:straße|str\.|weg|platz|allee|gasse|ring|ufer|chaussee|damm|steig|pfad|stieg|promenade)\s*\d+[a-zA-Z]?)',
    re.I
)

SOCIAL_URL_RE = re.compile(
    r'(https?://(?:www\.)?(?:linkedin\.com/(?:in|company)/[^\s"\'<>]+|xing\.com/profile/[^\s"\'<>]+|facebook\.com/[^\s"\'<>]+|instagram\.com/[^\s"\'<>]+|x\.com/[^\s"\'<>]+|twitter\.com/[^\s"\'<>]+|tiktok\.com/@[^\s"\'<>]+))',
    re.I
)
SOCIAL_DOMAINS = ("linkedin.com", "xing.com", "x.com", "twitter.com", "facebook.com", "instagram.com", "tiktok.com")

def extract_private_address(text: str) -> str:
    """
    Greift die erste wahrscheinliche Anschrift aus dem Text heraus (Straße + Hausnummer, optional PLZ/Ort).
    """
    if not text:
        return ""
    snippet = text[:5000]
    for pat in (ADDRESS_RE, ADDRESS_RE_ALT):
        m = pat.search(snippet)
        if m:
            addr = re.sub(r"\s+", " ", m.group(1)).strip(" ,;")
            return addr
    return ""

def extract_social_profile_url(soup: Optional[BeautifulSoup], text: str) -> str:
    """
    Sucht nach Social-Links (LinkedIn/Xing/etc.) und liefert den ersten priorisierten Treffer.
    """
    candidates: list[str] = []

    def _add(url: str):
        if not url:
            return
        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url
        low = url.lower()
        if not any(d in low for d in SOCIAL_DOMAINS):
            return
        clean = url.split("#", 1)[0].split("?", 1)[0]
        if clean not in candidates:
            candidates.append(clean)

    if soup:
        for a in soup.find_all("a", href=True):
            _add(a.get("href", ""))

    if not candidates and text:
        for m in SOCIAL_URL_RE.finditer(text):
            _add(m.group(1))

    if not candidates:
        return ""

    priority = ["linkedin.com", "xing.com", "x.com", "twitter.com", "facebook.com", "instagram.com", "tiktok.com"]
    candidates.sort(key=lambda u: min((priority.index(p) if p in u.lower() else len(priority) for p in priority)))
    return candidates[0]

def extract_locations(text:str)->str:
    cities = re.findall(r'\b(Düsseldorf|Köln|Essen|Dortmund|Mönchengladbach|Bochum|Wuppertal|Bonn|NRW|Nordrhein[-\s]?Westfalen)\b', text, re.I)
    out, seen=[], set()
    for c in cities:
        k=c.lower()
        if k in seen: continue
        seen.add(k); out.append(c)
    return ", ".join(out[:6]) if out else ""

def tags_from(text:str)->str:
    t=[]
    if JOBSEEKER_RE.search(text): t.append("jobseeker")
    elif RECRUITER_RE.search(text): t.append("recruiter")

    if CALLCENTER_HINT.search(text): t.append("callcenter")
    if D2D_HINT.search(text): t.append("d2d")
    if PROVISION_HINT.search(text): t.append("provision")
    if B2C_HINT.search(text): t.append("b2c")
    if CITY_RE.search(text): t.append("nrw")
    if WHATSAPP_RE.search(text) or WHATSAPP_INLINE.search(text) or WHATS_RE.search(text) \
       or WHATSAPP_PHRASE_RE.search(text) or WA_LINK_RE.search(text):
        t.append("whatsapp")
    if TELEGRAM_LINK_RE.search(text) or re.search(r'\btelegram\b', text, re.I):
        t.append("telegram")
    for k, pat in INDUSTRY_PATTERNS.items():
        if re.search(pat, text, re.I): t.append(k)
    return ",".join(dict.fromkeys(t))


def opening_line(lead:dict)->str:
    t = (lead.get("tags","") or "")
    if "d2d" in t: return "D2D in NRW: tägliche Touren + überdurchschnittliche Provision, Auszahlung wöchentlich."
    if "callcenter" in t: return "Outbound-Leads mit hoher Abschlussquote – Provision top, Auszahlung wöchentlich."
    return "Warme Leads, starker Provisionsplan, schnelle Auszahlung."

def normalize_phone(p: str) -> str:
    """
    DE-Telefon-Normalisierung (E.164-ähnlich) mit Edge-Cases wie '(0)'.
    Beispiele:
      '0211 123456'            -> '+49211123456'
      '+49 (0) 211 123456'     -> '+49211123456'
      '0049 (0) 211-123456'    -> '+49211123456'
      '+49-(0)-176 123 45 67'  -> '+491761234567'
    """
    if not p:
        return ""

    s = str(p).strip()

    # (0)-Edgecases vor der eigentlichen Bereinigung behandeln
    # Erfasst (), [], {} und beliebige Whitespaces: '(0)', '( 0 )', '[0]' etc.
    s = re.sub(r'[\(\[\{]\s*0\s*[\)\]\}]', '0', s)

    # Häufige Extension-/Zusatzangaben am Ende entfernen (ext, Durchwahl, DW, Tel.)
    s = re.sub(r'(?:durchwahl|dw|ext\.?|extension)\s*[:\-]?\s*\d+\s*$', '', s, flags=re.I)

    # Alle Zeichen außer Ziffern und Plus entfernen
    s = re.sub(r'[^\d+]', '', s)

    # Internationale Präfixe vereinheitlichen
    s = re.sub(r'^00', '+', s)        # 0049 -> +49, 0033 -> +33, etc.
    s = re.sub(r'^\+049', '+49', s)   # Tippfehler-Variante absichern
    s = re.sub(r'^0049', '+49', s)    # (redundant, aber explizit)

    # Optionales (0) hinter +49 entfernen (nach oben bereits zu '0' gemacht)
    # Beispiele: '+490211...' -> '+49211...'
    s = re.sub(r'^\+490', '+49', s)

    # Nationale führende 0 → +49
    if s.startswith('0') and not s.startswith('+'):
        s = '+49' + s[1:]

    # Mehrfaches '+' absichern
    if s.count('+') > 1:
        s = '+' + re.sub(r'\D', '', s)

    # Falls noch kein '+' vorhanden ist, hinzufügen (E.164-ähnlich)
    if not s.startswith('+'):
        s = '+' + re.sub(r'\D', '', s)

    # Plausibilitätscheck (Gesamtziffernzahl)
    digits = re.sub(r'\D', '', s)
    if len(digits) < 8 or len(digits) > 16:
        return s  # unbearbeitet zurückgeben, wenn außerhalb Range

    return s


def guess_name_around(pos:int, text:str, window=120):
    seg = text[max(0,pos-window):pos+window]
    m = PERSON_PREFIX.search(seg) or NAME_RE.search(seg)
    if not m: return ""
    return m.group(0).replace("Hr.","Herr").replace("Fr.","Frau")

def validate_contact(contact: dict, page_url: str = "") -> bool:
    email = (contact.get("email") or "").strip()
    phone = (contact.get("telefon") or "").strip()
    if email:
        low = email.lower()
        if not EMAIL_RE.search(email):
            return False
        local, _, domain = low.partition("@")
        if local in BAD_MAILBOXES:
            return False
        if any(domain.endswith(p) for p in PORTAL_DOMAINS):
            return False
        if page_url and not same_org_domain(page_url, domain):
            if domain not in {"gmail.com", "outlook.com", "hotmail.com", "gmx.de", "web.de"}:
                return False
        if re.fullmatch(r'\d{8,}', (local or "")):
            return False
    if phone:
        phone = normalize_phone(phone)
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 8:
            return False
        if re.search(r'(\d)\1{5,}', digits):
            return False
    if not email and not phone:
        return False
    return True

def regex_extract_contacts(text: str, src_url: str):
    # Text absichern
    text = text or ""

    # 2× De-Obfuscation (schluckt verschachtelte Varianten wie [at](punkt), ät, {dot}, etc.)
    for _ in range(2):
        text = deobfuscate_text_for_emails(text)

    # Gate: Sales/Jobseeker ODER offensichtliche Kontakt-/Messenger-URL zulassen
    is_contact_like = any(x in (src_url or "").lower() for x in ("/kontakt","/kontaktformular","/impressum","/team","/ansprechpartner"))
    messenger_hit = bool(
        WHATSAPP_RE.search(text) or WHATS_RE.search(text) or WA_LINK_RE.search(text) or
        WHATSAPP_PHRASE_RE.search(text) or TELEGRAM_LINK_RE.search(text) or re.search(r'\btelegram\b', text, re.I)
    )
    if not (SALES_WINDOW.search(text) or JOBSEEKER_WINDOW.search(text) or is_contact_like or messenger_hit):
        log("info", "Regex-Fallback: kein Sales/Jobseeker/Messenger-Kontext", url=src_url)
        return []


    # Näheprüfung mit erweitertem Fenster (±400 Zeichen)
    def _sales_near(a: int, b: int) -> bool:
        span = text[max(0, a - 400): min(len(text), b + 400)]
        return bool(SALES_WINDOW.search(span))

    # Treffer sammeln
    email_hits = [(m.group(0), m.start(), m.end()) for m in EMAIL_RE.finditer(text)]
    mobile_hits = [(m.group(0), m.start(), m.end(), True) for m in MOBILE_RE.finditer(text)]
    phone_hits_generic = [(m.group(0), m.start(), m.end(), False) for m in PHONE_RE.finditer(text)]
    phone_hits = []
    seen_spans = set()
    for hit in mobile_hits + phone_hits_generic:
        key = (hit[1], hit[2])
        if key in seen_spans:
            continue
        seen_spans.add(key)
        phone_hits.append(hit)
    wa_hits    = [(m.group(0), m.start(), m.end()) for m in WHATSAPP_RE.finditer(text)]
    wa_hits2   = [(m.group(0), m.start(), m.end()) for m in WHATS_RE.finditer(text)]

    rows = []
    if not email_hits and not phone_hits and not wa_hits and not wa_hits2:
        log("info", "Regex-Fallback: keine Treffer", url=src_url)
        return rows

    # E-Mails mit nächster Telefonnummer verbinden (falls vorhanden) + Name raten
    for e, es, ee in email_hits:
        if not _sales_near(es, ee):
            continue
        best_p, best_ppos, best_mobile = "", None, False
        best_dist = 10**9
        for p, ps, pe, is_mobile in phone_hits:
            if not _sales_near(ps, pe):
                continue
            d = min(abs(ps - es), abs(pe - ee))
            if d < best_dist or (d == best_dist and is_mobile and not best_mobile):
                best_dist, best_ppos, best_p, best_mobile = d, ps, p, is_mobile
        name = guess_name_around(es, text) or (guess_name_around(best_ppos, text) if best_ppos is not None else "")
        rows.append({
            "name": name,
            "rolle": "",
            "email": normalize_email(e),
            "telefon": normalize_phone(best_p) if best_p else "",
            "quelle": src_url
        })

    # Telefonnummern ergänzen, die noch nicht genutzt wurden
    used_tel = set(r["telefon"] for r in rows if r.get("telefon"))
    for p, ps, pe, _is_mobile in phone_hits:
        if not _sales_near(ps, pe):
            continue
        np = normalize_phone(p)
        if np and np in used_tel:
            continue
        rows.append({
            "name": guess_name_around(ps, text),
            "rolle": "",
            "email": "",
            "telefon": np,
            "quelle": src_url
        })

    # WhatsApp-Telefonnummern aus Text
    for (w, ws, we) in (wa_hits + wa_hits2):
        if not _sales_near(ws, we):
            continue
        tel_candidates = re.findall(r'\+?\d[\d \-()]{6,}', w)
        tel = normalize_phone(tel_candidates[0]) if tel_candidates else ""
        if tel:
            rows.append({
                "name": guess_name_around(ws, text),
                "rolle": "",
                "email": "",
                "telefon": tel,
                "quelle": src_url
            })

    # WhatsApp-Links (wa.me / api.whatsapp.com)
    for m in WA_LINK_RE.finditer(text):
        tel = re.sub(r'\D', '', m.group(0))
        if tel:
            tel_fmt = "+" + tel if not tel.startswith("+") else tel
            if tel_fmt not in {r.get("telefon") for r in rows}:
                rows.append({
                    "name": "",
                    "rolle": "",
                    "email": "",
                    "telefon": tel_fmt,
                    "quelle": src_url
                })

    log("info", "Regex-Fallback genutzt", url=src_url,
        emails=len(email_hits), phones=len(phone_hits),
        whatsapp=len(wa_hits) + len(wa_hits2), rows=len(rows))
    return rows


def _anchor_contacts_fast(soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
    """Liest nur <a href> auf Kontakt-/Impressum-/Team-Seiten: tel:, mailto:, wa.me / api.whatsapp.
    Liefert deduplizierte, validierte Kontakt-Records (ohne Volltext-Parsing)."""
    rows: List[Dict[str, Any]] = []
    if not soup:
        return rows

    for a in soup.find_all("a", href=True):
        h = a.get("href", "").strip()
        hl = h.lower()

        if hl.startswith("tel:"):
            tel = normalize_phone(h[4:])
            if tel:
                rows.append({"name": "", "rolle": "", "email": "", "telefon": tel, "quelle": url})

        elif hl.startswith("mailto:"):
            # alles nach mailto: bis evtl. '?' (Parameter) nehmen
            addr = h[7:].split("?", 1)[0].strip()
            if addr:
                rows.append({"name": "", "rolle": "", "email": addr, "telefon": "", "quelle": url})

        elif ("wa.me/" in hl) or ("api.whatsapp.com" in hl):
            digits = re.sub(r"\D", "", h)
            if digits:
                tel = "+" + digits if not digits.startswith("+") else digits
                tel = normalize_phone(tel)
                if tel:
                    rows.append({"name": "", "rolle": "", "email": "", "telefon": tel, "quelle": url})

    # Dedupe + Validierung (gleiche Logik wie sonst)
    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()
    for r in rows:
        key = ((r.get("email") or "").lower(), r.get("telefon") or "")
        if key in seen:
            continue
        if validate_contact(r, page_url=url):
            out.append(r)
            seen.add(key)
    return out

def _has_contact_anchor(soup: BeautifulSoup) -> bool:
    if not soup:
        return False
    for a in soup.find_all("a", href=True):
        h = a.get("href","").lower().strip()
        if h.startswith("mailto:") or h.startswith("tel:") or ("wa.me/" in h) or ("api.whatsapp.com" in h) \
           or ("chat.whatsapp.com" in h) or ("t.me/" in h) or ("telegram.me/" in h):
            return True
    return False


def extract_kleinanzeigen(html:str, url:str):
    lu = (url or "").lower()
    if ("kleinanzeigen.de" not in lu) and ("ebay-kleinanzeigen.de" not in lu):
        return []
    soup = BeautifulSoup(html, "html.parser")
    rows=[]
    wa = soup.select_one('a[href*="wa.me"], a[href*="api.whatsapp.com"]')
    tel = ""
    if wa:
        href = wa.get("href","")
        tel = re.sub(r'\D','', href)
        if tel: tel = "+"+tel
    if tel:
        rows.append({"name":"","rolle":"", "email":"", "telefon":tel, "quelle":url})
    return rows

def extract_kleinanzeigen_links(html: str, base_url: str = "") -> List[str]:
    """
    Extrahiert Anzeigen-Links aus einer Kleinanzeigen-Hub-Seite.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []
    links: List[str] = []
    blacklist = ("fahrer","kurier","lager","amazon","zusteller","lieferant","reinigung","pflege","stapler")
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if "/s-anzeige/" not in href:
            continue
        text = (a.get_text(" ", strip=True) or "").lower()
        href_lower = href.lower()
        if any(word in href_lower or word in text for word in blacklist):
            continue
        full = urllib.parse.urljoin(base_url or "https://www.kleinanzeigen.de", href)
        links.append(full)
    return list(dict.fromkeys(links))

# =========================
# Scoring
# =========================

def compute_score(text: str, url: str, html: str = "") -> int:
    t = (text or "").lower()
    u = (url or "").lower()
    # Zusatzflags für Off-Target-Quellen
    job_host_hints = (
        "ebay-kleinanzeigen.de",
        "kleinanzeigen.de",
        "/s-jobs/",
        "/stellenangebote",
        "/stellenangebot",
        "/job/",
        "/jobs/"
    )
    is_job_board = any(h in u for h in job_host_hints)

    public_hints = (
        "bundestag.de",
        "/rathaus/",
        "/verwaltung/",
        "/gleichstellungsstelle",
        "/grundsicherung",
        "/soziales-gesundheit-wohnen-und-recht",
        "/partei",
        "/landtag",
        "/ministerium"
    )
    is_public_context = any(h in u for h in public_hints)

    hr_role_hints = (
        "personalabteilung",
        "personalreferent",
        "personalreferentin",
        "sachbearbeiter personal",
        "sachbearbeiterin personal",
        "hr-manager",
        "hr manager",
        "human resources",
        "bewerbungen richten sie an",
        "bewerbung richten sie an",
        "pressesprecher",
        "pressesprecherin",
        "unternehmenskommunikation",
        "pressekontakt",
        "events-team",
        "veranstaltungen",
        "seminarprogramm"
    )
    is_hr_or_press = any(h in t for h in hr_role_hints)
    score = 0
    has_mobile = bool(MOBILE_RE.search(t))
    has_tel_number = bool(PHONE_RE.search(t))
    has_tel_word = ("tel:" in t) or ("telefon" in t) or ("tel." in t) or bool(re.search(r'\btelefon\b|\btel\.', t))
    has_tel = has_mobile or has_tel_number or has_tel_word
    has_wa_phrase = bool(WHATSAPP_PHRASE_RE.search(t))
    has_wa_word = ("whatsapp" in t) or has_wa_phrase
    has_wa_link = bool(WA_LINK_RE.search(html or "")) or bool(WA_LINK_RE.search(t))
    has_tg_link = bool(TELEGRAM_LINK_RE.search(html or "")) or bool(TELEGRAM_LINK_RE.search(t))
    has_telegram = has_tg_link or ("telegram" in t)
    has_whatsapp = has_wa_word or has_wa_link
    has_email = ("mailto:" in t) or ("e-mail" in t) or ("email" in t) or bool(re.search(r'\bmail\b', t))
    generic_mail_fragments = ("noreply@", "no-reply@", "donotreply@", "do-not-reply@", "info@", "kontakt@", "contact@", "office@", "support@", "service@")
    has_personal_email = has_email and not any(g in t for g in generic_mail_fragments)
    has_switch_now = any(k in t for k in [
        "quereinsteiger", "ab sofort", "sofort starten", "sofort start",
        "keine erfahrung nötig", "ohne erfahrung", "jetzt bewerben",
        "heute noch bewerben", "direkt bewerben"
    ])
    has_candidate_kw = any(k in t for k in CANDIDATE_KEYWORDS)
    has_ignore_kw = any(k in t for k in IGNORE_KEYWORDS)
    has_lowpay_or_prov = bool(PROVISION_HINT.search(t)) or any(k in t for k in [
        "nur provision", "provisionsbasis", "fixum + provision",
        "freelancer", "selbstständig", "selbststaendig", "werkvertrag"
    ])
    has_d2d = bool(D2D_HINT.search(t)) or any(k in t for k in ["door to door", "haustür", "haustuer", "kaltakquise"])
    has_callcenter = bool(CALLCENTER_HINT.search(t))
    has_b2c = bool(B2C_HINT.search(t))
    industry_hits = sum(1 for k in INDUSTRY_HINTS if k in t)
    in_nrw = bool(CITY_RE.search(t)) or any(k in t for k in [" nrw ", " nordrhein-westfalen "])
    on_contact_like = any(h in u for h in ["kontakt", "impressum"])
    on_sales_path = any(h in u for h in ["callcenter", "telesales", "outbound", "vertrieb", "verkauf", "sales", "d2d", "door-to-door"])
    job_like = any(h in u for h in ["jobs.", "/jobs", "/karriere", "/stellen", "/bewerb"])
    portal_like = any(b in u for b in ["google.com", "indeed", "stepstone", "monster.", "xing.", "linkedin.", "glassdoor."])
    negative_pages = any(k in u for k in ["/datenschutz", "/privacy", "/agb", "/terms", "/bedingungen", "/newsletter", "/search", "/login", "/account", "/warenkorb", "/checkout", "/blog/", "/news/"])

    if has_whatsapp:
        score += 28
        if has_wa_link:
            score += 6
    if has_telegram:
        score += 8
        if has_tg_link:
            score += 4
    if has_mobile:
        score += 50
    elif has_tel:
        score += 14
    if has_personal_email:
        score += 12
    elif has_email:
        score += 6
    channel_count = int(has_whatsapp) + int(has_mobile or has_tel) + int(has_email) + int(has_telegram)
    if channel_count >= 2:
        score += 10   # angehoben
    if channel_count >= 3:
        score += 16   # deutlich angehoben
    if has_lowpay_or_prov:
        score += 18
    if has_switch_now:
        score += 12
    if LOW_PAY_HINT.search(t):
        score += 10   # angehoben
    if has_d2d:
        score += 9
    if has_callcenter:
        score += 7
    if has_b2c:
        score += 4
    if has_candidate_kw:
        score += 20
    if has_ignore_kw:
        score -= 100
    if industry_hits:
        score += min(industry_hits * 4, 16)
    if in_nrw:
        score += 6
    if on_contact_like:
        score += 14   # angehoben
    if on_sales_path:
        score += 6
    if job_like:
        score -= 32
    if portal_like:
        score -= 24
    if negative_pages:
        score -= 10
    if any(k in t for k in [
        "per whatsapp bewerben", "bewerbung via whatsapp", "per telefon bewerben", "ruf uns an", "anrufen und starten",
        "meldet euch per whatsapp", "schreib mir per whatsapp", "meldet euch bei whatsapp"
    ]):
        score += 12
    if ("chat.whatsapp.com" in u) or ("t.me" in u):
        score += 100
    rec = detect_recency(html or "")
    if rec in ("aktuell", "sofort"):
        score += 8

    # Harte Abwertungen für Off-Target-Kontexte
    if is_job_board:
        score -= 40
    if is_public_context:
        score -= 40
    if is_hr_or_press:
        score -= 30

    return max(0, min(int(score), 100))

# =========================
# Content/Process (ASYNC)
# =========================

def validate_content(html: str, url: str) -> bool:
    if not html or not html.strip():
        return False
    raw = html.lstrip()
    if raw.startswith("<?xml") or "<urlset" in raw[:200].lower() or "<sitemapindex" in raw[:200].lower():
        log("debug", "XML/Sitemap erkannt (kein Lead-Content)", url=url)
        return False
    def _parse_html(doc: str, use_lxml_if_available: bool = True):
        soup_local = BeautifulSoup(doc, "html.parser")
        for el in soup_local.find_all(['script', 'style', 'noscript']):
            el.decompose()
        for c in soup_local.find_all(string=lambda t: isinstance(t, Comment)):
            c.extract()
        text_local = soup_local.get_text(" ", strip=True) if soup_local else ""
        text_local = text_local.replace("\xa0", " ").replace("\u200b", " ")
        text_local = re.sub(r"\s+", " ", text_local).strip()
        if use_lxml_if_available and len(text_local) < 120:
            try:
                soup_lx = BeautifulSoup(doc, "lxml")
                for el in soup_lx.find_all(['script', 'style', 'noscript']):
                    el.decompose()
                for c in soup_lx.find_all(string=lambda t: isinstance(t, Comment)):
                    c.extract()
                text_lx = soup_lx.get_text(" ", strip=True) if soup_lx else ""
                text_lx = text_lx.replace("\xa0", " ").replace("\u200b", " ")
                text_lx = re.sub(r"\s+", " ", text_lx).strip()
                if len(text_lx) > len(text_local) * 1.2:
                    return soup_lx, text_lx
            except Exception:
                pass
        return soup_local, text_local
    soup, text = _parse_html(raw)
    lower = text.lower()
    login_gate = (
        re.search(r'\b(anmelden|login|passwort)\b', lower, re.I) and
        re.search(r'\b(geschützt|nur\s*für\s*mitglieder|zugang\s*verweigert|restricted)\b', lower, re.I)
    )
    is_404 = any(phrase in lower for phrase in ["404", "seite nicht gefunden", "page not found", "not found"])
    german_core = re.search(r'\b(der|die|das|und|in|zu|für|mit|auf)\b', lower, re.I) is not None
    contact_tolerant = any(k in lower for k in ["kontakt", "impressum", "telefon", "e-mail", "email", "bewerben"])
    no_german = not (german_core or contact_tolerant)
    checks = {
        "too_short": len(text) < 200 and not contact_tolerant,
        "no_german": no_german,
        "is_404": is_404,
        "login_required": bool(login_gate),
    }
    if any(checks.values()):
        log("debug", "Content validation failed", url=url, checks=checks)
        return False
    return True

async def process_link_async(url: UrlLike, run_id: int, *, force: bool = False) -> Tuple[int, List[Dict[str, Any]]]:
    meta = url if isinstance(url, dict) else {}
    snippet_hint = (meta.get("snippet", "") or "")
    title_hint = (meta.get("title", "") or "")
    url = _extract_url(url)
    if not url:
        return (0, [])
    extra_followups: List[str] = []
    extra_checked = 0
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path_lower = (parsed.path or "").lower()
    is_linkedin = host.endswith("linkedin.com")
    linkedin_profile = is_linkedin and path_lower.startswith("/in/")
    linkedin_snippet_text = " ".join([title_hint, snippet_hint]).strip()

    def _random_desktop_ua() -> str:
        pool = [ua for ua in UA_POOL if "mobile" not in ua.lower() and "android" not in ua.lower()]
        return random.choice(pool or UA_POOL or [USER_AGENT])

    # History / Vorab-Checks
    if (not force) and url_seen(url):
        log("debug", "URL bereits gesehen (skip)", url=url)
        return (0, [])
    if (is_denied(url) or not path_ok(url)) and not linkedin_profile:
        log("debug", "Vorprüfung blockt URL", url=url)
        mark_url_seen(url, run_id)
        return (1, [])
    if not await robots_allowed_async(url):
        log("warn", "robots.txt verbietet Zugriff", url=url)
        mark_url_seen(url, run_id)
        return (1, [])

    # HTTP holen
    resp: Optional[Any] = None
    html = ""
    ct = ""
    using_linkedin_snippet = False
    li_status = None

    if linkedin_profile:
        li_status = -1
        login_wall = False
        ua_choice = _random_desktop_ua()
        try:
            async with _make_client(True, ua_choice, proxy_url=None, force_http1=False, timeout_s=HTTP_TIMEOUT) as client:
                resp = await client.get(url, allow_redirects=True, timeout=HTTP_TIMEOUT)
            li_status = getattr(resp, "status_code", 0) if resp else -1
            _LAST_STATUS[url] = li_status
            final_path = urllib.parse.urlparse(str(getattr(resp, "url", url))).path.lower() if resp else ""
            login_wall = (li_status == 999) or ("/login" in final_path)
            if login_wall and linkedin_snippet_text:
                log("info", "LinkedIn Login-Wall – nutze Snippet", url=url, status=li_status)
                using_linkedin_snippet = True
                html = linkedin_snippet_text
                resp = None
            elif resp and li_status == 200:
                setattr(resp, "insecure_ssl", False)
            else:
                resp = None
        except Exception as e:
            log("warn", "LinkedIn Fetch fehlgeschlagen", url=url, error=str(e))
            resp = None
            li_status = -1
            _LAST_STATUS[url] = li_status
    else:
        resp = await fetch_response_async(url)

    if (resp is None) and (not using_linkedin_snippet):
        st = _LAST_STATUS.get(url, li_status if li_status is not None else -1)
        if st in (429, 403, -1):
            log("warn", "Kein Content – Retry später (nicht markiert)", url=url, status=st)
            return (1, [])
        mark_url_seen(url, run_id)
        return (1, [])

    if resp is not None:
        ct = (resp.headers.get("Content-Type", "") or "").lower()
        if "application/pdf" in ct and not CFG.allow_pdf:
            log("info", "PDF übersprungen (ALLOW_PDF=0)", url=url)
            mark_url_seen(url, run_id)
            return (1, [])
        try:
            html = resp.text
        except Exception as e:
            log("error", "Response fehlerhaft", url=url, error=str(e))
            mark_url_seen(url, run_id)
            return (1, [])

    lu = url.lower()
    is_kleinanzeigen = ("kleinanzeigen.de" in lu) or ("ebay-kleinanzeigen.de" in lu)
    is_list_page = ("/k0" in lu or "/s-" in lu) and ("/s-anzeige/" not in lu)
    if is_kleinanzeigen and is_list_page:
        ka_links = extract_kleinanzeigen_links(html, url)
        collected: List[Dict[str, Any]] = []
        if ka_links:
            for link in ka_links:
                if link not in extra_followups:
                    extra_followups.append(link)
        if extra_followups:
            log("debug", "Kleinanzeigen-Hub erkannt, folge Anzeigenlinks", url=url, count=len(extra_followups))
            for fu in extra_followups:
                try:
                    inc2, items2 = await process_link_async(fu, run_id, force=force)
                    extra_checked += inc2
                    if items2:
                        collected.extend(items2)
                except Exception:
                    pass
        mark_url_seen(url, run_id)
        return (1 + extra_checked, collected if extra_followups else [])

    # Titel-basierter Guard (früher Exit, bevor teure Extraktion)
    title_text = ""
    try:
        soup_title = BeautifulSoup(html, "html.parser")
        ttag = soup_title.find("title")
        if ttag:
            title_text = ttag.get_text(" ", strip=True)
    except Exception:
        title_text = ""
    if using_linkedin_snippet and not title_text:
        title_text = title_hint or snippet_hint
    title_src = (title_text or linkedin_snippet_text or url or "").lower()
    pos_keys = ("vertrieb","sales","verkauf","account","aussendienst","außendienst","kundenberater",
                "handelsvertreter","makler","akquise","agent","berater","beraterin","geschäftsführer",
                "repräsentant","b2b","b2c","verkäufer","verkaeufer","vertriebler",
                "vertriebspartner","promoter","promotion","fundraiser","aushilfe verkauf")
    neg_keys = ("reinigung","putz","hilfe","helfer","lager","fahrer","zusteller","kommissionierer",
                "melker","tischler","handwerker","bauhelfer","produktionshelfer","stapler",
                "pflege","medizin","arzt","kassierer","kasse","verräumer","regal",
                "aushilfe","minijob","winterdienst","security","sicherheits")
    if any(k in title_src for k in neg_keys):
        log("debug", "Titel-Guard: Negative erkannt, skip", url=url, title=title_text)
        mark_url_seen(url, run_id)
        return (1, [])
    if not any(k in title_src for k in pos_keys):
        log("debug", "Titel-Guard: Keine positiven Keywords, skip", url=url, title=title_text)
        mark_url_seen(url, run_id)
        return (1, [])

    ssl_insecure = getattr(resp, "insecure_ssl", False)
    invite_link = ("chat.whatsapp.com" in url.lower()) or ("t.me" in url.lower())

    # XML/Sitemap ausfiltern (Invite-Links dürfen durch)
    if (("xml" in ct) or html.lstrip().startswith("<?xml") or "<urlset" in html[:200].lower() or "<sitemapindex" in html[:200].lower()) and not invite_link:
        log("debug", "XML/Sitemap erkannt (kein Lead-Content)", url=url)
        mark_url_seen(url, run_id)
        return (1, [])

    # Content validieren (Invite-Links überspringen strenge Prüfung)
    if (not invite_link) and (not using_linkedin_snippet) and (not validate_content(html, url)):
        mark_url_seen(url, run_id)
        return (1, [])

    if invite_link:
        soup_inv = BeautifulSoup(html, "html.parser")
        title_tag = soup_inv.find("title")
        og_title = soup_inv.find("meta", attrs={"property": "og:title"})
        group_title = ""
        if og_title and og_title.get("content"):
            group_title = og_title.get("content").strip()
        if (not group_title) and title_tag:
            group_title = title_tag.get_text(strip=True)

        record = {
            "name": group_title or "",
            "rolle": "Messenger Gruppe",
            "email": "",
            "telefon": "",
            "quelle": url,
            "score": 100,
            "tags": "group_invite",
            "region": "",
            "role_guess": "Messenger",
            "salary_hint": "",
            "commission_hint": "",
            "opening_line": "",
            "ssl_insecure": "yes" if ssl_insecure else "no",
            "company_name": "",
            "company_size": "",
            "hiring_volume": "",
            "industry": "",
            "recency_indicator": "",
            "location_specific": "",
            "confidence_score": 100,
            "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "data_quality": 50,
            "phone_type": "",
            "whatsapp_link": "yes" if "chat.whatsapp.com" in url.lower() else "",
            "private_address": "",
            "social_profile_url": "",
            "lead_type": "group_invite",
        }
        mark_url_seen(url, run_id)
        return (1, [record])

    # Robust parsen
    def _parse_html(doc: str) -> Tuple[BeautifulSoup, str]:
        soup_local = BeautifulSoup(doc, "html.parser")
        for el in soup_local.find_all(['script', 'style', 'noscript']):
            el.decompose()
        for c in soup_local.find_all(string=lambda t: isinstance(t, Comment)):
            c.extract()
        text_local = soup_local.get_text(" ", strip=True) if soup_local else ""
        text_local = text_local.replace("\xa0", " ").replace("\u200b", " ")
        text_local = re.sub(r"\s+", " ", text_local).strip()
        if len(text_local) < 120:
            try:
                soup_lx = BeautifulSoup(doc, "lxml")
                for el in soup_lx.find_all(['script', 'style', 'noscript']):
                    el.decompose()
                for c in soup_lx.find_all(string=lambda t: isinstance(t, Comment)):
                    c.extract()
                text_lx = soup_lx.get_text(" ", strip=True) if soup_lx else ""
                text_lx = text_lx.replace("\xa0", " ").replace("\u200b", " ")
                text_lx = re.sub(r"\s+", " ", text_lx).strip()
                if len(text_lx) > len(text_local) * 1.2:
                    return soup_lx, text_lx
            except Exception:
                pass
        return soup_local, text_local

    soup, text = _parse_html(html)
    if soup is None:
        soup = BeautifulSoup(html, "html.parser")

    private_address = extract_private_address(text)
    social_profile_url = extract_social_profile_url(soup, text)
    if linkedin_profile and not social_profile_url:
        social_profile_url = url

    # --- Job/Karriere/Jobs/stellen: nur weiter, wenn direkter Kontaktanker existiert ---
    lu = url.lower()
    if any(p in lu for p in ("/jobs", "/karriere", "/stellen")):
        if not _has_contact_anchor(soup):
            log("debug", "Jobpfad ohne Kontaktanker – skip", url=url)
            mark_url_seen(url, run_id)
            return (1, [])

    # >>> FAST-PATH: Kontakt/Impressum/Team/Ansprechpartner – Anker-Scan & Early-Return
    if any(key in lu for key in ("/kontakt", "/impressum", "/team", "/ansprechpartner")):
        fast_items = _anchor_contacts_fast(soup, url)
        if fast_items:
            # Erst normalen Score berechnen
            base_score = compute_score(text, url)
            # Wenn der Score unter der Mindest-Schwelle liegt, Fast-Path komplett verwerfen
            if base_score < CFG.min_score:
                log("debug", "Fast-Path Kontaktseite, aber Score unter Mindestwert", url=url, score=base_score)
                mark_url_seen(url, run_id)
                return (1, [])
            # Nur noch moderater Kontakt-Bonus, kein hartes Hochziehen mehr
            base_score = base_score + 10

            # Enrichment
            title_tag = soup.find('title') if soup else None
            comp_name = extract_company_name(title_tag.get_text() if title_tag else "")
            company_size = detect_company_size(text)
            company_domain = resolve_company_domain(comp_name) if comp_name else ""
            industry = detect_industry(text)
            recency = detect_recency(html)
            hiring_volume = estimate_hiring_volume(text)
            locations = extract_locations(text)
            base_tags = tags_from(text)
            role_guess = ("Jobseeker" if JOBSEEKER_RE.search(text) else
                          ("Callcenter" if CALLCENTER_HINT.search(text) else
                           ("D2D" if D2D_HINT.search(text) else "Vertrieb")))
            salary_hint = "low" if LOW_PAY_HINT.search(text) else ""
            commission_hint = "yes" if PROVISION_HINT.search(text) else ("maybe" if SALES_RE.search(text) else "")
            region = "NRW" if CITY_RE.search(text) else ""
            last_updated = datetime.now(timezone.utc).isoformat(timespec="seconds")

            def _confidence(r: Dict[str, Any]) -> int:
                c = 0
                if r.get("telefon"): c += 50
                if r.get("email"): c += 30
                if "whatsapp" in (r.get("tags","") or "") or WA_LINK_RE.search(html): c += 10
                if comp_name: c += 10
                return min(c, 100)

            def _quality(r: Dict[str, Any]) -> int:
                q = 0
                if validate_contact(r, page_url=url): q += 50
                if hiring_volume != "niedrig": q += 10
                if recency != "unbekannt": q += 20
                if not ssl_insecure: q += 10
                return min(q, 100)

            def _mail_boost_and_label(email: str):
                q = email_quality(email or "", url)
                if q == "reject": return (None, q)
                return ({"personal":8, "team":4, "generic":2, "weak":0}.get(q,0), q)

            def _tel_wa_boost(record: Dict[str, Any], page_text: str, page_html: str):
                t = (page_text or "").lower()
                h = (page_html or "").lower()
                tel = (record.get("telefon") or "").strip()
                boost = 0; extras={}
                has_wa_word = ("whatsapp" in t) or bool(WHATSAPP_PHRASE_RE.search(t))
                has_wa_link = bool(WA_LINK_RE.search(h)) or bool(WA_LINK_RE.search(t))
                if has_wa_word or has_wa_link:
                    boost += 12
                    extras["tags_add_whatsapp"] = True
                    extras["whatsapp_link"] = bool(has_wa_link)
                has_tg_link = bool(TELEGRAM_LINK_RE.search(h)) or bool(TELEGRAM_LINK_RE.search(t))
                if has_tg_link:
                    boost += 6
                    extras["tags_add_telegram"] = True
                is_mobile = bool(re.search(r'(?<!\d)(?:\+49|0049|0)\s*1[5-7]\d(?:[\s\/\-]?\d){6,}(?!\d)', tel)) if tel else False
                if is_mobile:
                    boost += 10; extras["phone_type"] = "mobile"
                elif tel:
                    boost += 6; extras["phone_type"] = "fixed"
                return boost, extras

            out: List[Dict[str, Any]] = []
            for r in fast_items:
                boost = 0
                if r.get("email"):
                    b = _mail_boost_and_label(r.get("email"))
                    if b[0] is None:
                        continue
                    boost += b[0]
                tb, extras = _tel_wa_boost(r, text, html)
                boost += tb

                tag_local = (base_tags or "").strip()
                if extras.get("tags_add_whatsapp"):
                    parts = [p for p in tag_local.split(",") if p]
                    if "whatsapp" not in parts:
                        parts.append("whatsapp")
                    tag_local = ",".join(parts)
                if extras.get("tags_add_telegram"):
                    parts = [p for p in tag_local.split(",") if p]
                    if "telegram" not in parts:
                        parts.append("telegram")
                    tag_local = ",".join(parts)
                if company_domain:
                    parts = [p for p in tag_local.split(",") if p]
                    dom_tag = f"domain:{company_domain}"
                    if dom_tag not in parts:
                        parts.append(dom_tag)
                    tag_local = ",".join(parts)

                # Lead-Type Logik
                lt = "other"
                if "group_invite" in (base_tags or ""):
                    lt = "group_invite"
                elif CANDIDATE_TEXT_RE.search(text) or any(k in text.lower() for k in CANDIDATE_KEYWORDS):
                    lt = "candidate"
                elif EMPLOYER_TEXT_RE.search(text) or RECRUITER_RE.search(text):
                    lt = "employer"

                enriched = {
                    **r,
                    "score": min(100, base_score + boost),
                    "tags": tag_local,
                    "region": region,
                    "role_guess": role_guess,
                    "lead_type": lt,
                    "salary_hint": salary_hint,
                    "commission_hint": commission_hint,
                    "opening_line": opening_line({"tags": tag_local}),
                    "ssl_insecure": "yes" if ssl_insecure else "no",
                    "company_name": comp_name,
                    "company_domain": company_domain,
                    "company_size": company_size,
                    "hiring_volume": hiring_volume,
                    "industry": industry,
                    "recency_indicator": recency,
                    "location_specific": locations,
                    "confidence_score": 0,
                    "last_updated": last_updated,
                    "data_quality": 0,
                    "phone_type": extras.get("phone_type",""),
                    "whatsapp_link": "yes" if extras.get("whatsapp_link") else "no",
                    "private_address": private_address,
                    "social_profile_url": social_profile_url,
                }
                enriched["confidence_score"] = _confidence(enriched)
                enriched["data_quality"] = _quality(enriched)
                out.append(enriched)

            if extra_followups:
                for fu in extra_followups:
                    try:
                        inc2, items2 = await process_link_async(fu, run_id, force=force)
                        extra_checked += inc2
                        if items2:
                            out.extend(items2)
                    except Exception:
                        pass

            mark_url_seen(url, run_id)
            return (1 + extra_checked, out)

    # Grundscore
    lead_score = compute_score(text, url, html=html)
    if private_address:
        lead_score += 15
    if social_profile_url:
        lead_score += 15
    lead_score = min(100, lead_score)
    if (lead_score < CFG.min_score) and (not using_linkedin_snippet):
        log("debug", "Lead zu schwach", url=url, score=lead_score)
        mark_url_seen(url, run_id)
        return (1, [])

    # --- Kontakte extrahieren: Regex zuerst, LLM nur wenn nötig ---
    items: List[Dict[str, Any]] = []

    # 1) Regex first (schnell & kostenlos)
    items = regex_extract_contacts(text, url)

    # 2) LLM nur, wenn keine verwertbaren Kontakte ODER nur E-Mails ohne Telefon
    need_llm = (len(items) == 0) or all(not r.get("telefon") for r in items)
    if need_llm and OPENAI_API_KEY:
        loop = asyncio.get_running_loop()
        try:
            max_bytes = int(os.getenv("OPENAI_MAX_BYTES", "12000"))
            llm_items = await loop.run_in_executor(None, openai_extract_contacts, text[:max_bytes], url)
            if llm_items:
                items = llm_items
        except Exception as e:
            log("warn", "openai_extract_contacts failed", url=url, err=str(e))

    # 3) Kleinanzeigen-Extractor als letzter Fallback (nur bei Domain)
    if not items and "kleinanzeigen.de" in url:
        items = extract_kleinanzeigen(html, url)

    if not items:
        mark_url_seen(url, run_id)
        return (1 + extra_checked, [])

    # Enrichment
    title_tag = soup.find('title') if soup else None
    comp_name = extract_company_name(title_tag.get_text() if title_tag else "")
    company_size = detect_company_size(text)
    company_domain = resolve_company_domain(comp_name) if comp_name else ""
    industry = detect_industry(text)
    recency = detect_recency(html)
    hiring_volume = estimate_hiring_volume(text)
    locations = extract_locations(text)
    base_tags = tags_from(text)
    role_guess = "Callcenter" if CALLCENTER_HINT.search(text) else ("D2D" if D2D_HINT.search(text) else "Vertrieb")
    salary_hint = "low" if LOW_PAY_HINT.search(text) else ""
    commission_hint = "yes" if PROVISION_HINT.search(text) else ("maybe" if SALES_RE.search(text) else "")
    region = "NRW" if CITY_RE.search(text) else ""
    last_updated = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _confidence(r: Dict[str, Any]) -> int:
        c = 0
        if r.get("telefon"): c += 50
        if r.get("email"): c += 30
        if "whatsapp" in (r.get("tags","") or "") or WA_LINK_RE.search(html): c += 10
        if comp_name: c += 10
        return min(c, 100)

    def _quality(r: Dict[str, Any]) -> int:
        q = 0
        if validate_contact(r, page_url=url): q += 50
        if hiring_volume != "niedrig": q += 10
        if recency != "unbekannt": q += 20
        if not ssl_insecure: q += 10
        return min(q, 100)

    def _mail_boost_and_label(email: str):
        q = email_quality(email or "", url)
        if q == "reject":
            return (None, q)
        boost = {"personal": 20, "team": 2, "generic": -6, "weak": 0}.get(q, 0)
        return (boost, q)

    def _tel_wa_boost(record: Dict[str, Any], page_text: str, page_html: str):
        t = (page_text or "").lower()
        h = (page_html or "").lower()
        tel = (record.get("telefon") or "").strip()
        boost = 0
        extras = {}
        has_wa_word = ("whatsapp" in t) or bool(WHATSAPP_PHRASE_RE.search(t))
        has_wa_link = bool(WA_LINK_RE.search(h)) or bool(WA_LINK_RE.search(t))
        if has_wa_word or has_wa_link:
            boost += 12
            extras["tags_add_whatsapp"] = True
            extras["whatsapp_link"] = bool(has_wa_link)
        has_tg_link = bool(TELEGRAM_LINK_RE.search(h)) or bool(TELEGRAM_LINK_RE.search(t))
        if has_tg_link:
            boost += 6
            extras["tags_add_telegram"] = True
        is_mobile = bool(re.search(r'(?<!\d)(?:\+49|0049|0)\s*1[5-7]\d(?:[\s\/\-]?\d){6,}(?!\d)', tel)) if tel else False
        if is_mobile:
            boost += 20
            extras["phone_type"] = "mobile"
        elif tel:
            boost += 6
            extras["phone_type"] = "fixed"
        return boost, extras

    out: List[Dict[str, Any]] = []
    for r in items:
        # Reject früh, damit kein Müll reinkommt
        if not (r.get("email") or r.get("telefon")):
            continue
        if not validate_contact(r, page_url=url):
            continue

        boost = 0
        if r.get("email"):
            boost_label = _mail_boost_and_label(r.get("email"))
            if boost_label[0] is None:
                continue
            boost += boost_label[0]

        tel_boost, extras = _tel_wa_boost(r, text, html)
        boost += tel_boost

        # Tags lokal ergänzen
        tag_local = (base_tags or "").strip()
        if extras.get("tags_add_whatsapp"):
            parts = [p for p in tag_local.split(",") if p]
            if "whatsapp" not in parts:
                parts.append("whatsapp")
            tag_local = ",".join(parts)
        if extras.get("tags_add_telegram"):
            parts = [p for p in tag_local.split(",") if p]
            if "telegram" not in parts:
                parts.append("telegram")
            tag_local = ",".join(parts)
        if company_domain:
            parts = [p for p in tag_local.split(",") if p]
            dom_tag = f"domain:{company_domain}"
            if dom_tag not in parts:
                parts.append(dom_tag)
            tag_local = ",".join(parts)

        # Lead-Type Logik
        lt = "other"
        if "group_invite" in (base_tags or ""):
            lt = "group_invite"
        elif CANDIDATE_TEXT_RE.search(text) or any(k in text.lower() for k in CANDIDATE_KEYWORDS):
            lt = "candidate"
        elif EMPLOYER_TEXT_RE.search(text) or RECRUITER_RE.search(text):
            lt = "employer"

        r["_phone_type"] = extras.get("phone_type", "")
        r["_whatsapp_link"] = "yes" if extras.get("whatsapp_link") else "no"
        r["company_domain"] = company_domain

        enriched = {
            **r,
            "score": min(100, lead_score + boost),
            "tags": tag_local,
            "region": region,
            "role_guess": role_guess,
            "lead_type": lt,
            "salary_hint": salary_hint,
            "commission_hint": commission_hint,
            "opening_line": opening_line({"tags": tag_local}),
            "ssl_insecure": "yes" if ssl_insecure else "no",
            "company_name": comp_name,
            "company_size": company_size,
            "hiring_volume": hiring_volume,
            "industry": industry,
            "recency_indicator": recency,
            "location_specific": locations,
            "confidence_score": 0,
            "last_updated": last_updated,
            "data_quality": 0,
            "phone_type": r.get("_phone_type", ""),
            "whatsapp_link": r.get("_whatsapp_link", ""),
            "private_address": private_address,
            "social_profile_url": social_profile_url,
        }
        enriched["confidence_score"] = _confidence(enriched)
        enriched["data_quality"] = _quality(enriched)
        out.append(enriched)

    if extra_followups:
        for fu in extra_followups:
            try:
                inc2, items2 = await process_link_async(fu, run_id, force=force)
                extra_checked += inc2
                if items2:
                    out.extend(items2)
            except Exception:
                pass

    mark_url_seen(url, run_id)
    return (1 + extra_checked, out)



# =========================
# Sitemap + interne Tiefe (robust)
# =========================

def find_internal_links(html: str, base_url: str) -> List[str]:
    try:
        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        for a in soup.find_all("a", href=True):
            href = urllib.parse.urljoin(base_url, a["href"])
            p = urllib.parse.urlparse(href)
            if p.scheme not in ("http", "https"):
                continue
            if urllib.parse.urlparse(base_url).netloc != p.netloc:
                continue
            if is_denied(href):
                continue
            if not path_ok(href):
                continue
            links.append(href)
        # Dedupe unter Erhalt der Reihenfolge
        return list(dict.fromkeys(links))
    except Exception:
        return []


async def try_sitemaps_async(base: str) -> List[str]:
    if "kleinanzeigen.de" in base or "ebay-kleinanzeigen.de" in base:
        return []
    candidates = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]
    out: List[str] = []
    for c in candidates:
        url = urllib.parse.urljoin(base, c)
        r = await http_get_async(url, timeout=10)
        if not r or r.status_code != 200:
            continue
        txt = r.text or ""
        try:
            soup = BeautifulSoup(txt, "xml")
            urls = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
        except Exception:
            urls = re.findall(r'<loc>(.*?)</loc>', txt, flags=re.I)
        for u in urls:
            u = (u or "").strip()
            if not u:
                continue
            if is_denied(u):
                continue
            if not path_ok(u):
                continue
            out.append(u)
        if out:
            break
    # Dedupe
    return list(dict.fromkeys(out))

# =========================
# Domain-Pivot Seeds
# =========================

def domain_pivot_queries(domain:str)->list[str]:
    return [
        f'site:{domain} (kontakt OR impressum OR ansprechpartner OR team)',
        f'site:{domain} (telesales OR outbound OR d2d OR "per WhatsApp bewerben")'
    ]

# =========================
# OpenAI
# =========================

def openai_extract_contacts(raw_text: str, src_url: str) -> List[Dict[str, Any]]:
    if not OPENAI_API_KEY:
        return []
    import requests, re

    def _preview(txt: Optional[str]) -> str:
        if not txt: return ""
        txt = re.sub(r"<[^>]+>", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt[:200]

    max_bytes = int(os.getenv("OPENAI_MAX_BYTES", "12000"))
    snippet = (raw_text or "")[:max_bytes]
    system = (
        "Extrahiere ausschließlich reale Vertrieb/Sales-Kontaktpersonen aus deutschem Webtext.\n"
        "Gib STRICT ein JSON-Objekt mit Schlüssel 'data' zurück:\n"
        "{\"data\":[{\"name\":str,\"rolle\":str,\"email\":str,\"telefon\":str,\"quelle\":str}]}\n"
        "Nur valide E-Mails/DE-Telefone; fehlende Felder als leere Strings. Keine Halluzinationen."
    )
    user = f"Quelle: {src_url}\n\nText:\n{snippet}"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    max_attempts = 4
    backoff = 1.5
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            status = r.status_code
            if status == 200:
                try:
                    j = r.json()
                except Exception as je:
                    last_err = f"JSON decode error: {je}"
                    raise
                choices = (j.get("choices") or [])
                if not choices or "message" not in choices[0] or "content" not in choices[0]["message"]:
                    log("error", "OpenAI Format unerwartet", url=src_url, raw=str(j)[:200])
                    return []
                content = choices[0]["message"]["content"]
                try:
                    obj = json.loads(content)
                except Exception:
                    log("error", "OpenAI JSON in content ungültig", url=src_url, content_preview=content[:200])
                    return []
                data = obj.get("data")
                if not isinstance(data, list):
                    log("error", "OpenAI JSON ohne 'data'[]", url=src_url, content_preview=str(obj)[:200])
                    return []
                cleaned: List[Dict[str, Any]] = []
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    rec = {
                        "name": (item.get("name") or "").strip(),
                        "rolle": (item.get("rolle") or "").strip(),
                        "email": (item.get("email") or "").strip(),
                        "telefon": normalize_phone(item.get("telefon") or ""),
                        "quelle": src_url,
                    }
                    if rec.get("email") or rec.get("telefon"):
                        if validate_contact(rec, page_url=src_url):
                            cleaned.append(rec)
                # dedupe
                dedup, seen_e, seen_t = [], set(), set()
                for x in cleaned:
                    e = (x.get("email") or "").lower()
                    t = x.get("telefon") or ""
                    if (e and e in seen_e) or (t and t in seen_t):
                        continue
                    dedup.append(x)
                    if e: seen_e.add(e)
                    if t: seen_t.add(t)
                log("info", "OpenAI-Extraktion", url=src_url, count=len(dedup))
                return dedup
            # Nicht-200 → nur kurze, bereinigte Preview loggen
            log("warn", "OpenAI Antwort != 200", status=status, body=_preview(r.text), url=src_url)
            last_err = f"HTTP {status}"
            if status in (429, 500, 502, 503, 504):
                time.sleep(backoff * attempt)
                continue
            return []
        except Exception as e:
            last_err = str(e)
            time.sleep(backoff * attempt)
    log("error", "OpenAI-Extraktion fehlgeschlagen", url=src_url, error=(last_err or "")[:200])
    return []

# =========================
# Export (CSV/XLSX append)
# =========================

def append_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]):
    if not rows:
        return
    import csv, os
    rewrite_existing = False
    existing_rows: List[Dict[str, Any]] = []
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames or []
                if header != fieldnames:
                    rewrite_existing = True
                    for row in reader:
                        existing_rows.append({k: row.get(k, "") for k in fieldnames})
        except Exception:
            pass
    write_header = (not os.path.exists(path)) or (os.path.getsize(path) == 0) or rewrite_existing
    mode = "w" if rewrite_existing else "a"
    def _coerce(row: Dict[str, Any]) -> Dict[str, Any]:
        safe = {k: ("" if row.get(k) is None else row.get(k)) for k in fieldnames}
        if "whatsapp_link" in safe:
            safe["whatsapp_link"] = int(bool(safe["whatsapp_link"]))
        return safe
    try:
        with open(path, mode, newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if write_header:
                w.writeheader()
            if rewrite_existing and existing_rows:
                for r in existing_rows:
                    w.writerow(_coerce(r))
            for r in rows:
                w.writerow(_coerce(r))
    except PermissionError:
        alt = os.path.join(os.path.expanduser("~"), f"vertrieb_kontakte_{int(time.time())}.csv")
        with open(alt, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if (not os.path.exists(alt)) or (os.path.getsize(alt) == 0):
                w.writeheader()
            for r in rows:
                w.writerow(_coerce(r))
        log("warn", "CSV war gelockt – in Home geschrieben", file=alt)

def append_xlsx(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]):
    if not rows:
        return
    try:
        from openpyxl import Workbook, load_workbook
        from openpyxl.utils import get_column_letter
    except ImportError:
        log("warn", "openpyxl nicht installiert – XLSX übersprungen")
        return
    def _coerce_row(row: Dict[str, Any]) -> List[Any]:
        safe = [("" if row.get(k) is None else row.get(k)) for k in fieldnames]
        try:
            idx = fieldnames.index("whatsapp_link")
            safe[idx] = int(bool(safe[idx]))
        except ValueError:
            pass
        return safe

    # Robuste Header-Behandlung (fehlende Spalten am Ende ergänzen)
    if os.path.exists(path):
        wb = load_workbook(path)
        ws = wb.active
        if ws.max_row < 1 or ws["A1"].value is None:
            ws.append(fieldnames)
        else:
            current = [c.value for c in ws[1] if c.value is not None]
            if current != fieldnames:
                for f in fieldnames[len(current):]:
                    ws.cell(row=1, column=len(current) + 1, value=f)
                    current.append(f)
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Leads"
        ws.append(fieldnames)

    for r in rows:
        ws.append(_coerce_row(r))

    for i, col in enumerate(fieldnames, start=1):
        ws.column_dimensions[get_column_letter(i)].width = min(max(len(col) + 2, 12), 40)
    wb.save(path)

# =========================
# Hauptlauf (ASYNC)
# =========================

class _Rate:
    def __init__(self, max_global:int=ASYNC_LIMIT, max_per_host:int=ASYNC_PER_HOST):
        self.sem_global = asyncio.Semaphore(max(1, max_global))
        self.per_host: Dict[str, asyncio.Semaphore] = {}
        self.max_per_host = max(1, max_per_host)
        self.lock = asyncio.Lock()

    async def acquire(self, url:str):
        host = _host_from(url)
        async with self.lock:
            if host not in self.per_host:
                self.per_host[host] = asyncio.Semaphore(self.max_per_host)
        await self.sem_global.acquire()
        await self.per_host[host].acquire()
        return host

    def release(self, host:str):
        try:
            self.sem_global.release()
            self.per_host.get(host, asyncio.Semaphore(1)).release()
        except Exception:
            pass

async def _bounded_process(urls: List[UrlLike], run_id:int, *, rate:_Rate, force:bool=False):
    """Prozessiert URLs mit globalem/per-Host-Limit. Liefert (links_checked, leads)."""
    links_checked = 0
    collected: List[Dict[str, Any]] = []

    async def _one(item: UrlLike, url: str):
        nonlocal links_checked, collected
        host = await rate.acquire(url)
        try:
            inc, items = await process_link_async(item, run_id, force=force)
            links_checked += int(inc)
            if items:
                collected.extend(items)
        finally:
            rate.release(host)

    candidates = []
    for entry in urls:
        raw_url = _extract_url(entry)
        if not raw_url:
            continue
        norm_url = _normalize_for_dedupe(raw_url)
        candidates.append((entry, raw_url, norm_url))

    if not candidates:
        return links_checked, collected

    ordered = prioritize_urls([c[2] for c in candidates])
    # Verarbeitung von Google-Snippets
    seed_leads = []
    for item in urls:
        if isinstance(item, dict):
            u = item.get("url", "")
            title = item.get("title", "")
            snip = item.get("snippet", "")
            name = extract_name_enhanced(f"{title} {snip}")
            rolle, _ = extract_role_with_context(f"{title} {snip}", u)
            company = extract_company_name(title)
            if name or rolle or company:
                seed_leads.append({
                    "name": name or "",
                    "rolle": rolle or "",
                    "company_guess": company or "",
                    "quelle": u,
                    "score": 0,
                    "telefon": "",
                    "email": ""
                })
    # Seed-Leads direkt in 'collected' einspeisen (nur wenn sinnvoll)
    if seed_leads:
        collected.extend(seed_leads)
    order_map = {u: i for i, u in enumerate(ordered)}
    candidates.sort(key=lambda tpl: order_map.get(tpl[2], len(order_map)))

    await asyncio.gather(*[_one(item, raw) for item, raw, _ in candidates])
    return links_checked, collected

def emergency_save(run_id, links_checked=None, leads_new_total=None):
    """
    Not-Speicherung:
    - kompatibel zu alten Aufrufen mit 1 oder 3 Parametern
    - versucht Export + finish_run, fällt bei Fehlern auf Minimaldump zurück
    - darf niemals eine Exception durchreichen
    """
    try:
        log("warn", "Not-Speicherung läuft ...", run_id=run_id,
            links_checked=links_checked, leads_new_total=leads_new_total)
    except Exception:
        pass

    # 1) Bestmöglicher Export/Run-Abschluss (nicht abbrechen, nur versuchen)
    try:
        try:
            export_xlsx(DEFAULT_XLSX)
        except Exception as e:
            try:
                log("error", "Export fehlgeschlagen (Ignoriert)", error=str(e))
            except Exception:
                pass

        try:
            # finish_run kann Links/Leads-Argumente optional verarbeiten
            finish_run(run_id, links_checked, leads_new_total, status="aborted")
        except TypeError:
            # Fallback für alte Signaturen
            finish_run(run_id, status="aborted")
        except Exception as e:
            try:
                log("error", "finish_run fehlgeschlagen (Ignoriert)", error=str(e))
            except Exception:
                pass
    except Exception:
        pass

    # 2) Minimaler Dump auf Platte (falls alles andere scheitert)
    try:
        import os, time, json
        stamp = time.strftime("%Y%m%d-%H%M%S")
        payload = {
            "run_id": run_id,
            "links_checked": links_checked,
            "leads_new_total": leads_new_total,
            "timestamp": stamp
        }
        path = os.path.join(os.getcwd(), f"emergency_run_{run_id}_{stamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        # Letzter Fallback: nichts tun, niemals hochwerfen
        pass



async def run_scrape_once_async(run_flag: Optional[dict] = None, ui_log=None, force: bool = False, date_restrict: Optional[str] = None):
    def _uilog(msg, **k):
        if ui_log:
            ui_log(msg)
        else:
            log("info", msg, **k)

    init_db()
    rate = _Rate(max_global=ASYNC_LIMIT, max_per_host=ASYNC_PER_HOST)

    total_links_checked = 0
    leads_new_total = 0
    run_id = start_run()
    _uilog(f"Run #{run_id} gestartet")


    try:
        for q in QUERIES:
            if run_flag and not run_flag.get("running", True):
                _uilog("STOP erkannt – breche ab")
                break
            if (not force) and is_query_done(q):
                log("info", "Query bereits erledigt (skip)", q=q)
                await asyncio.sleep(SLEEP_BETWEEN_QUERIES)
                continue

            log("info", "Starte Query", q=q)
            had_429_flag = False
            collected_rows = []
            links: List[UrlLike] = []

            try:
                g_links, had_429 = await google_cse_search_async(q, max_results=60, date_restrict=date_restrict)
                links.extend(g_links)
                had_429_flag |= had_429
            except Exception as e:
                log("error", "Google-Suche explodiert", q=q, error=str(e))

            if not links:
                try:
                    ddg_links = await duckduckgo_search_async(q, max_results=30)
                    links.extend(ddg_links)
                except Exception as e:
                    log("error", "DuckDuckGo-Suche explodiert", q=q, error=str(e))

            try:
                ka_links = await kleinanzeigen_search_async(q, max_results=KLEINANZEIGEN_MAX_RESULTS)
                if ka_links:
                    links.extend(ka_links)
            except Exception as e:
                log("warn", "Kleinanzeigen-Suche explodiert", q=q, error=str(e))

            if links:
                uniq_links: List[UrlLike] = []
                seen_links = set()
                for item in links:
                    raw_url = _extract_url(item)
                    if not raw_url:
                        continue
                    nu = _normalize_for_dedupe(raw_url)
                    if nu in seen_links:
                        continue
                    seen_links.add(nu)
                    if isinstance(item, dict):
                        uniq_links.append({**item, "url": nu})
                    else:
                        uniq_links.append(nu)
                links = uniq_links

            if not links:
                if had_429_flag:
                    log("warn", "Keine Links (429) - Query NICHT als erledigt markieren", q=q)
                await asyncio.sleep(SLEEP_BETWEEN_QUERIES + _jitter(0.4,1.2))
                continue

            per_domain_count = {}
            prim: List[UrlLike] = []
            for link in links:
                url = _extract_url(link)
                if not url:
                    continue
                dom = urllib.parse.urlparse(url).netloc.lower()
                extra = any(k in url.lower() for k in ("/jobs","/karriere","/stellen","/bewerb"))
                limit = CFG.max_results_per_domain + (1 if extra else 0)
                if per_domain_count.get(dom,0) >= limit:
                    continue
                per_domain_count[dom] = per_domain_count.get(dom,0)+1
                if not url_seen(url):
                    prim.append(link)

            chk, rows = await _bounded_process(prim, run_id, rate=rate, force=False)
            total_links_checked += chk
            collected_rows.extend(rows)

            pivot_seeds: List[UrlLike] = []
            for dom in per_domain_count.keys():
                for dq in domain_pivot_queries(dom):
                    try:
                        ps,_ = await google_cse_search_async(dq, max_results=10, date_restrict=date_restrict)
                        pivot_seeds.extend(ps)
                    except:
                        pass
            if pivot_seeds:
                uniq_pivots = []
                seen_p = set()
                for item in pivot_seeds:
                    p_url = _extract_url(item)
                    if not p_url:
                        continue
                    norm = _normalize_for_dedupe(p_url)
                    if norm in seen_p:
                        continue
                    seen_p.add(norm)
                    uniq_pivots.append((norm, item))
                ordered_p = prioritize_urls([u for u, _ in uniq_pivots]) if uniq_pivots else []
                order_map_p = {u: i for i, u in enumerate(ordered_p)}
                uniq_pivots.sort(key=lambda tpl: order_map_p.get(tpl[0], len(order_map_p)))
                pivot_batch = [it for _, it in uniq_pivots][:CFG.internal_depth_per_domain]
                if pivot_batch:
                    chk_p, rows_p = await _bounded_process(pivot_batch, run_id, rate=rate, force=False)
                    total_links_checked += chk_p
                    collected_rows.extend(rows_p)

            for dom in list(per_domain_count.keys()):
                base = f"https://{dom}"
                internal = []
                try:
                    sm = await try_sitemaps_async(base)
                except:
                    sm = []
                if sm:
                    internal.extend(sm[:CFG.internal_depth_per_domain])
                if not internal:
                    for pl in prim:
                        pl_url = _extract_url(pl)
                        if not pl_url:
                            continue
                        if urllib.parse.urlparse(pl_url).netloc.lower() != dom:
                            continue
                        r = await http_get_async(pl_url, timeout=10)
                        if not r or r.status_code != 200:
                            continue
                        more = find_internal_links(r.text, pl_url)
                        for u in more:
                            if url_seen(u): continue
                            if not path_ok(u): continue
                            internal.append(u)
                            if len(internal)>=CFG.internal_depth_per_domain:
                                break
                        if len(internal)>=CFG.internal_depth_per_domain:
                            break
                if internal:
                    internal = prioritize_urls(internal)
                    chk2, rows2 = await _bounded_process(internal, run_id, rate=rate, force=False)
                    total_links_checked += chk2
                    collected_rows.extend(rows2)

            mark_query_done(q, run_id)

            MIN_SCORE_TARGET = MIN_SCORE_ENV
            found = len(collected_rows)
            avg = int(sum(r.get("score",0) for r in collected_rows)/found) if found else 0
            if found >= 20 and avg < MIN_SCORE_ENV:
                MIN_SCORE_TARGET=min(80,MIN_SCORE_ENV+5)
            elif found < 10 and MIN_SCORE_ENV>=45:
                MIN_SCORE_TARGET=MIN_SCORE_ENV-10
            elif found <5 and MIN_SCORE_ENV>=35:
                MIN_SCORE_TARGET=MIN_SCORE_ENV-20

            def _is_offtarget_lead(r: Dict[str, Any]) -> bool:
                lead_type = (r.get("lead_type") or "").lower()
                if lead_type == "employer":
                    return True
                role = (r.get("rolle") or r.get("role_guess") or "").lower()
                company = (r.get("company_name") or "").lower()
                src_url = (r.get("quelle") or "").lower()

                hr_tokens = (
                    "personalreferent",
                    "personalreferentin",
                    "sachbearbeiter personal",
                    "sachbearbeiterin personal",
                    "hr-manager",
                    "hr manager",
                    "human resources",
                    "bewerbungen richten",
                    "bewerbung richten"
                )
                press_tokens = (
                    "pressesprecher",
                    "pressesprecherin",
                    "unternehmenskommunikation",
                    "pressekontakt",
                    "events",
                    "veranstaltungen",
                    "seminar",
                    "seminare"
                )
                public_tokens = (
                    "rathaus",
                    "verwaltung",
                    "gleichstellungsstelle",
                    "grundsicherung",
                    "bundestag",
                    "/stadtwerke",
                    "die-partei.de",
                    "oberhausen.de"
                )

                role_hit = any(tok in role for tok in hr_tokens + press_tokens)
                company_hit = any(tok in company for tok in ("stadtwerke", "bundestag", "die partei"))
                url_hit = any(tok in src_url for tok in public_tokens)

                return role_hit or company_hit or url_hit

            # NUR Kandidaten exportieren, wenn wir im Recruiter-Modus sind
            if "recruiter" in str(QUERIES).lower() or os.getenv("INDUSTRY") == "recruiter":
                collected_rows = [r for r in collected_rows if r.get("lead_type") in ("candidate", "group_invite")]
                log("info", "Filter aktiv: Nur Candidates/Gruppen behalten", remaining=len(collected_rows))

            filtered = _dedup_run(
                [
                    r for r in collected_rows
                    if r.get("score", 0) >= MIN_SCORE_TARGET and not _is_offtarget_lead(r)
                ]
            )
            if filtered:
                inserted = insert_leads(filtered)
                if inserted:
                    append_csv(DEFAULT_CSV, inserted, ENH_FIELDS)
                    append_xlsx(DEFAULT_XLSX, inserted, ENH_FIELDS)
                    _uilog(f"Export: +{len(inserted)} neue Leads")
                    leads_new_total += len(inserted)

            await asyncio.sleep(SLEEP_BETWEEN_QUERIES + _jitter(0.4,1.2))

        finish_run(run_id, total_links_checked, leads_new_total, "ok")
        _uilog(f"Run #{run_id} beendet")

    except Exception as e:
        emergency_save(run_id, total_links_checked, leads_new_total)
        log("error", "Run abgebrochen", error=str(e), tb=traceback.format_exc())
        raise

    finally:
        global _CLIENT_SECURE, _CLIENT_INSECURE
        for cl in (_CLIENT_SECURE,_CLIENT_INSECURE):
            if cl:
                try: await cl.aclose()
                except: pass
        _CLIENT_SECURE=None
        _CLIENT_INSECURE=None



# =========================
# UI (Flask + SSE)
# =========================

def start_ui(host="127.0.0.1", port=5055):
    from flask import Flask, render_template_string, Response
    app = Flask(__name__)

    TEMPLATE = """
<!doctype html><meta charset="utf-8">
<title>Leads-Scraper</title>
<style>
  html,body{font:14px system-ui;margin:0;background:#0b0f0c;color:#e8efe9}
  header{padding:16px 20px;border-bottom:1px solid #1c241e;background:#0f1511}
  main{padding:20px}
  button{padding:10px 16px;margin:6px 8px 6px 0;border:0;border-radius:8px;background:#1b5e20;color:#fff;cursor:pointer}
  button.stop{background:#a82b2b}
  .warn{background:#a8742b}
  .muted{background:#2b3a2f}
  .card{background:#0f1511;border:1px solid #1c241e;border-radius:12px;padding:12px;margin-top:16px}
  pre{white-space:pre-wrap;max-height:60vh;overflow:auto;margin:0}
</style>
<header><h2>NRW Leads-Scraper</h2></header>
<main>
  <button onclick="fetch('/start',{method:'POST'})">Start</button>
  <button class="warn" onclick="fetch('/start_force',{method:'POST'})">Start (Force)</button>
  <button class="stop" onclick="fetch('/stop',{method:'POST'})">Stop</button>
  <button class="warn" onclick="fetch('/reset',{method:'POST'})">Reset (History)</button>
  <button class="muted" onclick="fetch('/reset_seen',{method:'POST'})">Seen (24h) löschen</button>
  <button class="muted" onclick="fetch('/reset_queries',{method:'POST'})">Queries zurücksetzen</button>
  <a style="margin-left:12px;color:#9fe29f" href="/logs" target="_blank">Logs Stream</a>
  <div class="card"><pre id="p"></pre></div>
</main>
<script>
const p=document.getElementById('p');
const es=new EventSource('/stream');
es.onmessage=(e)=>{ if(e.data!==undefined){ p.textContent+=e.data+"\\n"; p.scrollTop=p.scrollHeight; } };
</script>
"""

    @app.route("/")
    def index():
        return render_template_string(TEMPLATE)

    @app.route("/start", methods=["POST"])
    def start():
        if RUN_FLAG["running"]: return "already running", 200
        RUN_FLAG["running"]=True
        RUN_FLAG["force"]=False
        threading.Thread(target=_ui_controller, daemon=True).start()
        return "ok", 200

    @app.route("/start_force", methods=["POST"])
    def start_force():
        if RUN_FLAG["running"]: return "already running", 200
        RUN_FLAG["running"]=True
        RUN_FLAG["force"]=True
        threading.Thread(target=_ui_controller, daemon=True).start()
        return "ok", 200

    @app.route("/stop", methods=["POST"])
    def stop():
        RUN_FLAG["running"]=False
        if UILOGQ: UILOGQ.put("STOP angefordert")
        return "ok", 200

    @app.route("/reset", methods=["POST"])
    def reset():
        a,b = reset_history()
        msg = f"Reset: queries_done={a}, urls_seen={b} gelöscht"
        if UILOGQ: UILOGQ.put(msg)
        return "ok", 200

    @app.route("/reset_seen", methods=["POST"])
    def reset_seen():
        con=db(); cur=con.cursor()
        cur.execute("DELETE FROM urls_seen WHERE ts < datetime('now','-1 day')")
        con.commit(); con.close()
        if UILOGQ: UILOGQ.put("urls_seen (älter 24h) bereinigt")
        return "ok", 200

    @app.route("/reset_queries", methods=["POST"])
    def reset_queries():
        con=db(); cur=con.cursor()
        cur.execute("DELETE FROM queries_done")
        con.commit(); con.close()
        if UILOGQ: UILOGQ.put("queries_done geleert")
        return "ok", 200

    @app.route("/stream")
    def stream():
        def gen():
            while True:
                try:
                    msg = UILOGQ.get(timeout=1)
                    yield f"data: {msg}\n\n"
                except queue.Empty:
                    time.sleep(0.5)  # entlastet CPU; kein leeres Event
        return Response(gen(), mimetype='text/event-stream')

    @app.route("/logs")
    def logs():
        return "<pre>Live-Logs im /stream-Event-Stream.</pre>"

    app.run(host=host, port=port, debug=False, threaded=True)

def _ui_controller():
    try:
        force = bool(RUN_FLAG.get("force"))
        # UI-Run: DATE_RESTRICT (falls gesetzt) aus ENV übernehmen
        dr = os.getenv("DATE_RESTRICT", "").strip() or None
        asyncio.run(
            run_scrape_once_async(
                RUN_FLAG,
                ui_log=lambda s: UILOGQ.put(s),
                force=force,
                date_restrict=dr
            )
        )
    except Exception as e:
        if UILOGQ: UILOGQ.put(f"Fehler: {e}")
    finally:
        RUN_FLAG["running"]=False
        RUN_FLAG["force"]=False
        if UILOGQ: UILOGQ.put("Run beendet")


# =========================
# CLI / Entry
# =========================

def validate_config():
    errs=[]
    if not OPENAI_API_KEY or len(OPENAI_API_KEY) < 40:
        errs.append("OPENAI_API_KEY zu kurz/leer (für KI-Extraktion). Regex-Fallback läuft dennoch.")
    if (GCS_KEYS and not GCS_CXS) or (GCS_CXS and not GCS_KEYS):
        errs.append("GCS_KEYS/GCS_CXS unvollständig (beide listenbasiert setzen oder deaktivieren).")
    if not (GCS_KEYS and GCS_CXS) and (GCS_API_KEY and not GCS_CX):
        errs.append("GCS_CX fehlt trotz GCS_API_KEY (Legacy-Single-Config).")
    if errs: log("warn","Konfiguration Hinweise", errors=errs)

def parse_args():
    ap = argparse.ArgumentParser(description="NRW Vertrieb-Leads Scraper (inkrementell + UI)")
    ap.add_argument("--ui", action="store_true", help="Web-UI starten (Start/Stop/Logs)")
    ap.add_argument("--once", action="store_true", help="Einmaliger Lauf im CLI")
    ap.add_argument("--force", action="store_true", help="Ignoriere History (queries_done)")
    ap.add_argument("--tor", action="store_true", help="Leite Traffic über Tor (SOCKS5 127.0.0.1:9050)")
    ap.add_argument("--reset", action="store_true", help="Lösche queries_done und urls_seen vor dem Lauf")
    ap.add_argument("--industry", choices=["all","recruiter"] + list(INDUSTRY_ORDER),
                default=os.getenv("INDUSTRY","all"),
                help="Branche für diesen Run (Standard: all)")
    ap.add_argument("--qpi", type=int, default=int(os.getenv("QPI","2")),
                    help="Queries pro Branche in diesem Run (Standard: 2)")
    ap.add_argument("--daterestrict", type=str, default=os.getenv("DATE_RESTRICT",""),
                    help="Google CSE dateRestrict, z.B. d30, w8, m3")
    return ap.parse_args()



if __name__ == "__main__":
    try:
        args = parse_args()
        USE_TOR = bool(getattr(args, "tor", False))
        if USE_TOR:
            log("info", "ANONYMITY MODE: Running over TOR Network")
            try:
                tor_resp = asyncio.run(http_get_async("https://check.torproject.org/api/ip", timeout=15))
                if tor_resp and getattr(tor_resp, "status_code", 0) == 200:
                    log("info", "TOR check ok", status=tor_resp.status_code, body=(getattr(tor_resp, "text", "") or "")[:200])
                else:
                    log("warn", "TOR check failed", status=getattr(tor_resp, "status_code", None))
            except Exception as e:
                log("warn", "TOR check failed", error=str(e))
        validate_config()
        init_db()
        migrate_db_unique_indexes()

        # Auswahl der Queries für diesen Run
        selected_industry = getattr(args, "industry", "all")
        per_industry_limit = max(1, getattr(args, "qpi", 2))
        QUERIES = build_queries(selected_industry, per_industry_limit)
        log("info", "Query-Set gebaut", industry=selected_industry,
            per_industry_limit=per_industry_limit, count=len(QUERIES))

        if args.reset:
            a,b = reset_history()
            log("info","Reset durchgeführt", queries_done=a, urls_seen=b)

        if args.ui:
            from flask import Flask
            UILOGQ = queue.Queue(maxsize=1000)
            RUN_FLAG["running"]=False
            RUN_FLAG["force"]=False
            start_ui()
        else:
            RUN_FLAG["running"]=True
            RUN_FLAG["force"]=bool(args.force)
            asyncio.run(
                run_scrape_once_async(
                    RUN_FLAG,
                    force=bool(args.force),
                    date_restrict=(args.daterestrict or None)
                )
            )

    except KeyboardInterrupt:
        die("Abgebrochen (Strg+C)")
    except Exception as e:
        die("Unerwarteter Fehler", error=str(e), tb=traceback.format_exc())
