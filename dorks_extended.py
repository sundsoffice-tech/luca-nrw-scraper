# -*- coding: utf-8 -*-
"""
Erweiterte Dork-Sammlung für maximale Lead-Generierung

Diese Datei enthält über 100 spezialisierte Google Dorks für:
- Direkte Stellengesuche
- Site-spezifische Suchen
- URL-Pattern Suchen
- Kontakt-Pattern Suchen
- Power-Dorks (kombinierte Suchen)
"""

import random
from typing import List, Dict


# Basis-Dorks für Stellengesuche
JOB_SEEKER_DORKS = [
    # Direkte Stellengesuche
    '"suche arbeit" telefon NRW',
    '"suche job" kontakt Nordrhein-Westfalen',
    '"suche stelle" mobil vertrieb',
    '"arbeit gesucht" telefonnummer',
    '"verfügbar ab sofort" kontakt vertrieb',
    '"auf jobsuche" telefon NRW',
    
    # Mit Ortsangaben - Düsseldorf
    '"suche arbeit" telefon Düsseldorf',
    '"suche arbeit" mobil Düsseldorf',
    '"arbeit gesucht" kontakt Düsseldorf',
    
    # Mit Ortsangaben - Köln
    '"suche arbeit" telefon Köln',
    '"suche arbeit" mobil Köln',
    '"arbeit gesucht" kontakt Köln',
    
    # Mit Ortsangaben - Dortmund
    '"suche arbeit" telefon Dortmund',
    '"suche arbeit" mobil Dortmund',
    
    # Mit Ortsangaben - Essen
    '"suche arbeit" telefon Essen',
    '"suche arbeit" mobil Essen',
    
    # Mit Ortsangaben - Duisburg
    '"suche arbeit" telefon Duisburg',
    
    # Mit Ortsangaben - Bochum
    '"suche arbeit" telefon Bochum',
    
    # Mit Ortsangaben - Wuppertal
    '"suche arbeit" telefon Wuppertal',
    
    # Mit Ortsangaben - Bielefeld
    '"suche arbeit" telefon Bielefeld',
    
    # Mit Ortsangaben - Münster
    '"suche arbeit" telefon Münster',
    
    # Mit Ortsangaben - Bonn
    '"suche arbeit" telefon Bonn',
    
    # Branchen-spezifisch
    '"vertriebserfahrung" "suche neue herausforderung" kontakt',
    '"sales manager" "offen für angebote" telefon',
    '"key account" stellengesuch mobil',
    '"außendienst" "suche position" telefon',
    '"kundenberater" stellengesuch kontakt',
    
    # Qualifikations-basiert
    '"kaufmännische ausbildung" "suche arbeit" telefon',
    '"berufserfahrung" "suche stelle" mobil NRW',
    '"führerschein klasse b" stellengesuch telefon',
    
    # Verfügbarkeit
    '"ab sofort verfügbar" telefon vertrieb',
    '"kurzfristig verfügbar" kontakt NRW',
    '"flexible arbeitszeiten" stellengesuch mobil',
    
    # Gehaltsvorstellung (zeigt ernsthafte Kandidaten)
    '"gehaltsvorstellung" stellengesuch telefon NRW',
    '"verhandlungsbasis" "suche stelle" kontakt',
]

# Site-spezifische Dorks
SITE_SPECIFIC_DORKS = [
    # Kleinanzeigen-Portale
    'site:kleinanzeigen.de stellengesuch telefon NRW',
    'site:kleinanzeigen.de stellengesuch mobil vertrieb',
    'site:kleinanzeigen.de "suche arbeit" kontakt',
    'site:quoka.de stellengesuch mobil',
    'site:quoka.de "suche job" telefon',
    'site:markt.de stellengesuch kontakt',
    'site:markt.de "arbeit gesucht" telefon',
    
    # Social Media
    'site:facebook.com "suche job" NRW telefon',
    'site:facebook.com/groups "stellengesuch" vertrieb',
    'site:linkedin.com "open to work" vertrieb NRW',
    'site:linkedin.com "offen für angebote" sales',
    'site:xing.com "auf jobsuche" kontakt',
    'site:xing.com "suche neue herausforderung" vertrieb',
    
    # Foren und Communities
    'site:reddit.com "suche arbeit" NRW',
    'site:gutefrage.net stellengesuch kontakt',
    'site:wiwi-treff.de "suche job" vertrieb',
    
    # Regionale Portale
    'site:kalaydo.de stellengesuch telefon',
    'site:rheinische-anzeigenblaetter.de stellengesuch',
    'site:meinestadt.de stellengesuch telefon NRW',
]

# URL-Pattern Dorks
URL_PATTERN_DORKS = [
    'inurl:stellengesuch telefon NRW',
    'inurl:jobsuche kontakt vertrieb',
    'inurl:bewerber telefon sales',
    'inurl:lebenslauf kontakt NRW',
    'inurl:bewerbung telefon vertrieb',
    'inurl:cv telefon NRW',
    'inurl:profile "suche job" telefon',
]

# Erweiterte Kontakt-Pattern Dorks
CONTACT_PATTERN_DORKS = [
    '"tel:" OR "telefon:" stellengesuch NRW',
    '"mobil:" OR "handy:" stellengesuch vertrieb',
    '"0151" OR "0152" OR "0157" OR "0160" stellengesuch',
    '"0170" OR "0171" OR "0172" OR "0173" stellengesuch',
    '"0174" OR "0175" OR "0176" OR "0177" stellengesuch',
    '"0178" OR "0179" stellengesuch NRW',
    '"+49" stellengesuch NRW vertrieb',
    '"whatsapp" stellengesuch telefon',
    '"rückruf" stellengesuch NRW',
    '"erreichbar unter" stellengesuch',
    '"kontaktiere mich" stellengesuch telefon',
]

# Kombinierte Power-Dorks
POWER_DORKS = [
    '"suche arbeit" ("0151" OR "0152" OR "0157" OR "0160" OR "0170" OR "0171" OR "0172" OR "0173" OR "0174" OR "0175" OR "0176" OR "0177" OR "0178" OR "0179") NRW',
    'stellengesuch (telefon OR mobil OR handy) (vertrieb OR sales OR verkauf) NRW',
    '"suche job" kontakt -stellenangebot -arbeitgeber NRW',
    '"biete arbeitskraft" telefon NRW',
    '"suche neue stelle" (kontakt OR telefon) vertrieb',
    '(stellengesuch OR "suche arbeit") (Düsseldorf OR Köln OR Dortmund OR Essen) telefon',
    '"verfügbar ab" (telefon OR mobil) vertrieb NRW -stellenangebot',
    '("außendienst" OR "sales" OR "vertrieb") "suche" (telefon OR mobil) NRW',
]

# Job-Portal spezifische Dorks
JOB_PORTAL_DORKS = [
    'site:indeed.com stellengesuch NRW',
    'site:stepstone.de "kandidat sucht" vertrieb',
    'site:monster.de stellengesuch telefon',
    'site:stellenanzeigen.de "bewerber" kontakt NRW',
    'site:arbeitsagentur.de stellengesuch telefon',
]

# Mobile-First Dorks (WhatsApp, Telegram)
MOBILE_DORKS = [
    'whatsapp stellengesuch NRW',
    '"wa.me" stellengesuch vertrieb',
    'telegram stellengesuch kontakt',
    '"t.me" stellengesuch NRW',
    '"whatsapp kontakt" stellengesuch',
]

# Freelancer & Remote Dorks
FREELANCER_DORKS = [
    '"remote vertrieb" "suche projekt" kontakt',
    '"freelancer" "sales" "verfügbar" telefon',
    '"freiberufler" "vertrieb" "suche aufträge" kontakt',
    'site:freelancermap.de vertrieb verfügbar telefon',
    'site:freelance.de sales deutsch kontakt',
]


def get_all_dorks() -> List[str]:
    """
    Gibt alle Dorks zurück
    
    Returns:
        Liste aller verfügbaren Dorks
    """
    return (
        JOB_SEEKER_DORKS + 
        SITE_SPECIFIC_DORKS + 
        URL_PATTERN_DORKS + 
        CONTACT_PATTERN_DORKS + 
        POWER_DORKS +
        JOB_PORTAL_DORKS +
        MOBILE_DORKS +
        FREELANCER_DORKS
    )


def get_dorks_by_category(category: str) -> List[str]:
    """
    Gibt Dorks nach Kategorie zurück
    
    Args:
        category: Kategorie-Name (job_seeker, site_specific, url_pattern, etc.)
    
    Returns:
        Liste der Dorks der gewählten Kategorie
    """
    categories = {
        "job_seeker": JOB_SEEKER_DORKS,
        "site_specific": SITE_SPECIFIC_DORKS,
        "url_pattern": URL_PATTERN_DORKS,
        "contact_pattern": CONTACT_PATTERN_DORKS,
        "power": POWER_DORKS,
        "job_portal": JOB_PORTAL_DORKS,
        "mobile": MOBILE_DORKS,
        "freelancer": FREELANCER_DORKS,
    }
    return categories.get(category, [])


def get_random_dorks(n: int = 10) -> List[str]:
    """
    Gibt n zufällige Dorks zurück
    
    Args:
        n: Anzahl der zurückzugebenden Dorks
    
    Returns:
        Liste mit n zufälligen Dorks
    """
    all_dorks = get_all_dorks()
    return random.sample(all_dorks, min(n, len(all_dorks)))


def get_dorks_for_city(city: str) -> List[str]:
    """
    Gibt Dorks spezifisch für eine Stadt zurück
    
    Args:
        city: Name der Stadt (z.B. "Düsseldorf", "Köln")
    
    Returns:
        Liste der stadtspezifischen Dorks
    """
    city_dorks = [
        f'"suche arbeit" telefon {city}',
        f'"suche job" kontakt {city}',
        f'"arbeit gesucht" mobil {city}',
        f'stellengesuch telefon {city}',
        f'site:kleinanzeigen.de stellengesuch {city}',
    ]
    return city_dorks


def get_dorks_count() -> Dict[str, int]:
    """
    Gibt die Anzahl der Dorks pro Kategorie zurück
    
    Returns:
        Dictionary mit Kategorie-Namen und Anzahl
    """
    return {
        "job_seeker": len(JOB_SEEKER_DORKS),
        "site_specific": len(SITE_SPECIFIC_DORKS),
        "url_pattern": len(URL_PATTERN_DORKS),
        "contact_pattern": len(CONTACT_PATTERN_DORKS),
        "power": len(POWER_DORKS),
        "job_portal": len(JOB_PORTAL_DORKS),
        "mobile": len(MOBILE_DORKS),
        "freelancer": len(FREELANCER_DORKS),
        "total": len(get_all_dorks()),
    }
