# -*- coding: utf-8 -*-
"""
Lead Scoring Module

This module contains functions for scoring leads based on various signals
such as contact methods, industry, location, and content quality.
"""

import re
import os
from typing import List, Tuple, Optional, Dict, Any
from bs4 import BeautifulSoup

# Try to import from luca_scraper modules
try:
    from luca_scraper.config import (
        NRW_REGIONS, HIDDEN_GEMS_PATTERNS, CANDIDATE_ALWAYS_ALLOW,
        INDUSTRY_PATTERNS
    )
except ImportError:
    # Fallback definitions
    NRW_REGIONS = [
        "nrw", "nordrhein-westfalen", "düsseldorf", "köln", "dortmund",
        "essen", "bochum", "ruhrgebiet"
    ]
    HIDDEN_GEMS_PATTERNS = {}
    CANDIDATE_ALWAYS_ALLOW = []
    INDUSTRY_PATTERNS = {}

# Try to import from scriptname.py (main script) for constants
try:
    from scriptname import (
        log, MOBILE_RE, PHONE_RE, WHATSAPP_PHRASE_RE, WA_LINK_RE,
        TELEGRAM_LINK_RE, CITY_RE, CANDIDATE_KEYWORDS, IGNORE_KEYWORDS,
        LOW_PAY_HINT, D2D_HINT, CALLCENTER_HINT, B2C_HINT, COMMISSION_HINT,
        INDUSTRY_HINTS, AGENT_FINGERPRINTS, JOBSEEKER_RE, RECRUITER_RE,
        PROVISION_HINT, WHATSAPP_RE, WHATSAPP_INLINE, WHATS_RE
    )
except ImportError:
    # Fallback implementations and definitions
    def log(level: str, msg: str, **ctx):
        """Fallback log function"""
        pass
    
    # Regex patterns
    PHONE_RE = re.compile(r'(?:\+49|0049|0)\s?(?:\(?\d{2,5}\)?[\s\/\-]?)?\d(?:[\s\/\-]?\d){5,10}')
    MOBILE_RE = re.compile(r'(?:\+49|0049|0)\s*1[5-7]\d(?:[\s\/\-]?\d){6,10}')
    D2D_HINT = re.compile(r'\b(Door[-\s]?to[-\s]?door|Haustür|Kaltakquise|D2D)\b', re.I)
    CALLCENTER_HINT = re.compile(r'\b(Call\s*Center|Telesales|Outbound|Inhouse-?Sales)\b', re.I)
    B2C_HINT = re.compile(
        r'\b(?:B2C|Privatkunden|Haushalte|Endkunden|Privatperson(?:en)?|'
        r'verschuld\w*|schuldenhilfe|schuldnerberatung|schuldner|'
        r'inkasso(?:[-\s]?f(?:ä|ae)lle?)?)\b',
        re.I,
    )
    WA_LINK_RE = re.compile(r'(?:https?://)?(?:wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+|chat\.whatsapp\.com/[A-Za-z0-9]+)', re.I)
    WHATSAPP_PHRASE_RE = re.compile(
        r'(?i)(meldet\s+euch\s+per\s+whatsapp|schreib(?:t)?\s+mir\s+(?:per|bei)\s+whatsapp|per\s+whatsapp\s+melden)'
    )
    TELEGRAM_LINK_RE = re.compile(r'(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_/-]+', re.I)
    CITY_RE = re.compile(r'\b(NRW|Nordrhein[-\s]?Westfalen|Düsseldorf|Köln|Essen|Dortmund|Mönchengladbach|Bochum|Wuppertal|Bonn)\b', re.I)
    JOBSEEKER_RE = re.compile(r'\b(jobsuche|stellensuche|arbeitslos|lebenslauf|bewerb(ung)?|cv|portfolio|offen\s*f(?:ür|uer)\s*neues)\b', re.I)
    RECRUITER_RE = re.compile(r'\b(recruit(er|ing)?|hr|human\s*resources|personalvermittlung|headhunter|wir\s*suchen|join\s*our\s*team)\b', re.I)
    PROVISION_HINT = re.compile(r'\b(Provisionsbasis|nur\s*Provision|hohe\s*Provision(en)?|Leistungsprovision)\b', re.I)
    WHATSAPP_RE = re.compile(r'(?i)\b(WhatsApp|Whats\s*App)[:\s]*\+?\d[\d \-()]{6,}\b')
    WHATSAPP_INLINE = re.compile(r'\+?\d[\d ()\-]{6,}\s*(?:WhatsApp|WA)', re.I)
    WHATS_RE = re.compile(r'(?:\+?\d{2,3}\s?)?(?:\(?0\)?\s?)?\d{2,4}[\s\-]?\d{3,}.*?(?:whatsapp|wa\.me|api\.whatsapp)', re.I)
    
    # Constants
    CANDIDATE_KEYWORDS = [
        "suche job", "biete mich an", "open to work",
        "neue herausforderung", "gesuch", "lebenslauf",
    ]
    
    IGNORE_KEYWORDS = [
        "wir suchen", "stellenanzeige", "gmbh",
        "hr manager", "karriere bei uns",
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


def _is_talent_hunt_mode() -> bool:
    """Check if we're in talent_hunt mode - looking for active sales professionals."""
    industry = str(os.getenv("INDUSTRY", "")).lower()
    return "talent_hunt" in industry


def is_commercial_agent(text: str) -> bool:
    """
    Detects legal/professional Handelsvertreter fingerprints in text.
    
    Args:
        text: Text content to analyze
        
    Returns:
        True if commercial agent fingerprints detected
    """
    if not text:
        return False
    low = text.lower()
    return any(fp in low for fp in AGENT_FINGERPRINTS)


def detect_company_size(text: str) -> str:
    """
    Detect company size from text.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Company size category: "klein", "mittel", "groß", or "unbekannt"
    """
    patterns = {
        "klein":  r'\b(1-10|klein|Inhaber|Familienunternehmen)\b',
        "mittel": r'\b(11-50|50-250|Mittelstand|[1-9]\d?\s*Mitarbeiter)\b',
        "groß":   r'\b(250\+|Konzern|Tochtergesellschaft|international|[2-9]\d{2,}\s*Mitarbeiter)\b'
    }
    for size, pat in patterns.items():
        if re.search(pat, text, re.I):
            return size
    return "unbekannt"


def detect_industry(text: str) -> str:
    """
    Detect industry from text.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Industry category or "unbekannt"
    """
    for k, pat in INDUSTRY_PATTERNS.items():
        if re.search(pat, text, re.I):
            return k
    return "unbekannt"


def detect_recency(html: str) -> str:
    """
    Detect how recent the posting is.
    
    Args:
        html: HTML content to analyze
        
    Returns:
        Recency category: "aktuell", "sofort", or "unbekannt"
    """
    if re.search(r'\b(2025|2024)\-(0[1-9]|1[0-2])\-(0[1-9]|[12]\d|3[01])\b', html):
        return "aktuell"
    if re.search(r'\b(0?[1-9]|[12]\d|3[01])\.(0?[1-9]|1[0-2])\.(2024|2025)\b', html):
        return "aktuell"
    if re.search(r'\b(ab\s*sofort|sofort|zum\s*nächsten?\s*möglichen\s*termin)\b', html, re.I):
        return "sofort"
    return "unbekannt"


def estimate_hiring_volume(text: str) -> str:
    """
    Estimate hiring volume from text.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Volume estimate: "hoch", "mittel", or "niedrig"
    """
    if re.search(r'\b(mehrere|Teams|Team-?Erweiterung|Verstärkung|wir wachsen)\b', text, re.I):
        return "hoch"
    if len(re.findall(r'\b(Stelle|Stellen|Job)\b', text, re.I)) > 1:
        return "mittel"
    return "niedrig"


def detect_hidden_gem(text: str, url: str = "") -> Tuple[Optional[str], int, str]:
    """
    Erkennt Quereinsteiger mit Vertriebspotenzial.
    
    Args:
        text: Text content to analyze
        url: URL of the content (optional)
        
    Returns:
        Tuple of (gem_type, confidence, reason) or (None, 0, "")
    """
    text_lower = text.lower()
    
    for gem_type, pattern in HIDDEN_GEMS_PATTERNS.items():
        keyword_hits = sum(1 for k in pattern["keywords"] if k in text_lower)
        positive_hits = sum(1 for p in pattern["positive"] if p in text_lower)
        
        if keyword_hits >= 1 and positive_hits >= 1:
            confidence = min(95, 50 + keyword_hits * 15 + positive_hits * 10)
            return gem_type, confidence, pattern["reason"]
    
    return None, 0, ""


def analyze_wir_suchen_context(text: str, url: str = "") -> Tuple[str, str]:
    """
    Analysiert "wir suchen" im Kontext.
    
    Args:
        text: Text content to analyze
        url: URL of the content (optional)
        
    Returns:
        Tuple of (classification, reason) where classification is:
        - "job_ad" = Stellenanzeige (BLOCK)
        - "candidate" = Kandidat sucht (ALLOW)
        - "business_inquiry" = Geschäftsanfrage (ALLOW mit Prüfung)
        - "unclear" = Unklar (weitere Prüfung)
    """
    text_lower = text.lower()
    
    wir_suchen_matches = list(re.finditer(r'wir\s+suchen', text_lower))
    
    if not wir_suchen_matches:
        return "unclear", "Kein 'wir suchen' gefunden"
    
    for match in wir_suchen_matches:
        start = max(0, match.start() - 200)
        end = min(len(text_lower), match.end() + 300)
        context = text_lower[start:end]
        
        # === STELLENANZEIGE (BLOCK) ===
        job_ad_signals = [
            "(m/w/d)", "(w/m/d)", "(d/m/w)",
            "zum nächstmöglichen", "zur verstärkung",
            "für unser team", "ihre aufgaben", "ihr profil",
            "wir bieten", "benefits", "festanstellung",
            "vollzeit", "teilzeit", "homeoffice möglich",
            "bewerbung an", "bewerben sie sich",
        ]
        job_ad_count = sum(1 for signal in job_ad_signals if signal in context)
        
        if job_ad_count >= 2:
            return "job_ad", f"Stellenanzeige ({job_ad_count} Signale)"
        
        # === KANDIDAT SUCHT (ALLOW) ===
        candidate_signals = [
            "wir suchen ein unternehmen", "wir suchen eine firma",
            "wir suchen aufträge", "wir suchen neue kunden",
            "wir suchen vertretungen", "wir suchen partner",
            "wir suchen projekte", "ich und mein team suchen",
            "wir als handelsvertretung suchen",
            "wir als freelancer suchen",
        ]
        for signal in candidate_signals:
            if signal in context:
                return "candidate", f"Kandidat/Team sucht: '{signal}'"
        
        # === EINZELPERSON (Pluralis Majestatis) ===
        solo_signals = [
            "biete meine dienste", "meine erfahrung",
            "mein profil", "ich bin", "verfügbar ab",
            "kontaktieren sie mich",
        ]
        for signal in solo_signals:
            if signal in context:
                return "candidate", f"Einzelperson ('{signal}' im Kontext)"
        
        # === BUSINESS INQUIRY ===
        business_signals = [
            "suchen lieferanten", "suchen hersteller",
            "suchen dienstleister", "suchen zusammenarbeit",
        ]
        for signal in business_signals:
            if signal in context:
                return "business_inquiry", f"Geschäftsanfrage: '{signal}'"
    
    return "unclear", "Kontext nicht eindeutig"


def tags_from(text: str) -> str:
    """
    Extract tags from text based on patterns.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Comma-separated string of tags
    """
    t = []
    if JOBSEEKER_RE.search(text):
        t.append("jobseeker")
    elif RECRUITER_RE.search(text):
        t.append("recruiter")

    if CALLCENTER_HINT.search(text):
        t.append("callcenter")
    if D2D_HINT.search(text):
        t.append("d2d")
    if PROVISION_HINT.search(text):
        t.append("provision")
    if B2C_HINT.search(text):
        t.append("b2c")
    if CITY_RE.search(text):
        t.append("nrw")
    if WHATSAPP_RE.search(text) or WHATSAPP_INLINE.search(text) or WHATS_RE.search(text) \
       or WHATSAPP_PHRASE_RE.search(text) or WA_LINK_RE.search(text):
        t.append("whatsapp")
    if TELEGRAM_LINK_RE.search(text) or re.search(r'\btelegram\b', text, re.I):
        t.append("telegram")
    for k, pat in INDUSTRY_PATTERNS.items():
        if re.search(pat, text, re.I):
            t.append(k)
    return ",".join(dict.fromkeys(t))


def compute_score(text: str, url: str, html: str = "") -> int:
    """
    Compute a quality score for a lead based on various signals.
    
    This function analyzes text, URL, and HTML content to score a lead from 0-100.
    Higher scores indicate better quality leads with more valuable contact information
    and relevant signals.
    
    Args:
        text: Text content to analyze
        url: URL of the source
        html: HTML content (optional)
        
    Returns:
        Score from 0-100
    """
    # Normalize text for consistent processing
    t_lower = (text or "").lower()
    t = t_lower  # Use lowercased text for all checks
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
    # Check for low pay / provision hints
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
    # Commission / high-value signals
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
        score += 10  # leichte Bevorzugung für Facebook-Gruppen

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
    
    # NEW: Candidate-focused scoring boosts
    candidate_signals = [sig.lower() for sig in CANDIDATE_ALWAYS_ALLOW]
    candidate_hits = sum(1 for sig in candidate_signals if sig in t_lower)
    if candidate_hits > 0:
        score += min(candidate_hits * 15, 45)  # Up to +45 for strong candidate signals
        reasons.append(f"candidate_signals_{candidate_hits}")
    
    # Social media profile boost
    if any(social in u for social in ["linkedin.com/in/", "xing.com/profile/"]):
        score += 20
        reasons.append("social_profile")
    
    # Freelancer/Available signals
    if any(sig in t_lower for sig in ["freelancer", "verfügbar ab", "ab sofort verfügbar", "freiberuflich"]):
        score += 10
        reasons.append("availability_signal")
    
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
    
    # NEW: In talent_hunt mode, HR contacts are valuable (not penalized)
    # In other modes, penalize HR/press contacts
    if not _is_talent_hunt_mode() and is_hr_or_press:
        score -= 30
    
    # NEW: Talent Hunt Mode Boosts (active salespeople, not job seekers)
    if _is_talent_hunt_mode():
        # Boost for LinkedIn/Xing profiles WITHOUT #opentowork
        if any(social in u for social in ["linkedin.com/in/", "xing.com/profile/"]):
            if "#opentowork" not in t_lower and "open to work" not in t_lower:
                score += 30
                reasons.append("active_profile_no_jobseek")
        
        # Boost for team page URLs
        if any(path in u for path in ["/team", "/mitarbeiter", "/unser-team", "/about", "/kontakt"]):
            score += 20
            reasons.append("team_page")
        
        # Boost for years of experience (active professionals)
        exp_match = re.search(r'(\d+)\+?\s*jahre', t_lower)
        if exp_match:
            years = int(exp_match.group(1))
            exp_boost = min(years * 3, 15)  # Max +15 for experience
            score += exp_boost
            reasons.append(f"experience_{years}y")
        
        # Remove boost for job seeking signals in talent hunt
        if any(kw in t_lower for kw in ["suche job", "stellengesuch", "arbeit gesucht", "auf jobsuche"]):
            score -= 10  # Actually penalize job seeking in talent hunt mode
            reasons.append("job_seeking_penalty")
        
        # Boost for freelancer/independent profiles
        if any(kw in t_lower for kw in ["freiberuflich", "selbstständig", "handelsvertreter"]):
            score += 15
            reasons.append("independent_professional")

    return max(0, min(int(score), 100))
