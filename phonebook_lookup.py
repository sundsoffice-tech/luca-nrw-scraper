# -*- coding: utf-8 -*-
"""
Phonebook Reverse Lookup Module

This module provides reverse phone lookup functionality to find the owner's name
given a phone number. It queries multiple German phonebook sources and caches results.

Features:
- Multiple phonebook sources (DasTelefonbuch.de, DasÖrtliche.de)
- Rate limiting (configurable, default 3 seconds)
- SQLite caching to avoid repeated queries
- Batch enrichment for existing leads
"""

import requests
import sqlite3
import time
import re
import sys
import urllib.parse
from typing import Optional, Dict
from bs4 import BeautifulSoup
from datetime import datetime

# Cache table schema
CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS phone_lookup_cache (
    phone TEXT PRIMARY KEY,
    name TEXT,
    address TEXT,
    source TEXT,
    confidence REAL,
    lookup_date TEXT,
    raw_response TEXT
)
"""

# List of invalid/placeholder names that should trigger enrichment
BAD_NAMES = ["_probe_", "", None, "Unknown Candidate", "Keine Fixkosten", 
             "Gastronomie", "Verkäufer", "Mitarbeiter", "Thekenverkäufer"]


class PhonebookLookup:
    """
    Reverse phone lookup using German phonebook services.
    
    Searches for the owner of a phone number by querying:
    - DasTelefonbuch.de reverse search
    - DasÖrtliche.de reverse search
    
    Results are cached in SQLite to minimize repeated queries.
    Rate limiting ensures we don't overwhelm the services.
    """
    
    def __init__(self, db_path: str = "scraper.db"):
        """
        Initialize the phonebook lookup service.
        
        Args:
            db_path: Path to SQLite database for caching
        """
        self.db_path = db_path
        self.last_request = 0
        self.min_delay = 3.0  # Seconds between requests
        self._init_cache()
    
    def _init_cache(self):
        """Create cache table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(CACHE_TABLE)
        conn.commit()
        conn.close()
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request = time.time()
    
    def _check_cache(self, phone: str) -> Optional[Dict]:
        """
        Check if result is already cached.
        
        Args:
            phone: Normalized phone number
            
        Returns:
            Cached result dict or None
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "SELECT name, address, source, confidence FROM phone_lookup_cache WHERE phone = ?",
            (phone,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {"name": row[0], "address": row[1], "source": row[2], "confidence": row[3]}
        return None
    
    def _save_cache(self, phone: str, result: Dict):
        """
        Save lookup result to cache.
        
        Args:
            phone: Normalized phone number
            result: Lookup result dict
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO phone_lookup_cache 
            (phone, name, address, source, confidence, lookup_date)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (phone, result.get("name"), result.get("address"), 
              result.get("source"), result.get("confidence")))
        conn.commit()
        conn.close()
    
    def _format_phone_for_german_sites(self, phone: str) -> str:
        """
        Format phone number for German phonebook sites.
        Converts +49... to 0... format.
        
        Args:
            phone: Phone number (e.g., +491721234567)
            
        Returns:
            Formatted number (e.g., 01721234567)
        """
        # Remove +49 and replace with 0
        clean = phone.strip()
        if clean.startswith("+49"):
            clean = "0" + clean[3:]
        # Remove spaces and common separators
        clean = clean.replace(" ", "").replace("-", "").replace("/", "")
        return clean
    
    def lookup_dastelefonbuch(self, phone: str) -> Optional[Dict]:
        """
        Search for phone owner at dastelefonbuch.de using reverse search.
        
        Args:
            phone: Phone number (normalized format)
            
        Returns:
            Dict with name, address, source, confidence or None
        """
        self._rate_limit()
        
        # Format number for German sites
        clean = self._format_phone_for_german_sites(phone)
        
        # Reverse search URL - encode the phone number properly
        encoded_phone = urllib.parse.quote(clean)
        url = f"https://www.dastelefonbuch.de/R%C3%BCckw%C3%A4rts-Suche/{encoded_phone}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Try different selectors for name
            name_elem = soup.select_one(".name, .entry-name, h2.name, .vcard .fn")
            if name_elem:
                name = name_elem.get_text(strip=True)
                
                # Clean up name (remove extra whitespace, special chars)
                name = re.sub(r'\s+', ' ', name).strip()
                
                # Skip if name looks like "Keine Einträge gefunden" or similar
                if any(skip in name.lower() for skip in ["keine", "nicht gefunden", "no entries"]):
                    return None
                
                # Try to extract address
                addr_elem = soup.select_one(".address, .entry-address, .adr, .street-address")
                address = ""
                if addr_elem:
                    address = addr_elem.get_text(strip=True)
                    address = re.sub(r'\s+', ' ', address).strip()
                
                return {
                    "name": name,
                    "address": address,
                    "source": "dastelefonbuch",
                    "confidence": 0.9
                }
        except requests.RequestException as e:
            # Network or HTTP-related errors
            print(f"[WARN] DasTelefonbuch lookup failed for {phone}: {e}", file=sys.stderr)
        except Exception as e:
            # Other unexpected errors
            print(f"[ERROR] Unexpected error in DasTelefonbuch lookup for {phone}: {e}", file=sys.stderr)
        
        return None
    
    def lookup_dasoertliche(self, phone: str) -> Optional[Dict]:
        """
        Search for phone owner at dasoertliche.de using reverse search.
        
        Args:
            phone: Phone number (normalized format)
            
        Returns:
            Dict with name, address, source, confidence or None
        """
        self._rate_limit()
        
        # Format number for German sites
        clean = self._format_phone_for_german_sites(phone)
        
        # Reverse search URL for DasÖrtliche - use proper URL encoding
        params = urllib.parse.urlencode({
            'form_name': 'search_inv',
            'ph': clean
        })
        url = f"https://www.dasoertliche.de/Controller?{params}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Try to find entry result
            entry = soup.select_one(".entry, .hit, .result-item, .hitliste .entry")
            if entry:
                # Extract name
                name_elem = entry.select_one(".name, h2, .entry-name, .vcard-name")
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    name = re.sub(r'\s+', ' ', name).strip()
                    
                    # Skip if no valid name
                    if not name or len(name) < 2:
                        return None
                    
                    # Skip if name looks like an error message
                    if any(skip in name.lower() for skip in ["keine", "nicht gefunden", "no entries"]):
                        return None
                    
                    # Extract address
                    addr_elem = entry.select_one(".address, .street, .adr")
                    address = ""
                    if addr_elem:
                        address = addr_elem.get_text(strip=True)
                        address = re.sub(r'\s+', ' ', address).strip()
                    
                    return {
                        "name": name,
                        "address": address,
                        "source": "dasoertliche",
                        "confidence": 0.85
                    }
        except requests.RequestException as e:
            # Network or HTTP-related errors
            print(f"[WARN] DasÖrtliche lookup failed for {phone}: {e}", file=sys.stderr)
        except Exception as e:
            # Other unexpected errors
            print(f"[ERROR] Unexpected error in DasÖrtliche lookup for {phone}: {e}", file=sys.stderr)
        
        return None
    
    def lookup(self, phone: str) -> Optional[Dict]:
        """
        Main lookup function: Find owner of phone number.
        
        Checks cache first, then tries multiple phonebook sources.
        Results are cached to avoid repeated queries.
        
        Args:
            phone: Phone number (normalized format like +491721234567)
            
        Returns:
            Dict with name, address, source, confidence or None if not found
        """
        # Normalize input
        phone = phone.strip()
        if not phone:
            return None
        
        # Check cache first
        cached = self._check_cache(phone)
        if cached:
            # Don't return cached non-results if name is None
            if cached.get("name"):
                return cached
            # If cached result had no name, we already tried, so return None
            return None
        
        # Try different sources
        result = None
        
        # 1. Try DasTelefonbuch first (usually has better data)
        result = self.lookup_dastelefonbuch(phone)
        if result and result.get("name"):
            self._save_cache(phone, result)
            return result
        
        # 2. Try DasÖrtliche as fallback
        result = self.lookup_dasoertliche(phone)
        if result and result.get("name"):
            self._save_cache(phone, result)
            return result
        
        # No result found - cache to avoid repeated queries
        self._save_cache(phone, {"name": None, "source": "not_found", "confidence": 0})
        return None


def enrich_lead_with_phonebook(lead: dict, lookup: PhonebookLookup = None) -> dict:
    """
    Enrich a single lead with name from phonebook reverse lookup.
    
    Only enriches if:
    - Lead has a phone number
    - Lead has no name OR name is invalid (placeholder, too short, etc.)
    
    Args:
        lead: Lead dict with at least "telefon" field
        lookup: Optional PhonebookLookup instance (created if None)
        
    Returns:
        Enriched lead dict (modified in place and returned)
    """
    if lookup is None:
        lookup = PhonebookLookup()
    
    phone = lead.get("telefon", "")
    current_name = lead.get("name", "")
    
    # Check if name needs enrichment using shared constant
    needs_enrichment = False
    if not current_name or current_name in BAD_NAMES:
        needs_enrichment = True
    elif len(current_name) < 3:  # Too short to be a real name
        needs_enrichment = True
    elif not any(c.isalpha() for c in current_name):  # No letters in name
        needs_enrichment = True
    
    # Only enrich if phone exists and name needs enrichment
    if phone and needs_enrichment:
        result = lookup.lookup(phone)
        if result and result.get("name"):
            lead["name"] = result["name"]
            # Also add address if available
            if result.get("address"):
                lead["private_address"] = result.get("address", "")
            # Tag the source
            lead["name_source"] = result.get("source", "phonebook")
            print(f"[OK] Lead enriched: {phone} -> {result['name']}", file=sys.stderr)
    
    return lead


def enrich_existing_leads(db_path: str = "scraper.db"):
    """
    Batch function: Enrich all existing leads that have phone but no valid name.
    
    This can be run as a one-time migration or periodically to clean up the database.
    
    Args:
        db_path: Path to SQLite database
    """
    lookup = PhonebookLookup(db_path)
    conn = sqlite3.connect(db_path)
    
    # Find leads with phone but invalid/missing name
    cur = conn.execute("""
        SELECT id, telefon, name FROM leads 
        WHERE telefon IS NOT NULL 
        AND telefon != ''
        AND (
            name IS NULL 
            OR name = '' 
            OR name = '_probe_' 
            OR name = 'Unknown Candidate'
            OR LENGTH(name) < 3
        )
    """)
    
    leads_to_update = cur.fetchall()
    print(f"[INFO] Found {len(leads_to_update)} leads without valid names")
    
    updated = 0
    for lead_id, phone, old_name in leads_to_update:
        result = lookup.lookup(phone)
        if result and result.get("name"):
            conn.execute(
                "UPDATE leads SET name = ?, private_address = ? WHERE id = ?",
                (result["name"], result.get("address", ""), lead_id)
            )
            updated += 1
            print(f"[OK] Lead {lead_id}: {phone} -> {result['name']}")
        else:
            print(f"[SKIP] Lead {lead_id}: {phone} -> No name found")
    
    conn.commit()
    conn.close()
    print(f"[DONE] Updated {updated} of {len(leads_to_update)} leads")


if __name__ == "__main__":
    # CLI interface
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--enrich":
        # Batch enrichment of existing leads
        enrich_existing_leads()
    elif len(sys.argv) > 1 and sys.argv[1] == "--lookup":
        # Single phone number lookup
        if len(sys.argv) > 2:
            test_phone = sys.argv[2]
            lookup = PhonebookLookup()
            result = lookup.lookup(test_phone)
            if result:
                print(f"✓ Found: {result['name']}")
                if result.get('address'):
                    print(f"  Address: {result['address']}")
                print(f"  Source: {result['source']}")
            else:
                print(f"✗ No result found for {test_phone}")
        else:
            print("Usage: python phonebook_lookup.py --lookup <phone_number>")
    else:
        # Demo/test mode
        print("Phonebook Lookup Module")
        print("=" * 50)
        print("Usage:")
        print("  python phonebook_lookup.py --lookup +491721234567")
        print("  python phonebook_lookup.py --enrich")
        print()
        
        # Run a simple test
        lookup = PhonebookLookup()
        test_phone = "+491721234567"
        print(f"Testing reverse lookup for: {test_phone}")
        result = lookup.lookup(test_phone)
        if result:
            print(f"✓ Result: {result}")
        else:
            print(f"✗ No result found (this is normal for test numbers)")
