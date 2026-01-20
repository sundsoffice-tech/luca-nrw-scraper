# -*- coding: utf-8 -*-
"""
Data Consistency Module

Provides functions for lead enrichment, normalization, and deduplication.

Features:
- Automatic name enrichment via phonebook lookup
- Lead normalization (phone, name, region)
- Deduplication by phone number
- Data quality validation

Usage:
    from data_consistency import enrich_leads_pipeline, normalize_lead
    
    enriched = await enrich_leads_pipeline(leads)
"""

import re
from typing import List, Dict, Optional
from datetime import datetime

# Import phonebook lookup at module level for better testability
try:
    from scripts.phonebook_lookup import PhonebookLookup
    PHONEBOOK_AVAILABLE = True
except ImportError:
    PhonebookLookup = None
    PHONEBOOK_AVAILABLE = False


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to +49 format.
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Normalized phone number (+49...)
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = re.sub(r'[^\d]', '', phone)
    
    # Convert to +49 format
    if digits.startswith('0049'):
        digits = digits[4:]
    elif digits.startswith('49') and len(digits) > 10:
        digits = digits[2:]
    elif digits.startswith('0'):
        digits = digits[1:]
    
    return f'+49{digits}'


def normalize_region(region: str) -> str:
    """
    Normalize region/city name.
    
    Args:
        region: Region name
        
    Returns:
        Normalized region name
    """
    if not region:
        return ""
    
    # Standardize common region names
    region = region.strip().title()
    
    # Handle NRW variations
    if region.lower() in ['nrw', 'nordrhein-westfalen', 'nordrhein westfalen']:
        return 'NRW'
    
    return region


def normalize_lead(lead: Dict) -> Dict:
    """
    Normalize lead data for consistency.
    
    Performs:
    - Phone number normalization
    - Name cleanup and capitalization
    - Region standardization
    - Timestamp addition
    
    Args:
        lead: Lead dictionary
        
    Returns:
        Normalized lead dictionary
    """
    # Normalize phone
    if lead.get("telefon"):
        lead["telefon"] = normalize_phone(lead["telefon"])
    
    # Normalize and clean name
    if lead.get("name"):
        name = lead["name"].strip()
        # Remove invalid names
        if name.lower() in ["_probe_", "unknown candidate", "unknown", ""]:
            lead["name"] = ""
        else:
            # Proper capitalization
            lead["name"] = " ".join(w.capitalize() for w in name.split())
    
    # Normalize region
    if lead.get("region"):
        lead["region"] = normalize_region(lead["region"])
    
    # Add timestamp if missing
    if not lead.get("created_at"):
        lead["created_at"] = datetime.now().isoformat()
    
    # Update last_updated
    lead["last_updated"] = datetime.now().isoformat()
    
    return lead


async def enrich_leads_pipeline(leads: List[Dict]) -> List[Dict]:
    """
    Automated lead enrichment pipeline.
    
    Process:
    1. Enrich names via phonebook lookup for leads with phone but no name
    2. Normalize all lead data
    3. Deduplicate by phone number
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        List of enriched and deduplicated leads
    """
    enriched = []
    phonebook = PhonebookLookup() if PHONEBOOK_AVAILABLE and PhonebookLookup else None
    
    for lead in leads:
        # 1. Name enrichment via phonebook
        if phonebook and lead.get("telefon") and not lead.get("name"):
            try:
                lookup_result = phonebook.lookup(lead["telefon"])
                if lookup_result and lookup_result.get("name"):
                    lead["name"] = lookup_result["name"]
                    if lookup_result.get("address"):
                        lead["private_address"] = lookup_result["address"]
                    lead["name_source"] = lookup_result.get("source", "phonebook")
                    lead["name_validated"] = 1
            except Exception:
                # Continue even if lookup fails
                pass
        
        # 2. Normalize lead data
        lead = normalize_lead(lead)
        
        enriched.append(lead)
    
    # 3. Deduplicate by phone number
    seen_phones = set()
    unique_leads = []
    for lead in enriched:
        phone = lead.get("telefon", "")
        if phone and phone not in seen_phones:
            seen_phones.add(phone)
            unique_leads.append(lead)
    
    return unique_leads


def deduplicate_by_phone(leads: List[Dict]) -> List[Dict]:
    """
    Remove duplicate leads based on phone number.
    
    Keeps the first occurrence of each unique phone number.
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        Deduplicated list of leads
    """
    seen_phones = set()
    unique_leads = []
    
    for lead in leads:
        phone = lead.get("telefon", "")
        if phone and phone not in seen_phones:
            seen_phones.add(phone)
            unique_leads.append(lead)
    
    return unique_leads


def validate_data_quality(lead: Dict) -> int:
    """
    Calculate data quality score for a lead.
    
    Scoring:
    - Has phone: +30
    - Has name: +20
    - Has email: +10
    - Has address: +10
    - Has region: +10
    - Has company info: +10
    - Name validated: +10
    
    Args:
        lead: Lead dictionary
        
    Returns:
        Quality score (0-100)
    """
    score = 0
    
    if lead.get("telefon"):
        score += 30
    if lead.get("name") and len(lead["name"]) >= 3:
        score += 20
    if lead.get("email"):
        score += 10
    if lead.get("private_address"):
        score += 10
    if lead.get("region"):
        score += 10
    if lead.get("company_name"):
        score += 10
    if lead.get("name_validated"):
        score += 10
    
    return min(score, 100)


if __name__ == "__main__":
    # Demo/test mode
    print("Data Consistency Module")
    print("=" * 50)
    
    # Test normalization
    test_lead = {
        "name": "max mustermann",
        "telefon": "0172 1234567",
        "region": "nordrhein-westfalen",
    }
    
    print("Before normalization:")
    print(f"  Name: {test_lead['name']}")
    print(f"  Phone: {test_lead['telefon']}")
    print(f"  Region: {test_lead['region']}")
    
    normalized = normalize_lead(test_lead)
    
    print("\nAfter normalization:")
    print(f"  Name: {normalized['name']}")
    print(f"  Phone: {normalized['telefon']}")
    print(f"  Region: {normalized['region']}")
    
    # Test quality score
    quality = validate_data_quality(normalized)
    print(f"\nData quality score: {quality}/100")
