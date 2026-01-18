# -*- coding: utf-8 -*-
"""
Utility helper functions for text processing, domain extraction, etc.

This module provides common helper functions used across the scraper.
"""

import re
import urllib.parse
from typing import Optional
import tldextract


def etld1(host: str) -> str:
    """
    Extract the effective top-level domain (eTLD+1) from a hostname.
    
    Examples: 
        - www.example.co.uk -> example.co.uk
        - subdomain.test.com -> test.com
    
    Args:
        host: Hostname or domain
        
    Returns:
        Effective top-level domain (eTLD+1)
        
    Examples:
        >>> etld1("www.example.com")
        'example.com'
        >>> etld1("subdomain.test.co.uk")
        'test.co.uk'
    """
    if not host:
        return ""
    ex = tldextract.extract(host)
    dom = getattr(ex, "top_domain_under_public_suffix", None) or ex.registered_domain
    return dom.lower() if dom else host.lower()


def is_likely_human_name(text: str) -> bool:
    """
    Heuristic check if text looks like a human name.
    
    Checks:
    - 2-3 words
    - No digits
    - No company markers (GmbH, AG, Team, etc.)
    - No job ad markers (gesucht, karriere, etc.)
    
    Args:
        text: Name candidate
        
    Returns:
        True if likely a human name, False otherwise
        
    Examples:
        >>> is_likely_human_name("Max Mustermann")
        True
        >>> is_likely_human_name("Example GmbH")
        False
        >>> is_likely_human_name("Team Vertrieb")
        False
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


def looks_like_company(text: str) -> bool:
    """
    Check if text looks like a company name rather than a person.
    
    Args:
        text: Name candidate
        
    Returns:
        True if likely a company name, False otherwise
        
    Examples:
        >>> looks_like_company("Example GmbH")
        True
        >>> looks_like_company("Max Mustermann")
        False
        >>> looks_like_company("Team Vertrieb gesucht")
        True
    """
    if not text:
        return False
    tl = text.lower()
    company_tokens = [
        "gmbh", "ag", "kg", "ug", "ltd", "inc", "team", "firma", "unternehmen",
        "holding", "group", "gbr", "gesucht"
    ]
    return any(tok in tl for tok in company_tokens)


def has_nrw_signal(text: str) -> bool:
    """
    Check if text contains NRW (Nordrhein-Westfalen) location signals.
    
    Args:
        text: Text to check
        
    Returns:
        True if NRW signal found, False otherwise
        
    Examples:
        >>> has_nrw_signal("Job in Köln")
        True
        >>> has_nrw_signal("Position in München")
        False
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # NRW cities
    nrw_cities = [
        "köln", "düsseldorf", "dortmund", "essen", "duisburg",
        "bochum", "wuppertal", "bielefeld", "bonn", "münster",
        "gelsenkirchen", "mönchengladbach", "aachen", "krefeld", "oberhausen"
    ]
    
    # NRW keywords
    nrw_keywords = ["nrw", "nordrhein-westfalen", "nordrhein westfalen", "ruhrgebiet"]
    
    return any(city in text_lower for city in nrw_cities) or \
           any(kw in text_lower for kw in nrw_keywords)


def extract_company_name(title_text: str) -> str:
    """
    Extract company name from page title.
    
    Args:
        title_text: Page title
        
    Returns:
        Extracted company name or empty string
        
    Examples:
        >>> extract_company_name("Example Company | Careers")
        'Example Company'
        >>> extract_company_name("Job Opening - Example GmbH")
        'Job Opening'
    """
    if not title_text:
        return ""
    m = re.split(r'[-–|•·:]', title_text)
    base = m[0].strip() if m else title_text.strip()
    if re.search(r'\b(Job|Karriere|Kontakt|Impressum)\b', base, re.I):
        return ""
    return base[:120]


def detect_company_size(text: str) -> str:
    """
    Detect company size from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        "klein", "mittel", "groß", or "unbekannt"
        
    Examples:
        >>> detect_company_size("Familienunternehmen mit 5 Mitarbeitern")
        'klein'
        >>> detect_company_size("Konzern mit 500 Mitarbeitern")
        'groß'
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


def detect_recency(html: str) -> str:
    """
    Detect how recent a job posting/profile is.
    
    Args:
        html: HTML content to check
        
    Returns:
        "aktuell", "sofort", or "unbekannt"
        
    Examples:
        >>> detect_recency("Posted 2024-12-15")
        'aktuell'
        >>> detect_recency("ab sofort verfügbar")
        'sofort'
    """
    if re.search(r'\b(2025|2024)\-(0[1-9]|1[0-2])\-(0[1-9]|[12]\d|3[01])\b', html):
        return "aktuell"
    if re.search(r'\b(0?[1-9]|[12]\d|3[01])\.(0?[1-9]|1[0-2])\.(2024|2025)\b', html):
        return "aktuell"
    if re.search(r'\b(ab\s*sofort|sofort|zum\s*nächsten?\s*möglichen\s*termin)\b', html, re.I):
        return "sofort"
    return "unbekannt"


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text (multiple spaces -> single space).
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
        
    Examples:
        >>> normalize_whitespace("Hello    world\\n\\n\\ntest")
        'Hello world test'
    """
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def clean_url(url: str) -> str:
    """
    Clean and normalize URL (remove fragments, strip whitespace).
    
    Args:
        url: URL to clean
        
    Returns:
        Cleaned URL
        
    Examples:
        >>> clean_url("https://example.com/page#section  ")
        'https://example.com/page'
    """
    if not url:
        return ""
    
    # Remove fragments and whitespace
    url = url.strip()
    if '#' in url:
        url = url.split('#')[0]
    
    return url
