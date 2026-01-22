"""
LUCA NRW Scraper - Search Query Manager
========================================
Query building and search strategy management for different modes.
Extracted from scriptname.py in Phase 3 refactoring.
"""

import random
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


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
    
    # ══════════════════════════════════════════════════════════════
    # NEU: HANDELSVERTRETER (90+ Quellen - Erweiterte Konfiguration)
    # Zielgruppe: Handelsvertreter + selbständige Vertriebs-/Außendienstkräfte in NRW/DE
    # ══════════════════════════════════════════════════════════════
    "handelsvertreter": [
        # ──────────────────────────────────────────────────────────
        # PRIORITÄT 6 (HÖCHST!): HANDELSREGISTER & OFFIZIELLE REGISTER
        # Domains: handelsregister.de, it.nrw, bundesanzeiger.de, ag-koeln.nrw.de, ag-duesseldorf.nrw.de
        # ──────────────────────────────────────────────────────────
        'site:handelsregister.de "Nordrhein-Westfalen" (Vertrieb OR Außendienst OR Handelsvertreter OR selbständige)',
        'site:it.nrw/thema/unternehmensregister (Vertrieb OR Handelsvertreter OR selbständige) (Köln OR Düsseldorf OR Essen)',
        'site:bundesanzeiger.de (Vertrieb OR Außendienst OR Handelsvertreter) "Nordrhein-Westfalen" (Geschäftsführer OR GF)',
        'site:ag-koeln.nrw.de Handelsregister (Vertrieb OR Handelsvertreter OR selbständig)',
        'site:ag-duesseldorf.nrw.de Handelsregister (Außendienst OR Vertrieb OR selbständige)',
        
        # ──────────────────────────────────────────────────────────
        # PRIORITÄT 5: TOP HANDELSVERTRETER-PORTALE
        # Domains: handelsvertreter.de, cdh.de, handelsvertreter-netzwerk.de
        # ──────────────────────────────────────────────────────────
        'site:handelsvertreter.de (NRW OR Köln OR Düsseldorf OR Essen OR Dortmund) (Telefon OR Mobil OR @ OR Kontakt)',
        'site:cdh.de (Institutionen OR Mitglieder OR Partner) (NRW OR Ruhrgebiet) (Telefon OR Kontakt OR E-Mail)',
        'site:cdh.de "Handelsvertreter" "sucht Vertretung" kontakt',
        'site:cdh.de "freie Kapazitäten" "Handelsvertreter"',
        'site:cdh.de/boerse "Handelsvertretersuche"',
        'site:handelsvertreter-netzwerk.de (NRW OR Köln OR Düsseldorf OR selbständig) (Profil OR Kontakt OR Handy)',
        
        # ──────────────────────────────────────────────────────────
        # PRIORITÄT 4: B2B-VERZEICHNISSE
        # Domains: gelbeseiten.de, dasoertliche.de, 11880.com
        # ──────────────────────────────────────────────────────────
        'site:gelbeseiten.de (Handelsvertreter OR Außendienst OR Gebietsvertreter OR selbständig) ("40000" OR "50000" OR "51000") (Telefon OR Mobil OR Kontakt)',
        'site:gelbeseiten.de "Handelsvertretung" ("NRW" OR "Nordrhein-Westfalen") telefon',
        'site:dasoertliche.de (Vertrieb OR Handelsvertreter OR selbständige) (Köln OR Düsseldorf OR Essen OR Dortmund) (Telefon OR Handy)',
        'site:dasoertliche.de "Vertriebsservice" (Düsseldorf OR Köln OR Dortmund OR Essen OR Duisburg OR Bochum)',
        'site:11880.com (Außendienst OR Vertrieb OR Handelsvertreter OR selbständig) NRW (Telefon OR Kontakt OR E-Mail)',
        'site:11880.com "Außendienst" OR "Handelsvertreter" NRW telefon',
        
        # ──────────────────────────────────────────────────────────
        # PRIORITÄT 4: FIRMENLISTEN & DATENBANKEN
        # Domains: listflix.de, adressbar.de, firmendatenbanken.de, datenparty.com
        # ──────────────────────────────────────────────────────────
        'site:listflix.de (handelsvertreter OR selbständige OR außendienst) (NRW OR Köln OR Düsseldorf OR Ruhrgebiet)',
        'site:adressbar.de (Handelsvertreter OR selbständige Vertrieb) (Nordrhein-Westfalen OR NRW)',
        'site:firmendatenbanken.de/firmen/liste/handelsvertreter (NRW OR Köln)',
        'site:datenparty.com (handelsvertreter OR selbständige) (Telefon OR E-Mail OR Kontakt)',
        
        # ──────────────────────────────────────────────────────────
        # PRIORITÄT 3: LOKALE NRW + VERBÄNDE
        # Domains: koeln.business, direktvertrieb.de, vertriebsoffice.de, ihk.de
        # ──────────────────────────────────────────────────────────
        'site:koeln.business (Vertrieb OR Außendienst OR Handelsvertreter OR selbständig) (Telefon OR Kontakt)',
        'site:direktvertrieb.de (Kooperationspartner OR Mitglieder OR selbständige) (Telefon OR Kontakt)',
        'site:vertriebsoffice.de/branchenbuch (Direktvertrieb OR Handelsvertreter) (NRW OR Köln)',
        'site:ihk.de/nordwestfalen (Firmenverzeichnis OR Mitglieder) (Vertrieb OR Handelsvertreter)',
        'site:ihk.de "Handelsvertreter" ("NRW" OR "Düsseldorf" OR "Köln") kontakt',
        'site:ihk.de "Handelsvertreterbörse" kontakt',
        'site:handelskammer.de "Handelsvertreter" "Vertretung gesucht"',
        
        # ──────────────────────────────────────────────────────────
        # PRIORITÄT 4: IHK & REGIONALE KAMMERN
        # ──────────────────────────────────────────────────────────
        'site:ihk-koeln.de "Vertrieb" kontakt',
        'site:ihk-duesseldorf.de "Vertrieb" kontakt',
        'site:ihk-dortmund.de "Vertrieb" kontakt',
        'site:northdata.de ("Vertriebsleitung" OR "Handelsvertretung") NRW',
        'site:bvmw.de "Mitglied" ("NRW" OR "Nordrhein-Westfalen") "Vertrieb" kontakt',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: KLEINANZEIGEN STELLENGESUCHE (Primäre Quelle!)
        # ──────────────────────────────────────────────────────────
        'site:kleinanzeigen.de/s-stellengesuche "handelsvertreter"',
        'site:kleinanzeigen.de/s-stellengesuche "freier handelsvertreter"',
        'site:kleinanzeigen.de/s-stellengesuche "industrievertretung"',
        'site:kleinanzeigen.de/s-stellengesuche "handelsvertretung" "suche"',
        'site:kleinanzeigen.de/s-stellengesuche "vertretung" "provision"',
        'site:kleinanzeigen.de/s-stellengesuche "selbstständiger vertreter"',
        'site:kleinanzeigen.de "handelsvertreter" "suche vertretung"',
        'site:kleinanzeigen.de "freiberuflicher handelsvertreter" "suche"',
        'site:markt.de/stellengesuche "handelsvertreter"',
        'site:markt.de/stellengesuche "industrievertretung"',
        'site:markt.de "handelsvertretung" "suche"',
        'site:quoka.de/stellengesuche "handelsvertreter"',
        'site:quoka.de "suche vertretung" "provision"',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: BUSINESS NETZWERKE (Xing, LinkedIn)
        # ──────────────────────────────────────────────────────────
        'site:xing.com/profile "Handelsvertreter" "offen für angebote"',
        'site:xing.com/profile "Handelsvertretung" "suche"',
        'site:xing.com/profile "freie Handelsvertretung" "NRW"',
        'site:xing.com/profile "Industrievertretung" "Vertretung gesucht"',
        'site:xing.com "Handelsvertreter" "neue Vertretung" kontakt',
        'site:xing.com "selbstständiger Handelsvertreter" "suche"',
        'site:linkedin.com/in "Handelsvertreter" "open to" germany',
        'site:linkedin.com/in "freier Handelsvertreter" "suche"',
        'site:linkedin.com/in "Industrievertretung" "verfügbar"',
        'site:linkedin.com/in "Handelsvertretung" "neue Mandate"',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: SOCIAL MEDIA
        # ──────────────────────────────────────────────────────────
        'site:facebook.com "Handelsvertreter" "suche Vertretung"',
        'site:facebook.com/groups "Handelsvertreter" "freie Kapazitäten"',
        'site:facebook.com "freier Handelsvertreter" "suche Mandate"',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: WEITERE B2B-VERZEICHNISSE
        # Domains: wlw.de, cylex.de, hotfrog.de, firmenabc.de
        # ──────────────────────────────────────────────────────────
        'site:wlw.de "Vertrieb" "Nordrhein-Westfalen" ("Ansprechpartner" OR "kontakt")',
        'site:cylex.de "Vertriebspartner" ("Düsseldorf" OR "Köln" OR "Dortmund") kontakt',
        'site:hotfrog.de "Handelsvertreter" "NRW" kontakt',
        'site:firmenabc.de "Handelsvertretung" kontakt',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: BRANCHEN-SPEZIFISCH
        # ──────────────────────────────────────────────────────────
        # SHK/Sanitär/Heizung
        '"Handelsvertreter" "SHK" "suche Vertretung" kontakt',
        '"Industrievertretung" "Sanitär" "Heizung" "freie Kapazitäten"',
        'site:kleinanzeigen.de "Handelsvertreter" "SHK" "suche"',
        
        # Elektro/Elektronik
        '"Handelsvertreter" "Elektrotechnik" "suche Vertretung"',
        '"Industrievertretung" "Elektronik" "freie Kapazität"',
        
        # Maschinenbau
        '"Handelsvertreter" "Maschinenbau" "suche Mandate"',
        '"Industrievertretung" "Werkzeug" "suche"',
        
        # Lebensmittel/Food
        '"Handelsvertreter" "Lebensmittel" "suche Vertretung"',
        '"Handelsvertreter" "Food" "freie Kapazitäten"',
        
        # Bau/Bauelemente
        '"Handelsvertreter" "Bauelemente" "suche"',
        '"Industrievertretung" "Baustoffe" "freie Kapazität"',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: REGIONALE NRW-SUCHE (Erweitert)
        # ──────────────────────────────────────────────────────────
        '"Handelsvertreter" "suche Vertretung" "Düsseldorf" kontakt',
        '"Handelsvertreter" "suche" "Köln" "NRW"',
        '"Industrievertretung" "Ruhrgebiet" "freie Kapazitäten"',
        '"freier Handelsvertreter" "Münsterland" "suche"',
        '"Handelsvertreter" (Essen OR Dortmund OR Bochum) (Telefon OR Kontakt)',
        '"selbständiger Außendienst" "NRW" (Mobil OR Telefon OR Kontakt)',
        '"Vertriebskraft" "Nordrhein-Westfalen" (selbständig OR freiberuflich) Kontakt',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: SPEZIFISCHE SUCHFORMULIERUNGEN
        # ──────────────────────────────────────────────────────────
        '"suche Vertretung" "Handelsvertreter" "Provision" kontakt',
        '"freie Kapazitäten" "Handelsvertreter" "Außendienst" telefon',
        '"Vertretung gesucht" "selbstständig" "Provision" mobil',
        '"neue Mandate" "Handelsvertreter" "Deutschland" kontakt',
        '"Industrievertretung" "suche Hersteller" kontakt',
        '"biete Handelsvertretung" "Erfahrung" telefon',
        '"Handelsvertreter" "Sortimentserweiterung" "suche"',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: MESSEN & EVENTS
        # ──────────────────────────────────────────────────────────
        'site:messe-duesseldorf.de "Aussteller" "Ansprechpartner" kontakt',
        'site:koelnmesse.de "Ausstellerprofil" ("Vertrieb" OR "Sales") telefon',
        'site:messe-essen.de "Aussteller" "Ansprechpartner" kontakt telefon',
        '("Messekatalog" OR "Ausstellerverzeichnis") ("Vertrieb" OR "Sales") NRW kontakt telefon',
        
        # ──────────────────────────────────────────────────────────
        # KATEGORIE: FREELANCER & PROJEKTBÖRSEN
        # ──────────────────────────────────────────────────────────
        'site:freelancermap.de ("Vertrieb" OR "Sales") "verfügbar" NRW kontakt',
        'site:freelance.de ("Handelsvertreter" OR "Vertriebsprofi") "freiberuflich" kontakt',
        'site:gulp.de ("Sales" OR "Business Development") NRW verfügbar telefon',
    ],
    
    # ══════════════════════════════════════════════════════════════
    # NEU: D2D (Door-to-Door)
    # ══════════════════════════════════════════════════════════════
    "d2d": [
        # Bestehende Queries
        '"door to door" "vertriebler" "sucht" "mobil"',
        '"haustürgeschäft" "erfahrung" "suche arbeit"',
        'site:kleinanzeigen.de/s-stellengesuche "d2d" "NRW"',
        '"außendienst" "haustür" "provision" telefon',
        'site:kleinanzeigen.de "door to door" "vertrieb"',
        'site:kleinanzeigen.de/s-stellengesuche "haustür" "NRW"',
        'site:kleinanzeigen.de/s-stellengesuche "außendienst" "erfahrung" "NRW"',
        '"d2d sales" "deutschland" "erfahrung" kontakt',
        'site:facebook.com "d2d" "vertrieb" "suche"',
        'site:xing.com "door to door" "sales" "profil"',
        '"haustürgeschäft" "solar" "erfahrung" NRW',
        '"tür zu tür" "vertrieb" "kontakt"',
        'site:linkedin.com/in "door to door" "sales" "germany"',
        '"field sales" "d2d" "erfahrung" telefon',
        '"direktvertrieb" "haustür" "suche stelle"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: SOLAR/PHOTOVOLTAIK (größter D2D Markt!)
        # ──────────────────────────────────────────────────────────
        'site:kleinanzeigen.de/s-stellengesuche "d2d" "solar"',
        'site:kleinanzeigen.de/s-stellengesuche "haustürvertrieb" "photovoltaik"',
        '"door to door" "solar" "erfahrung" "suche"',
        '"d2d" "photovoltaik" "vertriebler" "suche job"',
        'site:facebook.com/groups "d2d" "solar" "jobs"',
        '"solarvertrieb" "haustür" "erfahrung" "suche"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: GLASFASER (neuer Trend!)
        # ──────────────────────────────────────────────────────────
        '"glasfaser" "d2d" "vertriebler" "suche"',
        '"door to door" "telekom" "glasfaser" "erfahrung"',
        '"glasfaser ausbau" "haustür" "vertrieb" "suche"',
        'site:kleinanzeigen.de "glasfaser" "d2d" "suche"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: ENERGIE/STROM
        # ──────────────────────────────────────────────────────────
        '"strom" "haustürvertrieb" "erfahrung" "suche"',
        '"energievertrieb" "d2d" "suche stelle"',
        '"door to door" "energieversorger" "erfahrung"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: ALLGEMEIN VERBESSERT
        # ──────────────────────────────────────────────────────────
        'site:xing.com/profile "door to door" "verfügbar"',
        'site:linkedin.com/in "d2d sales" "germany" "open"',
    ],
    
    # ══════════════════════════════════════════════════════════════
    # NEU: CALLCENTER
    # ══════════════════════════════════════════════════════════════
    "callcenter": [
        # Bestehende Queries
        '"call center agent" "suche" "homeoffice" "NRW"',
        '"telesales" "erfahrung" "suche stelle"',
        '"kundenservice" "telefon" "suche job"',
        'site:kleinanzeigen.de/s-stellengesuche "call center"',
        '"outbound" "telefonie" "erfahrung" suche',
        'site:kleinanzeigen.de "telefonverkäufer" "suche"',
        '"inbound" "customer service" "suche" NRW',
        'site:kleinanzeigen.de/s-stellengesuche "telesales" "homeoffice"',
        '"telefonakquise" "erfahrung" "suche stelle"',
        '"telefon sales" "remote" "suche job"',
        'site:xing.com "call center" "agent" "suche"',
        'site:linkedin.com/in "telesales" "germany" "open"',
        '"kundenberater telefon" "suche" "homeoffice"',
        '"callcenter erfahrung" "suche neue" NRW',
        '"telefonist" "suche stelle" "erfahrung"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: REMOTE/HOMEOFFICE SPEZIFISCH (sehr gefragt!)
        # ──────────────────────────────────────────────────────────
        '"call center" "remote" "suche stelle" "sofort"',
        '"telesales" "100% homeoffice" "suche"',
        '"kundenservice" "von zuhause" "suche job"',
        '"callcenter" "homeoffice" "erfahrung" "suche"',
        'site:kleinanzeigen.de/s-stellengesuche "call center" "remote"',
        'site:kleinanzeigen.de/s-stellengesuche "homeoffice" "telefon"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: OUTBOUND SPEZIFISCH
        # ──────────────────────────────────────────────────────────
        '"outbound" "b2b" "terminierung" "suche"',
        '"kaltakquise" "telefon" "erfahrung" "suche stelle"',
        '"telefonakquise" "leadgenerierung" "suche"',
        '"neukundenakquise" "telefon" "suche job"',
        'site:kleinanzeigen.de/s-stellengesuche "outbound" "NRW"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: INBOUND SPEZIFISCH
        # ──────────────────────────────────────────────────────────
        '"inbound" "first level" "support" "suche"',
        '"kundenhotline" "erfahrung" "suche stelle"',
        '"technischer support" "telefon" "suche"',
        '"customer service" "deutsch" "suche job"',
    ],
    
    # ══════════════════════════════════════════════════════════════
    # RECRUITER (Vertriebler-Rekrutierung)
    # ══════════════════════════════════════════════════════════════
    "recruiter": [
        # Bestehende Queries
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
        
        # ──────────────────────────────────────────────────────────
        # NEU: LINKEDIN RECRUITER
        # ──────────────────────────────────────────────────────────
        'site:linkedin.com/in "Recruiter" "Vertrieb" "NRW"',
        'site:linkedin.com/in "Personalberater" "Sales" "Deutschland"',
        'site:linkedin.com/in "Talent Acquisition" "Sales" "germany"',
        'site:linkedin.com/in "HR" "Vertrieb" "recruiting"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: XING RECRUITER
        # ──────────────────────────────────────────────────────────
        'site:xing.com/profile "Personalberater" "Vertrieb"',
        'site:xing.com/profile "Recruiter" "Sales" "NRW"',
        'site:xing.com/profile "Headhunter" "Vertrieb"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: PERSONALDIENSTLEISTER
        # ──────────────────────────────────────────────────────────
        '"Personalvermittlung" "Vertrieb" kontakt telefon',
        '"Headhunter" "Sales" "NRW" kontakt',
        '"Personalberatung" "Vertriebspositionen" kontakt',
        '"Zeitarbeit" "Vertrieb" "NRW" telefon',
        
        # ──────────────────────────────────────────────────────────
        # NEU: STELLENGESUCHE VON RECRUITERN
        # ──────────────────────────────────────────────────────────
        'site:kleinanzeigen.de/s-stellengesuche "recruiter" "vertrieb"',
        'site:kleinanzeigen.de/s-stellengesuche "personalberater"',
        'site:markt.de "recruiter" "suche" "vertrieb"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: SPEZIALISIERTE RECRUITER
        # ──────────────────────────────────────────────────────────
        '"IT Recruiter" "Sales" kontakt',
        '"Pharma Recruiter" "Außendienst" telefon',
        '"Finance Recruiter" "Vertrieb" kontakt',
        
        # ──────────────────────────────────────────────────────────
        # NEU: FACEBOOK GRUPPEN FÜR RECRUITER
        # ──────────────────────────────────────────────────────────
        'site:facebook.com/groups "recruiter" "vertrieb" "deutschland"',
        'site:facebook.com/groups "personalvermittlung" "sales"',
        
        # ──────────────────────────────────────────────────────────
        # NEU: RECRUITING EVENTS
        # ──────────────────────────────────────────────────────────
        '"Recruiting Event" "Vertrieb" "NRW" kontakt',
        '"Karrieremesse" "Recruiter" "Sales"',
    ],
}


# =========================
# QUERY BUILDING FUNCTIONS
# =========================

def build_queries(
    selected_industry: Optional[str] = None,
    per_industry_limit: int = 20000
) -> List[str]:
    """
    Build a compact set of high-precision queries based on selected industry.
    If candidates/recruiter/talent_hunt/handelsvertreter/d2d/callcenter mode is selected,
    use INDUSTRY_QUERIES accordingly.
    
    Args:
        selected_industry: Industry/mode to use (candidates, recruiter, talent_hunt, 
                          handelsvertreter, d2d, callcenter, or None for standard)
        per_industry_limit: Maximum number of queries to return
        
    Returns:
        List of search queries
    """
    # Alle unterstützten Industry-Modi
    SUPPORTED_INDUSTRIES = [
        "candidates", "recruiter", "talent_hunt",
        "handelsvertreter", "d2d", "callcenter"
    ]
    
    # Use industry-specific queries if available
    if selected_industry and selected_industry.lower() in SUPPORTED_INDUSTRIES:
        base = INDUSTRY_QUERIES.get(selected_industry.lower(), [])
        if not base:
            # Log warning if industry is supported but has no queries
            logger.warning(
                f"Industry '{selected_industry}' is in SUPPORTED_INDUSTRIES but has no queries in INDUSTRY_QUERIES. "
                f"Falling back to DEFAULT_QUERIES."
            )
            queries = list(dict.fromkeys(_COMPLETE_DEFAULT_QUERIES))
        else:
            queries = list(dict.fromkeys(base))
        random.shuffle(queries)
        cap = min(max(1, per_industry_limit), len(queries))
        return queries[:cap]
    
    # Standard mode: use complete default queries list (including niche, freelance, guerilla)
    queries: List[str] = list(dict.fromkeys(_COMPLETE_DEFAULT_QUERIES))
    random.shuffle(queries)

    cap = min(max(1, per_industry_limit), len(queries))
    return queries[:cap]


# =========================
# NEU: DORK SET FUNCTIONS
# =========================

# NEU: Unterstützte Dork-Sets
DORK_SETS = {
    "default": _COMPLETE_DEFAULT_QUERIES,
    # "new_sources" wird dynamisch aus new_sources_config geladen
}


def get_dork_set(dork_set_name: str = "default") -> List[str]:
    """
    NEU: Lädt Dorks aus einem spezifischen Dork-Set.
    
    Unterstützte Sets:
    - "default": Standard-Dorks aus DEFAULT_QUERIES
    - "new_sources": Dorks aus NEW_SOURCES_CONFIG (Handelsvertreter, B2B, etc.)
    
    Args:
        dork_set_name: Name des Dork-Sets
        
    Returns:
        Liste von Dork-Strings
    """
    if dork_set_name == "new_sources":
        # NEU: Lade aus new_sources_config
        try:
            from ..config.new_sources_config import get_new_sources_dorks
            return get_new_sources_dorks()
        except ImportError:
            logger.warning("Could not import new_sources_config, using default dorks")
            return list(DORK_SETS.get("default", []))
    
    return list(DORK_SETS.get(dork_set_name, DORK_SETS.get("default", [])))


def build_queries_with_dork_set(
    dork_set_name: str = "default",
    selected_industry: Optional[str] = None,
    per_industry_limit: int = 20000,
) -> List[dict]:
    """
    NEU: Build queries mit Dork-Set Support und Metadaten.
    
    Wenn dork_set="new_sources" verwendet wird, werden Dorks mit Priorität
    und always_crawl-Flag zurückgegeben.
    
    Args:
        dork_set_name: Name des Dork-Sets ("default" oder "new_sources")
        selected_industry: Industry/mode für Standard-Queries
        per_industry_limit: Maximum Queries
        
    Returns:
        Liste von Dicts mit keys: dork, category, priority, always_crawl, domains
        Oder Liste von Dicts mit nur "dork" key für Standard-Sets
    """
    if dork_set_name == "new_sources":
        # NEU: Lade aus new_sources_config mit Metadaten
        try:
            from ..config.new_sources_config import get_new_sources_dorks_by_priority
            dorks_with_meta = get_new_sources_dorks_by_priority()
            # Begrenze Anzahl
            cap = min(max(1, per_industry_limit), len(dorks_with_meta))
            return dorks_with_meta[:cap]
        except ImportError:
            logger.warning("Could not import new_sources_config, using default dorks")
    
    # Standard-Verarbeitung für andere Sets oder Fallback
    if selected_industry:
        base_queries = build_queries(selected_industry, per_industry_limit)
    else:
        base_queries = get_dork_set(dork_set_name)
        random.shuffle(base_queries)
        cap = min(max(1, per_industry_limit), len(base_queries))
        base_queries = base_queries[:cap]
    
    # Konvertiere zu Dict-Format ohne Metadaten
    return [{"dork": dork, "category": "default", "priority": 1, "always_crawl": False, "domains": []} for dork in base_queries]
