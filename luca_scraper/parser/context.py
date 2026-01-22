"""Context analysis functions for detecting candidates, job ads, and hidden gems."""

import re
from typing import Optional, Tuple


# Constants

# CANDIDATE_STRONG_SIGNALS - Single phrase is enough to identify as candidate
CANDIDATE_STRONG_SIGNALS = [
    # Direct job search phrases
    "stellengesuch",
    "job gesucht",
    "arbeit gesucht",
    "stelle gesucht",
    "ich suche job",
    "ich suche arbeit",
    "ich suche stelle",
    "ich suche einen job",
    "ich suche eine arbeit",
    "ich suche eine stelle",
    "suche job",
    "suche arbeit",
    "suche stelle",
    "suche neuen job",
    "suche neue stelle",
    "suche neue arbeit",
    "suche neue herausforderung",
    "suche neuen wirkungskreis",
    
    # Availability signals
    "ab sofort verfügbar",
    "sofort verfügbar",
    "verfügbar ab",
    "freigestellt",
    "gekündigt",
    "arbeitslos",
    "arbeitssuchend",
    "jobsuchend",
    "auf jobsuche",
    
    # LinkedIn/Social signals
    "open to work",
    "#opentowork",
    "offen für angebote",
    "offen für neue chancen",
    "offen für neues",
    "offen für neue",
    "looking for opportunities",
    "seeking new opportunities",
    "seeking new",
    
    # Willingness to change
    "wechselwillig",
    "wechselbereit",
    "bereit für veränderung",
    "neue wege gehen",
    "neuen wirkungskreis",
    
    # Career change / Quereinstieg
    "quereinstieg",
    "quereinsteiger",
    "mehr geld verdienen",
    "bessere verdienstmöglichkeiten",
    "karrierewechsel",
    
    # General search phrases
    "bin auf der suche",
    "suche eine neue",
    "ich suche",
]

# CANDIDATE_MEDIUM_SIGNALS - Need context or contact data to confirm
CANDIDATE_MEDIUM_SIGNALS = [
    # Self-description
    "biete meine dienste",
    "biete mich an",
    "stelle mich vor",
    "mein profil",
    "meine erfahrung",
    "meine qualifikation",
    "mein lebenslauf",
    
    # CV/Application
    "lebenslauf",
    "curriculum vitae",
    "bewerberprofil",
    "qualifikationen",
    
    # Flexibility
    "flexibel einsetzbar",
    "deutschlandweit",
    "bundesweit",
    "regional flexibel",
    
    # Sales representatives
    "handelsvertreter",
    "handelsvertretung",
    "selbstständiger vertreter",
    "freiberuflicher vertrieb",
    "auf provisionsbasis",
]

# SALES_CONTEXT_SIGNALS - Strengthen other candidate signals
SALES_CONTEXT_SIGNALS = [
    "vertrieb",
    "verkauf",
    "sales",
    "außendienst",
    "aussendienst",
    "innendienst",
    "key account",
    "account manager",
    "business development",
    "akquise",
    "neukundengewinnung",
    "kundenbetreuung",
    "call center",
    "callcenter",
    "telesales",
    "telefonverkauf",
    "d2d",
    "door to door",
    "haustür",
    "kaltakquise",
]

# Combined list for backward compatibility
CANDIDATE_POSITIVE_SIGNALS = CANDIDATE_STRONG_SIGNALS + CANDIDATE_MEDIUM_SIGNALS

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

MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE = 2

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


# URL patterns that indicate job seekers (Stellengesuche)
CANDIDATE_URL_PATTERNS = [
    "/s-stellengesuche/",
    "/stellengesuche/",
    "/stellengesuch/",
    "/jobgesuche/",
    "/arbeitgesuche/",
]

# URL patterns that indicate job offers (Stellenangebote) - BLOCK these
EMPLOYER_URL_PATTERNS = [
    "/s-jobs/",
    "/stellenangebote/",
    "/stellenangebot/",
    "/karriere/",
    "/karriere-",
    "/jobs/",
    "/vacancy/",
    "/vacancies/",
    "/open-positions/",
    "/offene-stellen/",
]

# Regex for phone number detection (German mobile)
PHONE_PATTERN = re.compile(r'(?:\+49|0049|0)\s?1[5-7]\d(?:[\s\/\-]?\d){6,10}')
# Regex for email detection
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
# Regex for WhatsApp links
WHATSAPP_PATTERN = re.compile(r'wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+')


def has_contact_data(text: str) -> bool:
    """Check if text contains contact data (phone or email)."""
    text_lower = text.lower()
    return bool(
        PHONE_PATTERN.search(text) or 
        EMAIL_PATTERN.search(text) or 
        WHATSAPP_PATTERN.search(text_lower) or
        "tel:" in text_lower or
        "mailto:" in text_lower
    )


def has_sales_context(text: str) -> bool:
    """Check if text has sales/vertrieb context."""
    text_lower = text.lower()
    return any(signal in text_lower for signal in SALES_CONTEXT_SIGNALS)


def is_candidate_seeking_job(text: str = "", title: str = "", url: str = "") -> bool:
    """
    Check if content indicates a candidate seeking a job.
    
    This should NEVER be blocked as a job ad - these are people looking for work!
    
    Priority rules:
    1. URL pattern /s-stellengesuche/ → ALWAYS candidate
    2. Strong candidate signals → candidate
    3. Medium signals + contact data → candidate  
    4. Medium signals + sales context → candidate
    
    Returns:
        True if candidate signals are found
    """
    text_lower = (text + " " + title).lower()
    url_lower = (url or "").lower()
    
    # Rule 1: URL patterns that ALWAYS indicate job seekers
    for pattern in CANDIDATE_URL_PATTERNS:
        if pattern in url_lower:
            return True  # Stellengesuche URL = always candidate!
    
    # Rule 2: Strong candidate signals (single phrase is enough)
    for signal in CANDIDATE_STRONG_SIGNALS:
        if signal in text_lower:
            return True  # This is a candidate! Don't block!
    
    # Rule 3: Medium signals with contact data
    has_medium_signal = any(signal in text_lower for signal in CANDIDATE_MEDIUM_SIGNALS)
    if has_medium_signal and has_contact_data(text + " " + title):
        return True  # Medium signal + contact = candidate
    
    # Rule 4: Medium signals with sales context
    if has_medium_signal and has_sales_context(text + " " + title):
        return True  # Medium signal + sales context = candidate
    
    return False


def is_employer_url(url: str) -> bool:
    """Check if URL indicates an employer job posting."""
    url_lower = (url or "").lower()
    return any(pattern in url_lower for pattern in EMPLOYER_URL_PATTERNS)


def analyze_wir_suchen_context(text: str, url: str = "") -> Tuple[str, str]:
    """
    Analyze "wir suchen" (we are looking for) in context.
    
    Returns: (classification, reason)
    - "job_ad" = Job advertisement (BLOCK)
    - "candidate" = Candidate seeking (ALLOW)
    - "business_inquiry" = Business inquiry (ALLOW with check)
    - "unclear" = Unclear (needs further checking)
    """
    text_lower = text.lower()
    
    wir_suchen_matches = list(re.finditer(r'wir\s+suchen', text_lower))
    
    if not wir_suchen_matches:
        return "unclear", "Kein 'wir suchen' gefunden"
    
    for match in wir_suchen_matches:
        start = max(0, match.start() - 200)
        end = min(len(text_lower), match.end() + 300)
        context = text_lower[start:end]
        
        # === JOB ADVERTISEMENT (BLOCK) ===
        job_ad_signals = [
            "(m/w/d)", "(w/m/d)", "(d/m/w)",
            "zum nächstmöglichen", "zur verstärkung",
            "für unser team", "ihre aufgaben", "ihr profil",
            "wir bieten", "benefits", "festanstellung",
            "vollzeit", "teilzeit", "homeoffice möglich",
            "bewerbung an", "bewerben sie sich",
        ]
        job_ad_count = sum(1 for signal in job_ad_signals if signal in context)
        
        if job_ad_count >= 2:
            return "job_ad", f"Stellenanzeige ({job_ad_count} Signale)"
        
        # === CANDIDATE SEEKING (ALLOW) ===
        candidate_signals = [
            "wir suchen ein unternehmen", "wir suchen eine firma",
            "wir suchen aufträge", "wir suchen neue kunden",
            "wir suchen vertretungen", "wir suchen partner",
            "wir suchen projekte", "ich und mein team suchen",
            "wir als handelsvertretung suchen",
            "wir als freelancer suchen",
        ]
        for signal in candidate_signals:
            if signal in context:
                return "candidate", f"Kandidat/Team sucht: '{signal}'"
        
        # === SINGLE PERSON (Pluralis Majestatis) ===
        solo_signals = [
            "biete meine dienste", "meine erfahrung",
            "mein profil", "ich bin", "verfügbar ab",
            "kontaktieren sie mich",
        ]
        for signal in solo_signals:
            if signal in context:
                return "candidate", f"Einzelperson ('{signal}' im Kontext)"
        
        # === BUSINESS INQUIRY ===
        business_signals = [
            "suchen lieferanten", "suchen hersteller",
            "suchen dienstleister", "suchen zusammenarbeit",
        ]
        for signal in business_signals:
            if signal in context:
                return "business_inquiry", f"Geschäftsanfrage: '{signal}'"
    
    return "unclear", "Kontext nicht eindeutig"


def detect_hidden_gem(text: str, url: str = "") -> Tuple[Optional[str], int, str]:
    """
    Detect career changers with sales potential (hidden gems).
    
    Identifies people from industries like gastronomy, retail, call centers, etc.
    who could be great sales candidates due to their customer-facing experience.
    
    Returns: (gem_type, confidence, reason) or (None, 0, "")
    """
    text_lower = text.lower()
    
    for gem_type, pattern in HIDDEN_GEMS_PATTERNS.items():
        keyword_hits = sum(1 for k in pattern["keywords"] if k in text_lower)
        positive_hits = sum(1 for p in pattern["positive"] if p in text_lower)
        
        if keyword_hits >= 1 and positive_hits >= 1:
            confidence = min(95, 50 + keyword_hits * 15 + positive_hits * 10)
            return gem_type, confidence, pattern["reason"]
    
    return None, 0, ""
