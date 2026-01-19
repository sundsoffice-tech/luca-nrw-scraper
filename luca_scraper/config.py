"""
LUCA NRW Scraper - Zentrale Konfiguration
==========================================
Alle Konstanten und Environment Variables aus scriptname.py extrahiert.
Phase 1 der Modularisierung.

AI Configuration Priority:
--------------------------
Configuration is loaded in the following priority order:
1. Django DB via ai_config app (when available)
2. Environment variables
3. Hardcoded defaults

Use get_config() to access AI configuration with automatic fallback.
"""

import os
import random
import urllib.parse
from typing import List, Dict, Set, Tuple, Optional, Any
import logging

# Optional Django ai_config integration
# Falls back gracefully when Django is not available or configured
try:
    from telis_recruitment.ai_config.loader import (
        get_ai_config as _get_ai_config_django,
        get_prompt,
        log_usage,
        check_budget
    )
    AI_CONFIG_AVAILABLE = True
except (ImportError, Exception):
    AI_CONFIG_AVAILABLE = False
    _get_ai_config_django = None

# Optional Django scraper_control integration
try:
    from telis_recruitment.scraper_control.config_loader import (
        get_scraper_config as _get_scraper_config_django,
        get_regions as _get_regions_django,
        get_dorks as _get_dorks_django,
        get_portals as _get_portals_django,
        get_blacklists as _get_blacklists_django,
    )
    SCRAPER_CONFIG_AVAILABLE = True
except (ImportError, Exception):
    SCRAPER_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


# =========================
# ENVIRONMENT VARIABLES
# =========================

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
GCS_API_KEY = os.getenv("GCS_API_KEY", "")
GCS_CX_RAW = os.getenv("GCS_CX", "")
BING_API_KEY = os.getenv("BING_API_KEY", "")

# Database
DB_PATH = os.getenv("SCRAPER_DB", "scraper.db")

# =========================
# HTTP & NETWORKING
# =========================

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))
MAX_FETCH_SIZE = int(os.getenv("MAX_FETCH_SIZE", str(2 * 1024 * 1024)))  # 2MB default
POOL_SIZE = int(os.getenv("POOL_SIZE", "12"))

# Async settings
ASYNC_LIMIT = int(os.getenv("ASYNC_LIMIT", "35"))
ASYNC_PER_HOST = int(os.getenv("ASYNC_PER_HOST", "3"))
HTTP2_ENABLED = (os.getenv("HTTP2", "1") == "1")
USE_TOR = False

# SSL & PDF
ALLOW_PDF = (os.getenv("ALLOW_PDF", "0") == "1")
ALLOW_INSECURE_SSL = (os.getenv("ALLOW_INSECURE_SSL", "1") == "1")
ALLOW_PDF_NON_CV = (os.getenv("ALLOW_PDF_NON_CV", "0") == "1")

# User Agent
USER_AGENT = "Mozilla/5.0 (compatible; VertriebFinder/2.3; +https://example.com)"

# Proxy environment variables
PROXY_ENV_VARS = [
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
    "FTP_PROXY", "ftp_proxy", "SOCKS_PROXY", "socks_proxy"
]

# =========================
# RATE LIMITING & DELAYS
# =========================

SLEEP_BETWEEN_QUERIES = float(os.getenv("SLEEP_BETWEEN_QUERIES", "2.7"))
MAX_GOOGLE_PAGES = int(os.getenv("MAX_GOOGLE_PAGES", "2"))

# Circuit Breaker
CB_BASE_PENALTY = int(os.getenv("CB_BASE_PENALTY", "30"))
CB_API_PENALTY = int(os.getenv("CB_API_PENALTY", "15"))

# Retry settings
RETRY_INCLUDE_403 = (os.getenv("RETRY_INCLUDE_403", "0") == "1")
RETRY_MAX_PER_URL = int(os.getenv("RETRY_MAX_PER_URL", "2"))
RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "6.0"))

# Robots cache
_ROBOTS_CACHE_TTL = int(os.getenv("ROBOTS_CACHE_TTL", "21600"))  # 6h

# =========================
# SCORING & FILTERING
# =========================

MIN_SCORE_ENV = int(os.getenv("MIN_SCORE", "40"))
MAX_PER_DOMAIN = int(os.getenv("MAX_PER_DOMAIN", "5"))
INTERNAL_DEPTH_PER_DOMAIN = int(os.getenv("INTERNAL_DEPTH_PER_DOMAIN", "10"))
DEFAULT_QUALITY_SCORE = 50

# Content limits
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(MAX_FETCH_SIZE)))
BINARY_CT_PREFIXES = ("image/", "video/", "audio/")
DENY_CT_EXACT = {
    "application/zip", "application/x-tar", "application/x-gzip"
}
PDF_CT = "application/pdf"

# Seed force
SEED_FORCE = (os.getenv("SEED_FORCE", "0") == "1")

# =========================
# FEATURE FLAGS
# =========================

ENABLE_KLEINANZEIGEN = (os.getenv("ENABLE_KLEINANZEIGEN", "1") == "1")
KLEINANZEIGEN_MAX_RESULTS = int(os.getenv("KLEINANZEIGEN_MAX_RESULTS", "20"))

# Telefonbuch Enrichment
TELEFONBUCH_ENRICHMENT_ENABLED = (os.getenv("TELEFONBUCH_ENRICHMENT_ENABLED", "1") == "1")
TELEFONBUCH_STRICT_MODE = (os.getenv("TELEFONBUCH_STRICT_MODE", "1") == "1")
TELEFONBUCH_RATE_LIMIT = float(os.getenv("TELEFONBUCH_RATE_LIMIT", "3.0"))
TELEFONBUCH_CACHE_DAYS = int(os.getenv("TELEFONBUCH_CACHE_DAYS", "7"))
TELEFONBUCH_MOBILE_ONLY = (os.getenv("TELEFONBUCH_MOBILE_ONLY", "1") == "1")

# Portal crawling
PARALLEL_PORTAL_CRAWL = os.getenv("PARALLEL_PORTAL_CRAWL", "1") == "1"
MAX_CONCURRENT_PORTALS = int(os.getenv("MAX_CONCURRENT_PORTALS", "5"))
PORTAL_CONCURRENCY_PER_SITE = int(os.getenv("PORTAL_CONCURRENCY_PER_SITE", "2"))

# =========================
# NRW CITIES & REGIONS
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

NRW_BIG_CITIES = [
    "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Gelsenkirchen", "Mönchengladbach", "Aachen", "Chemnitz", "Krefeld", "Oberhausen", "Hagen", "Hamm", "Mülheim",
    "Leverkusen", "Solingen", "Herne", "Neuss", "Paderborn", "Bottrop", "Recklinghausen", "Bergisch Gladbach",
    "Remscheid", "Moers", "Siegen", "Gütersloh", "Witten", "Iserlohn", "Düren", "Ratingen", "Lünen", "Marl",
    "Velbert", "Minden", "Viersen"
]

METROPOLIS = ["Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Bonn", "Münster"]

NRW_REGIONS = [
    "nrw", "nordrhein-westfalen", "nordrhein westfalen",
    "düsseldorf", "köln", "dortmund", "essen", "duisburg",
    "bochum", "wuppertal", "bielefeld", "bonn", "münster",
    "gelsenkirchen", "mönchengladbach", "aachen", "krefeld",
    "oberhausen", "hagen", "hamm", "mülheim", "leverkusen",
    "solingen", "herne", "neuss", "paderborn", "bottrop",
    "ruhrgebiet", "rheinland", "sauerland", "münsterland", "owl",
]

# =========================
# JOB TITLES & ROLES
# =========================

SALES_TITLES = [
    "Vertrieb", "Sales Manager", "Account Manager", "Außendienst", "Telesales",
    "Verkäufer", "Handelsvertreter", "Key Account Manager", "Area Sales Manager"
]

# =========================
# SEARCH PATTERNS
# =========================

# Private Mail-Provider (keine Firmen!)
PRIVATE_MAILS = '("@gmail.com" OR "@gmx.de" OR "@web.de" OR "@t-online.de" OR "@yahoo.de" OR "@outlook.com" OR "@icloud.com")'

# Handy-Nummern Muster (Masse!)
MOBILE_PATTERNS = '("017" OR "016" OR "015" OR "+49 17" OR "+49 16" OR "+49 15" OR "+4917" OR "+4916" OR "+4915")'

# Search region and contact patterns
REGION = '(NRW OR "Nordrhein-Westfalen" OR Düsseldorf OR Köln OR Essen OR Dortmund OR Bochum OR Duisburg OR Mönchengladbach)'
CONTACT = '(kontakt OR impressum OR ansprechpartner OR "e-mail" OR email OR telefon OR whatsapp)'
SALES = '(vertrieb OR d2d OR "call center" OR telesales OR outbound OR verkauf OR sales)'

# =========================
# PORTAL URLS
# =========================

# Kleinanzeigen URLs
KLEINANZEIGEN_URLS: List[str] = [
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
MARKT_DE_URLS: List[str] = [
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
QUOKA_DE_URLS: List[str] = [
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

# Kalaydo.de Stellengesuche URLs
KALAYDO_DE_URLS: List[str] = [
    "https://www.kalaydo.de/stellengesuche/nordrhein-westfalen/",
    "https://www.kalaydo.de/stellengesuche/koeln/",
    "https://www.kalaydo.de/stellengesuche/duesseldorf/",
    "https://www.kalaydo.de/stellengesuche/bonn/",
    "https://www.kalaydo.de/stellengesuche/aachen/",
]

# Meinestadt.de Stellengesuche URLs
MEINESTADT_DE_URLS: List[str] = [
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

# Freelancer Portal URLs
FREELANCER_PORTAL_URLS: List[str] = [
    "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-vertrieb.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-sales.html",
    "https://www.freelance.de/Freiberufler/NRW/Vertrieb/",
    "https://www.freelance.de/Freiberufler/NRW/Sales/",
    "https://www.gulp.de/gulp2/g/projekte?region=nordrhein-westfalen&skill=vertrieb",
]

# DHD24.com Stellengesuche URLs
DHD24_URLS: List[str] = [
    "https://www.dhd24.com/kleinanzeigen/stellengesuche.html",
    "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-vertrieb.html",
    "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-verkauf.html",
]

# Freelancermap.de URLs
FREELANCERMAP_URLS: List[str] = [
    "https://www.freelancermap.de/freelancer-verzeichnis/sales.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/vertrieb.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/business-development.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/account-management.html",
    "https://www.freelancermap.de/freelancer-verzeichnis/key-account-management.html",
]

# Freelance.de URLs
FREELANCE_DE_URLS: List[str] = [
    "https://www.freelance.de/Freiberufler/Vertrieb/",
    "https://www.freelance.de/Freiberufler/Sales/",
    "https://www.freelance.de/Freiberufler/Key-Account/",
    "https://www.freelance.de/Freiberufler/Business-Development/",
    "https://www.freelance.de/Freiberufler/Account-Manager/",
]

# Direct crawl URLs (alias for backward compatibility)
DIRECT_CRAWL_URLS = KLEINANZEIGEN_URLS

# =========================
# BLACKLISTS & FILTERS
# =========================

# Drop mailbox prefixes (generic emails)
DROP_MAILBOX_PREFIXES: Set[str] = {
    "info", "kontakt", "contact", "support", "service",
    "privacy", "datenschutz", "noreply", "no-reply",
    "donotreply", "do-not-reply", "jobs", "karriere",
}

# Drop portal domains (job boards, etc.)
DROP_PORTAL_DOMAINS: Set[str] = {
    "stepstone.de", "indeed.com", "heyjobs.co", "heyjobs.de",
    "softgarden.io", "jobijoba.de", "jobijoba.com", "jobware.de",
    "monster.de", "kununu.com", "ok.ru", "tiktok.com",
    "patents.google.com", "linkedin.com", "xing.com",
    "arbeitsagentur.de", "meinestadt.de", "kimeta.de",
    "stellenanzeigen.de", "bewerbung.net", "freelancermap.de",
    "reddit.com", "jobboard-deutschland.de", "kleinanzeigen.de",
    "praca.egospodarka.pl", "tabellarischer-lebenslauf.net",
    "lexware.de", "tribeworks.de", "junico.de", "qonto.com",
    "accountable.de", "sevdesk.de", "mlp.de", "netspor-tv.com",
    "trendyol.com",
}

# Blacklist domains (kept for backward compatibility - same as DROP_PORTAL_DOMAINS)
BLACKLIST_DOMAINS: Set[str] = DROP_PORTAL_DOMAINS

# Blacklist path patterns
BLACKLIST_PATH_PATTERNS: Set[str] = {
    "lebenslauf", "vorlage", "muster", "sitemap", "seminar",
    "academy", "weiterbildung", "job", "stellenangebot",
    "news", "blog", "ratgeber", "portal"
}

# Always allow patterns (regex)
ALWAYS_ALLOW_PATTERNS: List[str] = [
    r'industrievertretung',
    r'handelsvertret',
    r'vertriebspartner',
    r'/ansprechpartner/',
    r'/team/',
    r'/ueber-uns/',
    r'/kontakt/',
    r'/impressum',
]

# =========================
# PORTAL CONFIGURATIONS
# =========================

# Portal-specific request delays (seconds)
PORTAL_DELAYS: Dict[str, float] = {
    "kleinanzeigen": 3.0,
    "markt_de": 4.0,
    "quoka": 6.0,
    "kalaydo": 4.0,
    "meinestadt": 3.0,
    "dhd24": 4.0,
    "freelancermap": 3.0,
    "freelance_de": 3.0,
}

# Direct crawl source configuration
DIRECT_CRAWL_SOURCES: Dict[str, bool] = {
    "kleinanzeigen": True,
    "markt_de": True,
    "quoka": True,
    "kalaydo": False,
    "meinestadt": False,
    "freelancer_portals": False,
    "dhd24": True,
    "freelancermap": True,
    "freelance_de": False,
}

# Max profiles per URL
MAX_PROFILES_PER_URL = 10

# =========================
# EXPORT FIELDS
# =========================

DEFAULT_CSV = "vertrieb_kontakte.csv"
DEFAULT_XLSX = "vertrieb_kontakte.xlsx"

ENH_FIELDS: List[str] = [
    "name", "rolle", "email", "telefon", "quelle", "score", "tags", "region",
    "role_guess", "lead_type", "salary_hint", "commission_hint", "opening_line",
    "ssl_insecure", "company_name", "company_size", "hiring_volume",
    "industry", "recency_indicator", "location_specific",
    "confidence_score", "last_updated", "data_quality",
    "phone_type", "whatsapp_link", "private_address", "social_profile_url",
    "ai_category", "ai_summary",
    "experience_years", "skills", "availability", "current_status", "industries", "location", "profile_text",
    "candidate_status", "mobility", "industries_experience", "source_type",
    "profile_url", "cv_url", "contact_preference", "last_activity", "name_validated"
]

LEAD_FIELDS: List[str] = [
    "name", "rolle", "email", "telefon", "quelle", "score", "tags", "region",
    "role_guess", "salary_hint", "commission_hint", "opening_line", "ssl_insecure",
    "company_name", "company_size", "hiring_volume", "industry",
    "recency_indicator", "location_specific", "confidence_score",
    "last_updated", "data_quality", "phone_type", "whatsapp_link",
    "private_address", "social_profile_url", "ai_category", "ai_summary",
    "lead_type",
]

# =========================
# HELPER FUNCTIONS
# =========================

def _normalize_cx(s: str) -> str:
    """Normalize Google Custom Search CX parameter."""
    if not s:
        return ""
    try:
        p = urllib.parse.urlparse(s)
        if p.query:
            q = urllib.parse.parse_qs(p.query)
            val = q.get("cx", [""])[0].strip()
            if val:
                return val
    except Exception:
        pass
    return s.strip()


def _jitter(a=0.2, b=0.8):
    """Generate random jitter value."""
    return a + random.random() * (b - a)


def _env_list(val: str, sep: str) -> List[str]:
    """Parse environment variable as list."""
    return [x.strip() for x in val.split(sep) if x.strip()]


# =========================
# GOOGLE CUSTOM SEARCH
# =========================

# Normalize and build GCS configuration
GCS_CX = _normalize_cx(GCS_CX_RAW)
GCS_KEYS = [k.strip() for k in os.getenv("GCS_KEYS", "").split(",") if k.strip()] or ([GCS_API_KEY] if GCS_API_KEY else [])
GCS_CXS = [_normalize_cx(x) for x in os.getenv("GCS_CXS", "").split(",") if _normalize_cx(x)] or ([GCS_CX] if GCS_CX else [])

# Enable/Disable search engines
ENABLE_GOOGLE_CSE = bool(GCS_KEYS and GCS_CXS)
ENABLE_PERPLEXITY = bool(PERPLEXITY_API_KEY)
ENABLE_BING = bool(BING_API_KEY)

# =========================
# BASE DORKS (Empty placeholder - filled in scriptname.py)
# =========================

BASE_DORKS: List[str] = []


# =========================
# AI CONFIGURATION
# =========================

def get_config(param: Optional[str] = None) -> Any:
    """
    Get AI configuration with automatic fallback priority.
    
    Priority order:
    1. Django DB via ai_config app (when available)
    2. Environment variables
    3. Hardcoded defaults
    
    Args:
        param: Optional specific parameter to retrieve. If None, returns full config dict.
               Available params: 'temperature', 'max_tokens', 'top_p', 'learning_rate',
                                'daily_budget', 'monthly_budget', 'confidence_threshold',
                                'retry_limit', 'timeout_seconds', 'default_provider',
                                'default_model', 'default_model_display'
    
    Returns:
        Full config dict or specific parameter value
    
    Examples:
        >>> config = get_config()  # Get full config
        >>> temp = get_config('temperature')  # Get specific param
        >>> model = get_config('default_model')
    """
    # Default configuration (Priority 3: Hardcoded defaults)
    defaults = {
        'temperature': 0.3,
        'top_p': 1.0,
        'max_tokens': 4000,
        'learning_rate': 0.01,
        'daily_budget': 5.0,
        'monthly_budget': 150.0,
        'confidence_threshold': 0.35,
        'retry_limit': 2,
        'timeout_seconds': 30,
        'default_provider': 'OpenAI',
        'default_model': 'gpt-4o-mini',
        'default_model_display': 'GPT-4o Mini',
    }
    
    # Priority 2: Override with environment variables if set
    env_overrides = {}
    if os.getenv('AI_TEMPERATURE'):
        try:
            env_overrides['temperature'] = float(os.getenv('AI_TEMPERATURE'))
        except ValueError:
            pass
    
    if os.getenv('AI_MAX_TOKENS'):
        try:
            env_overrides['max_tokens'] = int(os.getenv('AI_MAX_TOKENS'))
        except ValueError:
            pass
    
    if os.getenv('AI_MODEL'):
        env_overrides['default_model'] = os.getenv('AI_MODEL')
    
    if os.getenv('AI_PROVIDER'):
        env_overrides['default_provider'] = os.getenv('AI_PROVIDER')
    
    # Merge defaults with env overrides
    config = {**defaults, **env_overrides}
    
    # Priority 1: Django DB (when available)
    if AI_CONFIG_AVAILABLE:
        try:
            django_config = _get_ai_config_django()
            if django_config:
                config.update(django_config)
                logger.debug("AI config loaded from Django DB")
        except Exception as e:
            logger.debug(f"Could not load AI config from Django DB: {e}")
    
    # Return specific param or full config
    if param:
        return config.get(param)
    return config
