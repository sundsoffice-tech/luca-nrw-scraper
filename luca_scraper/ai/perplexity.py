"""
Perplexity AI Integration for LUCA NRW Scraper
===============================================

Provides Perplexity AI-powered functionality for:
- Web search with citations
- Smart search query (dork) generation

All functions gracefully handle missing API keys.
"""

import json
import os
from typing import Any, Dict, List

import aiohttp

from luca_scraper.config import PERPLEXITY_API_KEY, HTTP_TIMEOUT


def log(level: str, msg: str, **ctx):
    """Simple logging function - imports actual logger from parent if available."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    line = f"[{ts}] [{level.upper():7}] {msg}{ctx_str}"
    print(line, flush=True)


def _is_candidates_mode() -> bool:
    """Check if we're in candidates/recruiter mode based on INDUSTRY env var."""
    industry = str(os.getenv("INDUSTRY", "")).lower()
    if "talent_hunt" in industry:
        return False
    return "recruiter" in industry or "candidates" in industry


async def search_perplexity_async(query: str) -> List[Dict[str, str]]:
    """
    Perplexity (sonar) search returning citation URLs.
    
    Args:
        query: Search query string
    
    Returns:
        List of dicts with keys: link, title, snippet
    """
    pplx_key = os.getenv("PERPLEXITY_API_KEY", "")
    if not pplx_key:
        return []

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {pplx_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a lead generation engine. Search for the user's query and return relevant business URLs. ensure citations are included."},
            {"role": "user", "content": query}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=HTTP_TIMEOUT) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    citations = data.get("citations", []) or []
                    log("info", "Perplexity found citations", count=len(citations))
                    return [{'link': u, 'title': 'Perplexity Source', 'snippet': 'AI Verified'} for u in citations if u]
                log("error", "Perplexity API Error", status=resp.status)
                return []
    except Exception as e:
        log("error", "Perplexity Exception", error=str(e))
        return []


async def generate_smart_dorks(industry: str, count: int = 5) -> List[str]:
    """
    LLM-generated dorks for the specified industry.
    Uses different prompts for candidates/recruiter mode vs standard B2B.
    
    Args:
        industry: Industry name or "candidates"/"recruiter" for job seeker mode
        count: Number of dorks to generate (default: 5)
    
    Returns:
        List of search query strings (dorks)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []
    
    # Different prompt for candidates mode
    if industry.lower() in ("candidates", "recruiter"):
        prompt = (
            "Generate Google Dorks to find JOB SEEKERS (not companies hiring). "
            "Target: People actively looking for sales/vertrieb jobs. "
            "Required patterns: "
            'site:kleinanzeigen.de/s-stellengesuche "vertrieb"; '
            'site:xing.com/profile "offen für angebote" "sales"; '
            'site:linkedin.com/in "#opentowork" "vertrieb"; '
            '"ich suche job" "vertrieb" "NRW" "mobil"; '
            'site:facebook.com "suche arbeit" "verkauf". '
            "Return ONLY the dorks, one per line."
        )
        system_content = "You create Google search dorks to find job seekers and candidates."
    else:
        # Standard B2B prompt
        prompt = (
            "You are a Headhunter. Generate Google Dorks that find lists of employees, PDF CVs, 'Unser Team' pages, or Freelancer profiles. "
            "forbidden: Do NOT generate generic B2B searches like 'Händler' or 'Hersteller'. "
            "Required Patterns (mix these): "
            f'intitle:"Team" "Sales Manager" {industry}; '
            f'filetype:pdf "Lebenslauf" {industry} -job -anzeige; '
            f'site:linkedin.com/in/ "{industry}" "open to work"; '
            f'"stellengesuch" {industry} "verfügbar ab"; '
            f'"Ansprechpartner" "Vertrieb" {industry} -intitle:Jobs. '
            "Return ONLY the dorks, one per line."
        )
        system_content = "You create targeted Google search dorks for B2B lead generation."
    
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=HTTP_TIMEOUT) as resp:
                if resp.status != 200:
                    log("warn", "Smart dorks HTTP error", status=resp.status)
                    return []
                data = await resp.json()
                content = ""
                choices = data.get("choices") or []
                if choices and isinstance(choices, list):
                    content = ((choices[0] or {}).get("message") or {}).get("content", "")
                if not content:
                    return []
                
                lines = [ln.strip(" -*\t") for ln in content.splitlines() if ln.strip()]
                uniq = []
                seen = set()
                for ln in lines:
                    if ln.lower() in seen:
                        continue
                    seen.add(ln.lower())
                    uniq.append(ln)
                    if len(uniq) >= max(1, count):
                        break
                return uniq
    except Exception as e:
        log("warn", "Smart dorks generation failed", error=str(e))
        return []
    return []
