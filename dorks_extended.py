# -*- coding: utf-8 -*-
"""
Erweiterte Dork-Sammlung für maximale Lead-Generierung

Diese Datei enthält spezialisierte Google Dorks für:
- Talent Hunt (aktive Vertriebler finden)
- Direkte Stellengesuche
- Site-spezifische Suchen
- URL-Pattern Suchen
- Kontakt-Pattern Suchen
- Power-Dorks (kombinierte Suchen)
"""

import random
from typing import List, Dict


# ══════════════════════════════════════════════════════════════
# NEUE KATEGORIE: TALENT HUNT DORKS (Aktive Vertriebler)
# ══════════════════════════════════════════════════════════════

TALENT_HUNT_DORKS = [
    # LinkedIn Profiles - OHNE #opentowork
    'site:linkedin.com/in "Account Manager" "NRW" -"#opentowork"',
    'site:linkedin.com/in "Sales Manager" "Düsseldorf" -"#opentowork"',
    'site:linkedin.com/in "Vertriebsleiter" "NRW" -"open to work"',
    'site:linkedin.com/in "Key Account" "Deutschland" -"#opentowork"',
    'site:linkedin.com/in "Business Development" "NRW" -"#opentowork"',
    
    # Xing Profiles
    'site:xing.com/profile "Vertriebsmitarbeiter" "NRW" kontakt',
    'site:xing.com/profile "Handelsvertreter" "Nordrhein-Westfalen"',
    'site:xing.com/profile "Sales Representative" "Deutschland"',
    'site:xing.com/profile "Account Manager" telefon',
    
    # Team-Seiten
    'intitle:"Unser Team" "Vertrieb" "NRW" kontakt',
    'intitle:"Team" "Sales" telefon',
    '"Ansprechpartner Vertrieb" telefon NRW',
    'inurl:team "Vertriebsleiter" kontakt',
    'inurl:mitarbeiter "Account Manager" email',
]

TEAM_PAGE_DORKS = [
    'intitle:"Unser Team" "Vertrieb" kontakt',
    'intitle:"Team" "Sales" ("Düsseldorf" OR "Köln")',
    '"Ansprechpartner Vertrieb" telefon',
    '"Ihr Ansprechpartner" "Außendienst" kontakt',
    'inurl:team "Vertriebsleiter" telefon',
    'inurl:mitarbeiter "Sales" email',
    'inurl:about "Vertrieb" kontakt',
]

LINKEDIN_PROFILE_DORKS = [
    'site:linkedin.com/in "Sales Manager" "Germany" -"#opentowork"',
    'site:linkedin.com/in "Account Manager" "NRW" -"open to work"',
    'site:linkedin.com/in "Vertriebsleiter" "Deutschland" -"#opentowork"',
    'site:linkedin.com/in "Business Development" -"#opentowork"',
    'site:linkedin.com/in "Key Account Manager" "NRW" -"open to work"',
    'site:linkedin.com/in "Regional Sales" "Deutschland" -"#opentowork"',
]

FREELANCER_DORKS = [
    'site:freelancermap.de "Vertrieb" "verfügbar" kontakt',
    'site:gulp.de "Sales" "freiberuflich" telefon',
    'site:twago.de "Vertriebsprofi" kontakt',
    'site:freelance.de "Handelsvertreter" "selbstständig"',
]

HANDELSVERTRETER_REGISTRY_DORKS = [
    'site:cdh.de "Handelsvertreter" "NRW" kontakt',
    'site:handelskammer.de "Handelsvertreter" telefon',
    '"Handelsvertreterregister" NRW kontakt',
    'site:ihk.de "Handelsvertreter" "Vertretung" kontakt',
]

# ══════════════════════════════════════════════════════════════
# IHK & CHAMBER OF COMMERCE DORKS (Hochqualitative Quellen)
# ══════════════════════════════════════════════════════════════

IHK_BUSINESS_DIRECTORY_DORKS = [
    # IHK Firmendatenbanken
    'site:ihk.de "Mitgliedsunternehmen" "Vertrieb" kontakt',
    'site:ihk-nordwestfalen.de "Unternehmen" telefon',
    'site:ihk-koeln.de "Firmenprofil" kontakt',
    'site:ihk-duesseldorf.de "Unternehmensprofil" telefon',
    'site:ihk-dortmund.de "Firmendatenbank" kontakt',
    'site:ihk-bonn.de "Mitglied" "Ansprechpartner" telefon',
    'site:ihk-aachen.de "Unternehmen" "Kontakt" telefon',
    'site:ihk-muenster.de "Firmenprofil" kontakt',
    'site:ihk-bielefeld.de "Mitgliedsunternehmen" telefon',
    # Weitere IHK Regionen
    'site:ihk-essen.de "Unternehmensprofil" kontakt',
    'site:ihk-niederrhein.de "Firmenprofil" telefon',
    'site:ihk-siegen.de "Mitglied" kontakt',
    'site:ihk-bochum.de "Unternehmen" telefon',
]

BUSINESS_DIRECTORY_DORKS = [
    # Unternehmensverzeichnisse
    'site:wlw.de "Vertrieb" "NRW" kontakt',
    'site:firmenabc.de "Ansprechpartner Vertrieb" telefon',
    'site:unternehmensregister.de "Geschäftsführung" "NRW" kontakt',
    'site:northdata.de "Vertriebsleiter" kontakt',
    'site:bundesanzeiger.de "Handelsregister" "Vertrieb" NRW',
    # Gelbe Seiten & Telefonbuch
    'site:gelbeseiten.de "Vertrieb" "NRW" telefon',
    'site:dasoertliche.de "Vertriebsleiter" kontakt',
    'site:11880.com "Sales Manager" telefon NRW',
    'site:telefonbuch.de "Account Manager" "NRW" telefon',
    # Branchenbücher
    'site:branchenbuch-deutschland.de "Vertrieb" telefon',
    'site:hotfrog.de "Sales" "NRW" kontakt',
    'site:cylex.de "Vertriebsleiter" telefon',
]

COMPANY_WEBSITE_DORKS = [
    # Unternehmens-Teamseiten
    'intitle:"Unser Team" "Vertriebsleiter" telefon NRW',
    'intitle:"Team" "Sales Manager" kontakt -site:linkedin.com',
    'intitle:"Ansprechpartner" "Vertrieb" telefon NRW',
    'intitle:"Kontakt" "Account Manager" telefon -site:xing.com',
    'inurl:team "Vertrieb" telefon NRW',
    'inurl:kontakt "Sales" telefon NRW',
    'inurl:impressum "Vertriebsleiter" telefon',
    'inurl:mitarbeiter "Account Manager" kontakt',
    'inurl:about "Vertrieb" telefon NRW',
    '"Ihr Ansprechpartner" "Vertrieb" telefon NRW',
    '"Ansprechpartner Vertrieb" kontakt -site:stepstone.de',
]

# ══════════════════════════════════════════════════════════════
# INDUSTRY-SPECIFIC SOURCES (Branchenspezifische Quellen)
# ══════════════════════════════════════════════════════════════

INDUSTRY_ASSOCIATION_DORKS = [
    # Branchenverbände
    'site:bvmw.de "Mitglied" "NRW" kontakt',
    'site:bdvb.de "Vertriebler" kontakt',
    'site:bdi.eu "Vertrieb" "NRW" telefon',
    'site:handelsverband-nrw.de "Mitgliedsunternehmen" kontakt',
    'site:einzelhandel.de "Vertrieb" "NRW" telefon',
    # Branchenportale
    '"Branchenverzeichnis" "Vertrieb" "NRW" telefon',
    '"Firmenverzeichnis" "Sales" kontakt NRW',
]

TRADE_FAIR_DORKS = [
    # Messekontakte und Ausstellerverzeichnisse
    'site:messe-duesseldorf.de "Aussteller" kontakt',
    'site:koelnmesse.de "Ausstellerprofil" telefon',
    'site:messe-essen.de "Unternehmen" kontakt',
    'site:messe-dortmund.de "Aussteller" telefon',
    '"Messekatalog" "Vertrieb" "NRW" kontakt',
    '"Ausstellerverzeichnis" telefon NRW',
]

STARTUP_ECOSYSTEM_DORKS = [
    # Startup-Szene (oft auf der Suche nach Sales-Talenten)
    'site:startplatz.de "Team" "Sales" kontakt',
    'site:startercenter-nrw.de "Gründer" "Vertrieb" telefon',
    'site:gruenderwoche.de "Unternehmen" "NRW" kontakt',
    '"Startup" "Sales Manager" "NRW" telefon',
    '"Scale-up" "Vertriebsleiter" kontakt NRW',
]

# ══════════════════════════════════════════════════════════════
# PROFESSIONAL NETWORKING SOURCES
# ══════════════════════════════════════════════════════════════

PROFESSIONAL_BLOG_DORKS = [
    # Vertriebsblogs und Fachportale
    'site:vertriebszeitung.de "Experte" kontakt',
    'site:salesbusiness.de "Gastautor" telefon',
    '"Vertriebsexperte" "NRW" kontakt -site:linkedin.com',
    '"Sales Expert" telefon NRW -site:xing.com',
    # Speaker und Trainer
    '"Vertriebstrainer" "NRW" kontakt',
    '"Sales Coach" telefon NRW',
    '"Keynote Speaker Vertrieb" kontakt',
]

EXPERT_DIRECTORY_DORKS = [
    # Expertenverzeichnisse
    'site:speakerservice.de "Vertrieb" kontakt',
    'site:trainerliste.de "Sales" telefon',
    '"Vertriebsberater" "NRW" kontakt telefon',
    '"Sales Consultant" "NRW" telefon',
    '"Interim Manager Vertrieb" kontakt NRW',
]

# ══════════════════════════════════════════════════════════════
# AUTOMOTIVE & REAL ESTATE (High-Value Industries)
# ══════════════════════════════════════════════════════════════

AUTOMOTIVE_SALES_DORKS = [
    # Automobilbranche (hohe Qualität)
    '"Autohaus" "Verkaufsberater" "NRW" telefon',
    '"KFZ-Handel" "Vertrieb" kontakt NRW',
    'site:mobile.de "Händler" "NRW" kontakt',
    'site:autoscout24.de "Händlerprofil" "NRW" telefon',
    '"Fahrzeugverkäufer" telefon NRW',
]

REAL_ESTATE_DORKS = [
    # Immobilienbranche
    'site:immobilienscout24.de "Makler" "NRW" telefon',
    'site:immowelt.de "Ansprechpartner" "NRW" kontakt',
    '"Immobilienmakler" telefon NRW',
    '"Immobilienberater" kontakt NRW',
    'site:ivd.net "Mitglied" "NRW" telefon',
]

# ══════════════════════════════════════════════════════════════
# TECH & IT SALES (High-Growth Sector)
# ══════════════════════════════════════════════════════════════

IT_SALES_DORKS = [
    # IT & Software Sales
    'site:it-matchmaker.com "Sales" "NRW" kontakt',
    '"IT-Vertrieb" telefon NRW',
    '"Software Sales" "NRW" kontakt',
    '"Cloud Sales" telefon "Deutschland"',
    '"SaaS Sales" kontakt NRW',
    '"Tech Sales" "NRW" telefon',
]

# ══════════════════════════════════════════════════════════════
# MINIMIERTE JOB SEEKER DORKS (nur Top-Performer behalten)
# ══════════════════════════════════════════════════════════════

# Basis-Dorks für Stellengesuche - REDUZIERT
JOB_SEEKER_DORKS = [
    # Nur die Top-Performer-Dorks behalten
    'site:kleinanzeigen.de/s-stellengesuche "vertrieb" "NRW"',
    'site:kleinanzeigen.de/s-stellengesuche "sales" telefon',
    'site:kleinanzeigen.de/s-stellengesuche "außendienst"',
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
        # Original Categories
        JOB_SEEKER_DORKS + 
        SITE_SPECIFIC_DORKS + 
        URL_PATTERN_DORKS + 
        CONTACT_PATTERN_DORKS + 
        POWER_DORKS +
        JOB_PORTAL_DORKS +
        MOBILE_DORKS +
        FREELANCER_DORKS +
        # New High-Quality Categories
        IHK_BUSINESS_DIRECTORY_DORKS +
        BUSINESS_DIRECTORY_DORKS +
        COMPANY_WEBSITE_DORKS +
        INDUSTRY_ASSOCIATION_DORKS +
        TRADE_FAIR_DORKS +
        STARTUP_ECOSYSTEM_DORKS +
        PROFESSIONAL_BLOG_DORKS +
        EXPERT_DIRECTORY_DORKS +
        AUTOMOTIVE_SALES_DORKS +
        REAL_ESTATE_DORKS +
        IT_SALES_DORKS
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
        # Original Categories
        "job_seeker": JOB_SEEKER_DORKS,
        "site_specific": SITE_SPECIFIC_DORKS,
        "url_pattern": URL_PATTERN_DORKS,
        "contact_pattern": CONTACT_PATTERN_DORKS,
        "power": POWER_DORKS,
        "job_portal": JOB_PORTAL_DORKS,
        "mobile": MOBILE_DORKS,
        "freelancer": FREELANCER_DORKS,
        # New High-Quality Categories
        "ihk_business": IHK_BUSINESS_DIRECTORY_DORKS,
        "business_directory": BUSINESS_DIRECTORY_DORKS,
        "company_website": COMPANY_WEBSITE_DORKS,
        "industry_association": INDUSTRY_ASSOCIATION_DORKS,
        "trade_fair": TRADE_FAIR_DORKS,
        "startup_ecosystem": STARTUP_ECOSYSTEM_DORKS,
        "professional_blog": PROFESSIONAL_BLOG_DORKS,
        "expert_directory": EXPERT_DIRECTORY_DORKS,
        "automotive": AUTOMOTIVE_SALES_DORKS,
        "real_estate": REAL_ESTATE_DORKS,
        "it_sales": IT_SALES_DORKS,
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
        # Original Categories
        "job_seeker": len(JOB_SEEKER_DORKS),
        "site_specific": len(SITE_SPECIFIC_DORKS),
        "url_pattern": len(URL_PATTERN_DORKS),
        "contact_pattern": len(CONTACT_PATTERN_DORKS),
        "power": len(POWER_DORKS),
        "job_portal": len(JOB_PORTAL_DORKS),
        "mobile": len(MOBILE_DORKS),
        "freelancer": len(FREELANCER_DORKS),
        # New High-Quality Categories
        "ihk_business": len(IHK_BUSINESS_DIRECTORY_DORKS),
        "business_directory": len(BUSINESS_DIRECTORY_DORKS),
        "company_website": len(COMPANY_WEBSITE_DORKS),
        "industry_association": len(INDUSTRY_ASSOCIATION_DORKS),
        "trade_fair": len(TRADE_FAIR_DORKS),
        "startup_ecosystem": len(STARTUP_ECOSYSTEM_DORKS),
        "professional_blog": len(PROFESSIONAL_BLOG_DORKS),
        "expert_directory": len(EXPERT_DIRECTORY_DORKS),
        "automotive": len(AUTOMOTIVE_SALES_DORKS),
        "real_estate": len(REAL_ESTATE_DORKS),
        "it_sales": len(IT_SALES_DORKS),
        "total": len(get_all_dorks()),
    }
