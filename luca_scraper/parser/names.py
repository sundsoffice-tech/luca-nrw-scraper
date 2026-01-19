"""Name validation and company detection functions."""

import re
from typing import Tuple


def is_likely_human_name(text: str) -> bool:
    """
    Heuristic check to determine if text looks like a human name.
    
    Returns True if:
        - 2-3 words
        - No digits
        - No company markers (GmbH, AG, etc.)
        - No job ad markers (Team, Karriere, etc.)
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
    Check if text contains company indicators.
    
    Returns True if text contains company tokens like GmbH, AG, Team, etc.
    """
    if not text:
        return False
    tl = text.lower()
    company_tokens = [
        "gmbh", "ag", "kg", "ug", "ltd", "inc", "team", "firma", "unternehmen",
        "holding", "group", "gbr", "gesucht"
    ]
    return any(tok in tl for tok in company_tokens)


def _validate_name_heuristic(name: str) -> Tuple[bool, int, str]:
    """
    Fallback heuristic for name validation without AI.
    
    Returns: (is_valid, confidence, reason)
    """
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
    
    # Must have at least 2 words
    words = name.split()
    if len(words) < 2:
        return False, 70, "Nur ein Wort"
    
    # No numbers
    if re.search(r'\d', name):
        return False, 85, "Enthält Zahlen"
    
    return True, 75, "Heuristik: wahrscheinlich echter Name"


def _looks_like_company_name(name: str) -> bool:
    """
    Check if name looks like a company name.
    
    Returns True for:
        - "GmbH", "AG", "KG", "UG" in name
        - "Team", "Vertrieb", "Sales" in name
        - Only one word
        - Contains numbers
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
