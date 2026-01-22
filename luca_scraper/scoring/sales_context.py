# -*- coding: utf-8 -*-
"""
Sales Context Detection & Lead Scoring Module
=============================================

This module provides sales/recruiting context detection and lead scoring:

Aufgabe 2 - Vertriebs-Kontext-Erkennung:
- Sales/Vertrieb keywords (German + English)
- Job-seeking signal phrases
- Point-based scoring model
- Lead classification thresholds (High/Medium/Low)

Scoring Model:
=============
Points are awarded for various signals:
- Sales/Vertrieb keywords: +1 point each (max 5)
- Job-seeking signals: +2 points each (max 8)
- Phone number present: +3 points
- Email present: +2 points
- NRW region indicator: +2 points
- Mobile number (vs landline): +2 bonus points
- WhatsApp contact: +3 bonus points

Thresholds:
- High-Value Lead: Score >= 8
- Medium Lead: Score 4-7
- Low Lead: Score < 4
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


# ========================================
# SALES/VERTRIEB KEYWORDS (German + English)
# ========================================

# Primary sales keywords - indicate sales professional
SALES_KEYWORDS_PRIMARY: List[str] = [
    # German
    "vertrieb",
    "außendienst",
    "aussendienst",
    "innendienst",
    "verkäufer",
    "verkaeuferin",
    "handelsvertreter",
    "vertriebsmitarbeiter",
    "vertriebsleiter",
    "vertriebsberater",
    "key account",
    "kundenbetreuer",
    "kundenberater",
    "telesales",
    "telefonverkauf",
    "callcenter",
    "call center",
    "outbound",
    "inbound",
    "akquise",
    "neukundengewinnung",
    
    # English
    "sales",
    "account manager",
    "business development",
    "sales representative",
    "sales executive",
    "sales manager",
    "field sales",
    "inside sales",
]

# Secondary sales keywords - indicate sales-related context
SALES_KEYWORDS_SECONDARY: List[str] = [
    # German
    "provision",
    "provisionsbasis",
    "bonus",
    "zielgehalt",
    "umsatzbeteiligung",
    "erfolgsbeteiligung",
    "vermittlung",
    "vermittler",
    "berater",
    "beratung",
    "kundenakquise",
    "abschluss",
    "abschlussstark",
    "hunter",
    "farmer",
    "closer",
    "setter",
    "d2d",
    "door to door",
    "haustür",
    "haustuergeschaeft",
    "kaltakquise",
    "warmakquise",
    
    # English
    "commission",
    "target",
    "quota",
    "pipeline",
    "leads",
    "closing",
    "prospecting",
    "cold calling",
    "b2b",
    "b2c",
]

# Industry keywords that indicate high-value sales
HIGH_VALUE_INDUSTRIES: List[str] = [
    # Energy/Solar
    "solar",
    "photovoltaik",
    "pv-anlage",
    "energie",
    "energieberatung",
    "strom",
    "gas",
    "wärmepumpe",
    
    # Telco/Internet
    "glasfaser",
    "telekommunikation",
    "mobilfunk",
    "dsl",
    "internet",
    
    # Insurance/Finance
    "versicherung",
    "finanzberatung",
    "bausparen",
    "altersvorsorge",
    
    # Real Estate
    "immobilien",
    "makler",
    
    # Home Services
    "fenster",
    "türen",
    "dämmung",
    "renovierung",
]


# ========================================
# JOB-SEEKING SIGNAL PHRASES
# ========================================

# Strong job-seeking signals - person is actively looking
JOB_SEEKING_SIGNALS_STRONG: List[str] = [
    # German - Direct job search
    "ich suche einen job",
    "suche einen job",
    "suche arbeit",
    "suche neue stelle",
    "suche neuen job",
    "stellengesuch",
    "biete mich an",
    "bin auf der suche",
    "auf jobsuche",
    
    # German - Status indicators
    "arbeitslos",
    "arbeitssuchend",
    "gekündigt",
    "freigestellt",
    "wechselwillig",
    "wechselbereit",
    "unzufrieden",
    "mehr geld",
    "mehr verdienen",
    "bessere bezahlung",
    
    # German - Availability
    "verfügbar ab",
    "ab sofort verfügbar",
    "sofort verfügbar",
    "kurzfristig verfügbar",
    
    # German - Career change
    "quereinstieg",
    "quereinsteiger",
    "umorientierung",
    "berufliche neuorientierung",
    "neue herausforderung",
    "neuer wirkungskreis",
    
    # English
    "open to work",
    "#opentowork",
    "seeking new opportunities",
    "looking for job",
    "job hunting",
    "available for hire",
]

# Moderate job-seeking signals
JOB_SEEKING_SIGNALS_MODERATE: List[str] = [
    # German
    "suche nebenjob",
    "nebentätigkeit gesucht",
    "zusatzverdienst",
    "teilzeit gesucht",
    "minijob gesucht",
    "offen für angebote",
    "offen für neues",
    "interessiert an",
    "bewerbung",
    "lebenslauf",
    
    # English
    "open to offers",
    "exploring opportunities",
    "freelance available",
    "cv",
    "resume",
]


# ========================================
# NRW REGION INDICATORS
# ========================================

NRW_INDICATORS: List[str] = [
    # Region names
    "nrw",
    "nordrhein-westfalen",
    "nordrhein westfalen",
    "ruhrgebiet",
    "rheinland",
    "sauerland",
    "münsterland",
    "ostwestfalen",
    "owl",
    
    # Major cities
    "düsseldorf",
    "duesseldorf",
    "köln",
    "koeln",
    "dortmund",
    "essen",
    "duisburg",
    "bochum",
    "wuppertal",
    "bielefeld",
    "bonn",
    "münster",
    "muenster",
    "gelsenkirchen",
    "mönchengladbach",
    "moenchengladbach",
    "aachen",
    "krefeld",
    "oberhausen",
    "hagen",
    "hamm",
    "leverkusen",
    "solingen",
    "neuss",
    "paderborn",
    
    # PLZ ranges for NRW
    "40xxx",  # Düsseldorf area
    "41xxx",  # Mönchengladbach area
    "42xxx",  # Wuppertal area
    "44xxx",  # Dortmund area
    "45xxx",  # Essen area
    "46xxx",  # Duisburg/Oberhausen area
    "47xxx",  # Duisburg area
    "48xxx",  # Münster area
    "50xxx",  # Köln area
    "51xxx",  # Köln area
    "52xxx",  # Aachen area
    "53xxx",  # Bonn area
]


# ========================================
# SCORING CONFIGURATION
# ========================================

@dataclass
class ScoringConfig:
    """Configuration for lead scoring points."""
    
    # Keyword points
    sales_keyword_primary: int = 1      # Per keyword found
    sales_keyword_secondary: int = 1    # Per keyword found
    sales_keyword_max: int = 5          # Max points from keywords
    
    high_value_industry: int = 2        # Per industry keyword
    industry_max: int = 4               # Max industry points
    
    # Job-seeking signal points
    job_signal_strong: int = 3          # Per strong signal
    job_signal_moderate: int = 2        # Per moderate signal
    job_signal_max: int = 8             # Max points from signals
    
    # Contact information points
    phone_present: int = 3              # Has any phone number
    mobile_phone_bonus: int = 2         # Mobile (vs landline)
    email_present: int = 2              # Has email
    whatsapp_present: int = 3           # Has WhatsApp contact
    
    # Location points
    nrw_indicator: int = 2              # NRW location mention
    
    # Lead classification thresholds
    high_value_threshold: int = 8       # >= this is High-Value Lead
    medium_threshold: int = 4           # >= this is Medium Lead
    # Below medium_threshold is Low Lead


# Default configuration
DEFAULT_SCORING_CONFIG = ScoringConfig()


# ========================================
# SCORING FUNCTIONS
# ========================================

@dataclass
class LeadScore:
    """Result of lead scoring."""
    
    total_score: int = 0
    classification: str = "LOW"  # HIGH, MEDIUM, LOW
    
    # Score breakdown
    sales_keywords_score: int = 0
    sales_keywords_found: List[str] = field(default_factory=list)
    
    industry_score: int = 0
    industries_found: List[str] = field(default_factory=list)
    
    job_signals_score: int = 0
    job_signals_found: List[str] = field(default_factory=list)
    
    contact_score: int = 0
    contact_details: Dict[str, bool] = field(default_factory=dict)
    
    location_score: int = 0
    location_found: List[str] = field(default_factory=list)
    
    # Recommendations
    is_high_priority: bool = False
    reasons: List[str] = field(default_factory=list)


def score_lead(
    text: str,
    has_phone: bool = False,
    has_mobile: bool = False,
    has_email: bool = False,
    has_whatsapp: bool = False,
    config: Optional[ScoringConfig] = None,
) -> LeadScore:
    """
    Calculate lead score based on sales context and signals.
    
    Args:
        text: Text content to analyze (title + description + body)
        has_phone: Whether a phone number was found
        has_mobile: Whether the phone is a mobile number
        has_email: Whether an email was found
        has_whatsapp: Whether WhatsApp contact was found
        config: Optional scoring configuration
        
    Returns:
        LeadScore object with detailed breakdown
        
    Example:
        >>> result = score_lead(
        ...     "Vertriebsmitarbeiter sucht neue Herausforderung in Köln, Tel: 0176...",
        ...     has_phone=True,
        ...     has_mobile=True
        ... )
        >>> result.classification
        'HIGH'
        >>> result.total_score
        12
    """
    if config is None:
        config = DEFAULT_SCORING_CONFIG
    
    result = LeadScore()
    text_lower = text.lower() if text else ""
    
    # ========================================
    # 1. Sales Keywords Score
    # ========================================
    keywords_points = 0
    keywords_found = []
    
    # Primary keywords
    for kw in SALES_KEYWORDS_PRIMARY:
        if kw in text_lower:
            keywords_points += config.sales_keyword_primary
            keywords_found.append(kw)
    
    # Secondary keywords
    for kw in SALES_KEYWORDS_SECONDARY:
        if kw in text_lower:
            keywords_points += config.sales_keyword_secondary
            keywords_found.append(kw)
    
    result.sales_keywords_score = min(keywords_points, config.sales_keyword_max)
    result.sales_keywords_found = keywords_found[:10]  # Limit to first 10
    
    # ========================================
    # 2. Industry Score
    # ========================================
    industry_points = 0
    industries_found = []
    
    for industry in HIGH_VALUE_INDUSTRIES:
        if industry in text_lower:
            industry_points += config.high_value_industry
            industries_found.append(industry)
    
    result.industry_score = min(industry_points, config.industry_max)
    result.industries_found = industries_found[:5]
    
    # ========================================
    # 3. Job-Seeking Signals Score
    # ========================================
    signals_points = 0
    signals_found = []
    
    # Strong signals
    for signal in JOB_SEEKING_SIGNALS_STRONG:
        if signal in text_lower:
            signals_points += config.job_signal_strong
            signals_found.append(f"[STRONG] {signal}")
    
    # Moderate signals
    for signal in JOB_SEEKING_SIGNALS_MODERATE:
        if signal in text_lower:
            signals_points += config.job_signal_moderate
            signals_found.append(f"[MOD] {signal}")
    
    result.job_signals_score = min(signals_points, config.job_signal_max)
    result.job_signals_found = signals_found[:8]
    
    # ========================================
    # 4. Contact Information Score
    # ========================================
    contact_points = 0
    contact_details = {
        "phone": has_phone,
        "mobile": has_mobile,
        "email": has_email,
        "whatsapp": has_whatsapp,
    }
    
    if has_phone:
        contact_points += config.phone_present
        result.reasons.append("Telefonnummer vorhanden")
        
        if has_mobile:
            contact_points += config.mobile_phone_bonus
            result.reasons.append("Mobilnummer (hohe Erreichbarkeit)")
    
    if has_email:
        contact_points += config.email_present
        result.reasons.append("E-Mail vorhanden")
    
    if has_whatsapp:
        contact_points += config.whatsapp_present
        result.reasons.append("WhatsApp-Kontakt (direkte Kommunikation)")
    
    result.contact_score = contact_points
    result.contact_details = contact_details
    
    # ========================================
    # 5. Location Score
    # ========================================
    location_points = 0
    location_found = []
    
    for indicator in NRW_INDICATORS:
        if indicator in text_lower:
            if location_points == 0:  # Only count once
                location_points = config.nrw_indicator
                result.reasons.append("NRW-Region erkannt")
            location_found.append(indicator)
    
    result.location_score = location_points
    result.location_found = location_found[:5]
    
    # ========================================
    # 6. Total Score & Classification
    # ========================================
    result.total_score = (
        result.sales_keywords_score +
        result.industry_score +
        result.job_signals_score +
        result.contact_score +
        result.location_score
    )
    
    # Classify the lead
    if result.total_score >= config.high_value_threshold:
        result.classification = "HIGH"
        result.is_high_priority = True
    elif result.total_score >= config.medium_threshold:
        result.classification = "MEDIUM"
    else:
        result.classification = "LOW"
    
    # Add classification reason
    if result.classification == "HIGH":
        result.reasons.insert(0, f"HIGH-VALUE LEAD (Score: {result.total_score})")
    elif result.classification == "MEDIUM":
        result.reasons.insert(0, f"MEDIUM LEAD (Score: {result.total_score})")
    else:
        result.reasons.insert(0, f"LOW LEAD (Score: {result.total_score})")
    
    return result


def is_sales_context(text: str) -> Tuple[bool, List[str]]:
    """
    Quick check if text contains sales/Vertrieb context.
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (is_sales_context: bool, keywords_found: List[str])
    """
    text_lower = text.lower() if text else ""
    found = []
    
    all_keywords = SALES_KEYWORDS_PRIMARY + SALES_KEYWORDS_SECONDARY
    for kw in all_keywords:
        if kw in text_lower:
            found.append(kw)
    
    return (len(found) > 0, found)


def is_job_seeker(text: str) -> Tuple[bool, List[str]]:
    """
    Quick check if text indicates a job seeker.
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (is_job_seeker: bool, signals_found: List[str])
    """
    text_lower = text.lower() if text else ""
    found = []
    
    all_signals = JOB_SEEKING_SIGNALS_STRONG + JOB_SEEKING_SIGNALS_MODERATE
    for signal in all_signals:
        if signal in text_lower:
            found.append(signal)
    
    return (len(found) > 0, found)


def is_nrw_region(text: str) -> Tuple[bool, List[str]]:
    """
    Quick check if text mentions NRW region.
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (is_nrw: bool, indicators_found: List[str])
    """
    text_lower = text.lower() if text else ""
    found = []
    
    for indicator in NRW_INDICATORS:
        if indicator in text_lower:
            found.append(indicator)
    
    return (len(found) > 0, found)


# ========================================
# EXPORTS
# ========================================

__all__ = [
    # Keyword lists
    "SALES_KEYWORDS_PRIMARY",
    "SALES_KEYWORDS_SECONDARY",
    "HIGH_VALUE_INDUSTRIES",
    "JOB_SEEKING_SIGNALS_STRONG",
    "JOB_SEEKING_SIGNALS_MODERATE",
    "NRW_INDICATORS",
    # Configuration
    "ScoringConfig",
    "DEFAULT_SCORING_CONFIG",
    # Data classes
    "LeadScore",
    # Main functions
    "score_lead",
    "is_sales_context",
    "is_job_seeker",
    "is_nrw_region",
]
