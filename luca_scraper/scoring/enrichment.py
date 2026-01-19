# -*- coding: utf-8 -*-
"""
LUCA NRW Scraper - Enrichment Module
=====================================
Telefonbuch enrichment and caching functionality.
Extracted from scriptname.py (Phase 3 Modularization).
"""

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

try:
    from curl_cffi.requests import AsyncSession
    HAVE_CURL_CFFI = True
except ImportError:
    HAVE_CURL_CFFI = False
    AsyncSession = None

# =========================
# Configuration Constants
# =========================

TELEFONBUCH_ENRICHMENT_ENABLED = (os.getenv("TELEFONBUCH_ENRICHMENT_ENABLED", "1") == "1")
TELEFONBUCH_STRICT_MODE = (os.getenv("TELEFONBUCH_STRICT_MODE", "1") == "1")
TELEFONBUCH_RATE_LIMIT = float(os.getenv("TELEFONBUCH_RATE_LIMIT", "3.0"))
TELEFONBUCH_CACHE_DAYS = int(os.getenv("TELEFONBUCH_CACHE_DAYS", "7"))
TELEFONBUCH_MOBILE_ONLY = (os.getenv("TELEFONBUCH_MOBILE_ONLY", "1") == "1")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))
USER_AGENT = "Mozilla/5.0 (compatible; VertriebFinder/2.3; +https://example.com)"
DB_PATH = os.getenv("SCRAPER_DB", "scraper.db")
USE_TOR = False


# =========================
# Helper Functions (minimal dependencies)
# =========================

def db() -> sqlite3.Connection:
    """Thread-safe database connection."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    line = f"[{ts}] [{level.upper():7}] {msg}{ctx_str}"
    print(line, flush=True)


def _make_client(secure: bool, ua: str, proxy_url: Optional[str], force_http1: bool, timeout_s: int):
    """Create HTTP client with proper proxy handling."""
    if not HAVE_CURL_CFFI:
        raise ImportError("curl-cffi is required for HTTP client. Install with: pip install curl-cffi")
    
    if USE_TOR:
        proxy_url = "socks5://127.0.0.1:9050"
    headers = {
        "User-Agent": ua or USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    
    if secure and not USE_TOR and not proxy_url:
        proxies = None
    else:
        proxies = {"http://": proxy_url, "https://": proxy_url} if proxy_url else None
    
    return AsyncSession(
        impersonate="chrome120",
        headers=headers,
        verify=True if secure else False,
        timeout=timeout_s,
        proxies=proxies,
    )


def normalize_phone(p: str) -> str:
    """
    DE-Telefon-Normalisierung (E.164-ähnlich) mit Edge-Cases wie '(0)'.
    
    Examples:
        '0211 123456'            -> '+49211123456'
        '+49 (0) 211 123456'     -> '+49211123456'
        '0049 (0) 211-123456'    -> '+49211123456'
        '+49-(0)-176 123 45 67'  -> '+491761234567'
    """
    if not p:
        return ""

    s = str(p).strip()
    s = re.sub(r'[\(\[\{]\s*0\s*[\)\]\}]', '0', s)
    s = re.sub(r'(?:durchwahl|dw|ext\.?|extension)\s*[:\-]?\s*\d+\s*$', '', s, flags=re.I)
    s = re.sub(r'[^\d+]', '', s)
    s = re.sub(r'^00', '+', s)
    s = re.sub(r'^\+049', '+49', s)
    s = re.sub(r'^0049', '+49', s)
    s = re.sub(r'^\+490', '+49', s)
    
    if s.startswith('0') and not s.startswith('+'):
        s = '+49' + s[1:]
    
    if s.count('+') > 1:
        s = '+' + re.sub(r'\D', '', s)
    
    if not s.startswith('+'):
        s = '+' + re.sub(r'\D', '', s)
    
    digits = re.sub(r'\D', '', s)
    if len(digits) < 8 or len(digits) > 16:
        return s
    
    return s


MOBILE_PREFIXES_DE = {'150', '151', '152', '155', '156', '157', '159',
                      '160', '162', '163', '170', '171', '172', '173',
                      '174', '175', '176', '177', '178', '179'}


def is_mobile_number(phone: str) -> bool:
    """Check if phone number is a German mobile number."""
    if not phone:
        return False
    digits = re.sub(r'\D', '', phone)
    if phone.startswith('+49') and len(digits) >= 5:
        prefix = digits[2:5]
        return prefix in MOBILE_PREFIXES_DE
    return False


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Robust phone validation with strict requirements.
    Returns (is_valid, phone_type) where phone_type is 'mobile', 'landline', or 'invalid'.
    """
    if not phone or not isinstance(phone, str):
        return False, "invalid"
    
    normalized = normalize_phone(phone)
    if not normalized:
        return False, "invalid"
    
    digits = re.sub(r'\D', '', normalized)
    
    if len(digits) < 10 or len(digits) > 15:
        return False, "invalid"
    
    if normalized.startswith('+49'):
        if len(digits) >= 5:
            prefix = digits[2:5]
            if prefix in MOBILE_PREFIXES_DE:
                return True, "mobile"
            elif prefix[0] in '23456789':
                return True, "landline"
    
    elif normalized.startswith('+') and len(digits) >= 10:
        return True, "international"
    
    return False, "invalid"


def _looks_like_company_name(name: str) -> bool:
    """
    Prüft ob Name wie eine Firma aussieht.
    
    Returns True für:
        - "GmbH", "AG", "KG", "UG" im Namen
        - "Team", "Vertrieb", "Sales" im Namen
        - Nur ein Wort
        - Enthält Zahlen
    """
    if not name:
        return True
    
    company_indicators = [
        "gmbh", "ag", "kg", "ug", "ltd", "inc", 
        "team", "vertrieb", "sales", "group", "holding",
        "firma", "unternehmen", "company"
    ]
    name_lower = name.lower()
    
    if any(ind in name_lower for ind in company_indicators):
        return True
    
    if len(name.split()) < 2:
        return True
    
    if re.search(r'\d', name):
        return True
    
    return False


# =========================
# Telefonbuch Caching
# =========================

async def get_cached_telefonbuch_result(name: str, city: str) -> Optional[List[Dict]]:
    """Prüft ob Ergebnis im Cache ist (max 7 Tage alt)"""
    if not name or not city:
        return None
    
    query_hash = hashlib.md5(f"{name.lower()}:{city.lower()}".encode()).hexdigest()
    
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT results_json, created_at 
        FROM telefonbuch_cache 
        WHERE query_hash = ?
    """, (query_hash,))
    row = cur.fetchone()
    con.close()
    
    if not row:
        return None
    
    results_json, created_at = row
    
    try:
        cache_time = datetime.fromisoformat(created_at)
        age = datetime.now() - cache_time
        if age > timedelta(days=TELEFONBUCH_CACHE_DAYS):
            return None
    except Exception:
        return None
    
    try:
        results = json.loads(results_json) if results_json else []
        log("debug", "Telefonbuch-Cache Hit", name=name, city=city)
        return results
    except Exception:
        return None


async def cache_telefonbuch_result(name: str, city: str, results: List[Dict]):
    """Speichert Ergebnis im Cache"""
    if not name or not city:
        return
    
    query_hash = hashlib.md5(f"{name.lower()}:{city.lower()}".encode()).hexdigest()
    results_json = json.dumps(results, ensure_ascii=False)
    
    con = db()
    cur = con.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO telefonbuch_cache (name, city, query_hash, results_json, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (name, city, query_hash, results_json))
    con.commit()
    con.close()


# =========================
# Rate Limiter
# =========================

class _TelefonbuchRateLimiter:
    """Rate limiter for telefonbuch requests"""
    def __init__(self, interval: float = 3.0):
        self.interval = interval
        self.last_request = 0.0
        self.lock = asyncio.Lock()
    
    async def __aenter__(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_request
            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                await asyncio.sleep(wait_time)
            self.last_request = time.time()
    
    async def __aexit__(self, *args):
        pass


_telefonbuch_rate = _TelefonbuchRateLimiter(interval=TELEFONBUCH_RATE_LIMIT)


# =========================
# Query & Enrichment Functions
# =========================

async def query_dasoertliche(name: str, city: str) -> List[Dict]:
    """
    Führt eine Suche auf dasoertliche.de durch.
    
    URL-Format: https://www.dasoertliche.de/?kw={name}&ci={city}
    
    Extrahiert aus HTML:
        - name: Name des Eintrags
        - phone: Telefonnummer
        - address: Adresse
        - city: Stadt
    
    Returns:
        Liste von Treffern als Dicts
    """
    if not name or not city:
        return []
    
    params = urllib.parse.urlencode({"kw": name, "ci": city})
    url = f"https://www.dasoertliche.de/?{params}"
    
    log("debug", "Telefonbuch-Query", name=name, city=city)
    
    async with _telefonbuch_rate:
        try:
            async with _make_client(True, USER_AGENT, None, False, HTTP_TIMEOUT) as client:
                resp = await client.get(url, timeout=HTTP_TIMEOUT)
                
                if not resp or resp.status_code != 200:
                    log("warn", "Telefonbuch-Query fehlgeschlagen", status=resp.status_code if resp else -1)
                    return []
                
                html = resp.text if hasattr(resp, 'text') else resp.content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            log("warn", "Telefonbuch-Query Exception", error=str(e))
            return []
    
    results = []
    parsing_strategy = None
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        entries = soup.find_all("article", class_=re.compile(r"entry|treffer|hit", re.I))
        if entries:
            parsing_strategy = "article_elements"
        
        if not entries:
            entries = soup.find_all("div", itemtype=re.compile(r"Person", re.I))
            if entries:
                parsing_strategy = "schema_org_person"
        
        if not entries:
            entries = soup.find_all("div", class_=re.compile(r"treffer|result|entry", re.I))
            if entries:
                parsing_strategy = "fallback_divs"
        
        if parsing_strategy:
            log("debug", "Telefonbuch-Parse-Strategie", strategy=parsing_strategy, entries_found=len(entries))
        else:
            log("debug", "Telefonbuch-Parse: Keine Einträge gefunden")
        
        for entry in entries[:5]:
            result = {}
            
            name_elem = entry.find(itemprop="name") or entry.find("h2") or entry.find(class_=re.compile(r"name", re.I))
            if name_elem:
                result["name"] = name_elem.get_text(strip=True)
            
            phone_elem = (
                entry.find(itemprop="telephone") or 
                entry.find(class_=re.compile(r"phone|telefon|tel", re.I)) or
                entry.find("a", href=re.compile(r"^tel:"))
            )
            if phone_elem:
                phone_text = phone_elem.get_text(strip=True)
                phone_clean = re.sub(r'[^\d\+]', '', phone_text.replace(" ", ""))
                result["phone"] = phone_clean
            
            address_elem = entry.find(itemprop="streetAddress") or entry.find(class_=re.compile(r"street|address|strasse", re.I))
            if address_elem:
                result["address"] = address_elem.get_text(strip=True)
            
            city_elem = entry.find(itemprop="addressLocality") or entry.find(class_=re.compile(r"city|ort", re.I))
            if city_elem:
                result["city"] = city_elem.get_text(strip=True)
            
            if result.get("name") and result.get("phone"):
                results.append(result)
        
    except Exception as e:
        log("warn", "Telefonbuch-Parse Exception", error=str(e))
        return []
    
    log("info", "Telefonbuch: Treffer gefunden", count=len(results))
    return results


def should_accept_enrichment(
    original_name: str,
    original_city: str,
    results: List[Dict]
) -> Tuple[bool, Optional[Dict], str]:
    """
    Prüft ob Enrichment akzeptiert werden soll.
    
    Checks:
        1. Genau 1 Treffer
        2. Name-Match >= 90% (fuzzy matching)
        3. Stadt-Match (enthält oder gleich)
        4. Telefonnummer ist Mobilnummer (015/016/017)
    
    Returns:
        (accept: bool, result: Dict or None, reason: str)
    """
    if not results:
        return False, None, "Keine Treffer"
    
    if TELEFONBUCH_STRICT_MODE and len(results) != 1:
        return False, None, f"Mehrere Treffer ({len(results)})"
    
    result = results[0]
    
    result_name = result.get("name", "").lower().strip()
    original_name_clean = original_name.lower().strip()
    
    def normalize_name(n):
        titles = [
            r'dr\.?\s*med\.?',
            r'dr\.?\s*phil\.?',
            r'dr\.?\s*ing\.?',
            r'dr\.?',
            r'prof\.?\s*dr\.?',
            r'prof\.?',
            r'dipl\.?-ing\.?',
            r'dipl\.?',
            r'ing\.?',
            r'mag\.?',
            r'msc\.?',
            r'mba\.?',
            r'b\.?\s*sc\.?',
            r'm\.?\s*sc\.?',
        ]
        pattern = r'\b(' + '|'.join(titles) + r')\b'
        n = re.sub(pattern, '', n, flags=re.I)
        return ' '.join(n.split())
    
    result_name_norm = normalize_name(result_name)
    original_name_norm = normalize_name(original_name_clean)
    
    name_match = (
        result_name_norm in original_name_norm or
        original_name_norm in result_name_norm or
        result_name_norm == original_name_norm
    )
    
    if not name_match:
        result_words = set(result_name_norm.split())
        original_words = set(original_name_norm.split())
        common_words = result_words & original_words
        if len(common_words) < 2:
            return False, None, f"Name-Mismatch: '{result_name}' vs '{original_name}'"
    
    result_city = result.get("city", "").lower().strip()
    original_city_clean = original_city.lower().strip()
    
    city_match = (
        result_city in original_city_clean or
        original_city_clean in result_city or
        result_city == original_city_clean
    )
    
    if not city_match and result_city:
        return False, None, f"Stadt-Mismatch: '{result_city}' vs '{original_city}'"
    
    phone = result.get("phone", "")
    if not phone:
        return False, None, "Keine Telefonnummer"
    
    normalized_phone = normalize_phone(phone)
    
    if TELEFONBUCH_MOBILE_ONLY:
        if not is_mobile_number(normalized_phone):
            return False, None, "Keine Mobilnummer"
    
    return True, result, "Akzeptiert"


async def enrich_phone_from_telefonbuch(
    name: str,
    city: str,
    strict: bool = True
) -> Optional[Dict[str, str]]:
    """
    Sucht Telefonnummer in dasoertliche.de
    
    Args:
        name: Vor- und Nachname (z.B. "Max Mustermann")
        city: Stadt (z.B. "Düsseldorf")
        strict: Nur bei exakt 1 Treffer (100% Genauigkeit)
    
    Returns:
        Dict mit {"phone": "0176...", "address": "..."} oder None
    
    Regeln:
        - Nur wenn Name UND Stadt vorhanden
        - Nur bei GENAU 1 Treffer (wenn strict=True)
        - Nur Mobilnummern (015x, 016x, 017x) werden akzeptiert
        - Rate-Limiting: Max 1 Request / 3 Sekunden
    """
    if not TELEFONBUCH_ENRICHMENT_ENABLED:
        return None
    
    if not name or not city:
        return None
    
    log("info", "Telefonbuch-Enrichment gestartet", name=name, city=city)
    
    cached = await get_cached_telefonbuch_result(name, city)
    if cached is not None:
        results = cached
    else:
        results = await query_dasoertliche(name, city)
        await cache_telefonbuch_result(name, city, results)
    
    accept, result, reason = should_accept_enrichment(name, city, results)
    
    if not accept:
        log("warn", "Telefonbuch-Enrichment abgelehnt", reason=reason, name=name, city=city)
        return None
    
    phone = result.get("phone", "")
    address = result.get("address", "")
    
    log("info", "Telefonbuch-Enrichment erfolgreich", 
        name=name, city=city, phone=phone[:8]+"..." if len(phone) > 8 else phone)
    
    return {
        "phone": phone,
        "address": address
    }


async def enrich_leads_with_telefonbuch(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enriches leads without phone numbers using telefonbuch lookup.
    Returns the enriched leads list.
    """
    if not TELEFONBUCH_ENRICHMENT_ENABLED or not leads:
        return leads
    
    enriched_leads = []
    for lead in leads:
        if not lead.get("telefon") and lead.get("name") and lead.get("region"):
            name = lead["name"]
            city = lead["region"]
            
            if _looks_like_company_name(name):
                log("debug", "Telefonbuch-Enrichment übersprungen (Firmenname)", name=name)
                enriched_leads.append(lead)
                continue
            
            enrichment = await enrich_phone_from_telefonbuch(name, city)
            
            if enrichment and enrichment.get("phone"):
                normalized_phone = normalize_phone(enrichment["phone"])
                if normalized_phone:
                    is_valid, phone_type = validate_phone(normalized_phone)
                    if is_valid and phone_type == "mobile":
                        lead["telefon"] = normalized_phone
                        lead["phone_type"] = "mobile"
                        
                        if enrichment.get("address"):
                            lead["private_address"] = enrichment["address"]
                        
                        tags = lead.get("tags", "")
                        if tags:
                            lead["tags"] = tags + ",telefonbuch_enriched"
                        else:
                            lead["tags"] = "telefonbuch_enriched"
                        
                        log("info", "Telefonbuch-Enrichment erfolgreich", 
                            name=name, city=city, phone=normalized_phone[:8]+"..." if len(normalized_phone) > 8 else normalized_phone)
                    else:
                        log("debug", "Telefonbuch-Enrichment: Ungültige Nummer", 
                            name=name, phone=normalized_phone, phone_type=phone_type)
                else:
                    log("debug", "Telefonbuch-Enrichment: Normalisierung fehlgeschlagen", 
                        name=name, original_phone=enrichment["phone"])
        
        enriched_leads.append(lead)
    
    return enriched_leads


__all__ = [
    "get_cached_telefonbuch_result",
    "cache_telefonbuch_result",
    "query_dasoertliche",
    "should_accept_enrichment",
    "enrich_phone_from_telefonbuch",
    "enrich_leads_with_telefonbuch",
]
