# -*- coding: utf-8 -*-
"""
Search manager utilities for URL normalization, prioritization, and helper functions.
"""

import random
import re
import urllib.parse
from typing import Any, Dict, List, Union

# Type alias for URL-like objects
UrlLike = Union[str, Dict[str, Any]]


def _normalize_cx(s: str) -> str:
    if not s: return ""
    try:
        p = urllib.parse.urlparse(s)
        if p.query:
            q = urllib.parse.parse_qs(p.query)
            val = q.get("cx", [""])[0].strip()
            if val: return val
    except Exception:
        pass
    return s.strip()

def _jitter(a=0.2,b=0.8): return a + random.random()*(b-a)

def _normalize_for_dedupe(u: str) -> str:
    try:
        pu = urllib.parse.urlparse(u)

        # Query normalisieren – Tracking & Paginierung raus
        q = urllib.parse.parse_qsl(pu.query, keep_blank_values=False)
        q = [
            (k, v) for (k, v) in q
            if not (
                k.lower().startswith(("utm_",))                       # utm_*
                or k.lower() in {"gclid", "fbclid", "mc_eid", "page"} # + page-Param raus
            )
        ]
        new_q = urllib.parse.urlencode(q, doseq=True)

        # Pfad normalisieren: Fragment weg, trailing slash schlucken
        path = pu.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        pu = pu._replace(query=new_q, fragment="", path=path)
        return urllib.parse.urlunparse(pu)
    except Exception:
        return u


def _extract_url(item: UrlLike) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("url") or item.get("link", "")
    return ""


def prioritize_urls(urls: List[str]) -> List[str]:
    """
    Priorisiert typische Kontaktseiten deutlich höher als Karriere/Jobs/Datenschutz.
    - Additives Scoring (nicht nur erstes Pattern)
    - Starke Upvotes: /kontakt, /impressum
    - Downvotes: /karriere, /jobs, /stellen, /datenschutz, /privacy, /agb
    - Leichte Bevorzugung kurzer/oberflächlicher Pfade; Abwertung bei Paginierung/Fragmenten
    """
    # --- POSITIVE & NEGATIVE Schlüsselwörter ---
    # Hinweis: additive Bewertung; ein Pfad kann mehrere Treffer bekommen.
    PRIORITY_PATTERNS = [
        (r'/kontakt(?:/|$)',                    +40),
        (r'/kontaktformular(?:/|$)',            +32),
        (r'/impressum(?:/|$)',                  +35),
        (r'/team(?:/|$)',                       +12),
        (r'/ueber-uns|/über-uns|/unternehmen',  +10),
        # NEU: Jobseeker-Signale boosten
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

        # Positive Muster: additiv werten
        for pat, pts in PRIORITY_PATTERNS:
            if re.search(pat, low, re.I):
                s += pts

        # Negative Muster: additiv abwerten
        for pat, pts in PENALTY_PATTERNS:
            if re.search(pat, low, re.I):
                s += pts

        # Query-Hints (selten, aber wenn vorhanden → leicht positiv)
        if re.search(r'(\?|#).*(kontakt|impressum)', low, re.I):
            s += 12

        # Pfad-Länge / -Tiefe: kurze, flache Pfade bevorzugen
        depth = max(0, path.count('/') - 1)
        s += max(0, 20 - len(path))           # kürzerer Pfad = besser
        s += max(0, 10 - 5*depth)             # weniger Unterverzeichnisse = besser

        # Rauschfilter / Paginierung / Fragmente
        if len(u) > 220:                      # sehr lange URLs wirken oft „Rauschen"
            s -= 40
        if re.search(r'(\?|&)page=\d{1,3}\b', low):
            s -= 25
        if re.search(r'/page/\d{1,3}\b', low):
            s -= 25
        if '#' in u:                          # Anker/Kommentare/Blogfragmente
            s -= 10

        return s

    # Dedupe (auf Basis deiner Normalisierung) + Scoring + Sortierung
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
