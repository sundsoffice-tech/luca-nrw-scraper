"""Context analysis functions for detecting candidates, job ads, and hidden gems."""

import re
from typing import Optional, Tuple


# Constants
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


def is_candidate_seeking_job(text: str = "", title: str = "", url: str = "") -> bool:
    """
    Check if content indicates a candidate seeking a job.
    
    This should NEVER be blocked as a job ad - these are people looking for work!
    
    Returns:
        True if candidate signals are found
    """
    text_lower = (text + " " + title).lower()
    
    # Check if candidate is seeking job
    for signal in CANDIDATE_POSITIVE_SIGNALS:
        if signal in text_lower:
            return True  # This is a candidate! Don't block!
    
    return False


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
