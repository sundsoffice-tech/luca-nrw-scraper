"""Contact information extraction and validation functions."""

import re
import urllib.parse
from typing import Optional

import tldextract


# Constants
EMPLOYER_EMAIL_PREFIXES = {
    "jobs", "job", "karriere", "career", "recruiting", "recruit",
    "bewerbung", "application", "hr", "humanresources", "personal",
    "info", "kontakt", "contact", "service", "support", "office",
    "gf", "geschaeftsfuehrung", "management", "hello", "mail",
    "team", "admin", "datenschutz",
}

BAD_MAILBOXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "info", "kontakt", "contact", "office", "service", "support", "news", "presse",
    "bewerbung", "recruiting", "karriere", "jobs", "hr", "humanresources",
    "talent", "people", "personal", "datenschutz", "privacy"
}

PORTAL_DOMAINS = {
    "adecco.de",
    "arbeitsagentur.de",
    "glassdoor.de",
    "hays.de",
    "heyjobs.co",
    "heyjobs.de",
    "indeed.com",
    "jobware.de",
    "join.com",
    "kimeta.de",
    "kununu.com",
    "linkedin.com",
    "meinestadt.de",
    "monster.de",
    "randstad.de",
    "softgarden.io",
    "stellenanzeigen.de",
    "stepstone.de",
    "talents.studysmarter.de",
    "xing.com",
    "jobijoba.de",
    "jobijoba.com",
    "ok.ru",
    "patents.google.com",
    "tiktok.com",
}

GENERIC_BOXES = {"sales", "vertrieb", "verkauf", "marketing", "kundenservice", "hotline"}

_OBFUSCATION_PATTERNS = [
    (r'\s*(\[\s*at\s*\]|\(\s*at\s*\)|\{\s*at\s*\}|\s+at\s+|\s+ät\s+)\s*', '@'),
    (r'\s*(\[\s*dot\s*\]|\(\s*dot\s*\)|\{\s*dot\s*\}|\s+dot\s+|\s+punkt\s*|\s*\.\s*)\s*', '.'),
    (r'\s*(ät|@t)\s*', '@'),
]


def etld1(host: str) -> str:
    """Extract the effective top-level domain + 1 from a hostname."""
    if not host:
        return ""
    ex = tldextract.extract(host)
    dom = getattr(ex, "top_domain_under_public_suffix", None) or ex.registered_domain
    return dom.lower() if dom else host.lower()


def same_org_domain(page_url: str, email_domain: str) -> bool:
    """Check if page URL and email domain belong to the same organization."""
    try:
        host = urllib.parse.urlparse(page_url).netloc
        return etld1(host) == etld1(email_domain)
    except Exception:
        return False


def deobfuscate_text_for_emails(text: str) -> str:
    """
    Deobfuscate email addresses by replacing common obfuscation patterns.
    
    Examples:
        "name [at] domain [dot] com" -> "name@domain.com"
        "name (at) domain punkt de" -> "name@domain.de"
    """
    s = text
    for pat, rep in _OBFUSCATION_PATTERNS:
        s = re.sub(pat, rep, s, flags=re.I)
    return s


def email_quality(email: str, page_url: str) -> str:
    """
    Assess the quality of an email address for lead generation.
    
    Returns:
        "reject": Email should be rejected (employer/generic mailbox, portal domain)
        "weak": Weak quality (personal email on wrong domain)
        "personal": Personal email (likely individual)
        "team": Team/department mailbox
        "generic": Generic mailbox
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


def is_employer_email(email: str) -> bool:
    """
    Detect recruiter/company mailboxes by local-part prefixes.
    
    Returns True if email looks like it belongs to an employer/recruiter.
    """
    if not email or "@" not in email:
        return False
    local = email.split("@", 1)[0].lower()
    normalized_local = re.sub(r"[._\\-]+", "", local)
    return any(normalized_local.startswith(pref) for pref in EMPLOYER_EMAIL_PREFIXES)
