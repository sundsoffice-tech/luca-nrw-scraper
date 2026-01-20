"""
LUCA NRW Scraper - Portal URLs and Regional Configuration
=========================================================
Portal URLs, city lists, blacklists, and related functions.
"""

import logging
from typing import List, Dict, Set, Any, Optional

logger = logging.getLogger(__name__)


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

# WLW (Wer liefert was) - B2B Business Directory URLs
WLW_URLS: List[str] = [
    "https://www.wlw.de/de/suche?q=vertrieb&location=nordrhein-westfalen",
    "https://www.wlw.de/de/suche?q=sales&location=nordrhein-westfalen",
    "https://www.wlw.de/de/suche?q=handelsvertretung&location=nordrhein-westfalen",
    "https://www.wlw.de/de/suche?q=vertriebspartner&location=nordrhein-westfalen",
]

# Gelbe Seiten (Yellow Pages) - Business Directory URLs
GELBE_SEITEN_URLS: List[str] = [
    "https://www.gelbeseiten.de/suche/vertrieb/nordrhein-westfalen",
    "https://www.gelbeseiten.de/suche/sales/nordrhein-westfalen",
    "https://www.gelbeseiten.de/suche/handelsvertreter/nordrhein-westfalen",
    "https://www.gelbeseiten.de/suche/vertriebsleiter/koeln",
    "https://www.gelbeseiten.de/suche/vertriebsleiter/duesseldorf",
    "https://www.gelbeseiten.de/suche/vertriebsleiter/dortmund",
]

# Das Örtliche (Local Business Directory) URLs
DAS_OERTLICHE_URLS: List[str] = [
    "https://www.dasoertliche.de/Themen/vertrieb-nordrhein-westfalen.html",
    "https://www.dasoertliche.de/Themen/sales-nordrhein-westfalen.html",
    "https://www.dasoertliche.de/Themen/handelsvertreter-nordrhein-westfalen.html",
]

# Northdata - Company Register URLs
NORTHDATA_URLS: List[str] = [
    "https://www.northdata.de/",  # Main search - requires search query
]

# Firmen ABC - Business Directory URLs
FIRMEN_ABC_URLS: List[str] = [
    "https://www.firmenabc.de/nordrhein-westfalen/",
]

# Cylex - Local Business Directory URLs
CYLEX_URLS: List[str] = [
    "https://www.cylex.de/nordrhein-westfalen/vertrieb.html",
    "https://www.cylex.de/nordrhein-westfalen/sales.html",
    "https://www.cylex.de/koeln/vertrieb.html",
    "https://www.cylex.de/duesseldorf/vertrieb.html",
]

# Hotfrog - Business Directory URLs
HOTFROG_URLS: List[str] = [
    "https://www.hotfrog.de/suche/nordrhein-westfalen/vertrieb",
    "https://www.hotfrog.de/suche/nordrhein-westfalen/sales",
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
    # New business directories (conservative delays for professional sites)
    "wlw": 4.0,
    "gelbe_seiten": 3.0,
    "das_oertliche": 3.0,
    "northdata": 5.0,
    "firmen_abc": 4.0,
    "cylex": 3.0,
    "hotfrog": 3.0,
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
    # New high-quality sources (enabled for professional directories)
    "wlw": True,
    "gelbe_seiten": True,
    "das_oertliche": True,
    "northdata": False,  # Requires API or special handling
    "firmen_abc": True,
    "cylex": True,
    "hotfrog": True,
}

# Max profiles per URL
MAX_PROFILES_PER_URL = 10


# =========================
# BASE DORKS
# =========================
# Empty placeholder for future implementation
# Dorks are currently defined in other modules or dynamically generated

BASE_DORKS: List[str] = []


# =========================
# PORTAL URL FUNCTIONS
# =========================

# These will be set by config.py after imports to avoid circular dependencies
_get_portals_django = None
_SCRAPER_CONFIG_AVAILABLE = False


def _set_django_loaders(get_portals_func, scraper_config_available):
    """Set Django loader functions from config.py to avoid circular imports."""
    global _get_portals_django, _SCRAPER_CONFIG_AVAILABLE
    _get_portals_django = get_portals_func
    _SCRAPER_CONFIG_AVAILABLE = scraper_config_available


def get_portal_urls(portal_name: str) -> List[str]:
    """
    Get URLs for a portal from database, with fallback to hardcoded lists.
    
    This function enables database-managed portal URLs while maintaining
    backward compatibility with hardcoded URL lists.
    
    Args:
        portal_name: Internal portal name (e.g., 'kleinanzeigen', 'markt_de')
    
    Returns:
        List of URLs to crawl for the portal
        
    Priority:
        1. Django DB (PortalSource.urls) - if available and non-empty
        2. Hardcoded URL lists - as fallback
    """
    # Mapping from portal names to hardcoded URL lists
    _HARDCODED_URLS = {
        'kleinanzeigen': KLEINANZEIGEN_URLS,
        'markt_de': MARKT_DE_URLS,
        'quoka': QUOKA_DE_URLS,
        'kalaydo': KALAYDO_DE_URLS,
        'meinestadt': MEINESTADT_DE_URLS,
        'dhd24': DHD24_URLS,
        'freelancermap': FREELANCERMAP_URLS,
        'freelance_de': FREELANCE_DE_URLS,
        'freelancer_portals': FREELANCER_PORTAL_URLS,
        # New High-Quality Business Directories
        'wlw': WLW_URLS,
        'gelbe_seiten': GELBE_SEITEN_URLS,
        'das_oertliche': DAS_OERTLICHE_URLS,
        'northdata': NORTHDATA_URLS,
        'firmen_abc': FIRMEN_ABC_URLS,
        'cylex': CYLEX_URLS,
        'hotfrog': HOTFROG_URLS,
    }
    
    # Try to load from database first
    if _SCRAPER_CONFIG_AVAILABLE and _get_portals_django:
        try:
            portals = _get_portals_django()
            if portals and portal_name in portals:
                db_urls = portals[portal_name].get('urls', [])
                if db_urls:
                    logger.debug(f"Loaded {len(db_urls)} URLs for {portal_name} from database")
                    return db_urls
        except Exception as e:
            logger.debug(f"Could not load portal URLs from DB for {portal_name}: {e}")
    
    # Fallback to hardcoded lists
    fallback_urls = _HARDCODED_URLS.get(portal_name, [])
    if fallback_urls:
        logger.debug(f"Using {len(fallback_urls)} hardcoded URLs for {portal_name}")
    return fallback_urls


def get_portal_config(portal_name: str) -> Dict[str, Any]:
    """
    Get complete configuration for a portal from database, with fallback to defaults.
    
    Returns a dict with:
        - urls: List[str] - URLs to crawl
        - rate_limit_seconds: float - Delay between requests
        - max_results: int - Maximum results per crawl
        - is_active: bool - Whether portal is enabled
    
    Args:
        portal_name: Internal portal name (e.g., 'kleinanzeigen', 'markt_de')
    
    Returns:
        Dict with portal configuration
    """
    # Default configuration using hardcoded values
    default_config = {
        'urls': get_portal_urls(portal_name),
        'rate_limit_seconds': PORTAL_DELAYS.get(portal_name, 3.0),
        'max_results': 20,
        'is_active': DIRECT_CRAWL_SOURCES.get(portal_name, False),
    }
    
    # Try to load from database
    if _SCRAPER_CONFIG_AVAILABLE and _get_portals_django:
        try:
            portals = _get_portals_django()
            if portals and portal_name in portals:
                db_config = portals[portal_name]
                # Merge with defaults, preferring DB values
                # Note: config_loader returns 'rate_limit' key from rate_limit_seconds field
                db_rate_limit = db_config.get('rate_limit') or db_config.get('rate_limit_seconds')
                return {
                    'urls': db_config.get('urls') or default_config['urls'],
                    'rate_limit_seconds': db_rate_limit or default_config['rate_limit_seconds'],
                    'max_results': db_config.get('max_results', default_config['max_results']),
                    'is_active': True,  # If in DB and active filter, it's active
                }
        except Exception as e:
            logger.debug(f"Could not load portal config from DB for {portal_name}: {e}")
    
    return default_config


def get_all_portal_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get configurations for all portals from database, with fallback to defaults.
    
    Returns a dict mapping portal names to their configurations.
    New portals can be added via the database without code changes.
    """
    # Start with hardcoded portal names
    all_portals = {
        'kleinanzeigen', 'markt_de', 'quoka', 'kalaydo', 'meinestadt',
        'dhd24', 'freelancermap', 'freelance_de',
        # New high-quality business directories
        'wlw', 'gelbe_seiten', 'das_oertliche', 'northdata',
        'firmen_abc', 'cylex', 'hotfrog'
    }
    
    # Try to get additional portals from database
    if _SCRAPER_CONFIG_AVAILABLE and _get_portals_django:
        try:
            db_portals = _get_portals_django()
            if db_portals:
                all_portals.update(db_portals.keys())
        except Exception as e:
            logger.debug(f"Could not load portal list from DB: {e}")
    
    # Build config for all portals
    configs = {}
    for portal_name in all_portals:
        configs[portal_name] = get_portal_config(portal_name)
    
    return configs
