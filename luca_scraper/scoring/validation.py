"""
LUCA NRW Scraper - Validation Module
=====================================
Lead validation, filtering, and classification functions.
Extracted from scriptname.py in Phase 3 refactoring.
"""

import re
import urllib.parse
from typing import Any, Dict, Tuple


# =========================
# REGEX PATTERNS
# =========================

EMAIL_RE   = re.compile(r'\b(?!noreply|no-reply|donotreply)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}\b', re.I)
PHONE_RE   = re.compile(r'(?:\+49|0049|0)\s?(?:\(?\d{2,5}\)?[\s\/\-]?)?\d(?:[\s\/\-]?\d){5,10}')
MOBILE_RE  = re.compile(r'(?:\+49|0049|0)\s*1[5-7]\d(?:[\s\/\-]?\d){6,10}')
SALES_RE   = re.compile(r'\b(vertrieb|vertriebs|sales|account\s*manager|key\s*account|business\s*development|aussendienst|aussendienst|handelsvertreter|telesales|call\s*center|outbound|haust?r|d2d)\b', re.I)
PROVISION_HINT = re.compile(r'\b(Provisionsbasis|nur\s*Provision|hohe\s*Provision(en)?|Leistungsprovision)\b', re.I)
D2D_HINT       = re.compile(r'\b(Door[-\s]?to[-\s]?door|Haustür|Kaltakquise|D2D)\b', re.I)
CALLCENTER_HINT= re.compile(r'\b(Call\s*Center|Telesales|Outbound|Inhouse-?Sales)\b', re.I)
B2C_HINT       = re.compile(
    r'\b(?:B2C|Privatkunden|Haushalte|Endkunden|Privatperson(?:en)?|'
    r'verschuld\w*|schuldenhilfe|schuldnerberatung|schuldner|'
    r'inkasso(?:[-\s]?f(?:ä|ae)lle?)?)\b',
    re.I,
)
JOBSEEKER_RE  = re.compile(r'\b(jobsuche|stellensuche|arbeitslos|lebenslauf|bewerb(ung)?|cv|portfolio|offen\s*f(?:ür|uer)\s*neues)\b', re.I)
CANDIDATE_TEXT_RE = re.compile(r'(?is)\b(ich\s+suche|suche\s+job|biete\s+mich|arbeitslos|stellengesuch|open\s+to\s+work)\b')
EMPLOYER_TEXT_RE  = re.compile(r'(?is)\b(wir\s+suchen|wir\s+stellen\s+ein|deine\s+aufgaben|unser\s+angebot|jetzt\s+bewerben)\b')
RECRUITER_RE  = re.compile(r'\b(recruit(er|ing)?|hr|human\s*resources|personalvermittlung|headhunter|wir\s*suchen|join\s*our\s*team)\b', re.I)

WHATSAPP_RE    = re.compile(r'(?i)\b(WhatsApp|Whats\s*App)[:\s]*\+?\d[\d \-()]{6,}\b')
WA_LINK_RE     = re.compile(r'(?:https?://)?(?:wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+|chat\.whatsapp\.com/[A-Za-z0-9]+)', re.I)
WHATS_RE       = re.compile(r'(?:\+?\d{2,3}\s?)?(?:\(?0\)?\s?)?\d{2,4}[\s\-]?\d{3,}.*?(?:whatsapp|wa\.me|api\.whatsapp)', re.I)
WHATSAPP_PHRASE_RE = re.compile(
    r'(?i)(meldet\s+euch\s+per\s+whatsapp|schreib(?:t)?\s+mir\s+(?:per|bei)\s+whatsapp|per\s+whatsapp\s+melden)'
)
TELEGRAM_LINK_RE = re.compile(r'(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_/-]+', re.I)

CITY_RE        = re.compile(r'\b(NRW|Nordrhein[-\s]?Westfalen|Düsseldorf|Köln|Essen|Dortmund|Mönchengladbach|Bochum|Wuppertal|Bonn)\b', re.I)
NAME_RE        = re.compile(r'\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+){0,2})\b')

# Context window patterns
SALES_WINDOW = re.compile(
    r'(?is).{0,400}(vertrieb|verkauf|sales|akquise|außendienst|aussendienst|'
    r'call\s*center|telefonverkauf|door\s*to\s*door|d2d|provision).{0,400}'
)

JOBSEEKER_WINDOW = re.compile(
    r'(?is).{0,400}(jobsuche|stellensuche|arbeitslos|bewerb(?:ung)?|lebenslauf|'
    r'cv|portfolio|offen\s*f(?:ür|uer)\s*neues|profil).{0,400}'
)


# =========================
# SIGNAL LISTS
# =========================

# CANDIDATE POSITIVE SIGNALS - Menschen die Jobs SUCHEN (dürfen NICHT als job_ad geblockt werden!)
CANDIDATE_POSITIVE_SIGNALS = [
    "suche job",
    "suche arbeit",
    "suche stelle",
    "suche neuen job",
    "suche neue stelle",
    "ich suche",
    "stellengesuch",
    "auf jobsuche",
    "offen für angebote",
    "offen für neue",
    "suche neue herausforderung",
    "suche neuen wirkungskreis",
    "verfügbar ab",
    "freigestellt",
    "open to work",
    "#opentowork",
    "looking for opportunities",
    "seeking new",
    "jobsuchend",
    "arbeitslos",
    "gekündigt",
    "wechselwillig",
    "bin auf der suche",
    "suche eine neue",
]

# JOB OFFER SIGNALS - Firmen die Mitarbeiter SUCHEN (SOLLEN geblockt werden)
JOB_OFFER_SIGNALS = [
    "(m/w/d)",
    "(w/m/d)",
    "wir suchen",
    "gesucht:",
    "ab sofort zu besetzen",
    "stellenangebot",
    "job zu vergeben",
    "mitarbeiter gesucht",
    "verstärkung gesucht",
    "team sucht",
    "für unser team",
]

STRICT_JOB_AD_MARKERS = [
    "(m/w/d)", "(w/m/d)", "(d/m/w)", "(m/f/d)", "(f/m/d)", "(gn)",
    "wir suchen", "we are hiring", "wir stellen ein", "join our team",
    "ausbildungsplatz", "azubi gesucht", "ab sofort gesucht",
    "ihre aufgaben", "wir bieten", "dein profil", "your profile", "benefits:",
    "stellenanzeige", "jobangebot", "vacancy", "karriere bei",
    "teamleiter gesucht", "sales manager gesucht", "benefits", "corporate benefits",
]

# Minimum number of job offer signals required to override a candidate signal
MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE = 2

JOB_AD_MARKERS = [
    "(m/w/d)", "(w/m/d)", "(d/m/w)", "(m/f/d)", "(f/m/d)",
    "wir suchen", "we are hiring", "stellenangebot", "jobangebot",
    "ausbildungsplatz", "azubi", "ausbildung zum",
    "teamleiter", "sales manager", "mitarbeiter",
    "gesucht", "join us", "karriere bei", "vacancies",
    "wir bieten", "deine aufgaben", "ihr profil", "your profile", "benefits", "corporate benefits",
    "obstkorb", "flache hierarchien", "bewerben sie sich", "apply now",
]

HIRING_INDICATORS = (
    "wir suchen", "suchen wir", "wir stellen ein", "join our team",
    "deine aufgaben", "ihr profil", "your profile", "wir bieten", "benefits",
    "bewerben sie sich", "jetzt bewerben", "apply now",
    "stellenanzeige", "jobangebot", "vacancy", "karriere bei",
    "(m/w/d)", "(m/f/d)", "(gn)", "einstiegsgehalt", "festanstellung",
)

SOLO_BIZ_INDICATORS = (
    # Original
    "handelsvertretung", "handelsvertreter", "selbstständiger vertriebspartner",
    "industrievertretung", "agentur für", "vertriebsbüro",
    # NEW from Research
    "§ 84 hgb", "§84 hgb", "cdh-mitglied", "cdh mitglied",
    "freie handelsvertretung", "vertriebsunternehmer", "eigenständige vertriebsunternehmung",
    "handelsagentur", "vertriebsrepräsentanz", "gebietsvertretung",
    "provisionsbasis", "courtage-vereinbarung", "übernehme vertretungen",
    "inhaltlich verantwortlicher", "einzelunternehmen", "einzelkaufmann",
    "registriert bei handelsvertreter.de", "iucab"
)

# Spezifische Handelsvertreter-Fingerprint-Phrasen
AGENT_FINGERPRINTS = (
    "selbstständiger handelsvertreter", "handelsvertretung cdh", "cdh-mitglied",
    "gemäß § 84 hgb", "gemäß §84 hgb", "industrievertretung",
    "vertriebsbüro inhaber", "auf provisionsbasis", "vertretung für plz",
    "freie handelsvertretung", "vertriebsagentur", "gebiete: plz",
    "mitglied im handelsvertreterverband", "iucab", "handelsregister a",
    "einzelkaufmann", "e.k."
)

RETAIL_ROLES = [
    "kuechen", "kueche", "moebel", "einzelhandel", "verkaeufer", "verkaeuferin",
    "kassierer", "servicekraft", "filialleiter", "shop manager", "baecker",
    "metzger", "floor manager", "call center", "telefonist", "promoter",
]

CANDIDATE_KEYWORDS = [
    "suche job",
    "biete mich an",
    "open to work",
    "neue herausforderung",
    "gesuch",
    "lebenslauf",
]

IGNORE_KEYWORDS = [
    "wir suchen",
    "stellenanzeige",
    "gmbh",
    "hr manager",
    "karriere bei uns",
]


# =========================
# VALIDATION FUNCTIONS
# =========================

def is_candidate_seeking_job(text: str = "", title: str = "", url: str = "") -> bool:
    """
    Prüft ob es sich um einen jobsuchenden Kandidaten handelt (darf NICHT geblockt werden!).
    
    Args:
        text: Page text content
        title: Page title
        url: Page URL (unused but kept for API compatibility)
        
    Returns:
        True if this is a candidate seeking a job, False otherwise
    """
    text_lower = (text + " " + title).lower()
    
    # ERST prüfen: Ist es ein KANDIDAT der einen Job SUCHT?
    for signal in CANDIDATE_POSITIVE_SIGNALS:
        if signal in text_lower:
            return True  # Das ist ein Kandidat! Nicht blocken!
    
    return False


def is_job_advertisement(text: str = "", title: str = "", snippet: str = "") -> bool:
    """
    Return True if content/title/snippet contains strict job-ad markers (company hiring).
    
    Args:
        text: Page text content
        title: Page title
        snippet: Search result snippet
        
    Returns:
        True if this is a job advertisement, False otherwise
    """
    combined = " ".join([(text or ""), (title or ""), (snippet or "")]).lower()
    
    # FIRST: Check if this is a CANDIDATE seeking a job - NEVER block candidates!
    if is_candidate_seeking_job(text, title):
        # If candidate signal is found, only mark as job ad if there are MULTIPLE strong job offer signals
        job_offer_count = sum(1 for offer in JOB_OFFER_SIGNALS if offer in combined)
        if job_offer_count < MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE:
            return False  # It's a candidate, not a job ad!
    
    # THEN: Check for job offer signals
    return any(m in combined for m in STRICT_JOB_AD_MARKERS)


def classify_lead(lead: Dict[str, Any], title: str = "", text: str = "") -> str:
    """
    Classify lead/persona type for lead_type column.
    
    Args:
        lead: Lead dictionary with name and other fields
        title: Page title
        text: Page text
        
    Returns:
        Lead type: "job_ad", "company", "individual", or "candidate"
    """
    name = (lead.get("name") or "").strip()
    combined = " ".join([(title or ""), (text or ""), name]).lower()
    name_lower = name.lower()
    title_lower = (title or "").lower()
    text_lower = (text or "").lower()

    job_triggers = set(STRICT_JOB_AD_MARKERS + [
        "your profile",
        "wir bieten",
        "gesucht",
    ])

    # Hard job-ad signals
    if any(m in combined for m in job_triggers):
        return "job_ad"

    company_markers = (
        "gmbh", "ag", "kg", "ug", "co. kg", "inc", "ltd", "holding", "group",
        "unternehmen", "firma", "company",
    )
    if any(tok in name_lower for tok in company_markers) or any(tok in title_lower for tok in company_markers):
        return "company"
    
    # Check if name looks like company (requires helper function from scriptname)
    # For now, simplified check
    if any(marker in name_lower for marker in company_markers):
        return "company"

    sales_tokens = [
        "vertrieb", "verkauf", "sales", "handelsvertreter", "aussendienst",
        "account manager", "key account", "call center", "telefonverkauf",
        "sales representative", "commercial agent", "account executive",
    ]
    
    # Simplified human name check - at least 2 words with capitals
    is_human = len(name.split()) >= 2 and any(c.isupper() for c in name)
    has_sales = any(tok in combined for tok in sales_tokens)
    
    if is_human and has_sales:
        return "individual"
    if is_human:
        return "candidate"
    if has_sales:
        return "candidate"
    return "candidate"


def is_garbage_context(text: str, url: str = "", title: str = "", h1: str = "") -> Tuple[bool, str]:
    """
    Detect obvious non-candidate contexts (blogs, shops, company imprint, job ads).
    
    Args:
        text: Page text content
        url: Page URL
        title: Page title
        h1: H1 heading
        
    Returns:
        Tuple of (is_garbage, reason)
    """
    # Note: This function relies on some external functions that need to be available:
    # - _is_candidates_mode()
    # - SOCIAL_PROFILE_PATTERNS
    # These will need to be imported from scriptname.py in the integration step
    
    t = (text or "").lower()
    ttl = (title or "").lower()
    h1l = (h1 or "").lower()
    url_lower = url.lower() if url else ""

    # FIRST: Check if this is a CANDIDATE seeking a job - NEVER mark candidates as garbage!
    if is_candidate_seeking_job(text, title, url):
        return False, ""  # Not garbage - this is a candidate!
    
    # Allow social media profiles
    social_profile_urls = [
        "linkedin.com/in/", "xing.com/profile/", "facebook.com/profile/",
        "instagram.com/", "twitter.com/", "x.com/",
    ]
    if any(social_url in url_lower for social_url in social_profile_urls):
        return False, ""  # Social profiles are allowed

    news_tokens = (
        "news", "artikel", "bericht", "tipps", "trends", "black friday",
        "angebot", "webinar", "termine", "veranstaltung",
    )
    if any(tok in ttl for tok in news_tokens) or any(tok in h1l for tok in news_tokens):
        return True, "news_blog"

    shop_tokens = ("warenkorb", "kasse", "preis inkl", "preis inkl. mwst", "versandkosten", "lieferzeit", "bestellen")
    if any(tok in t for tok in shop_tokens):
        return True, "shop_product"

    company_tokens = (" gmbh", "gmbh", " ag", " kg")
    profile_tokens = ("profil", "lebenslauf", "gesuch")
    if any(tok in ttl for tok in company_tokens) and not any(pk in ttl for pk in profile_tokens):
        return True, "company_imprint"

    job_ad_tokens = ("wir suchen", "wir bieten", "deine aufgaben", "bewirb dich jetzt", "stellenanzeige", "jobangebot") + tuple(STRICT_JOB_AD_MARKERS)
    if any(tok in t for tok in job_ad_tokens):
        # Double-check: make sure it's not a candidate with these words in context
        if not is_candidate_seeking_job(text, title, url):
            return True, "job_ad"

    return False, ""


def should_drop_lead(lead: Dict[str, Any], page_url: str, text: str = "", title: str = "") -> Tuple[bool, str]:
    """
    Post-extraction lead validation with strict phone/email/content checks.
    
    **IMPORTANT**: This is a simplified version for the refactored module.
    The full implementation requires integration with scriptname.py dependencies:
    - is_job_posting() from learning_engine
    - validate_phone() from lead_validation
    - normalize_phone() from lead_validation or phone_extractor
    - is_mobile_number() from learning_engine
    - Various constants (DROP_MAILBOX_PREFIXES, DROP_PORTAL_DOMAINS, etc.)
    - Helper functions (_matches_hostlist, log, etc.)
    
    For now, this provides the basic structure and documentation.
    Integration will be completed when scriptname.py is fully refactored.
    
    Args:
        lead: Lead dictionary
        page_url: Source URL
        text: Page text
        title: Page title
        
    Returns:
        Tuple of (should_drop, reason)
    """
    # Basic validation that doesn't require external dependencies
    email = (lead.get("email") or "").strip().lower()
    phone = (lead.get("telefon") or "").strip()

    def _drop(reason: str) -> Tuple[bool, str]:
        return True, reason
    
    # Basic phone check
    if not phone:
        return _drop("no_phone")
    
    # TODO: Integrate full validation when dependencies are available:
    # - Check is_job_posting() 
    # - Validate phone format with validate_phone()
    # - Check if mobile number with is_mobile_number()
    # - Check email against DROP_MAILBOX_PREFIXES
    # - Check domain against DROP_PORTAL_DOMAINS
    # - Check URL patterns
    
    return False, ""


def should_skip_url_prefetch(url: str, title: str = "", snippet: str = "", is_snippet_jackpot: bool = False) -> Tuple[bool, str]:
    """
    Pre-fetch URL filtering: check blacklist hosts and path patterns.
    Snippet jackpots with contact data are always allowed through (unless job postings).
    
    **IMPORTANT**: This is a simplified version for the refactored module.
    The full implementation requires integration with scriptname.py dependencies:
    - is_job_posting() from learning_engine
    - _is_candidates_mode() helper function
    - is_candidate_url() validation function
    - Various constants (ALWAYS_ALLOW_PATTERNS, DROP_PORTAL_DOMAINS, BLACKLIST_PATH_PATTERNS)
    - Helper function _matches_hostlist()
    
    For now, this provides the basic structure and documentation.
    Integration will be completed when scriptname.py is fully refactored.
    
    Args:
        url: URL to check
        title: Page title
        snippet: Search snippet
        is_snippet_jackpot: Whether snippet contains contact data
        
    Returns:
        Tuple of (should_skip, reason)
    """
    if not url:
        return False, ""
    
    # Basic URL validation without dependencies
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()
        url_lower = url.lower()
        
        # TODO: Integrate full filtering when dependencies are available:
        # - Check is_job_posting()
        # - Check _is_candidates_mode() and is_candidate_url()
        # - Check against ALWAYS_ALLOW_PATTERNS
        # - Check snippet jackpots
        # - Check host against DROP_PORTAL_DOMAINS
        # - Check path against BLACKLIST_PATH_PATTERNS
        
        return False, ""
    except Exception:
        return False, ""
