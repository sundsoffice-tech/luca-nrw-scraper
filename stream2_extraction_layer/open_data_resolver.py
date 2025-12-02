import re
import urllib.parse
from typing import Optional

import requests


def _clean_domain(dom: str) -> str:
    if not dom:
        return ""
    d = dom.strip().lower()
    if d.startswith("www."):
        d = d[4:]
    blocked = {
        "linkedin.com",
        "de.linkedin.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
    }
    if any(d == b or d.endswith("." + b) for b in blocked):
        return ""
    return d


def _domain_from_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        return _clean_domain(parsed.netloc)
    except Exception:
        return ""


def _guess_domain_from_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9äöüÄÖÜß ]+", " ", name or "").strip()
    if not cleaned:
        return ""
    token = re.sub(r"\s+", "-", cleaned).lower()
    for suffix in (".de", ".com", ".eu"):
        candidate = _clean_domain(f"{token}{suffix}")
        if candidate:
            return candidate
    return ""


def _from_clearbit(name: str) -> str:
    try:
        r = requests.get(
            "https://autocomplete.clearbit.com/v1/companies/suggest",
            params={"query": name},
            timeout=5,
        )
        data = r.json()
        if data and isinstance(data, list):
            dom = _clean_domain(data[0].get("domain", ""))
            if dom:
                return dom
    except Exception:
        return ""
    return ""


def _from_opencorporates(name: str) -> str:
    try:
        r = requests.get(
            "https://api.opencorporates.com/companies/search",
            params={"q": name},
            timeout=6,
        )
        data = r.json() if r.ok else {}
        companies = data.get("results", {}).get("companies", [])
        for entry in companies:
            comp = entry.get("company") or {}
            for key in ("website", "homepage_url", "url"):
                dom = _domain_from_url(comp.get(key, ""))
                if dom:
                    return dom
            dom_guess = _guess_domain_from_name(comp.get("name", ""))
            if dom_guess:
                return dom_guess
    except Exception:
        return ""
    return ""


def _from_duckduckgo(name: str) -> str:
    try:
        r = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": name, "kl": "de-de"},
            headers={"User-Agent": "Mozilla/5.0 (compatible; OpenDataResolver/1.0)"},
            timeout=6,
        )
        if not r.ok:
            return ""
        html = r.text
        m = re.search(r'href=\"[^\"?]*uddg=([^\"&]+)', html)
        if not m:
            return ""
        target = urllib.parse.unquote(m.group(1))
        dom = _domain_from_url(target)
        return dom
    except Exception:
        return ""


def resolve_company_domain(name: str) -> str:
    """
    Try to resolve a company domain from open/free sources (no LinkedIn, no logins).
    Fast path: Clearbit autocomplete -> OpenCorporates -> DuckDuckGo HTML.
    """
    if not name:
        return ""

    for resolver in (_from_clearbit, _from_opencorporates, _from_duckduckgo):
        dom = resolver(name)
        if dom:
            return dom
    return ""
