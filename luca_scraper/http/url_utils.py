"""
URL utilities for filtering, normalizing, and prioritizing URLs.
"""

import re
import urllib.parse
from typing import Any, Dict, List, Union


# Deny domains and hosts
DENY_DOMAINS = {
    "stepstone.de", "indeed.com", "monster.de", "arbeitsagentur.de",
    "xing.com/jobs", "linkedin.com/jobs", "meinestadt.de", "kimeta.de",
    "jobware.de", "stellenanzeigen.de", "absolventa.de", "glassdoor.de",
    "kununu.com", "azubiyo.de", "ausbildung.de", "gehalt.de", "lehrstellen-radar.de",
    "wikipedia.org", "youtube.com", "amazon.de", "ebay.de",
    "heyjobs.de", "heyjobs.co", "softgarden.io", "jobijoba.de", "jobijoba.com",
    "ok.ru", "tiktok.com", "patents.google.com",
    "stellenonline.de", "stellenmarkt.de", "nadann.de", "freshplaza.de", "kikxxl.de",
}

SOCIAL_HOSTS = {
    "linkedin.com", "www.linkedin.com", "de.linkedin.com",
    "xing.com", "www.xing.com",
    "facebook.com", "www.facebook.com",
    "instagram.com", "www.instagram.com",
    "twitter.com", "x.com",
    "tiktok.com",
}

NEG_PATH_HINTS = (
    "/jobs/", "/job/", "/stellenangebot/", "/company/", "/companies/",
    "/unternehmen/", "/business/", "/school/", "/university/",
    "/pulse/", "/article/", "/learning/", "/groups/", "/feed/",
    "/events/", "/search/", "/salary/", "/gehalt/",
)

ALLOW_PATH_HINTS = (
    "/profil", "/profile", "/cv", "/lebenslauf", "/resume",
    "/user", "/nutzer", "/candidate", "/bewerber",
    "/in/", "/pub/", "/p/",  # Social media profile markers
)


def _host_from(url: str) -> str:
    """
    Extract hostname from URL.
    
    Args:
        url: URL to extract hostname from
        
    Returns:
        Hostname (lowercased) or empty string on error
    """
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""


def _is_talent_hunt_mode() -> bool:
    """Check if talent hunt mode is active."""
    import os
    return os.getenv("TALENT_HUNT_MODE", "0") == "1"


def is_denied(url: str) -> bool:
    """
    Check if URL should be denied based on domain and host rules.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL should be denied
    """
    p = urllib.parse.urlparse(url)
    host = (p.netloc or "").lower()
    
    # Normalize: strip www./m. prefixes
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("m."):
        host = host[2:]

    # In talent_hunt mode, allow social profiles and team pages
    if _is_talent_hunt_mode():
        url_lower = url.lower()
        talent_hunt_allowed_patterns = [
            "linkedin.com/in/",
            "xing.com/profile/",
            "xing.com/profiles/",
            "/team",
            "/unser-team",
            "/mitarbeiter",
            "/ansprechpartner",
        ]
        talent_hunt_allowed_hosts = [
            "cdh.de",
            "ihk.de", 
            "freelancermap.de",
            "gulp.de",
            "freelance.de",
            "twago.de",
        ]
        
        # Check URL patterns
        if any(pattern in url_lower for pattern in talent_hunt_allowed_patterns):
            return False
        
        # Check special hosts for talent_hunt
        for allowed_host in talent_hunt_allowed_hosts:
            if host == allowed_host or host.endswith("." + allowed_host):
                return False

    if host in SOCIAL_HOSTS:
        return False

    # Hard domain blocklist
    for d in DENY_DOMAINS:
        d = d.lower()
        if host == d or host.endswith("." + d):
            return True

    # Existing heuristics
    if host.startswith(("uni-", "cdu-", "stadtwerke-")):
        return True
    if host in {"ruhr-uni-bochum.de"}:
        return True

    # NRW noise — IHK/HWK/Bildung (but not in talent_hunt mode)
    if not _is_talent_hunt_mode():
        if host.endswith(".ihk.de") or host.startswith(("ihk-", "hwk-")):
            return True
        if any(k in host for k in (
            "schule", "berufskolleg", "weiterbildung", "bildungszentrum",
            "akademie", "bbw-", "bfw-", "leb-"
        )):
            return True

    # Job portals/aggregators
    PORTAL_HOST_HINTS = (
        "stepstone", "indeed", "monster", "jobware", "stellenanzeigen",
        "jobvector", "yourfirm", "metajob", "stellenangebotevertrieb",
        "jobanzeiger", "jobboerse.arbeitsagentur", "meinestadt"
    )
    if any(h in host for h in PORTAL_HOST_HINTS):
        return True

    return False


def path_ok(url: str) -> bool:
    """
    Check if URL path is acceptable.
    
    Args:
        url: URL to check
        
    Returns:
        True if path is acceptable
    """
    p = urllib.parse.urlparse(url)
    path = (p.path or "").lower()
    q = (p.query or "").lower()
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
    """
    Normalize URL for deduplication.
    
    Removes tracking parameters, normalizes query strings, and removes fragments.
    
    Args:
        u: URL to normalize
        
    Returns:
        Normalized URL
    """
    try:
        pu = urllib.parse.urlparse(u)

        # Normalize query - remove tracking & pagination params
        q = urllib.parse.parse_qsl(pu.query, keep_blank_values=False)
        q = [
            (k, v) for (k, v) in q
            if not (
                k.lower().startswith(("utm_",))
                or k.lower() in {"gclid", "fbclid", "mc_eid", "page"}
            )
        ]
        new_q = urllib.parse.urlencode(q, doseq=True)

        # Normalize path: remove fragment, strip trailing slash
        path = pu.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        pu = pu._replace(query=new_q, fragment="", path=path)
        return urllib.parse.urlunparse(pu)
    except Exception:
        return u


UrlLike = Union[str, Dict[str, Any]]


def _extract_url(item: UrlLike) -> str:
    """
    Extract URL from item (string or dict).
    
    Args:
        item: URL string or dict with 'url' or 'link' key
        
    Returns:
        URL string
    """
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("url") or item.get("link", "")
    return ""


def prioritize_urls(urls: List[str]) -> List[str]:
    """
    Prioritize contact pages over jobs/privacy/login pages.
    
    Uses additive scoring to rank URLs by relevance:
    - High priority: /kontakt, /impressum, /team
    - Boosted: /karriere, /jobs (for jobseeker signals)
    - Penalized: /datenschutz, /login, /cart, /blog
    
    Args:
        urls: List of URLs to prioritize
        
    Returns:
        Sorted list of URLs (highest priority first)
    """
    PRIORITY_PATTERNS = [
        (r'/kontakt(?:/|$)',                    +40),
        (r'/kontaktformular(?:/|$)',            +32),
        (r'/impressum(?:/|$)',                  +35),
        (r'/team(?:/|$)',                       +12),
        (r'/ueber-uns|/über-uns|/unternehmen',  +10),
        # Jobseeker signals boost
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

        # Positive patterns: additive scoring
        for pat, pts in PRIORITY_PATTERNS:
            if re.search(pat, low, re.I):
                s += pts

        # Negative patterns: additive penalties
        for pat, pts in PENALTY_PATTERNS:
            if re.search(pat, low, re.I):
                s += pts

        # Query hints
        if re.search(r'(\?|#).*(kontakt|impressum)', low, re.I):
            s += 12

        # Path length / depth: prefer short, flat paths
        depth = max(0, path.count('/') - 1)
        s += max(0, 20 - len(path))
        s += max(0, 10 - 5*depth)

        # Noise filter / pagination / fragments
        if len(u) > 220:
            s -= 40
        if re.search(r'(\?|&)page=\d{1,3}\b', low):
            s -= 25
        if re.search(r'/page/\d{1,3}\b', low):
            s -= 25
        if '#' in u:
            s -= 10

        return s

    # Dedupe + scoring + sorting
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
