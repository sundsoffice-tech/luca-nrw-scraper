"""
LUCA NRW Scraper - Search Query Manager
========================================
Query building and search strategy management for different modes.
Extracted from scriptname.py in Phase 3 refactoring.
"""

import random
from typing import List, Optional


# =========================
# DEFAULT QUERIES
# =========================

DEFAULT_QUERIES: List[str] = [
    # --- GROUP A: AGENCY & PARTNER LISTS (B2B) ---
    'site:de "Unsere Vertriebspartner" "PLZ" "Mobil" -jobs',
    'site:de "Unsere Vertretungen" "Industrievertretung" "Kontakt"',
    'site:de "Vertriebsnetz" "Handelsvertretung" "Ansprechpartner"',
    'site:de "Gebietsvertretung" "PLZ" "Telefon" -stepstone -indeed',
    'site:de "Vertragshändler" "Maschinenbau" "Ansprechpartner"',
    'filetype:pdf "Vertreterliste" "Mobil" "PLZ" -bewerbung',
    'filetype:pdf "Preisliste" "Industrievertretung" "Kontakt"',
    'filetype:xlsx "Händlerverzeichnis" "Ansprechpartner" "Mobil"',
    '"Inhaltlich Verantwortlicher" "Handelsvertretung" "Mobil" -GmbH -UG',
    '"Angaben gemäß § 5 TMG" "Handelsvertretung" "Inhaber" "Mobil"',
    'inurl:impressum "Handelsvertretung" "powered by WordPress" "Mobil"',
    'site:cdh.de "Mitglied" "Kontakt"',

    # --- GROUP B: JOBSEEKERS & CVs (B2C) ---
    'filetype:pdf "Lebenslauf" "Vertrieb" "Mobil" "Wohnhaft" -muster -vorlage',
    'filetype:pdf "Curriculum Vitae" "Sales Manager" "Handy" -sample',
    'filetype:pdf "Bewerbung als" "Vertriebsmitarbeiter" "Anlagen" "Mobil"',
    'site:kleinanzeigen.de "Stellengesuch" "Vertrieb" -stellenangebot',
    'site:quoka.de "Stellengesuch" "Vertrieb" "Kontakt"',
    'site:markt.de "Jobgesuch" "Verkauf" "Mobil"',
    'site:linkedin.com/in/ "Suche neue Herausforderung" "Vertrieb" "Kontakt"',
    'site:xing.com/profile "ab sofort verfügbar" "Sales" "Mobil"',
]

NICHE_QUERIES = {
    "construction": [
        '("Werksvertretung" OR "Handelsvertretung") ("SHK" OR "Sanitär" OR "Heizung") "Gebietsleiter" "Mobil"',
        '("Bauelemente" OR "Fenster") ("Werksvertretung" OR "Fachhandelspartner") "PLZ" "Ansprechpartner"',
        'site:de ("Außendienst" OR "Vertriebsaußendienst") ("SHK" OR "Elektro") "Gebietsverkaufsleiter" "Kontakt"',
        'filetype:pdf "Fachpartnerliste" "Heizung" "Vertriebspartner" "Telefon"'
    ],
    "medical": [
        '("Medizinprodukteberater" OR "Klinikreferent") "Gebietsleiter" "Kontakt" "Mobil"',
        '("Außendienst" OR "Key Account Manager") ("Medizintechnik" OR "Medical Devices") "Region" "Deutschland"',
        'filetype:pdf "Lebenslauf" "Medizinprodukteberater" "Geburtsdatum" "Mobil"',
        'site:de "Unsere Außendienstmitarbeiter" "Medizintechnik" "Ansprechpartner"'
    ],
    "food": [
        '("Distributorenliste" OR "Distributor list") ("Food" OR "Lebensmittel") "Deutschland"',
        '("Großhandel" OR "Großhändler") "Gastronomie" "Vertriebspartner" "Kontakt"',
        '("Food Startup" OR "Getränke") "sucht Vertrieb" "Handelspartner"',
        'filetype:pdf "Vertriebspartner" "Getränke" "Kontakt" "Deutschland"'
    ]
}

# Freelancer & Modern Sales
FREELANCE_QUERIES = [
    # 1. Freelancer Portals (Scraping Profiles)
    'site:freelancermap.de "Vertrieb" "Deutschland" "verfügbar" -projekt',
    'site:freelance.de "Vertriebsfreelancer" "Kaltakquise" "Kontakt"',
    'site:freelancermap.de "Telesales" "Muttersprache Deutsch" "Mobil"',

    # 2. Modern Sales / Closer (High Ticket)
    '("High Ticket Closer" OR "Closer") "deutschsprachig" "Provision" "Kontakt"',
    '("Setter" OR "Appointment Setter") "Remote" "Vertrieb" "Gesuch"',
    '"Remote Vertrieb" "SaaS" "deutschsprachig" "Provision"',

    # 3. Trade Fair Lists (Germany)
    'site:.de filetype:pdf "Ausstellerverzeichnis" "Halle" "Kontakt" -2019 -2020',
    'site:.de filetype:xls "Ausstellerliste" "Vertrieb" "Telefon" "Deutschland"',
    '"Ausstellerverzeichnis" "Fachmesse" "Deutschland" "Mobil" filetype:pdf'
]

GUERILLA_QUERIES = [
    # 1. Insolvency & Layoffs (Trigger Events)
    '("Entlassungswelle" OR "Stellenabbau") "Vertrieb" "Deutschland" "2024" -news',
    '("Insolvenz" OR "Geschäftsaufgabe") "Vertriebsteam" "suche Job" site:linkedin.com',
    'site:kununu.com "Kündigung" "Vertrieb" "Bewertung" "2025"',

    # 2. Frustration & Advice (Community Hacking)
    'site:reddit.com ("Vertrieb" OR "Sales") "gekündigt" "was tun"',
    'site:wiwi-treff.de "Vertrieb" "Kündigung" "Wechsel" -stellenmarkt',
    'site:gutefrage.net "Vertrieb" "gekündigt" "neuer Job"',

    # 3. Career Changers (Quereinsteiger)
    '("Suche Job ohne Ausbildung" OR "Quereinstieg") "Vertrieb" "schnell Geld" site:.de',
    'site:urbia.de "Job ohne Ausbildung" "Vertrieb" "Teilzeit"',

    # 4. Social Public Posts (Real-time Signals)
    'site:facebook.com "Ich suche Arbeit" "Vertrieb" "bitte melden"',
    'site:instagram.com "Suche Job" "Vertrieb" "DM me"',
    'site:tiktok.com "Suche Job" "Sales" "Deutschland"',
    '("Job gesucht" OR "Arbeit gesucht") "Vertrieb" "#jobgesucht" site:.de'
]


def _build_default_queries() -> List[str]:
    """
    Build the complete default queries list by combining all query sources.
    
    This function is called once at module import to create DEFAULT_QUERIES.
    Separated into a function to avoid side effects during import.
    
    Returns:
        Combined list of all default queries
    """
    queries = DEFAULT_QUERIES.copy()
    
    # Add niche queries
    for industry_dorks in NICHE_QUERIES.values():
        queries.extend(industry_dorks)
    
    # Add freelance and guerilla queries
    queries.extend(FREELANCE_QUERIES)
    queries.extend(GUERILLA_QUERIES)
    
    return queries


# Build complete DEFAULT_QUERIES list
_COMPLETE_DEFAULT_QUERIES = _build_default_queries()

# For backward compatibility, we keep DEFAULT_QUERIES as the base list
# Users should use build_queries() function for mode-aware query building


# =========================
# INDUSTRY-SPECIFIC QUERIES
# =========================

INDUSTRY_QUERIES: dict[str, list[str]] = {
    "candidates": [
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 1: KLEINANZEIGEN STELLENGESUCHE (Primäre Quelle!)
        # ══════════════════════════════════════════════════════════════
        
        # Kleinanzeigen.de - Stellengesuche Vertrieb
        'site:kleinanzeigen.de/s-stellengesuche "vertrieb" "NRW"',
        'site:kleinanzeigen.de/s-stellengesuche "sales" "nordrhein-westfalen"',
        'site:kleinanzeigen.de/s-stellengesuche "außendienst" "erfahrung"',
        'site:kleinanzeigen.de/s-stellengesuche "key account" "suche"',
        'site:kleinanzeigen.de/s-stellengesuche "handelsvertreter" "freiberuflich"',
        'site:kleinanzeigen.de/s-stellengesuche "verkäufer" "mobil"',
        'site:kleinanzeigen.de/s-stellengesuche "kundenberater" "NRW"',
        'site:kleinanzeigen.de/s-stellengesuche "akquise" "erfahrung"',
        'site:kleinanzeigen.de/s-stellengesuche "telesales" "homeoffice"',
        'site:kleinanzeigen.de/s-stellengesuche "call center" "agent"',
        'site:kleinanzeigen.de "ich suche arbeit" "vertrieb"',
        'site:kleinanzeigen.de "suche stelle" "verkauf" "NRW"',
        'site:kleinanzeigen.de "biete meine dienste" "vertrieb"',
        
        # Markt.de - Stellengesuche
        'site:markt.de/stellengesuche "vertrieb"',
        'site:markt.de/stellengesuche "sales manager"',
        'site:markt.de/stellengesuche "außendienst" "PKW"',
        'site:markt.de/stellengesuche "handelsvertreter"',
        'site:markt.de "suche arbeit" "vertrieb" "NRW"',
        
        # Quoka - Stellengesuche
        'site:quoka.de/stellengesuche "vertrieb"',
        'site:quoka.de/stellengesuche "verkauf" "erfahrung"',
        'site:quoka.de "suche job" "sales"',
        
        # Kalaydo (Regional NRW)
        'site:kalaydo.de/stellengesuche "vertrieb"',
        'site:kalaydo.de "suche stelle" "außendienst"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 2: BUSINESS NETZWERKE (Xing, LinkedIn)
        # ══════════════════════════════════════════════════════════════
        
        # Xing - Offene Kandidaten
        'site:xing.com/profile "offen für angebote" "vertrieb" "NRW"',
        'site:xing.com/profile "auf jobsuche" "sales"',
        'site:xing.com/profile "suche neue herausforderung" "key account"',
        'site:xing.com/profile "verfügbar ab" "vertriebsleiter"',
        'site:xing.com/profile "in ungekündigter stellung" "außendienst"',
        'site:xing.com/profile "wechselwillig" "sales manager"',
        'site:xing.com "freiberuflicher handelsvertreter" "sucht"',
        'site:xing.com "sales" "open to work" "düsseldorf"',
        'site:xing.com "vertrieb" "neue chancen" "köln"',
        'site:xing.com "b2b vertrieb" "suche" "NRW"',
        
        # LinkedIn - Open to Work
        'site:linkedin.com/in "open to work" "sales" "germany"',
        'site:linkedin.com/in "offen für" "vertrieb" "NRW"',
        'site:linkedin.com/in "looking for" "sales" "düsseldorf"',
        'site:linkedin.com/in "seeking" "business development" "köln"',
        'site:linkedin.com/in "available" "account manager" "essen"',
        'site:linkedin.com/in "#opentowork" "vertrieb"',
        'site:linkedin.com "actively looking" "sales representative" "germany"',
        'site:linkedin.com "job seeker" "key account" "NRW"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 3: SOCIAL MEDIA (Facebook, Instagram, TikTok)
        # ══════════════════════════════════════════════════════════════
        
        # Facebook - Job Suche Posts
        'site:facebook.com "suche neue herausforderung" "vertrieb"',
        'site:facebook.com "suche arbeit" "sales" "NRW"',
        'site:facebook.com "wer kennt wen" "vertriebsjob"',
        'site:facebook.com "bin auf jobsuche" "verkauf"',
        'site:facebook.com "suche stelle" "außendienst" "erfahrung"',
        'site:facebook.com/groups "vertriebler" "jobsuche"',
        'site:facebook.com/groups "sales jobs" "deutschland"',
        'site:facebook.com "freelancer" "vertrieb" "verfügbar"',
        'site:facebook.com "gekündigt" "vertrieb" "suche"',
        
        # Instagram - Job Seeker Bios
        'site:instagram.com "open for work" "sales"',
        'site:instagram.com "job gesucht" "vertrieb"',
        'site:instagram.com "DM for work" "sales"',
        'site:instagram.com "suche job" "verkauf"',
        'site:instagram.com "available for hire" "business"',
        'site:instagram.com "freelancer" "vertrieb" "kontakt"',
        
        # TikTok - Karriere Content
        'site:tiktok.com "jobsuche" "vertrieb"',
        'site:tiktok.com "suche arbeit" "sales"',
        'site:tiktok.com "arbeitslos" "vertriebler"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 4: MESSENGER GRUPPEN (Telegram, WhatsApp, Discord)
        # ══════════════════════════════════════════════════════════════
        
        # Telegram - Öffentliche Gruppen
        'site:t.me "vertrieb" "jobs" "gruppe"',
        'site:t.me "sales jobs" "germany"',
        'site:t.me "jobsuche" "NRW"',
        'site:t.me "vertriebler" "netzwerk"',
        'site:t.me "stellengesuche" "vertrieb"',
        'site:t.me/joinchat "vertrieb"',
        'site:t.me/joinchat "sales" "jobs"',
        'site:t.me "vertrieb" "NRW" OR "düsseldorf" OR "köln"',
        'site:t.me "sales jobs" "deutschland" "nrw"',
        'site:t.me "handelsvertreter" "gruppe"',
        '"telegram gruppe" "vertrieb" "NRW"',
        
        # WhatsApp - Öffentliche Einladungslinks
        'site:chat.whatsapp.com "vertrieb" "jobs"',
        'site:chat.whatsapp.com "sales" "netzwerk"',
        'site:chat.whatsapp.com "vertriebler" "gruppe"',
        'site:chat.whatsapp.com "jobsuche" "NRW"',
        'site:chat.whatsapp.com "vertrieb" "nrw"',
        'site:chat.whatsapp.com "sales" "düsseldorf"',
        '"whatsapp gruppe" "vertriebler" "köln"',
        
        # Discord - Karriere Server
        'site:discord.gg "vertrieb" "jobs"',
        'site:discord.gg "sales" "karriere"',
        'site:discord.com/invite "jobs" "deutschland"',
        'site:discord.gg "vertrieb" "deutschland"',
        'site:discord.com/invite "sales" "karriere"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 5: FOREN & COMMUNITIES
        # ══════════════════════════════════════════════════════════════
        
        # Reddit - Deutsche Karriere-Subreddits
        'site:reddit.com/r/arbeitsleben "vertrieb" "neuer job"',
        'site:reddit.com/r/arbeitsleben "sales" "kündigung"',
        'site:reddit.com/r/arbeitsleben "außendienst" "wechsel"',
        'site:reddit.com/r/de_EDV "vertrieb" "jobsuche"',
        'site:reddit.com/r/FragReddit "vertriebsjob" "erfahrung"',
        'site:reddit.com/r/Finanzen "vertrieb" "gehalt" "wechsel"',
        'site:reddit.com "gekündigt" "sales" "was tun"',
        'site:reddit.com "arbeitslos" "vertrieb" "bewerbung"',
        
        # Gutefrage.net
        'site:gutefrage.net "vertrieb" "stelle suchen"',
        'site:gutefrage.net "sales job" "erfahrung"',
        'site:gutefrage.net "außendienst" "bewerbung"',
        'site:gutefrage.net "handelsvertreter werden"',
        
        # Wer-weiss-was.de
        'site:wer-weiss-was.de "vertriebsjob" "suche"',
        'site:wer-weiss-was.de "sales karriere"',
        
        # Motor-Talk (Autoverkäufer)
        'site:motor-talk.de "autoverkäufer" "suche stelle"',
        'site:motor-talk.de "verkaufsberater" "wechsel"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 6: FREELANCER PORTALE
        # ══════════════════════════════════════════════════════════════
        
        # Freelancer Profile
        'site:freelancermap.de "vertrieb" "verfügbar"',
        'site:freelancermap.de "sales" "freiberufler"',
        'site:freelance.de "vertriebsexperte" "profil"',
        'site:freelance.de "handelsvertreter" "selbstständig"',
        'site:gulp.de "sales" "verfügbar"',
        'site:gulp.de "vertrieb" "freiberuflich"',
        
        # Fiverr/Upwork (Vertriebs-Freelancer)
        'site:fiverr.com "sales" "germany" "b2b"',
        'site:upwork.com "sales representative" "german"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 7: LEBENSLAUF-DATENBANKEN & JOBPORTALE
        # ══════════════════════════════════════════════════════════════
        
        # Lebenslauf-Portale (wo Kandidaten sich eintragen)
        'site:lebenslaufmuster.de "vertrieb" "berufserfahrung"',
        '"mein lebenslauf" "vertrieb" "NRW" "mobil" filetype:pdf',
        '"curriculum vitae" "sales" "germany" "phone" filetype:pdf',
        '"bewerbung" "vertriebserfahrung" "kontakt" filetype:pdf',
        
        # StepStone Kandidatenprofile
        'site:stepstone.de/kandidat "vertrieb"',
        'site:stepstone.de "profil" "sales manager"',
        
        # Indeed Kandidatensuche
        'site:indeed.com/r "vertrieb" "NRW"',
        'site:indeed.com "lebenslauf" "sales"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 8: BRANCHEN-SPEZIFISCHE KANDIDATEN
        # ══════════════════════════════════════════════════════════════
        
        # D2D / Door-to-Door Vertriebler
        'site:kleinanzeigen.de "d2d" "suche" "erfahrung"',
        '"door to door" "vertriebler" "sucht" "mobil"',
        '"haustürgeschäft" "erfahrung" "suche arbeit"',
        'site:kleinanzeigen.de/s-stellengesuche "haustür" "NRW"',
        'site:kleinanzeigen.de/s-stellengesuche "außendienst" "erfahrung" "NRW"',
        
        # Call Center / Telesales
        '"call center agent" "suche" "homeoffice" "NRW"',
        '"telesales" "erfahrung" "suche stelle"',
        '"telefonvertrieb" "freiberuflich" "verfügbar"',
        'site:kleinanzeigen.de "telefonverkäufer" "suche"',
        
        # Energie / Solar Vertriebler
        '"solarvertrieb" "suche" "erfahrung" "NRW"',
        '"energieberater" "freiberuflich" "sucht"',
        '"photovoltaik" "vertrieb" "suche stelle"',
        'site:kleinanzeigen.de/s-stellengesuche "solar" "NRW"',
        'site:kleinanzeigen.de/s-stellengesuche "photovoltaik" "köln"',
        'site:kleinanzeigen.de/s-stellengesuche "energie" "düsseldorf"',
        
        # Versicherung / Finanz
        '"versicherungsvertreter" "suche" "neue"',
        '"finanzberater" "wechselwillig" "kontakt"',
        '"makler" "sucht" "neue herausforderung"',
        'site:kleinanzeigen.de/s-stellengesuche "versicherung" "NRW"',
        'site:kleinanzeigen.de/s-stellengesuche "finanzberater" "köln"',
        
        # Telekommunikation
        '"telekom vertrieb" "suche" "erfahrung"',
        '"mobilfunk" "sales" "suche stelle"',
        '"provider" "vertrieb" "wechsel"',
        'site:kleinanzeigen.de/s-stellengesuche "telekom" "NRW"',
        'site:kleinanzeigen.de/s-stellengesuche "mobilfunk" "düsseldorf"',
        
        # Medizin / Pharma
        '"pharmareferent" "sucht" "neue"',
        '"medizinprodukteberater" "verfügbar"',
        '"healthcare sales" "germany" "open"',
        
        # IT / Software
        '"software sales" "suche" "germany"',
        '"it vertrieb" "suche stelle" "NRW"',
        '"saas" "account executive" "open to"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 9: REGIONALE NRW-SUCHE
        # ══════════════════════════════════════════════════════════════
        
        # Düsseldorf
        '"vertrieb" "suche" "düsseldorf" "mobil"',
        '"sales" "jobsuche" "düsseldorf" "kontakt"',
        'site:xing.com "vertrieb" "düsseldorf" "offen für"',
        
        # Köln
        '"vertrieb" "suche" "köln" "erfahrung"',
        '"außendienst" "köln" "suche stelle"',
        'site:linkedin.com "sales" "köln" "open"',
        
        # Essen/Ruhrgebiet
        '"vertrieb" "essen" "suche" "mobil"',
        '"sales" "ruhrgebiet" "jobsuche"',
        '"dortmund" "vertrieb" "suche stelle"',
        
        # Weitere NRW Städte
        '"vertrieb" "wuppertal" "suche"',
        '"sales" "bonn" "suche stelle"',
        '"außendienst" "münster" "suche"',
        '"vertrieb" "bielefeld" "jobsuche"',
        '"verkauf" "aachen" "suche stelle"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 10: KARRIERE-EVENTS & NETZWERKE
        # ══════════════════════════════════════════════════════════════
        
        # Karrieremessen Teilnehmer
        '"jobmesse" "NRW" "vertrieb" "besucher"',
        '"karrieretag" "düsseldorf" "sales"',
        '"connecticum" "vertrieb" "teilnehmer"',
        
        # Vertriebler-Netzwerke
        'site:vertriebsmanager.de "mitglied" "profil"',
        'site:salesjob.de "kandidat" "profil"',
        '"bdvt" "mitglied" "vertrieb" "kontakt"',
        
        # Alumni-Netzwerke
        '"sales" "alumni" "NRW" "kontakt"',
        '"vertrieb" "absolvent" "suche stelle"',
    ],
    
    "talent_hunt": [
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 1: LINKEDIN PROFILES (OHNE #opentowork - aktive Vertriebler!)
        # ══════════════════════════════════════════════════════════════
        
        # LinkedIn Profile - Aktive Account Manager
        'site:linkedin.com/in "Account Manager" "NRW" -"#opentowork"',
        'site:linkedin.com/in "Sales Manager" ("Düsseldorf" OR "Köln" OR "Dortmund") -"#opentowork"',
        'site:linkedin.com/in "Vertriebsleiter" "Nordrhein-Westfalen" -"open to work"',
        'site:linkedin.com/in "Key Account" "NRW" "Jahre Erfahrung" -"#opentowork"',
        'site:linkedin.com/in "Außendienst" ("NRW" OR "Ruhrgebiet") -"open to work"',
        'site:linkedin.com/in "Business Development" "NRW" -"#opentowork"',
        'site:linkedin.com/in "Senior Sales" "Deutschland" -"#opentowork"',
        'site:linkedin.com/in "Vertriebsmitarbeiter" "Köln" -"open to work"',
        'site:linkedin.com/in "Regional Sales" "NRW" -"#opentowork"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 2: XING PROFILE (Aktive Vertriebler)
        # ══════════════════════════════════════════════════════════════
        
        # Xing Profile - Etablierte Vertriebler
        'site:xing.com/profile "Vertriebsmitarbeiter" "NRW"',
        'site:xing.com/profile "Handelsvertreter" "Nordrhein-Westfalen"',
        'site:xing.com/profile "Sales Representative" "Deutschland"',
        'site:xing.com/profile "Außendienstmitarbeiter" kontakt',
        'site:xing.com/profile "Account Manager" "Düsseldorf"',
        'site:xing.com/profile "Key Account" "Köln" "Berufserfahrung"',
        'site:xing.com/profile "Vertriebsleiter" "Dortmund"',
        'site:xing.com/profile "Sales Director" "NRW"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 3: HANDELSVERTRETER-REGISTER & VERBÄNDE
        # ══════════════════════════════════════════════════════════════
        
        # Offizielle Register
        'site:cdh.de "Handelsvertreter" "NRW" kontakt',
        'site:handelskammer.de "Handelsvertreter" telefon',
        '"Handelsvertreterregister" NRW kontakt email',
        'site:ihk.de "Handelsvertreter" "Vertretung" kontakt',
        'site:bdvi.de "Mitglied" "NRW" kontakt',
        '"Verband deutscher Handelsvertreter" NRW',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 4: FIRMEN-TEAM-SEITEN (Dort sind Vertriebler gelistet!)
        # ══════════════════════════════════════════════════════════════
        
        # Team-Seiten mit Vertriebs-Kontakten
        'intitle:"Unser Team" "Vertrieb" "NRW" kontakt',
        'intitle:"Team" "Sales" ("Düsseldorf" OR "Köln") telefon',
        '"Ansprechpartner Vertrieb" telefon NRW',
        '"Ihr Ansprechpartner" "Außendienst" kontakt',
        'inurl:team "Vertriebsleiter" telefon',
        'inurl:mitarbeiter "Account Manager" email',
        'intitle:"Unser Team" "Key Account" kontakt',
        '"Team Vertrieb" telefon NRW',
        'inurl:about "Sales Team" kontakt',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 5: FREELANCER-PORTALE (Aktive Vertriebler)
        # ══════════════════════════════════════════════════════════════
        
        # Freiberufler-Profile
        'site:freelancermap.de "Vertrieb" "verfügbar" kontakt',
        'site:gulp.de "Sales" "freiberuflich" telefon',
        'site:twago.de "Vertriebsprofi" kontakt',
        'site:freelance.de "Handelsvertreter" "selbstständig"',
        'site:freelancermap.de "Business Development" "verfügbar"',
        'site:gulp.de "Account Manager" "freiberuflich"',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 6: LEBENSLAUF-DATENBANKEN (Sichtbare Profile)
        # ══════════════════════════════════════════════════════════════
        
        # PDF Lebensläufe mit Kontaktdaten
        'filetype:pdf "Lebenslauf" "Vertriebserfahrung" "NRW"',
        'filetype:pdf "CV" "Sales Manager" "Düsseldorf"',
        'filetype:pdf "Außendienst" "Berufserfahrung" kontakt',
        'filetype:pdf "Vertrieb" "Key Account" telefon NRW',
        'filetype:pdf "Sales Representative" "Germany" email',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 7: BRANCHENSPEZIFISCHE VERTRIEBLER
        # ══════════════════════════════════════════════════════════════
        
        # Solar/Energie Vertriebler
        'site:linkedin.com/in "Solar" "Vertrieb" "NRW" -"#opentowork"',
        'site:xing.com/profile "Photovoltaik" "Vertrieb" kontakt',
        '"Energieberater" "Vertrieb" kontakt NRW',
        'site:linkedin.com/in "Erneuerbare Energien" "Sales" "Deutschland" -"#opentowork"',
        
        # Versicherung Vertriebler
        'site:linkedin.com/in "Versicherung" "Außendienst" "NRW" -"#opentowork"',
        'site:xing.com/profile "Versicherungsvertrieb" kontakt',
        '"Versicherungsmakler" "selbstständig" kontakt NRW',
        
        # Telekommunikation Vertriebler
        'site:linkedin.com/in "Telekommunikation" "Sales" "NRW" -"#opentowork"',
        'site:xing.com/profile "Telekom" "Vertrieb" kontakt',
        '"Mobilfunk" "Vertrieb" kontakt NRW',
        
        # Automotive Vertriebler
        'site:linkedin.com/in "Automotive" "Sales" "NRW" -"#opentowork"',
        'site:xing.com/profile "Autoverkäufer" kontakt',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 8: MESSE-/EVENT-TEILNEHMER (Vertriebler gehen zu Messen!)
        # ══════════════════════════════════════════════════════════════
        
        # Messe-Ansprechpartner
        '"Messestand" "Vertrieb" "Ansprechpartner" NRW',
        'site:xing.com/events "Vertrieb" "NRW" teilnehmer',
        '"Messe Düsseldorf" "Sales" "Kontakt"',
        '"IHK Veranstaltung" "Vertrieb" telefon',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 9: UNTERNEHMENSWEBSEITEN - KONTAKTSEITEN
        # ══════════════════════════════════════════════════════════════
        
        # Kontakt-Seiten mit Vertriebs-Ansprechpartnern
        'inurl:kontakt "Vertrieb" telefon NRW',
        'inurl:contact "Sales" email NRW',
        '"Vertriebsleitung" kontakt telefon',
        '"Sales Manager" "direkt erreichen" telefon',
        
        # ══════════════════════════════════════════════════════════════
        # KATEGORIE 10: GESCHÄFTSFÜHRER MIT VERTRIEBSHINTERGRUND
        # ══════════════════════════════════════════════════════════════
        
        # Geschäftsführer/Inhaber mit Sales-Background
        'site:linkedin.com/in "Geschäftsführer" "ehemals Vertrieb" "NRW" -"#opentowork"',
        'site:xing.com/profile "Inhaber" "Handelsvertreter" kontakt',
        '"Selbstständiger Vertriebsprofi" kontakt NRW',
    ],
}

# NEU: Recruiter-spezifische Queries für Vertriebler-Rekrutierung
RECRUITER_QUERIES = {
    'recruiter': [
        'site:kleinanzeigen.de/s-stellengesuche/ "außendienst" NRW',
        'site:kleinanzeigen.de/s-stellengesuche/ "handelsvertreter" NRW',
        'site:kleinanzeigen.de/s-stellengesuche/ "verkauf" NRW',
        'site:kleinanzeigen.de/s-stellengesuche/ "kundenberater" NRW',
        'site:kleinanzeigen.de/s-stellengesuche/ "suche job" "vertrieb" NRW',
        'site:kleinanzeigen.de/s-stellengesuche/ "arbeit" "verkauf" NRW',
        'site:kleinanzeigen.de/s-stellengesuche/ "quereinsteiger" "vertrieb" NRW',
        # Facebook Gruppen & Profile
        'site:facebook.com "suche arbeit" "vertrieb" ("017" OR "016" OR "015" OR "+49")',
        'site:facebook.com/groups/ "stellengesuche" ("017" OR "016")',
        'site:facebook.com "jobsuche" "verkauf" ("017" OR "016" OR "015")',
    ]
}


# =========================
# QUERY BUILDING FUNCTIONS
# =========================

def build_queries(
    selected_industry: Optional[str] = None,
    per_industry_limit: int = 20000
) -> List[str]:
    """
    Build a compact set of high-precision Handelsvertreter dorks.
    If candidates/recruiter/talent_hunt mode is selected, use INDUSTRY_QUERIES accordingly.
    
    Args:
        selected_industry: Industry/mode to use (candidates, recruiter, talent_hunt, or None for standard)
        per_industry_limit: Maximum number of queries to return
        
    Returns:
        List of search queries
    """
    # CRITICAL FIX: Use appropriate queries based on mode
    if selected_industry and selected_industry.lower() in ("candidates", "recruiter", "talent_hunt"):
        base = INDUSTRY_QUERIES.get(selected_industry.lower(), [])
        queries = list(dict.fromkeys(base))
        random.shuffle(queries)
        cap = min(max(1, per_industry_limit), len(queries))
        return queries[:cap]
    
    # Standard mode: use complete default queries list (including niche, freelance, guerilla)
    queries: List[str] = list(dict.fromkeys(_COMPLETE_DEFAULT_QUERIES))
    random.shuffle(queries)

    cap = min(max(1, per_industry_limit), len(queries))
    return queries[:cap]
