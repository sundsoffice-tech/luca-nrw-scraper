# -*- coding: utf-8 -*-
"""
Dynamic Query Generator Module

This module provides dynamic query generation for the lead scraper.
It generates industry-specific search queries based on the given industry type.
"""

import random
from typing import List


def get_dynamic_queries(industry: str, count: int = 20) -> List[str]:
    """
    Generate dynamic search queries based on the industry type.
    
    Args:
        industry: The industry type (e.g., 'candidates', 'recruiter', 'talent_hunt', 'all')
        count: Number of queries to generate (default: 20)
    
    Returns:
        List of search query strings
    """
    # Base queries for different industries
    industry_queries = {
        "candidates": [
            '"Vertrieb" "suche Job" "NRW"',
            '"Sales" "looking for" "Germany"',
            '"Account Manager" "suche Stelle" "Nordrhein-Westfalen"',
            'site:stellenanzeigen.de "Vertrieb" CV',
            'site:indeed.de "Sales" Lebenslauf',
            'site:monster.de "Vertriebsmitarbeiter" Bewerbung',
            '"Key Account" "suche Position" Deutschland',
            '"Business Development" Lebenslauf NRW',
            'site:stepstone.de "Vertrieb" Profil',
            'site:xing.com "Vertrieb" "suche Job"',
            '"Handelsvertreter" "verfügbar" kontakt',
            '"Außendienst" Bewerbung NRW',
            'site:linkedin.com "Sales Manager" "#opentowork"',
            '"Vertriebsleiter" "suche neue Herausforderung"',
            'site:arbeitsagentur.de "Vertrieb" Bewerberprofil',
        ],
        "recruiter": [
            '"Personalvermittlung" "Vertrieb" "NRW"',
            '"Recruiting" "Sales" kontakt',
            '"Headhunter" "Vertrieb" telefon',
            'site:recruiting.de "Vertrieb" kontakt',
            '"Personalberater" "Sales" NRW',
            'site:personalberatung.de "Vertrieb" telefon',
            '"Vermittlung" "Vertriebsmitarbeiter" kontakt',
            '"Zeitarbeit" "Sales" NRW telefon',
            'site:randstad.de "Vertrieb" kontakt',
            'site:manpower.de "Sales" telefon',
            '"Arbeitnehmerüberlassung" "Vertrieb" NRW',
            'site:adecco.de "Vertrieb" kontakt',
            '"HR Consulting" "Vertrieb" telefon',
            '"Personaldienstleister" "Sales" NRW',
        ],
        "talent_hunt": [
            'site:linkedin.com/in "Sales Manager" "NRW" -"#opentowork"',
            'site:linkedin.com/in "Account Manager" "Germany" -"open to work"',
            'site:linkedin.com/in "Vertriebsleiter" "Deutschland" -"#opentowork"',
            'site:xing.com/profile "Vertriebsmitarbeiter" "NRW" kontakt',
            'site:xing.com/profile "Key Account" telefon',
            'intitle:"Unser Team" "Vertrieb" kontakt',
            'intitle:"Team" "Sales" telefon NRW',
            '"Ansprechpartner Vertrieb" telefon',
            'inurl:team "Vertriebsleiter" kontakt',
            'inurl:mitarbeiter "Account Manager" email',
            'site:linkedin.com/in "Business Development" "Deutschland" -"#opentowork"',
            '"Ihr Ansprechpartner" "Außendienst" kontakt',
            'site:xing.com/profile "Handelsvertreter" telefon',
            'inurl:about "Vertrieb" kontakt',
        ],
        "all": [
            '"Vertrieb" "Job" "NRW" kontakt',
            '"Sales" "Karriere" telefon',
            '"Handelsvertreter" "suche" kontakt',
            'site:ebay-kleinanzeigen.de "Vertrieb" "Job"',
            'site:quoka.de "Sales" Stellengesuch',
            '"Außendienst" "Bewerbung" NRW',
            '"Vertriebsmitarbeiter" kontakt telefon',
            '"Account Manager" Lebenslauf',
            'site:kalaydo.de "Vertrieb" Stellengesuch',
            '"Business Development" CV Deutschland',
            '"Key Account" "suche" NRW',
            'site:markt.de "Vertrieb" Job',
            '"Vertriebsleiter" Bewerbung kontakt',
            '"Sales Representative" Deutschland telefon',
            '"Vertriebsprofi" "verfügbar" kontakt',
        ],
    }
    
    # Select queries based on industry
    industry_lower = industry.lower() if industry else "all"
    
    # Get queries for the specified industry, fallback to 'all' if not found
    queries = industry_queries.get(industry_lower, industry_queries["all"])
    
    # Shuffle for variety
    random.shuffle(queries)
    
    # Return requested count (or all if count is larger)
    return queries[:min(count, len(queries))]
