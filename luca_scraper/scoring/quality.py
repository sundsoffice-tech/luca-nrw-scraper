# -*- coding: utf-8 -*-
"""
LUCA NRW Scraper - Quality & Scoring Module
===========================================
Lead scoring, deduplication and quality assessment functions.
Extracted from scriptname.py (Phase 3 Modularization).
"""

import os
import re
import urllib.parse
from typing import Any, Dict, List, Tuple

import tldextract
from bs4 import BeautifulSoup

# =========================
# Pattern Constants
# =========================

PHONE_RE = re.compile(r'(?:\+49|0049|0)\s?(?:\(?\d{2,5}\)?[\s\/\-]?)?\d(?:[\s\/\-]?\d){5,10}')
MOBILE_RE = re.compile(r'(?:\+49|0049|0)\s*1[5-7]\d(?:[\s\/\-]?\d){6,10}')
D2D_HINT = re.compile(r'\b(Door[-\s]?to[-\s]?door|Haustür|Kaltakquise|D2D)\b', re.I)
CALLCENTER_HINT = re.compile(r'\b(Call\s*Center|Telesales|Outbound|Inhouse-?Sales)\b', re.I)
B2C_HINT = re.compile(r'\b(B2C|Endkunden|Privatkunden|Door[-\s]?to[-\s]?Door)\b', re.I)
WA_LINK_RE = re.compile(r'(?:https?://)?(?:wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+|chat\.whatsapp\.com/[A-Za-z0-9]+)', re.I)
WHATSAPP_PHRASE_RE = re.compile(
    r'(?i)(meldet\s+euch\s+per\s+whatsapp|schreib(?:t)?\s+mir\s+(?:per|bei)\s+whatsapp|per\s+whatsapp\s+melden)'
)
TELEGRAM_LINK_RE = re.compile(r'(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_/-]+', re.I)
CITY_RE = re.compile(r'\b(NRW|Nordrhein[-\s]?Westfalen|Düsseldorf|Köln|Essen|Dortmund|Mönchengladbach|Bochum|Wuppertal|Bonn)\b', re.I)


# =========================
# Signal Lists
# =========================

CANDIDATE_ALWAYS_ALLOW = [
    "suche job", "suche arbeit", "suche stelle",
    "suche neue herausforderung", "stellengesuch",
    "#opentowork", "offen für angebote", "offen für neues",
    "arbeitslos", "arbeitssuchend", "freigestellt", "gekündigt",
    "verfügbar ab", "ab sofort verfügbar", "wechselwillig",
    "auf jobsuche", "biete meine dienste", "biete mich an",
    "freiberuflich verfügbar",
]

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

LOW_PAY_HINT = (
    "mindestlohn", "minijob", "aushilfe", "student", "praktikum",
    "ferienjob", "saison", "helfer", "azubi", "ausbildung",
    "promoter", "kommission"
)

COMMISSION_HINT = (
    "provision", "bonus", "uncapped", "hohe verdienstmoeglichkeiten",
    "abschlussstark", "hunter", "akquise", "vertriebsstark"
)

INDUSTRY_HINTS = [
    "solar", "photovoltaik", "pv", "energie", "energieberatung", "strom", "gas",
    "glasfaser", "telekom", "telekommunikation", "dsl", "mobilfunk", "internet",
    "vorwerk", "kobold", "staubsauger", "haushaltswaren",
    "fenster", "türen", "tueren", "dämm", "daemm", "wärmepumpe", "waermepumpe",
    "versicherung", "versicherungen", "bausparen", "immobilien", "makler",
    "onlineshop", "e-commerce", "shop", "kundengewinnung"
]

AGENT_FINGERPRINTS = (
    "selbstständiger handelsvertreter", "handelsvertretung cdh", "cdh-mitglied",
    "gemäß § 84 hgb", "gemäß §84 hgb", "industrievertretung",
    "vertriebsbüro inhaber", "auf provisionsbasis", "vertretung für plz",
    "freie handelsvertretung", "vertriebsagentur", "gebiete: plz",
    "mitglied im handelsvertreterverband", "iucab", "handelsregister a",
    "einzelkaufmann", "e.k."
)


# =========================
# Helper Functions
# =========================

def _is_talent_hunt_mode() -> bool:
    """Check if we're in talent_hunt mode - looking for active sales professionals."""
    industry = str(os.getenv("INDUSTRY", "")).lower()
    return "talent_hunt" in industry


def is_commercial_agent(text: str) -> bool:
    """
    Detects legal/professional Handelsvertreter fingerprints in text.
    """
    if not text:
        return False
    low = text.lower()
    return any(fp in low for fp in AGENT_FINGERPRINTS)


def detect_recency(html: str) -> str:
    """Detect recency indicators in HTML."""
    if re.search(r'\b(2025|2024)\-(0[1-9]|1[0-2])\-(0[1-9]|[12]\d|3[01])\b', html):
        return "aktuell"
    if re.search(r'\b(0?[1-9]|[12]\d|3[01])\.(0?[1-9]|1[0-2])\.(2024|2025)\b', html):
        return "aktuell"
    if re.search(r'\b(ab\s*sofort|sofort|zum\s*nächsten?\s*möglichen\s*termin)\b', html, re.I):
        return "sofort"
    return "unbekannt"


# =========================
# Domain Utilities
# =========================

def etld1(host: str) -> str:
    """Extract effective top-level domain + 1."""
    if not host:
        return ""
    ex = tldextract.extract(host)
    dom = getattr(ex, "top_domain_under_public_suffix", None) or ex.registered_domain
    return dom.lower() if dom else host.lower()


# =========================
# Deduplication
# =========================

def _dedup_run(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Entdoppelt pro Run anhand (eTLD+1 der Quelle, normalisierte E-Mail, normalisierte Tel).
    Spart sinnlose DB-Inserts/Exports.
    """
    seen: set[Tuple[str, str, str]] = set()
    out: List[Dict[str, Any]] = []
    for r in rows:
        try:
            dom = etld1(urllib.parse.urlparse(r.get("quelle", "")).netloc)
        except Exception:
            dom = ""
        e = (r.get("email") or "").strip().lower()
        t = re.sub(r'\D', '', r.get("telefon") or "")
        key = (dom, e, t)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def deduplicate_parallel_leads(leads: List[Dict]) -> List[Dict]:
    """
    Entfernt Duplikate die durch paralleles Crawling entstehen können.
    Priorisiert nach: Telefon > URL > Name+Region
    
    Args:
        leads: Liste von Lead-Dicts
        
    Returns:
        Deduplizierte Liste von Lead-Dicts
    """
    seen_phones = set()
    seen_urls = set()
    unique_leads = []
    
    for lead in leads:
        phone = lead.get("telefon", "").strip()
        url = lead.get("quelle", "").strip()
        
        if phone and phone in seen_phones:
            continue
        if url and url in seen_urls:
            continue
        
        if phone:
            seen_phones.add(phone)
        if url:
            seen_urls.add(url)
        
        unique_leads.append(lead)
    
    return unique_leads


# =========================
# Scoring Function
# =========================

def compute_score(text: str, url: str, html: str = "") -> int:
    """
    Compute quality score for a lead based on text, URL, and HTML content.
    
    Args:
        text: Extracted text content
        url: Source URL
        html: Raw HTML content (optional)
        
    Returns:
        Score between 0-100
    """
    t = text or ""
    t_lower = t.lower()
    t = t_lower
    u = (url or "").lower()
    title_text = ""
    if html:
        try:
            soup_title = BeautifulSoup(html, "html.parser")
            ttag = soup_title.find("title")
            if ttag:
                title_text = ttag.get_text(" ", strip=True)
        except Exception:
            title_text = ""
    title_lower = title_text.lower()
    
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
    reasons: List[str] = []
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
        "keine erfahrung noetig", "ohne erfahrung", "jetzt bewerben",
        "heute noch bewerben", "direkt bewerben"
    ])
    has_candidate_kw = any(k in t for k in CANDIDATE_KEYWORDS)
    has_ignore_kw = any(k in t for k in IGNORE_KEYWORDS)
    has_lowpay_or_prov = any(h in t_lower for h in LOW_PAY_HINT) or any(k in t_lower for k in [
        "nur provision", "provisionsbasis", "fixum + provision",
        "freelancer", "selbststaendig", "werkvertrag",
    ])
    agent_fingerprint = is_commercial_agent(t)
    if agent_fingerprint:
        score += 40
        reasons.append("agent_fingerprint")
    has_d2d = bool(D2D_HINT.search(t)) or any(k in t for k in ["door to door", "haustür", "haustuer", "kaltakquise"])
    has_callcenter = bool(CALLCENTER_HINT.search(t))
    has_b2c = bool(B2C_HINT.search(t))
    if any(h in t_lower for h in COMMISSION_HINT):
        score += 15
        reasons.append("commission_terms")
    industry_hits = sum(1 for k in INDUSTRY_HINTS if k in t)
    in_nrw = bool(CITY_RE.search(t)) or any(k in t for k in [" nrw ", " nordrhein-westfalen "])
    on_contact_like = any(h in u for h in ["kontakt", "impressum"])
    on_sales_path = any(h in u for h in ["callcenter", "telesales", "outbound", "vertrieb", "verkauf", "sales", "d2d", "door-to-door"])
    job_like = any(h in u for h in ["jobs.", "/jobs", "/karriere", "/stellen", "/bewerb"])
    portal_like = any(b in u for b in ["google.com", "indeed", "stepstone", "monster.", "xing.", "linkedin.", "glassdoor."])
    negative_pages = any(k in u for k in ["/datenschutz", "/privacy", "/agb", "/terms", "/bedingungen", "/newsletter", "/search", "/login", "/account", "/warenkorb", "/checkout", "/blog/", "/news/"])

    if "kleinanzeigen.de" in u:
        if "/s-stellengesuche/" in u:
            score += 30
        elif ("gesuch" in title_lower) or ("suche" in title_lower):
            score += 30
        elif ("gesuch" in t) or ("suche" in t):
            score += 30
        if "/s-stellengesuche/" in u and not has_ignore_kw:
            score = max(score, 50)

    if ("facebook.com" in u) and ("/groups" in u):
        score += 10

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
        score += 10
    if channel_count >= 3:
        score += 16
    if has_lowpay_or_prov:
        score -= 20
        reasons.append("low_pay_terms")
    if has_switch_now:
        score += 12
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
    
    candidate_signals = [sig.lower() for sig in CANDIDATE_ALWAYS_ALLOW]
    candidate_hits = sum(1 for sig in candidate_signals if sig in t_lower)
    if candidate_hits > 0:
        score += min(candidate_hits * 15, 45)
        reasons.append(f"candidate_signals_{candidate_hits}")
    
    if any(social in u for social in ["linkedin.com/in/", "xing.com/profile/"]):
        score += 20
        reasons.append("social_profile")
    
    if any(sig in t_lower for sig in ["freelancer", "verfügbar ab", "ab sofort verfügbar", "freiberuflich"]):
        score += 10
        reasons.append("availability_signal")
    
    if industry_hits:
        score += min(industry_hits * 4, 16)
    if in_nrw:
        score += 6
    if on_contact_like:
        score += 14
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

    if is_job_board:
        score -= 40
    if is_public_context:
        score -= 40
    
    if not _is_talent_hunt_mode() and is_hr_or_press:
        score -= 30
    
    if _is_talent_hunt_mode():
        if any(social in u for social in ["linkedin.com/in/", "xing.com/profile/"]):
            if "#opentowork" not in t_lower and "open to work" not in t_lower:
                score += 30
                reasons.append("active_profile_no_jobseek")
        
        if any(path in u for path in ["/team", "/mitarbeiter", "/unser-team", "/about", "/kontakt"]):
            score += 20
            reasons.append("team_page")
        
        exp_match = re.search(r'(\d+)\+?\s*jahre', t_lower)
        if exp_match:
            years = int(exp_match.group(1))
            exp_boost = min(years * 3, 15)
            score += exp_boost
            reasons.append(f"experience_{years}y")
        
        if any(kw in t_lower for kw in ["suche job", "stellengesuch", "arbeit gesucht", "auf jobsuche"]):
            score -= 10
            reasons.append("job_seeking_penalty")
        
        if any(kw in t_lower for kw in ["freiberuflich", "selbstständig", "handelsvertreter"]):
            score += 15
            reasons.append("independent_professional")

    return max(0, min(int(score), 100))


__all__ = [
    "compute_score",
    "etld1",
    "_dedup_run",
    "deduplicate_parallel_leads",
    "detect_recency",
    "is_commercial_agent",
]
