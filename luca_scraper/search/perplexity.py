# -*- coding: utf-8 -*-
"""
Perplexity AI search integration for lead generation.
"""

import os
from typing import Dict, List

import aiohttp

from luca_scraper.config import HTTP_TIMEOUT

# Try to import from scriptname.py, fallback if not available
try:
    from scriptname import log
except ImportError:
    def log(level: str, msg: str, **ctx):
        """Fallback log function when running as standalone module."""
        pass


async def search_perplexity_async(query: str) -> List[Dict[str, str]]:
    """
    Perplexity (sonar) search returning citation URLs.
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
            {"role": "system", "content": "You are a lead generation engine. Search for the user's query and return relevant business URLs. Ensure citations are included."},
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
