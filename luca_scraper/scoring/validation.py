# -*- coding: utf-8 -*-
"""
Lead Validation Module

This module contains functions for validating leads, checking for job postings,
and filtering out low-quality or irrelevant leads.
"""

import re
import os
import urllib.parse
from typing import Dict, Any, Tuple

# Try to import from luca_scraper modules
try:
    from luca_scraper.config import (
        NRW_REGIONS, CANDIDATE_ALWAYS_ALLOW, STRICT_JOB_AD_MARKERS,
        JOB_OFFER_SIGNALS, MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE,
        CANDIDATE_POSITIVE_SIGNALS, EMPLOYER_EMAIL_PREFIXES,
        PORTAL_DOMAINS, BAD_MAILBOXES, GENERIC_BOXES,
        DROP_MAILBOX_PREFIXES, DROP_PORTAL_DOMAINS, DROP_PORTAL_PATH_FRAGMENTS
    )
except ImportError:
    # Fallback definitions
    NRW_REGIONS = ["nrw", "nordrhein-westfalen", "düsseldorf", "köln"]
    CANDIDATE_ALWAYS_ALLOW = []
    STRICT_JOB_AD_MARKERS = [
        "(m/w/d)", "(w/m/d)", "(d/m/w)", "wir suchen", "stellenanzeige"
    ]
    JOB_OFFER_SIGNALS = ["(m/w/d)", "wir suchen", "stellenangebot"]
    MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE = 2
    CANDIDATE_POSITIVE_SIGNALS = [
        "suche job", "suche arbeit", "stellengesuch", "#opentowork"
    ]
    EMPLOYER_EMAIL_PREFIXES = {"jobs", "karriere", "hr", "bewerbung", "info"}
    PORTAL_DOMAINS = {"stepstone.de", "indeed.com", "linkedin.com", "xing.com"}
    BAD_MAILBOXES = {"noreply", "info", "kontakt", "support"}
    GENERIC_BOXES = {"sales", "vertrieb", "verkauf", "marketing"}
    DROP_MAILBOX_PREFIXES = {"info", "kontakt", "jobs", "karriere"}
    DROP_PORTAL_DOMAINS = {"stepstone.de", "indeed.com", "linkedin.com"}
    DROP_PORTAL_PATH_FRAGMENTS = ("linkedin.com/jobs", "xing.com/jobs")

# Try to import from scriptname.py
try:
    from scriptname import (
        log, NAME_RE, PHONE_RE, EMAIL_RE, WA_LINK_RE, WHATS_RE,
        WHATSAPP_RE, TELEGRAM_LINK_RE, IMPRINT_PATH_RE, CV_HINT_RE,
        ALLOW_PDF_NON_CV
    )
except ImportError:
    # Fallback implementations
    def log(level: str, msg: str, **ctx):
        """Fallback log function"""
        pass
    
    # Regex patterns
    NAME_RE = re.compile(r'\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+){0,2})\b')
    PHONE_RE = re.compile(r'(?:\+49|0049|0)\s?(?:\(?\d{2,5}\)?[\s\/\-]?)?\d(?:[\s\/\-]?\d){5,10}')
    EMAIL_RE = re.compile(r'\b(?!noreply|no-reply|donotreply)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}\b', re.I)
    WA_LINK_RE = re.compile(r'(?:https?://)?(?:wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+|chat\.whatsapp\.com/[A-Za-z0-9]+)', re.I)
    WHATS_RE = re.compile(r'(?:\+?\d{2,3}\s?)?(?:\(?0\)?\s?)?\d{2,4}[\s\-]?\d{3,}.*?(?:whatsapp|wa\.me|api\.whatsapp)', re.I)
    WHATSAPP_RE = re.compile(r'(?i)\b(WhatsApp|Whats\s*App)[:\s]*\+?\d[\d \-()]{6,}\b')
    TELEGRAM_LINK_RE = re.compile(r'(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_/-]+', re.I)
    IMPRINT_PATH_RE = re.compile(r"/(impressum|datenschutz|privacy|agb)(?:/|\\?|#|$)", re.I)
    CV_HINT_RE = re.compile(r"\b(lebenslauf|curriculum vitae|cv)\b", re.I)
    ALLOW_PDF_NON_CV = (os.getenv("ALLOW_PDF_NON_CV", "0") == "1")

# Try to import phone validation functions
try:
    from luca_scraper.extraction.phone import validate_phone, normalize_phone, is_mobile_number
except ImportError:
    # Fallback implementations
    def normalize_phone(p: str) -> str:
        """Fallback phone normalization"""
        if not p:
            return ""
        s = re.sub(r'[^\d+]', '', str(p))
        if s.startswith('0'):
            s = '+49' + s[1:]
        elif not s.startswith('+'):
            s = '+' + s
        return s
    
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Fallback phone validation"""
        if not phone:
            return False, "invalid"
        normalized = normalize_phone(phone)
        digits = re.sub(r'\D', '', normalized)
        if len(digits) < 10 or len(digits) > 15:
            return False, "invalid"
        if normalized.startswith('+49') and any(normalized.startswith(f'+4915{i}') or 
                                                  normalized.startswith(f'+4916{i}') or 
                                                  normalized.startswith(f'+4917{i}') 
                                                  for i in range(10)):
            return True, "mobile"
        return True, "landline"
    
    def is_mobile_number(phone: str) -> bool:
        """Fallback mobile number check"""
        if not phone:
            return False
        return any(phone.startswith(f'+4915{i}') or phone.startswith(f'+4916{i}') or 
                   phone.startswith(f'+4917{i}') for i in range(10))

# Try to import tldextract for domain comparison
try:
    import tldextract
    
    def etld1(host: str) -> str:
        """Extract eTLD+1 from hostname"""
        if not host:
            return ""
        ex = tldextract.extract(host)
        dom = getattr(ex, "top_domain_under_public_suffix", None) or ex.registered_domain
        return dom.lower() if dom else host.lower()
except ImportError:
    def etld1(host: str) -> str:
        """Fallback eTLD+1 extraction"""
        if not host:
            return ""
        parts = host.lower().split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return host.lower()


def has_nrw_signal(text: str) -> bool:
    """
    Prüft ob Text NRW-Bezug hat.
    
    Args:
        text: Text content to check
        
    Returns:
        True if NRW signal found
    """
    text_lower = text.lower()
    return any(region in text_lower for region in NRW_REGIONS)


def is_candidate_seeking_job(text: str = "", title: str = "", url: str = "") -> bool:
    """
    Prüft ob es sich um einen jobsuchenden Kandidaten handelt (darf NICHT geblockt werden!).
    
    Args:
        text: Text content to analyze
        title: Title/heading text
        url: URL (optional, not currently used but part of signature)
        
    Returns:
        True if candidate seeking job detected
    """
    text_lower = (text + " " + title).lower()
    
    # ERST prüfen: Ist es ein KANDIDAT der einen Job SUCHT?
    for signal in CANDIDATE_POSITIVE_SIGNALS:
        if signal in text_lower:
            return True  # Das ist ein Kandidat! Nicht blocken!
    
    return False


def is_job_advertisement(text: str = "", title: str = "", snippet: str = "") -> bool:
    """
    Return True if content/title/snippet contains strict job-ad markers (company hiring).
    
    Args:
        text: Text content to analyze
        title: Title/heading text
        snippet: Snippet/summary text
        
    Returns:
        True if job advertisement detected
    """
    combined = " ".join([(text or ""), (title or ""), (snippet or "")]).lower()
    
    # FIRST: Check if this is a CANDIDATE seeking a job - NEVER block candidates!
    if is_candidate_seeking_job(text, title):
        # If candidate signal is found, only mark as job ad if there are MULTIPLE strong job offer signals
        job_offer_count = sum(1 for offer in JOB_OFFER_SIGNALS if offer in combined)
        if job_offer_count < MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE:
            return False  # It's a candidate, not a job ad!
    
    # THEN: Check for job offer signals
    return any(m in combined for m in STRICT_JOB_AD_MARKERS)


def _looks_like_company_name(name: str) -> bool:
    """
    Prüft ob Name wie eine Firma aussieht.
    
    Returns True für:
        - "GmbH", "AG", "KG", "UG" im Namen
        - "Team", "Vertrieb", "Sales" im Namen
        - Nur ein Wort
        - Enthält Zahlen
        
    Args:
        name: Name to check
        
    Returns:
        True if looks like a company name
    """
    if not name:
        return True
    
    company_indicators = [
        "gmbh", "ag", "kg", "ug", "ltd", "inc", 
        "team", "vertrieb", "sales", "group", "holding",
        "firma", "unternehmen", "company"
    ]
    name_lower = name.lower()
    
    # Check for company indicators
    if any(ind in name_lower for ind in company_indicators):
        return True
    
    # Check for single word (not a full name)
    if len(name.split()) < 2:
        return True
    
    # Check for numbers
    if re.search(r'\d', name):
        return True
    
    return False


def is_likely_human_name(text: str) -> bool:
    """
    Heuristic: 2-3 words, no digits, no company/ad markers.
    
    Args:
        text: Name text to check
        
    Returns:
        True if likely a human name
    """
    if not text:
        return False
    s = re.sub(r"\s+", " ", text).strip(" ,;|")
    if not s:
        return False
    lower = s.lower()
    corporate_tokens = (
        "gmbh", "ag", "kg", "ug", "co. kg", "inc", "ltd", "gbr",
        "unternehmen", "firma", "company", "holding",
    )
    ad_tokens = (
        "team", "karriere", "job", "stellenanzeige", "gesucht", "wir suchen",
        "abteilung",
    )
    if any(tok in lower for tok in corporate_tokens + ad_tokens):
        return False
    if re.search(r"\d", s):
        return False
    words = [w for w in re.split(r"[\s\-\|_]+", s) if w]
    if not (2 <= len(words) <= 3):
        return False
    if any(len(w) == 1 for w in words):
        return False
    return True


def same_org_domain(page_url: str, email_domain: str) -> bool:
    """
    Check if page URL and email domain belong to same organization.
    
    Args:
        page_url: URL of the page
        email_domain: Domain part of email address
        
    Returns:
        True if same organization domain
    """
    try:
        host = urllib.parse.urlparse(page_url).netloc
        return etld1(host) == etld1(email_domain)
    except Exception:
        return False


def email_quality(email: str, page_url: str) -> str:
    """
    Assess email quality for lead validation.
    
    Args:
        email: Email address to check
        page_url: URL of the page where email was found
        
    Returns:
        Quality category: "reject", "weak", "personal", "team", or "generic"
    """
    if not email:
        return "reject"
    low = email.strip().lower()
    local, _, domain = low.partition("@")
    if local in EMPLOYER_EMAIL_PREFIXES:
        return "reject"
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


def _matches_hostlist(host: str, blocked: set) -> bool:
    """
    Check if host matches any in blocked list.
    
    Args:
        host: Hostname to check
        blocked: Set of blocked hostnames
        
    Returns:
        True if host is in blocked list
    """
    h = (host or "").lower()
    if h.startswith("www."):
        h = h[4:]
    return any(h == d or h.endswith("." + d) for d in (b.lower() for b in blocked))


def should_drop_lead(lead: Dict[str, Any], page_url: str, text: str = "", title: str = "") -> Tuple[bool, str]:
    """
    Main validation function to determine if a lead should be dropped.
    
    This function performs comprehensive validation including:
    - Job posting detection (never save job postings as leads)
    - Phone number validation (must have valid mobile number)
    - Email validation (check for generic/portal emails)
    - Portal/host filtering
    - Impressum page validation
    - PDF file validation
    
    Args:
        lead: Lead dictionary with contact information
        page_url: URL where lead was found
        text: Full text content (optional)
        title: Page title (optional)
        
    Returns:
        Tuple of (should_drop: bool, reason: str)
    """
    email = (lead.get("email") or "").strip().lower()
    url_lower = (page_url or "").lower()
    text_lower = (text or "").lower()
    title_lower = (title or "").lower()
    host = (urllib.parse.urlparse(page_url or "").netloc or "").lower()
    person_blob = " ".join([lead.get("name", ""), lead.get("rolle", "")]).strip()

    def _drop(reason: str) -> Tuple[bool, str]:
        log("debug", "lead dropped", reason=reason, url=page_url)
        return True, reason
    
    # CRITICAL: Check for job postings first - NEVER save as lead
    if is_job_advertisement(text=text, title=title, snippet=lead.get("opening_line", "")):
        return _drop("job_posting")

    # Telefonnummer Pflicht - strict validation
    phone = (lead.get("telefon") or "").strip()
    if not phone:
        return _drop("no_phone")
    
    is_valid, phone_type = validate_phone(phone)
    if not is_valid:
        return _drop("no_phone")
    
    # STRICT: Only mobile numbers allowed
    # Normalize phone first before checking if it's mobile
    normalized_phone = normalize_phone(phone)
    if not is_mobile_number(normalized_phone):
        return _drop("not_mobile_number")

    if email:
        local, _, domain = email.partition("@")
        if local in DROP_MAILBOX_PREFIXES:
            return _drop("generic_mailbox")
        if domain and _matches_hostlist(domain, DROP_PORTAL_DOMAINS):
            return _drop("portal_domain")

    host_is_portal = _matches_hostlist(host, DROP_PORTAL_DOMAINS)
    if host_is_portal and host in {"linkedin.com", "www.linkedin.com", "xing.com", "www.xing.com"}:
        if "/jobs" not in url_lower:
            host_is_portal = False
    if host_is_portal or any(frag in url_lower for frag in DROP_PORTAL_PATH_FRAGMENTS):
        return _drop("portal_host")

    if IMPRINT_PATH_RE.search(url_lower):
        has_phone = bool(lead.get("telefon") or PHONE_RE.search(text_lower))
        has_messenger = bool(
            WA_LINK_RE.search(text_lower) or WHATS_RE.search(text_lower) or
            WHATSAPP_RE.search(text_lower) or TELEGRAM_LINK_RE.search(text_lower)
        )
        has_email = bool(lead.get("email") or EMAIL_RE.search(text or ""))
        has_person = (
            is_likely_human_name(person_blob) or
            len(person_blob.split()) >= 2 or
            bool(NAME_RE.search(text or ""))
        )
        if not (has_person or has_phone or has_messenger):
            if not has_email:
                return _drop("impressum_no_contact")

    if url_lower.endswith(".pdf"):
        hint_blob = " ".join([url_lower, person_blob, title_lower])
        has_cv_hint = bool(
            CV_HINT_RE.search(text_lower) or
            CV_HINT_RE.search(hint_blob) or
            CV_HINT_RE.search(title_lower)
        )
        if not has_cv_hint and not ALLOW_PDF_NON_CV:
            return _drop("pdf_without_cv_hint")

    return False, ""
