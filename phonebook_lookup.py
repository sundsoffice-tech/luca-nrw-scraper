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
    company TEXT,
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
    
    Searches for the owner of a phone number by querying multiple sources:
    - DasTelefonbuch.de reverse search
    - DasÖrtliche.de reverse search
    - 11880.com
    - GoYellow.de
    - Klicktel.de
    
    Results are cached in SQLite to minimize repeated queries.
    Rate limiting ensures we don't overwhelm the services.
    """
    
    # Source configurations with URLs and CSS selectors
    SOURCES = [
        {
            "name": "dastelefonbuch",
            "url_template": "https://www.dastelefonbuch.de/R%C3%BCckw%C3%A4rts-Suche/{phone}",
            "selectors": {
                "name": [".vcard .fn", ".entry-name", "h2.name", ".hititem .name", ".name"],
                "address": [".adr", ".address", ".street-address", ".entry-address"],
                "company": [".org", ".organization", ".company", ".firma", ".vcard .org", ".entry-company"]
            }
        },
        {
            "name": "dasoertliche", 
            "url_template": "https://www.dasoertliche.de/Controller?form_name=search_inv&ph={phone}",
            "selectors": {
                "name": [".hit__name", ".name", "h2", ".entry-name", ".vcard-name"],
                "address": [".hit__address", ".address", ".street", ".adr"],
                "company": [".hit__company", ".organization", ".company", ".org", ".firma"]
            }
        },
        {
            "name": "11880",
            "url_template": "https://www.11880.com/suche/{phone}/deutschland",
            "selectors": {
                "name": [".entry-title", ".result-name", "h3", ".name"],
                "address": [".entry-address", ".result-address", ".address"],
                "company": [".entry-company", ".result-company", ".organization", ".firma"]
            }
        },
        {
            "name": "goyellow",
            "url_template": "https://www.goyellow.de/suche/telefon/{phone}",
            "selectors": {
                "name": [".entry-name", ".result-title", ".name"],
                "address": [".entry-address", ".address"],
                "company": [".entry-company", ".company", ".organization", ".firma"]
            }
        },
        {
            "name": "klicktel",
            "url_template": "https://www.klicktel.de/rueckwaertssuche/{phone}",
            "selectors": {
                "name": [".result-name", ".entry-title", ".name"],
                "address": [".result-address", ".address"],
                "company": [".result-company", ".company", ".organization", ".firma"]
            }
        }
    ]
    
    def __init__(self, db_path: str = "scraper.db"):
        """
        Initialize the phonebook lookup service.
        
        Args:
            db_path: Path to SQLite database for caching
        """
        self.db_path = db_path
        self.last_request = 0
        self.min_delay = 2.0  # Seconds between requests (reduced from 3.0)
        self._init_cache()
    
    def _init_cache(self):
        """Create cache table if it doesn't exist and ensure schema is up to date."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(CACHE_TABLE)
        # Add company column if it doesn't exist (migration for existing databases)
        try:
            conn.execute("ALTER TABLE phone_lookup_cache ADD COLUMN company TEXT")
        except sqlite3.OperationalError as e:
            # Column already exists - this is expected for existing databases
            if "duplicate column name" not in str(e).lower():
                raise  # Re-raise unexpected errors
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
            "SELECT name, address, company, source, confidence FROM phone_lookup_cache WHERE phone = ?",
            (phone,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {"name": row[0], "address": row[1], "company": row[2], "source": row[3], "confidence": row[4]}
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
            (phone, name, address, company, source, confidence, lookup_date)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (phone, result.get("name"), result.get("address"), result.get("company"),
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
    
    def _get_headers(self) -> dict:
        """Generate realistic browser headers for requests."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def _is_valid_name(self, name: str) -> bool:
        """
        Validates if name is a real person name (not a company or placeholder).
        
        Args:
            name: Name to validate
            
        Returns:
            True if valid person name, False otherwise
        """
        if not name or len(name) < 3:
            return False
        
        # Block company indicators
        invalid_patterns = [
            "gmbh", "ag", "kg", "ohg", "ug", "mbh",
            "keine angabe", "unbekannt", "privat",
            "telefon", "mobil", "handy",
            "keine einträge", "nicht gefunden", "no entries",
            "firma", "company", "unternehmen"
        ]
        name_lower = name.lower()
        if any(p in name_lower for p in invalid_patterns):
            return False
        
        # Must have at least 2 words (first name and last name)
        words = [w for w in name.split() if len(w) > 1]
        return len(words) >= 2
    
    def _lookup_source(self, phone: str, source: dict) -> Optional[Dict]:
        """
        Query a single phonebook source.
        
        Args:
            phone: Phone number to lookup
            source: Source configuration dict
            
        Returns:
            Dict with name, address, company, source, confidence or None
        """
        clean_phone = self._format_phone_for_german_sites(phone)
        url = source["url_template"].format(phone=clean_phone)
        
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Try multiple selectors to find name
            name = None
            for selector in source["selectors"].get("name", []):
                elem = soup.select_one(selector)
                if elem:
                    candidate_name = elem.get_text(strip=True)
                    # Clean up name
                    candidate_name = re.sub(r'\s+', ' ', candidate_name).strip()
                    if self._is_valid_name(candidate_name):
                        name = candidate_name
                        break
            
            if not name:
                return None
            
            # Try to extract address
            address = ""
            for selector in source["selectors"].get("address", []):
                elem = soup.select_one(selector)
                if elem:
                    address = elem.get_text(strip=True)
                    address = re.sub(r'\s+', ' ', address).strip()
                    break
            
            # Try to extract company/organization information
            company = ""
            for selector in source["selectors"].get("company", []):
                elem = soup.select_one(selector)
                if elem:
                    candidate_company = elem.get_text(strip=True)
                    candidate_company = re.sub(r'\s+', ' ', candidate_company).strip()
                    # Only use if not a duplicate of the name
                    if candidate_company and candidate_company.lower() != name.lower():
                        company = candidate_company
                        break
                    # If it's a duplicate of the name, continue looking for other selectors
            
            return {
                "name": name,
                "address": address,
                "company": company,
                "source": source["name"],
                "confidence": 0.85,
                "phone": phone
            }
        except (requests.RequestException, Exception) as e:
            # Log error for debugging if needed, but continue with other sources
            print(f"[DEBUG] Lookup failed for {source['name']}: {type(e).__name__}", file=sys.stderr)
            return None
    
    def lookup_all_sources(self, phone: str) -> Optional[Dict]:
        """
        Try all phonebook sources until a name is found.
        
        This method iterates through all configured sources and returns
        the first successful result.
        
        Args:
            phone: Phone number to lookup
            
        Returns:
            Dict with name, address, source, confidence or None if not found
        """
        for source in self.SOURCES:
            # Use existing rate limiting
            self._rate_limit()
            result = self._lookup_source(phone, source)
            if result and result.get("name"):
                return result
        return None
    
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
        
        Checks cache first, then tries all phonebook sources using the
        new multi-source lookup system.
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
        
        # Try all sources using the new multi-source system
        result = self.lookup_all_sources(phone)
        if result and result.get("name"):
            self._save_cache(phone, result)
            return result
        
        # No result found - cache to avoid repeated queries
        self._save_cache(phone, {"name": None, "source": "not_found", "confidence": 0})
        return None


def enrich_lead_with_phonebook(lead: dict, lookup: PhonebookLookup = None) -> dict:
    """
    Enrich a single lead with name and company from phonebook reverse lookup.
    
    Only enriches if:
    - Lead has a phone number
    - Lead has no name OR name is invalid (placeholder, too short, etc.)
    
    Enrichment includes:
    - name: Person/business name from phonebook
    - private_address: Address if available
    - company_name: Company/organization if available
    - name_source: Source of the enrichment data
    
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
            # Add company/organization if available
            if result.get("company"):
                lead["company_name"] = result.get("company", "")
            # Tag the source
            lead["name_source"] = result.get("source", "phonebook")
            enrichment_info = f"[OK] Lead enriched: {phone} -> {result['name']}"
            if result.get("company"):
                enrichment_info += f" (Company: {result['company']})"
            print(enrichment_info, file=sys.stderr)
    
    return lead


def enrich_existing_leads(db_path: str = "scraper.db"):
    """
    Batch function: Enrich all existing leads that have phone but no valid name.
    
    This can be run as a one-time migration or periodically to clean up the database.
    Enrichment includes name, address, and company information when available.
    
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
            # Update with name, address, and company if available
            conn.execute(
                "UPDATE leads SET name = ?, private_address = ?, company_name = ? WHERE id = ?",
                (result["name"], result.get("address", ""), result.get("company", ""), lead_id)
            )
            updated += 1
            info = f"[OK] Lead {lead_id}: {phone} -> {result['name']}"
            if result.get("company"):
                info += f" (Company: {result['company']})"
            print(info)
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
