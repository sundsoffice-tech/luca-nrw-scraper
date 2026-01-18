# -*- coding: utf-8 -*-
"""
Configuration module for Luca NRW Scraper
Contains all constants, environment variables, and configuration settings.
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# =========================
# NRW Städte für städtebasierte Suche
# =========================
NRW_CITIES = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg",
    "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Gelsenkirchen", "Aachen", "Mönchengladbach"
]
NRW_CITIES_EXTENDED = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg",
    "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Gelsenkirchen", "Mönchengladbach", "Aachen", "Krefeld", "Oberhausen",
    "Hagen", "Hamm", "Mülheim an der Ruhr", "Leverkusen", "Solingen",
    "Neuss", "Paderborn", "Recklinghausen", "Remscheid", "Moers",
    "Siegen", "Witten", "Iserlohn", "Bergisch Gladbach", "Herne"
]
# Top 40 Städte in NRW für massive Abdeckung
NRW_BIG_CITIES = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Gelsenkirchen", "Mönchengladbach", "Aachen", "Chemnitz", "Krefeld", "Oberhausen", "Hagen", "Hamm", "Mülheim",
    "Leverkusen", "Solingen", "Herne", "Neuss", "Paderborn", "Bottrop", "Recklinghausen", "Bergisch Gladbach",
    "Remscheid", "Moers", "Siegen", "Gütersloh", "Witten", "Iserlohn", "Düren", "Ratingen", "Lünen", "Marl",
    "Velbert", "Minden", "Viersen"
]
# Großstädte mit stärkerer Titel-Streuung
METROPOLIS = ["Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Bonn", "Münster"]

# Professionelle Job-Titel für LinkedIn/Xing
SALES_TITLES = [
    "Vertrieb", "Sales Manager", "Account Manager", "Außendienst", "Telesales",
    "Verkäufer", "Handelsvertreter", "Key Account Manager", "Area Sales Manager"
]
# Regionen statt nur Städte (für breite Suche)
NRW_REGIONS = [
    "nrw", "nordrhein-westfalen", "nordrhein westfalen",
    "düsseldorf", "köln", "dortmund", "essen", "duisburg",
    "bochum", "wuppertal", "bielefeld", "bonn", "münster",
    "gelsenkirchen", "mönchengladbach", "aachen", "krefeld",
    "oberhausen", "hagen", "hamm", "mülheim", "leverkusen",
    "solingen", "herne", "neuss", "paderborn", "bottrop",
    "ruhrgebiet", "rheinland", "sauerland", "münsterland", "owl",
]

# Private Mail-Provider (keine Firmen!)
PRIVATE_MAILS = '("@gmail.com" OR "@gmx.de" OR "@web.de" OR "@t-online.de" OR "@yahoo.de" OR "@outlook.com" OR "@icloud.com")'

# Handy-Nummern Muster (Masse!)
MOBILE_PATTERNS = '("017" OR "016" OR "015" OR "+49 17" OR "+49 16" OR "+49 15" OR "+4917" OR "+4916" OR "+4915")'

# --- Globales Query-Set (wird in __main__ gesetzt) ---
QUERIES: List[str] = []
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
# Flatten the niche queries into the main list
for industry_dorks in NICHE_QUERIES.values():
    DEFAULT_QUERIES.extend(industry_dorks)
DEFAULT_QUERIES.extend(FREELANCE_QUERIES)
DEFAULT_QUERIES.extend(GUERILLA_QUERIES)

# === Export-Felder (CSV/XLSX) ===
ENH_FIELDS = [
    "name","rolle","email","telefon","quelle","score","tags","region",
    "role_guess","lead_type","salary_hint","commission_hint","opening_line",
    "ssl_insecure","company_name","company_size","hiring_volume",
    "industry","recency_indicator","location_specific",
    "confidence_score","last_updated","data_quality",
    "phone_type","whatsapp_link","private_address","social_profile_url",
    "ai_category","ai_summary",
    "experience_years","skills","availability","current_status","industries","location","profile_text",
    # New candidate-focused fields
    "candidate_status","mobility","industries_experience","source_type",
    "profile_url","cv_url","contact_preference","last_activity","name_validated"
]

# =========================
# API Keys & Database
# =========================
USER_AGENT = "Mozilla/5.0 (compatible; VertriebFinder/2.3; +https://example.com)"
DEFAULT_CSV = "vertrieb_kontakte.csv"
DEFAULT_XLSX = "vertrieb_kontakte.xlsx"
DB_PATH = os.getenv("SCRAPER_DB", "scraper.db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GCS_API_KEY    = os.getenv("GCS_API_KEY", "")
GCS_CX_RAW     = os.getenv("GCS_CX", "")
BING_API_KEY   = os.getenv("BING_API_KEY", "")

# =========================
# HTTP & Performance Settings
# =========================
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))  # Reduced to 10s for cost control
MAX_FETCH_SIZE = int(os.getenv("MAX_FETCH_SIZE", str(2 * 1024 * 1024)))  # 2MB default

POOL_SIZE = int(os.getenv("POOL_SIZE", "12"))  # (historisch; wird in Async-Version nicht mehr genutzt)

ALLOW_PDF = (os.getenv("ALLOW_PDF", "0") == "1")
ALLOW_INSECURE_SSL = (os.getenv("ALLOW_INSECURE_SSL", "1") == "1")

# Neue Async-ENV
ASYNC_LIMIT = int(os.getenv("ASYNC_LIMIT", "35"))          # globale max. gleichzeitige Requests (reduziert von 50)
ASYNC_PER_HOST = int(os.getenv("ASYNC_PER_HOST", "3"))     # pro Host
HTTP2_ENABLED = (os.getenv("HTTP2", "1") == "1")
USE_TOR = False

# Proxy environment variables to clear for nuclear cleanup
PROXY_ENV_VARS = [
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
    "FTP_PROXY", "ftp_proxy", "SOCKS_PROXY", "socks_proxy"
]

# =========================
# Portal Configurations
# =========================
ENABLE_KLEINANZEIGEN = (os.getenv("ENABLE_KLEINANZEIGEN", "1") == "1")
KLEINANZEIGEN_MAX_RESULTS = int(os.getenv("KLEINANZEIGEN_MAX_RESULTS", "20"))

# Telefonbuch Enrichment Config
TELEFONBUCH_ENRICHMENT_ENABLED = (os.getenv("TELEFONBUCH_ENRICHMENT_ENABLED", "1") == "1")
TELEFONBUCH_STRICT_MODE = (os.getenv("TELEFONBUCH_STRICT_MODE", "1") == "1")
TELEFONBUCH_RATE_LIMIT = float(os.getenv("TELEFONBUCH_RATE_LIMIT", "3.0"))
TELEFONBUCH_CACHE_DAYS = int(os.getenv("TELEFONBUCH_CACHE_DAYS", "7"))
TELEFONBUCH_MOBILE_ONLY = (os.getenv("TELEFONBUCH_MOBILE_ONLY", "1") == "1")

# Direct crawl URLs for Kleinanzeigen Stellengesuche (bypassing Google)
DIRECT_CRAWL_URLS = [
    # Stellengesuche NRW - Vertrieb/Sales
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/vertrieb/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/sales/k0c107l929", 
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/verkauf/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/aussendienst/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/kundenberater/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/handelsvertreter/k0c107l929",
    
    # Bundesweit (mehr Volumen)
    "https://www.kleinanzeigen.de/s-stellengesuche/vertrieb/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/sales/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/verkauf/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/handelsvertreter/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/akquise/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/telesales/k0c107",
    "https://www.kleinanzeigen.de/s-stellengesuche/call-center/k0c107",
    
    # Alle großen NRW-Städte
    # Köln
    "https://www.kleinanzeigen.de/s-stellengesuche/koeln/vertrieb/k0c107l945",
    "https://www.kleinanzeigen.de/s-stellengesuche/koeln/sales/k0c107l945",
    "https://www.kleinanzeigen.de/s-stellengesuche/koeln/verkauf/k0c107l945",
    
    # Dortmund
    "https://www.kleinanzeigen.de/s-stellengesuche/dortmund/vertrieb/k0c107l947",
    "https://www.kleinanzeigen.de/s-stellengesuche/dortmund/sales/k0c107l947",
    
    # Essen
    "https://www.kleinanzeigen.de/s-stellengesuche/essen/vertrieb/k0c107l939",
    "https://www.kleinanzeigen.de/s-stellengesuche/essen/sales/k0c107l939",
    
    # Duisburg
    "https://www.kleinanzeigen.de/s-stellengesuche/duisburg/vertrieb/k0c107l940",
    
    # Bochum
    "https://www.kleinanzeigen.de/s-stellengesuche/bochum/vertrieb/k0c107l941",
    
    # Wuppertal
    "https://www.kleinanzeigen.de/s-stellengesuche/wuppertal/vertrieb/k0c107l942",
    
    # Bielefeld
    "https://www.kleinanzeigen.de/s-stellengesuche/bielefeld/vertrieb/k0c107l943",
    
    # Bonn
    "https://www.kleinanzeigen.de/s-stellengesuche/bonn/vertrieb/k0c107l944",
    
    # Münster
    "https://www.kleinanzeigen.de/s-stellengesuche/muenster/vertrieb/k0c107l946",
    
    # Gelsenkirchen
    "https://www.kleinanzeigen.de/s-stellengesuche/gelsenkirchen/vertrieb/k0c107l948",
    
    # Mönchengladbach
    "https://www.kleinanzeigen.de/s-stellengesuche/moenchengladbach/vertrieb/k0c107l949",
    
    # Aachen
    "https://www.kleinanzeigen.de/s-stellengesuche/aachen/vertrieb/k0c107l950",
    
    # Krefeld
    "https://www.kleinanzeigen.de/s-stellengesuche/krefeld/vertrieb/k0c107l951",
    
    # Oberhausen
    "https://www.kleinanzeigen.de/s-stellengesuche/oberhausen/vertrieb/k0c107l952",
    
    # Hagen
    "https://www.kleinanzeigen.de/s-stellengesuche/hagen/vertrieb/k0c107l953",
    
    # Hamm
    "https://www.kleinanzeigen.de/s-stellengesuche/hamm/vertrieb/k0c107l954",
    
    # Zusätzliche Berufsfelder NRW
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/kundenservice/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/call-center/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/promotion/k0c107l929",
    "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/telefonverkauf/k0c107l929",
]

# Markt.de Stellengesuche URLs
MARKT_DE_URLS = [
    # NRW
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/vertrieb/",
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/sales/",
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/verkauf/",
    "https://www.markt.de/stellengesuche/nordrhein-westfalen/kundenberater/",
    # Bundesweit
    "https://www.markt.de/stellengesuche/vertrieb/",
    "https://www.markt.de/stellengesuche/sales/",
    "https://www.markt.de/stellengesuche/handelsvertreter/",
]

# Quoka.de Stellengesuche URLs
QUOKA_DE_URLS = [
    # NRW Städte (erweitert)
    "https://www.quoka.de/stellengesuche/duesseldorf/",
    "https://www.quoka.de/stellengesuche/koeln/",
    "https://www.quoka.de/stellengesuche/dortmund/",
    "https://www.quoka.de/stellengesuche/essen/",
    "https://www.quoka.de/stellengesuche/duisburg/",
    "https://www.quoka.de/stellengesuche/bochum/",
    "https://www.quoka.de/stellengesuche/wuppertal/",
    "https://www.quoka.de/stellengesuche/bielefeld/",
    "https://www.quoka.de/stellengesuche/bonn/",
    "https://www.quoka.de/stellengesuche/muenster/",
    "https://www.quoka.de/stellengesuche/gelsenkirchen/",
    "https://www.quoka.de/stellengesuche/moenchengladbach/",
    "https://www.quoka.de/stellengesuche/aachen/",
    # Kategorien
    "https://www.quoka.de/stellengesuche/vertrieb-verkauf/",
    "https://www.quoka.de/stellengesuche/kundenservice/",
]

# Kalaydo.de Stellengesuche URLs (NRW-fokussiert!)
KALAYDO_DE_URLS = [
    # Kalaydo ist stark in NRW
    "https://www.kalaydo.de/stellengesuche/nordrhein-westfalen/",
    "https://www.kalaydo.de/stellengesuche/koeln/",
    "https://www.kalaydo.de/stellengesuche/duesseldorf/",
    "https://www.kalaydo.de/stellengesuche/bonn/",
    "https://www.kalaydo.de/stellengesuche/aachen/",
]

# Meinestadt.de Stellengesuche URLs
MEINESTADT_DE_URLS = [
    # Alle Top-15 NRW Städte
    "https://www.meinestadt.de/duesseldorf/stellengesuche",
    "https://www.meinestadt.de/koeln/stellengesuche",
    "https://www.meinestadt.de/dortmund/stellengesuche",
    "https://www.meinestadt.de/essen/stellengesuche",
    "https://www.meinestadt.de/duisburg/stellengesuche",
    "https://www.meinestadt.de/bochum/stellengesuche",
    "https://www.meinestadt.de/wuppertal/stellengesuche",
    "https://www.meinestadt.de/bielefeld/stellengesuche",
    "https://www.meinestadt.de/bonn/stellengesuche",
    "https://www.meinestadt.de/muenster/stellengesuche",
    "https://www.meinestadt.de/gelsenkirchen/stellengesuche",
    "https://www.meinestadt.de/moenchengladbach/stellengesuche",
    "https://www.meinestadt.de/aachen/stellengesuche",
    "https://www.meinestadt.de/krefeld/stellengesuche",
    "https://www.meinestadt.de/oberhausen/stellengesuche",
]

# Freelancer Portal URLs (NRW-focused)
FREELANCER_PORTAL_URLS = [
    # Freelancermap.de - NRW Filter
    "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-vertrieb.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-sales.html",
    
    # Freelance.de - NRW
    "https://www.freelance.de/Freiberufler/NRW/Vertrieb/",
    "https://www.freelance.de/Freiberufler/NRW/Sales/",
    
    # GULP - NRW
    "https://www.gulp.de/gulp2/g/projekte?region=nordrhein-westfalen&skill=vertrieb",
]

# DHD24.com Stellengesuche URLs (neues Kleinanzeigen-Portal mit öffentlichen Kontaktdaten)
DHD24_URLS = [
    "https://www.dhd24.com/kleinanzeigen/stellengesuche.html",
    "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-vertrieb.html",
    "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-verkauf.html",
]

# Freelancermap.de URLs - Vertrieb/Sales Freelancer mit öffentlichen Telefonnummern
FREELANCERMAP_URLS = [
    "https://www.freelancermap.de/freelancer-verzeichnis/sales.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/vertrieb.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/business-development.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/account-management.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/key-account-management.html",
]

# Freelance.de URLs - Vertrieb/Sales Freelancer
FREELANCE_DE_URLS = [
    "https://www.freelance.de/Freiberufler/Vertrieb/",
    "https://www.freelance.de/Freiberufler/Sales/",
    "https://www.freelance.de/Freiberufler/Key-Account/",
    "https://www.freelance.de/Freiberufler/Business-Development/",
    "https://www.freelance.de/Freiberufler/Account-Manager/",
]

# Freelancer portal crawling configuration
MAX_PROFILES_PER_URL = 10  # Limit profiles crawled per URL to avoid overload

# Direct crawl source configuration
DIRECT_CRAWL_SOURCES = {
    "kleinanzeigen": True,
    "markt_de": True,
    "quoka": True,
    "kalaydo": False,  # Deaktiviert - Blockiert Requests
    "meinestadt": False,  # DEAKTIVIERT - 0 Stellengesuche bei 12 Städten (komplett nutzlos)
    "freelancer_portals": False,  # Deaktiviert - Kontaktdaten hinter Login
    "dhd24": True,  # AKTIVIERT - Alternative zu meinestadt
    "freelancermap": True,  # NEU - Freelancer-Portal mit öffentlichen Handynummern
    "freelance_de": False,  # DEAKTIVIERT - Server blockiert Requests (HTTP 403/Timeout)
}

# Portal-specific request delays (seconds) to avoid rate limiting
PORTAL_DELAYS = {
    "kleinanzeigen": 3.0,
    "markt_de": 4.0,
    "quoka": 6.0,  # ERHÖHT von 3.0 - 429 Rate-Limit Detection
    "kalaydo": 4.0,
    "meinestadt": 3.0,
    "dhd24": 4.0,
    "freelancermap": 3.0,
    "freelance_de": 3.0,
}

# ==================== NEW PORTAL CONFIGURATIONS ====================
# Extended portal configuration with priorities and detailed settings
PORTAL_CONFIGS = {
    "kleinanzeigen": {
        "enabled": True,
        "base_urls": DIRECT_CRAWL_URLS,
        "delay": 3.0,
        "priority": 1,
        "type": "classifieds"
    },
    "markt_de": {
        "enabled": True,
        "base_urls": MARKT_DE_URLS,
        "delay": 4.0,
        "priority": 2,
        "type": "classifieds"
    },
    "quoka": {
        "enabled": True,
        "base_urls": QUOKA_DE_URLS,
        "delay": 6.0,
        "priority": 3,
        "type": "classifieds"
    },
    "indeed": {
        "enabled": True,
        "base_urls": [
            "https://de.indeed.com/Jobs?q=stellengesuch&l=Nordrhein-Westfalen",
            "https://de.indeed.com/Jobs?q=suche+arbeit+vertrieb&l=NRW",
            "https://de.indeed.com/Jobs?q=vertrieb+verfügbar&l=Düsseldorf",
            "https://de.indeed.com/Jobs?q=sales+offen&l=Köln",
        ],
        "delay": 3.0,
        "priority": 4,
        "type": "job_board"
    },
    "stepstone": {
        "enabled": True,
        "base_urls": [
            "https://www.stepstone.de/jobs/vertrieb/in-nordrhein-westfalen",
            "https://www.stepstone.de/jobs/sales/in-nrw",
            "https://www.stepstone.de/jobs/au%C3%9Fendienst/in-nordrhein-westfalen",
        ],
        "delay": 3.0,
        "priority": 5,
        "type": "job_board"
    },
    "arbeitsagentur": {
        "enabled": True,
        "base_urls": [
            "https://www.arbeitsagentur.de/jobsuche/suche?was=Vertrieb&wo=Nordrhein-Westfalen",
            "https://www.arbeitsagentur.de/jobsuche/suche?was=Sales&wo=NRW",
        ],
        "delay": 2.0,
        "priority": 6,
        "type": "job_board"
    },
    "monster": {
        "enabled": True,
        "base_urls": [
            "https://www.monster.de/jobs/suche/?q=vertrieb&where=nordrhein-westfalen",
            "https://www.monster.de/jobs/suche/?q=sales&where=nrw",
        ],
        "delay": 3.0,
        "priority": 7,
        "type": "job_board"
    },
    "stellenanzeigen": {
        "enabled": True,
        "base_urls": [
            "https://www.stellenanzeigen.de/jobs-vertrieb-nordrhein-westfalen/",
            "https://www.stellenanzeigen.de/jobs-sales-nrw/",
        ],
        "delay": 2.5,
        "priority": 8,
        "type": "job_board"
    },
    "meinestadt": {
        "enabled": True,  # Reaktiviert mit besserer Handhabung
        "base_urls": MEINESTADT_DE_URLS,
        "delay": 3.0,
        "priority": 9,
        "type": "classifieds"
    },
    "dhd24": {
        "enabled": False,  # Bleibt deaktiviert (oft blockiert)
        "base_urls": DHD24_URLS,
        "delay": 5.0,
        "priority": 99,
        "type": "classifieds"
    },
    "kalaydo": {
        "enabled": False,  # Deaktiviert - blockiert Requests
        "base_urls": KALAYDO_DE_URLS,
        "delay": 4.0,
        "priority": 99,
        "type": "classifieds"
    },
    "freelancermap": {
        "enabled": True,
        "base_urls": FREELANCERMAP_URLS,
        "delay": 3.0,
        "priority": 10,
        "type": "freelancer"
    },
    "freelance_de": {
        "enabled": True,
        "base_urls": FREELANCE_DE_URLS,
        "delay": 3.0,
        "priority": 11,
        "type": "freelancer"
    },
}

# Parallel crawling configuration
PARALLEL_PORTAL_CRAWL = os.getenv("PARALLEL_PORTAL_CRAWL", "1") == "1"
MAX_CONCURRENT_PORTALS = int(os.getenv("MAX_CONCURRENT_PORTALS", "5"))
PORTAL_CONCURRENCY_PER_SITE = int(os.getenv("PORTAL_CONCURRENCY_PER_SITE", "2"))

# =========================
# Candidate-Focused Constants
# =========================

# Source Types - Extensive list for candidate-focused scraping
SOURCE_TYPES = {
    # PRIMÄR - Direkte Jobsuche
    "stellengesuch_kleinanzeigen": "Kleinanzeigen.de Stellengesuch",
    "stellengesuch_markt": "Markt.de Stellengesuch",
    "stellengesuch_quoka": "Quoka Stellengesuch",
    "stellengesuch_kalaydo": "Kalaydo Stellengesuch",
    
    # SOCIAL MEDIA - Aktiv suchend
    "linkedin_opentowork": "LinkedIn #OpenToWork",
    "linkedin_seeking": "LinkedIn 'seeking opportunities'",
    "xing_offen": "Xing 'offen für Angebote'",
    "xing_jobsuche": "Xing 'auf Jobsuche'",
    "facebook_jobpost": "Facebook Jobsuche-Post",
    "facebook_gruppe": "Facebook Vertriebs-Gruppe",
    "instagram_bio": "Instagram 'looking for work'",
    "tiktok_karriere": "TikTok Karriere-Content",
    
    # MESSENGER GRUPPEN
    "telegram_vertrieb": "Telegram Vertriebsgruppe",
    "telegram_jobs": "Telegram Jobs-Kanal",
    "whatsapp_gruppe": "WhatsApp Vertriebsgruppe",
    "discord_karriere": "Discord Karriere-Server",
    
    # FOREN & COMMUNITIES
    "reddit_arbeitsleben": "Reddit r/arbeitsleben",
    "reddit_fragreddit": "Reddit Karrierefrage",
    "gutefrage_job": "Gutefrage Jobsuche",
    "wiwi_treff": "WiWi-Treff Forum",
    
    # FREELANCER PORTALE
    "freelancermap": "Freelancermap Profil",
    "freelance_de": "Freelance.de Profil",
    "gulp": "GULP Freiberufler",
    "fiverr_sales": "Fiverr Sales-Services",
    "upwork_german": "Upwork deutschsprachig",
    
    # LEBENSLAUF/CV
    "cv_pdf_public": "Öffentliches PDF (Lebenslauf)",
    "cv_stepstone": "StepStone Kandidatenprofil",
    "cv_indeed": "Indeed Lebenslauf",
    
    # KRISENUNTERNEHMEN (Abwerbung)
    "kununu_krise": "Kununu Bewertung (Krise)",
    "linkedin_layoff": "LinkedIn Entlassungs-Post",
    "insolvenz_news": "Insolvenz-Meldung",
    
    # BRANCHEN-SPEZIFISCH
    "solar_vertrieb": "Solar-Branche Vertrieb",
    "telekom_sales": "Telekom-Branche Sales",
    "versicherung_makler": "Versicherungs-Makler",
    "energie_berater": "Energieberater",
    "immobilien_makler": "Immobilien-Makler",
    
    # QUEREINSTEIGER-POTENZIAL
    "gastro_wechsler": "Gastro → Vertrieb Wechsler",
    "einzelhandel_pro": "Einzelhandel mit Sales-Talent",
    "mlm_aussteiger": "MLM/Network Marketing Aussteiger",
    "callcenter_erfahren": "Call-Center mit Erfahrung",
    "promotion_aktiv": "Promoter mit Ambitionen",
    "door2door_veteran": "D2D Erfahrung",
}

# Required vs Optional Fields
REQUIRED_FIELDS = {
    "name": "Echter menschlicher Name (KI-geprüft!)",
    "telefon": "Handynummer (015x, 016x, 017x)",
}

OPTIONAL_FIELDS = {
    "email": "E-Mail (bevorzugt privat)",
    "whatsapp_link": "WhatsApp-Link",
    "profile_url": "Social-Media Profil",
    "skills": "Fähigkeiten",
    "experience_years": "Berufserfahrung",
    "availability": "Verfügbarkeit",
    "industries_experience": "Branchenerfahrung",
    "location": "Standort/Region",
    "mobility": "Mobilität",
    "cv_url": "Lebenslauf-URL",
}

# Hidden Gems - Quereinsteiger with sales potential
HIDDEN_GEMS_PATTERNS = {
    "gastro_talent": {
        "keywords": ["restaurant", "gastronomie", "kellner", "service"],
        "positive": ["kundenorientiert", "stressresistent", "kommunikativ"],
        "reason": "Gastro-Erfahrung = Kundenkontakt + Belastbarkeit"
    },
    "einzelhandel_pro": {
        "keywords": ["einzelhandel", "verkäufer", "filiale", "retail"],
        "positive": ["umsatz", "beratung", "kasse", "kundenservice"],
        "reason": "Einzelhandel = Verkaufserfahrung + Kundenumgang"
    },
    "callcenter_veteran": {
        "keywords": ["callcenter", "call center", "kundenservice", "hotline"],
        "positive": ["outbound", "telefonverkauf", "telesales"],
        "reason": "Call-Center = Telefonakquise-Erfahrung"
    },
    "mlm_refugee": {
        "keywords": ["network marketing", "mlm", "direktvertrieb", "tupperware"],
        "positive": ["selbstständig", "provision", "akquise"],
        "reason": "MLM-Aussteiger = Kaltakquise + Hunger auf echten Job"
    },
    "promotion_hustler": {
        "keywords": ["promotion", "promoter", "messe", "events"],
        "positive": ["kommunikativ", "überzeugend", "präsentation"],
        "reason": "Promoter = Ansprache-Erfahrung + keine Scheu"
    },
    "door2door_warrior": {
        "keywords": ["d2d", "door to door", "haustür", "außendienst"],
        "positive": ["provision", "abschlussstark", "hartnäckig"],
        "reason": "D2D-Erfahrung = Härtester Vertrieb überhaupt"
    },
    "fitness_coach": {
        "keywords": ["fitness", "personal trainer", "coach", "studio"],
        "positive": ["motivierend", "zielorientiert", "membership"],
        "reason": "Fitness = Verkauf + Überzeugungskraft"
    },
}

# Default mode is now candidates
DEFAULT_MODE = "candidates"

# Hard blocks - never save these
UNIVERSAL_HARD_BLOCKS = [
    r'\(m/w/d\)', r'\(w/m/d\)', r'\(d/m/w\)',
    r'jetzt bewerben', r'bewerbung an:',
    r'stellenanzeige', r'vakanz',
    r'recruiting@', r'bewerbung@', r'karriere@',
    r'hr-manager', r'talent acquisition',
    r'crypto.*gewinn', r'bitcoin.*investier',
    r'casino', r'dating',
]

# Always allow in candidate mode
CANDIDATE_ALWAYS_ALLOW = [
    "suche job", "suche arbeit", "suche stelle",
    "suche neue herausforderung", "stellengesuch",
    "#opentowork", "offen für angebote", "offen für neues",
    "arbeitslos", "arbeitssuchend", "freigestellt", "gekündigt",
    "verfügbar ab", "ab sofort verfügbar", "wechselwillig",
    "auf jobsuche", "biete meine dienste", "biete mich an",
    "freiberuflich verfügbar",
]

# Candidate export fields
CANDIDATE_EXPORT_FIELDS = [
    # Pflicht
    "name", "telefon",
    
    # Kandidaten-spezifisch
    "candidate_status", "source_type", "lead_type",
    "experience_years", "skills", "industries_experience",
    "availability", "mobility",
    
    # Kontakt
    "email", "whatsapp_link", "profile_url", "contact_preference",
    
    # Meta
    "score", "region", "last_activity", "last_updated",
    "name_validated",
]

# =========================
# Mode Configurations
# =========================
MODE_CONFIGS = {
    "standard": {
        "description": "Normaler Betrieb mit Learning",
        "deep_crawl": True,
        "learning_enabled": True,
        "async_limit": 35,
        "request_delay": 2.5,
        "max_retries": 2,
        "snippet_priority": False,
        "save_patterns": True
    },
    "learning": {
        "description": "Lernt aus erfolgreichen Extraktionen",
        "deep_crawl": True,
        "learning_enabled": True,
        "async_limit": 30,
        "request_delay": 3.0,
        "max_retries": 3,
        "snippet_priority": True,
        "save_patterns": True,
        "pattern_analysis": True,
        "success_tracking": True,
        "domain_scoring": True,
        "query_optimization": True
    },
    "aggressive": {
        "description": "Maximale Geschwindigkeit mit Learning",
        "deep_crawl": True,
        "learning_enabled": True,
        "async_limit": 75,
        "request_delay": 1.0,
        "max_retries": 1,
        "snippet_priority": False,
        "save_patterns": True,
        "follow_links": True,
        "crawl_depth": 3
    },
    "snippet_only": {
        "description": "Nur Snippet-Extraktion mit Learning",
        "deep_crawl": False,
        "learning_enabled": True,
        "async_limit": 50,
        "request_delay": 1.5,
        "max_retries": 1,
        "snippet_priority": True,
        "save_patterns": True
    }
}

# Global mode configuration (will be set in main)
ACTIVE_MODE_CONFIG = None

# =========================
# Proxy & User Agent Rotation
# =========================
def _env_list(val: str, sep: str) -> List[str]:
    return [x.strip() for x in (val or "").split(sep) if x.strip()]

PROXY_POOL = _env_list(os.getenv("PROXY_POOL", ""), ",")  # "http://user:pass@ip1:port, http://ip2:port"
UA_POOL_ENV = _env_list(os.getenv("UA_POOL", ""), "|")

# Realistische Desktop-UAs (falls UA_POOL leer)
UA_POOL_DEFAULT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/121.0.0.0 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]
UA_POOL = UA_POOL_ENV if UA_POOL_ENV else UA_POOL_DEFAULT

# =========================
# Performance & Limits
# =========================
# Basis-MinScore aus .env; wird pro Query-Runde dynamisch angepasst
MIN_SCORE_ENV = int(os.getenv("MIN_SCORE", "40"))

MAX_PER_DOMAIN = int(os.getenv("MAX_PER_DOMAIN", "5"))
INTERNAL_DEPTH_PER_DOMAIN = int(os.getenv("INTERNAL_DEPTH_PER_DOMAIN", "10"))

SLEEP_BETWEEN_QUERIES = float(os.getenv("SLEEP_BETWEEN_QUERIES", "2.7"))  # konservativ für Rate-Limit Schutz
SEED_FORCE = (os.getenv("SEED_FORCE", "0") == "1")


def get_performance_params():
    """
    Fetch current performance parameters from dashboard API.
    Returns effective parameters based on performance mode and system load.
    """
    try:
        import requests
        response = requests.get('http://127.0.0.1:5056/api/performance/effective', timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get('params', {})
    except Exception:
        pass
    
    # Fallback to environment variables/defaults
    return {
        'threads': int(os.getenv("THREADS", "4")),
        'async_limit': int(os.getenv("ASYNC_LIMIT", "35")),
        'batch_size': int(os.getenv("BATCH_SIZE", "20")),
        'request_delay': float(os.getenv("SLEEP_BETWEEN_QUERIES", "2.7"))
    }
