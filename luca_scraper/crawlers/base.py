# -*- coding: utf-8 -*-
"""Base crawler utilities and helper functions"""

import urllib.parse
from typing import Optional

# Try importing from scriptname.py
try:
    from scriptname import log, _normalize_for_dedupe, _seen_urls_cache, db
except ImportError:
    # Fallback implementations
    def log(level: str, msg: str, **ctx):
        """Fallback log function"""
        print(f"[{level.upper()}] {msg}", ctx)
    
    def _normalize_for_dedupe(u: str) -> str:
        """Fallback URL normalizer"""
        try:
            pu = urllib.parse.urlparse(u)
            q = urllib.parse.parse_qsl(pu.query, keep_blank_values=False)
            q = [
                (k, v) for (k, v) in q
                if not (
                    k.lower().startswith(("utm_",))
                    or k.lower() in {"gclid", "fbclid", "mc_eid", "page"}
                )
            ]
            new_q = urllib.parse.urlencode(q, doseq=True)
            path = pu.path or "/"
            if path != "/" and path.endswith("/"):
                path = path.rstrip("/")
            return urllib.parse.urlunparse((pu.scheme, pu.netloc, path, "", new_q, ""))
        except Exception:
            return u
    
    _seen_urls_cache = set()
    
    def db():
        """Fallback db function"""
        raise ImportError("Database not available")


def _mark_url_seen(url: str, source: str = "") -> None:
    """
    Helper function to mark a URL as seen in the database.
    
    Args:
        url: The URL to mark as seen
        source: Optional source name for logging (e.g., "Markt.de", "Quoka")
    """
    try:
        con = db()
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO urls_seen (url) VALUES (?)", (url,))
        con.commit()
        con.close()
        _seen_urls_cache.add(_normalize_for_dedupe(url))
    except Exception as e:
        log_prefix = f"{source}: " if source else ""
        log("warn", f"{log_prefix}Konnte URL nicht als gesehen markieren", url=url, error=str(e))
