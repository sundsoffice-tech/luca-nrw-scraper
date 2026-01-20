"""
OpenAI Integration for LUCA NRW Scraper
========================================

Provides AI-powered contact extraction, name validation, and content analysis.
All functions gracefully handle missing API keys by returning empty results or fallbacks.
"""

import hashlib
import json
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import tldextract

from cache import get_ai_response_cache
from luca_scraper.config import OPENAI_API_KEY, HTTP_TIMEOUT


# =========================
# HELPER FUNCTIONS (imported from scriptname.py)
# =========================

def log(level: str, msg: str, **ctx):
    """Simple logging function - imports actual logger from parent if available."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    line = f"[{ts}] [{level.upper():7}] {msg}{ctx_str}"
    print(line, flush=True)


def etld1(host: str) -> str:
    """Extract eTLD+1 (registered domain) from hostname."""
    if not host:
        return ""
    ex = tldextract.extract(host)
    dom = getattr(ex, "top_domain_under_public_suffix", None) or ex.registered_domain
    return dom.lower() if dom else host.lower()


def same_org_domain(page_url: str, email_domain: str) -> bool:
    """Check if page URL and email domain belong to same organization."""
    try:
        host = urllib.parse.urlparse(page_url).netloc
        return etld1(host) == etld1(email_domain)
    except Exception:
        return False


def normalize_phone(p: str) -> str:
    """
    Normalize German phone numbers to E.164-like format.
    Examples:
      '0211 123456'            -> '+49211123456'
      '+49 (0) 211 123456'     -> '+49211123456'
      '0049 (0) 211-123456'    -> '+49211123456'
    """
    if not p:
        return ""
    s = str(p).strip()
    s = re.sub(r'[\(\[\{]\s*0\s*[\)\]\}]', '0', s)
    s = re.sub(r'(?:durchwahl|dw|ext\.?|extension)\s*[:\-]?\s*\d+\s*$', '', s, flags=re.I)
    s = re.sub(r'[^\d+]', '', s)
    if not s:
        return ""
    if s.startswith("00"):
        s = "+" + s[2:]
    if s.startswith("0") and not s.startswith("00"):
        s = "+49" + s[1:]
    if s.startswith("+49") and len(s) >= 8:
        return s
    if s.startswith("+") and len(s) >= 8:
        return s
    return ""


AI_RESPONSE_CACHE = get_ai_response_cache()


def _build_ai_cache_key(prefix: str, url: str, text: str) -> str:
    """Create a stable cache key for AI requests."""
    key_material = f"{prefix}:{url}:{text}"
    digest = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def _clone_cached_value(value: Any) -> Any:
    """Return a deep copy of cached data to prevent mutations."""
    try:
        return json.loads(json.dumps(value))
    except Exception:
        return value


# Constants needed for validation
EMAIL_RE = re.compile(r'\b(?!noreply|no-reply|donotreply)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}\b', re.I)

EMPLOYER_EMAIL_PREFIXES = {
    "career", "careers", "hr", "humanresources", "recruiting", "recruitment",
    "talent", "jobs", "job", "bewerbung", "application", "stellenangebot",
    "stellenangebote", "karriere", "personal", "hiring"
}

BAD_MAILBOXES = {
    "noreply", "no-reply", "donotreply", "mailer-daemon", "postmaster",
    "webmaster", "hostmaster", "abuse", "security", "support", "admin"
}

PORTAL_DOMAINS = {
    "ebay-kleinanzeigen.de", "kleinanzeigen.de", "quoka.de", "markt.de",
    "kalaydo.de", "jobscout24.de", "stepstone.de", "indeed.com", "monster.de"
}

CANDIDATE_POS_MARKERS = (
    "stellengesuch", "jobgesuch", "ich suche", "suche job", "suche arbeit",
    "auf jobsuche", "open to work", "offen für angebote", "verfügbar ab",
    "ab sofort verfügbar", "arbeitsuchend"
)


def _is_candidates_mode() -> bool:
    """Check if we're in candidates/recruiter mode based on INDUSTRY env var."""
    industry = str(os.getenv("INDUSTRY", "")).lower()
    if "talent_hunt" in industry:
        return False
    return "recruiter" in industry or "candidates" in industry


def is_candidate_url(url: Optional[str]) -> Optional[bool]:
    """
    Check if URL is likely a candidate profile.
    Returns: True (candidate), False (definitely not), None (uncertain)
    """
    if not url:
        return None
    
    url_lower = url.lower()
    
    if 'stellengesuch' in url_lower or 'jobgesuch' in url_lower:
        return True
    
    positive_patterns = [
        '/s-stellengesuche/', '/stellengesuche/', 'linkedin.com/in/',
        'xing.com/profile/', '/freelancer/', 'facebook.com/groups/',
        't.me/', 'chat.whatsapp.com/', 'reddit.com/r/',
        'gutefrage.net', 'freelancermap.de', 'freelance.de'
    ]
    
    for pattern in positive_patterns:
        if pattern in url_lower:
            return True
    
    return None


def validate_contact(contact: dict, page_url: str = "", page_text: str = "") -> bool:
    """Validate that a contact has valid email/phone and passes quality checks."""
    email = (contact.get("email") or "").strip()
    phone = (contact.get("telefon") or "").strip()
    text_lower = (page_text or "").lower()
    
    info_like_localparts = {"info", "kontakt", "service", "office", "news", "presse"}
    candidate_context = any(tok in text_lower for tok in CANDIDATE_POS_MARKERS)
    
    if email:
        low = email.lower()
        if not EMAIL_RE.search(email):
            return False
        local, _, domain = low.partition("@")
        if local in EMPLOYER_EMAIL_PREFIXES:
            return False
        if local in info_like_localparts and not candidate_context:
            return False
        if local in BAD_MAILBOXES and local not in info_like_localparts:
            return False
        if any(domain.endswith(p) for p in PORTAL_DOMAINS):
            return False
        if page_url and not same_org_domain(page_url, domain):
            if domain not in {"gmail.com", "outlook.com", "hotmail.com", "gmx.de", "web.de"}:
                return False
        if re.fullmatch(r'\d{8,}', (local or "")):
            return False
    
    if phone:
        if len(phone) < 8:
            return False
    
    return bool(email or phone)


# =========================
# NAME VALIDATION
# =========================

def _validate_name_heuristic(name: str) -> Tuple[bool, int, str]:
    """Fallback heuristic for name validation without AI."""
    if not name or len(name.strip()) < 3:
        return False, 0, "Name zu kurz"
    
    name_lower = name.lower().strip()
    
    blacklist = [
        "gmbh", "ag", "kg", "ug", "ltd", "inc",
        "team", "vertrieb", "sales", "info", "kontakt",
        "ansprechpartner", "unknown", "n/a", "k.a.",
        "firma", "unternehmen", "company", "abteilung",
    ]
    if any(b in name_lower for b in blacklist):
        return False, 90, f"Blacklist-Wort gefunden"
    
    words = name.split()
    if len(words) < 2:
        return False, 70, "Nur ein Wort"
    
    if re.search(r'\d', name):
        return False, 85, "Enthält Zahlen"
    
    return True, 75, "Heuristik: wahrscheinlich echter Name"


async def validate_real_name_with_ai(name: str, context: str = "") -> Tuple[bool, int, str]:
    """
    AI-based validation to check if name is a real human name.
    
    Args:
        name: Name to validate
        context: Optional context for better validation
    
    Returns:
        Tuple of (is_real_name, confidence, reason)
    """
    if not OPENAI_API_KEY:
        return _validate_name_heuristic(name)
    
    prompt = f"""
    Prüfe ob dieser Name ein ECHTER menschlicher Name ist:
    
    Name: "{name}"
    Kontext: "{context}"
    
    ECHTE Namen:
    ✅ "Max Mustermann" - Vor- und Nachname
    ✅ "Anna-Maria Schmidt" - Doppelname
    ✅ "Dr. Hans Meier" - Mit Titel
    ✅ "Mehmet Yılmaz" - Internationale Namen
    
    KEINE echten Namen:
    ❌ "Vertrieb NRW" - Firmenname
    ❌ "Team Sales" - Abteilung
    ❌ "info" - Generisch
    ❌ "123456" - Zahlen
    ❌ "Ansprechpartner" - Rolle
    ❌ "GmbH" - Firma
    ❌ "Unknown Candidate" - Platzhalter
    ❌ "N/A", "k.A.", "-" - Leer
    
    Return JSON: {{"is_real_name": true/false, "confidence": 0-100, "reason": "..."}}
    """
    
    try:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=150
            )
            
            result = json.loads(response.choices[0].message.content)
            is_real = result.get("is_real_name", False)
            confidence = result.get("confidence", 0)
            reason = result.get("reason", "")
            
            return (is_real, confidence, reason)
        except ImportError:
            log("warn", "openai package not available, using heuristic")
            return _validate_name_heuristic(name)
    except Exception as e:
        log("warn", "AI name validation failed, using heuristic", error=str(e))
        return _validate_name_heuristic(name)


# =========================
# CONTENT ANALYSIS
# =========================

async def analyze_content_async(text: str, url: str) -> Dict[str, Any]:
    """
    LLM-based scoring of page content. Returns score/category/summary.
    
    Args:
        text: Page text content (first 2000 chars)
        url: Source URL
    
    Returns:
        Dict with keys: score, category, summary
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"score": 100, "category": "Unchecked", "summary": "No AI Key"}

    clean_text = (text or "")[:2000].replace("\n", " ")
    cache_key = _build_ai_cache_key("analysis", url, clean_text)
    cached = AI_RESPONSE_CACHE.get(cache_key)
    if cached is not None:
        return _clone_cached_value(cached)
    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    system_prompt = (
        "You are an expert Headhunter AI. Your goal is to find CANDIDATES, not companies.\n"
        "Analyze the text and determine if it contains contact details of a human that can be recruited.\n\n"
        "1. CLASSIFY the content:\n"
        '   - "POACHING": A specific employee listed on a company team page (e.g., "Sales Manager" at Company X).\n'
        '   - "FREELANCER": A freelancer/contractor website or profile offering services.\n'
        '   - "CV_DISCOVERY": A CV, Resume, or "Lebenslauf" document (often PDF) or an "Open to Work" post.\n'
        '   - "IRRELEVANT": Job boards, general company homepages, news, shops, or agencies trying to sell recruiting services.\n\n'
        "2. DECIDE:\n"
        "   - Set \"is_relevant\": true ONLY if it is POACHING, FREELANCER, or CV_DISCOVERY.\n"
        "   - Set \"is_relevant\": false for IRRELEVANT.\n\n"
        'Return JSON: {"is_relevant": bool, "lead_type": string, "score": int, "reason": string}'
    )
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"URL: {url}\nTEXT: {clean_text}"}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=payload, timeout=HTTP_TIMEOUT) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    choices = data.get("choices") or []
                    content = ""
                    if choices and isinstance(choices, list):
                        content = ((choices[0] or {}).get("message") or {}).get("content", "")
                    if content:
                        try:
                            parsed = json.loads(content)
                            is_relevant = parsed.get("is_relevant", False)
                            lead_type = parsed.get("lead_type", "Unknown")
                            score = parsed.get("score", 50)
                            reason = parsed.get("reason", "")
                            result = {
                                "score": score if is_relevant else 0,
                                "category": lead_type,
                                "summary": reason
                            }
                            AI_RESPONSE_CACHE.set(cache_key, _clone_cached_value(result))
                            return result
                        except json.JSONDecodeError:
                            log("warn", "AI analysis JSON parse error", url=url)
                    else:
                        log("warn", "AI analysis empty response", url=url, status=resp.status)
                else:
                    log("warn", "AI analysis HTTP error", url=url, status=resp.status)
    except Exception as e:
        log("warn", "AI Analysis failed", url=url, error=str(e))

    fallback = {"score": 50, "category": "Error", "summary": "Analysis failed"}
    AI_RESPONSE_CACHE.set(cache_key, _clone_cached_value(fallback))
    return fallback


# =========================
# CONTACT EXTRACTION
# =========================

async def extract_contacts_with_ai(text_content: str, url: str) -> List[Dict[str, Any]]:
    """
    Extract contacts (name/role/email/phone) using LLM. Returns empty list on errors.
    
    Args:
        text_content: Page text content (first 3000 chars)
        url: Source URL
    
    Returns:
        List of contact dicts with keys: name, rolle, email, telefon, quelle
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []

    clean_text = (text_content or "")[:3000].replace("\n", " ")
    cache_key = _build_ai_cache_key("contacts", url, clean_text)
    cached = AI_RESPONSE_CACHE.get(cache_key)
    if cached is not None:
        return _clone_cached_value(cached)

    def _store_contacts(result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        AI_RESPONSE_CACHE.set(cache_key, _clone_cached_value(result))
        return result
    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # In candidates mode, use enhanced prompt for likely candidate URLs
    if _is_candidates_mode() and is_candidate_url(url) is True:
        system_prompt = (
            'Analyze this profile of a person SEEKING a job (Stellengesuch - NOT a job offer). '
            'IMPORTANT: '
            '- This is a JOB SEEKER profile - the person is LOOKING FOR work '
            '- Extract contact data of the PERSON (not a company) '
            '- Mobile phone number is REQUIRED (015x, 016x, 017x, 01xx format) '
            '- If this is a COMPANY (not a person), set is_job_seeker to false '
            '- If no mobile phone found, still extract but note it '
            'Return JSON: {"is_job_seeker": true/false, "contacts": [{"name": "...", "role": "...", "email": "...", "phone": "...", "location": "...", "availability": "..."}]}. '
            "If no specific job seeker found, return empty contacts list."
        )
    else:
        system_prompt = (
            'Extract contact persons. Return JSON: {"contacts": [{"name": "...", "role": "...", "email": "...", "phone": "..."}]}. '
            "If no specific person found, return empty list."
        )
    
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"URL: {url}\nTEXT: {clean_text}"}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=payload, timeout=HTTP_TIMEOUT) as resp:
                if resp.status != 200:
                    log("warn", "AI contact extraction HTTP error", url=url, status=resp.status)
                    return []
                data = await resp.json()
                choices = data.get("choices") or []
                content = ""
                if choices and isinstance(choices, list):
                    content = ((choices[0] or {}).get("message") or {}).get("content", "")
                if not content:
                    return []
                try:
                    parsed = json.loads(content)
                except Exception as e:
                    log("warn", "AI contact extraction parse failed", url=url, error=str(e))
                    return []
                
                is_job_seeker = parsed.get("is_job_seeker") if isinstance(parsed, dict) else None
                if is_job_seeker is False:
                    log("debug", "AI: Not a job seeker profile", url=url)
                    return _store_contacts([])
                
                contacts_raw = parsed.get("contacts") if isinstance(parsed, dict) else None
                if not isinstance(contacts_raw, list):
                    return _store_contacts([])
                
                cleaned: List[Dict[str, Any]] = []
                for c in contacts_raw:
                    if not isinstance(c, dict):
                        continue
                    name = (c.get("name") or "").strip()
                    role = (c.get("role") or "").strip()
                    email = (c.get("email") or "").strip()
                    phone = normalize_phone(c.get("phone") or "")
                    location = (c.get("location") or "").strip()
                    availability = (c.get("availability") or "").strip()
                    
                    if not (email or phone):
                        continue
                    
                    contact_record = {
                        "name": name,
                        "rolle": role,
                        "email": email,
                        "telefon": phone,
                        "quelle": url
                    }
                    
                    if location:
                        contact_record["location"] = location
                    if availability:
                        contact_record["availability"] = availability
                   
                    cleaned.append(contact_record)
                return _store_contacts(cleaned)
    except Exception as e:
        log("warn", "AI contact extraction failed", url=url, error=str(e))
        return []
    return []


def openai_extract_contacts(raw_text: str, src_url: str) -> List[Dict[str, Any]]:
    """
    Full contact extraction using OpenAI with retries.
    Synchronous version for backward compatibility.
    
    Args:
        raw_text: Raw HTML/text content (first 12000 bytes)
        src_url: Source URL
    
    Returns:
        List of contact dicts with keys: name, rolle, email, telefon, quelle
    """
    if not OPENAI_API_KEY:
        return []
    
    try:
        import requests
    except ImportError:
        log("error", "requests library not available")
        return []

    def _preview(txt: Optional[str]) -> str:
        if not txt:
            return ""
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
                        if validate_contact(rec, page_url=src_url, page_text=raw_text):
                            cleaned.append(rec)
                
                # Deduplicate
                dedup, seen_e, seen_t = [], set(), set()
                for x in cleaned:
                    e = (x.get("email") or "").lower()
                    t = x.get("telefon") or ""
                    if (e and e in seen_e) or (t and t in seen_t):
                        continue
                    dedup.append(x)
                    if e:
                        seen_e.add(e)
                    if t:
                        seen_t.add(t)
                
                log("info", "OpenAI-Extraktion", url=src_url, count=len(dedup))
                return dedup
            
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
