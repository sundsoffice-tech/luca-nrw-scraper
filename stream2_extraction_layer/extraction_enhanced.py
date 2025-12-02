from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

Text = str
Html = str


@dataclass
class ExtractionResult:
    name: Optional[str] = None
    rolle: Optional[str] = None
    email: Optional[str] = None
    extraction_method: Optional[str] = None
    confidence: float = 0.0


NAME_PATTERNS: List[Tuple[str, int]] = [
    (r'([A-ZÄÖÜß-ẞ][a-zäöüßẞ]+(?:\s+[A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+)+)\s*[\(,]', 1),
    (r'(?:Manager|Owner|Kontakt|Contact):\s*([A-ZÄÖÜß-ẞ][a-zäöüßẞ]+(?:\s+[A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+)+)', 1),
    (r'\b(Herr|Frau|Hr\.|Fr\.)\s+([A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+(?:\s+[A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+)?)', 2),
    (r'Ihr\s+Ansprechpartner:\s*([A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+(?:\s+[A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+)+)', 1),
    (r'Ansprechpartner\s+([A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+(?:\s+[A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+)+)', 1),
]

ROLE_KEYWORDS: Dict[str, List[str]] = {
    "vertriebsleiter": [
        "vertriebsleiter",
        "sales director",
        "vertriebsleitung",
        "head of sales",
        "verkaufsleiter",
    ],
    "aussendienst": [
        "außendienst",
        "aussendienst",
        "außendienstmitarbeiter",
        "aussendienstmitarbeiter",
        "feldvertrieb",
    ],
    "callcenter": [
        "call center",
        "callcenter",
        "telesales",
        "outbound",
        "inbound",
        "customer service",
    ],
    "recruiter": [
        "recruiter",
        "recruiting",
        "personalberater",
        "headhunter",
        "talent acquisition",
    ],
    "verkauf": [
        "verkäufer",
        "verkauf",
        "sales",
        "account manager",
        "kundenberater",
        "key account",
    ],
    "innendienst": [
        "innendienst",
        "inside sales",
        "vertriebsinnendienst",
        "sales support",
    ],
    "business_development": [
        "business development",
        "bdm",
        "partner manager",
        "growth manager",
    ],
}

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}\b", re.I)
BAD_LOCAL_PREFIXES = {"noreply", "no-reply", "donotreply", "do-not-reply", "privacy", "datenschutz"}
PORTAL_DOMAINS = {"stepstone.de", "indeed.com", "heyjobs.co", "arbeitsagentur.de", "softgarden.io", "join.com"}


def _deobfuscate(text: str) -> str:
    """
    Wandelt typische E-Mail-Obfuskationen in echte Adressen um.
    Beispiele:
    - max [at] firma [dot] de
    - max (at) firma (dot) de
    - max at firma dot de
    - max ät firma punkt de
    """
    t = text or ""

    t = re.sub(r"\s*\[\s*at\s*\]\s*", "@", t, flags=re.I)
    t = re.sub(r"\s*\(\s*at\s*\)\s*", "@", t, flags=re.I)
    t = re.sub(r"\s*\{\s*at\s*\}\s*", "@", t, flags=re.I)
    t = re.sub(r"\s+at\s+", "@", t, flags=re.I)
    t = re.sub(r"\s+ät\s+", "@", t, flags=re.I)

    t = re.sub(r"\s*\[\s*(dot|punkt)\s*\]\s*", ".", t, flags=re.I)
    t = re.sub(r"\s*\(\s*(dot|punkt)\s*\)\s*", ".", t, flags=re.I)
    t = re.sub(r"\s*\{\s*(dot|punkt)\s*\}\s*", ".", t, flags=re.I)
    t = re.sub(r"\s+(dot|punkt)\s+", ".", t, flags=re.I)

    return t


def _normalize_email(e: str) -> str:
    """
    Lowercase and normalize plus/dot variants where appropriate.
    """
    normalized = (e or "").strip().lower()
    local, _, domain = normalized.partition("@")
    if domain == "gmail.com":
        local = local.split("+", 1)[0].replace(".", "")
    return f"{local}@{domain}" if local and domain else normalized


def validate_name(name: Optional[str]) -> bool:
    """
    Rudimentary validation of extracted names to reduce false positives.
    """
    if not name:
        return False

    cleaned = re.sub(r"\s+", " ", name).strip()
    if not cleaned:
        return False

    lowered = cleaned.lower()
    generic_phrases = (
        "ihr ansprechpartner",
        "unsere ansprechpartner",
        "dein ansprechpartner",
    )
    if any(phrase in lowered for phrase in generic_phrases):
        return False

    words = cleaned.split(" ")
    if len(words) < 2 or len(words) > 4:
        return False

    blocked_suffixes = {"gmbh", "ug", "ag", "kg", "mbh", "inc", "co", "llc"}
    for word in words:
        if len(word) <= 1:
            return False
        if any(char.isdigit() for char in word):
            return False
        if word.lower() in blocked_suffixes:
            return False
        if not re.fullmatch(r"[A-ZÄÖÜß-ẞ][a-zäöüßẞ-]+", word):
            return False

    return True


def extract_name_enhanced(text: Text, html: Html = "") -> Optional[str]:
    """
    Extract a likely contact name from combined text/HTML content.
    """
    base_text = text or ""
    html_snippet = (html or "")[:1000]
    input_text = base_text
    if html_snippet:
        input_text = f"{base_text}\n{html_snippet}" if base_text else html_snippet

    for pattern, group_idx in NAME_PATTERNS:
        match = re.search(pattern, input_text)
        if not match:
            continue

        candidate = match.group(group_idx).strip()
        candidate = re.sub(r"\s+", " ", candidate)

        if validate_name(candidate):
            return candidate

    return None


def extract_role_with_context(text: Text, url: str, company_name: str = "") -> Tuple[Optional[str], float]:
    """
    Derive a role/title with contextual hints from the text and URL.
    """
    text_low = (text or "").lower()
    url_low = (url or "").lower()
    company_low = (company_name or "").lower()

    scores: Dict[str, int] = {}
    for role, keywords in ROLE_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            count += text_low.count(keyword)
        scores[role] = count

    if all(score == 0 for score in scores.values()):
        return None, 0.0

    best_role = max(scores, key=scores.get)
    base_confidence = min(scores[best_role] / 3.0, 1.0)

    if best_role == "recruiter" and "recruit" in url_low:
        base_confidence *= 1.2

    if best_role == "callcenter" and ("callcenter" in url_low or "callcenter" in company_low):
        base_confidence *= 1.2

    if best_role == "vertriebsleiter" and ("leitung" in company_low or "director" in company_low):
        base_confidence += 0.1

    confidence = max(0.0, min(base_confidence, 1.0))
    return best_role, confidence


def extract_email_robust(text: Text, html: Html = "", *, allow_generic: bool = True) -> Optional[str]:
    """
    Capture email addresses with tolerance for obfuscations and inline HTML.
    """
    raw = (text or "") + "\n" + (html or "")
    s = _deobfuscate(raw)

    best_email: Optional[str] = None
    best_score = -1

    for match in EMAIL_RE.finditer(s):
        norm = _normalize_email(match.group(0))
        local, _, domain = norm.partition("@")

        if not local or not domain:
            continue
        if local in BAD_LOCAL_PREFIXES:
            continue
        if domain in PORTAL_DOMAINS:
            continue
        if "." not in domain:
            continue

        score = 0
        if allow_generic and local in {"info", "kontakt", "contact", "office", "support"}:
            score = 1
        elif re.match(r"[a-z]+[._][a-z]+", local):
            score = 3
        else:
            score = 2

        if score > best_score:
            best_score = score
            best_email = norm

    return best_email


async def extract_with_multi_tier_fallback(html: Html, text: Text, url: str, company: str = "") -> Dict[str, Any]:
    """
    Orchestrate extraction of name, role, and email with fallbacks across tiers.
    """
    result: Dict[str, Any] = {
        "name": None,
        "rolle": None,
        "email": None,
        "extraction_method": None,
        "confidence": 0.0,
    }

    # Tier 1: Name via regex patterns
    try:
        name = extract_name_enhanced(text, html)
        if name:
            result["name"] = name
            result["extraction_method"] = "regex_name"
            result["confidence"] = max(result["confidence"], 0.4)
    except Exception:
        pass

    # Tier 2: Role via contextual keywords
    try:
        rolle, conf = extract_role_with_context(text, url, company)
        if rolle:
            result["rolle"] = rolle
            result["confidence"] = max(result["confidence"], conf)
    except Exception:
        pass

    # Tier 3: Email via robust extraction
    try:
        email = extract_email_robust(text, html)
        if email:
            result["email"] = email
            if result["extraction_method"] is None:
                result["extraction_method"] = "regex_email"
            result["confidence"] = max(result["confidence"], 0.5)
    except Exception:
        pass

    # Bonus boosts
    if result["name"] and result["email"]:
        result["confidence"] += 0.2
    if result["rolle"] and result["email"]:
        result["confidence"] += 0.1

    result["confidence"] = max(0.0, min(result["confidence"], 1.0))
    return result


__all__ = [
    "ExtractionResult",
    "validate_name",
    "extract_name_enhanced",
    "extract_role_with_context",
    "extract_email_robust",
    "extract_with_multi_tier_fallback",
]


if __name__ == "__main__":
    print("extraction_enhanced stub")
