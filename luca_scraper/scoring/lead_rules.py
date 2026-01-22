# -*- coding: utf-8 -*-
"""
Lead Inclusion/Exclusion Rules & CSV Export Module
=================================================

This module provides clear rules for deciding which leads to include in CSV export:

Aufgabe 3 - Entscheidung, was in die CSV kommt:
- Clear inclusion rules (when to ALWAYS save a lead)
- Clear exclusion rules (when to NEVER save a lead)  
- Standardized CSV fields for lead export

Inclusion Rules (Lead ALWAYS saved):
===================================
1. Score >= 8 (HIGH-VALUE classification)
2. Has phone number AND (sales keyword OR job-seeking signal)
3. Has WhatsApp contact
4. Matches "Vertrieb + Handy + NRW" pattern
5. From known high-quality portal (Kleinanzeigen Stellengesuch, etc.)

Exclusion Rules (Lead NEVER saved):
==================================
1. Pure job offer without candidate signals (only "Wir suchen", no "Ich suche")
2. HR/Recruiting pages (only hiring, not seeking)
3. Generic company contact pages (no individual contact)
4. News articles, blog posts, aggregator content
5. Duplicate of existing lead (same phone or email)
6. Blacklisted phone number (service numbers, fake patterns)
7. Score < 2 (clearly irrelevant)

CSV Fields:
==========
Required: Name, Rolle/Kontext, Quelle-URL, Telefon, E-Mail, Region, Score, Lead-Typ
Optional: Firma, Branche, Verfügbarkeit, WhatsApp, Confidence, Tags
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum


# ========================================
# LEAD DECISION ENUMS
# ========================================

class LeadDecision(Enum):
    """Decision on whether to include lead in CSV."""
    INCLUDE = "INCLUDE"           # Always include
    EXCLUDE = "EXCLUDE"           # Always exclude
    REVIEW = "REVIEW"             # Needs manual review (borderline)


class ExclusionReason(Enum):
    """Reason why a lead was excluded."""
    JOB_OFFER_ONLY = "job_offer_only"           # Company hiring, not candidate
    HR_RECRUITING_PAGE = "hr_recruiting_page"    # HR department page
    GENERIC_CONTACT = "generic_contact"          # Generic company contact
    NEWS_ARTICLE = "news_article"                # News/blog content
    DUPLICATE = "duplicate"                       # Duplicate lead
    BLACKLISTED_PHONE = "blacklisted_phone"      # Service/fake number
    LOW_SCORE = "low_score"                       # Score too low
    NO_CONTACT_INFO = "no_contact_info"          # No phone or email
    PRIVACY_PAGE = "privacy_page"                # Datenschutz/AGB page
    AGGREGATOR = "aggregator"                     # Job aggregator site


class InclusionReason(Enum):
    """Reason why a lead was included."""
    HIGH_VALUE_SCORE = "high_value_score"        # Score >= threshold
    PHONE_WITH_SIGNAL = "phone_with_signal"      # Phone + sales/job signal
    WHATSAPP_CONTACT = "whatsapp_contact"        # Has WhatsApp
    SALES_MOBILE_NRW = "sales_mobile_nrw"        # Vertrieb + Handy + NRW
    QUALITY_PORTAL = "quality_portal"            # From trusted portal
    CANDIDATE_SIGNALS = "candidate_signals"      # Strong job-seeker signals


# ========================================
# EXCLUSION PATTERNS
# ========================================

# Job offer patterns (company hiring, NOT candidate seeking)
JOB_OFFER_PATTERNS: List[str] = [
    "wir suchen",
    "wir stellen ein",
    "gesucht:",
    "suchen wir",
    "(m/w/d)",
    "(w/m/d)",
    "(d/m/w)",
    "(m/f/d)",
    "ab sofort zu besetzen",
    "verstärkung gesucht",
    "team sucht",
    "für unser team",
    "stellenangebot",
    "job zu vergeben",
    "mitarbeiter gesucht",
    "mitarbeiterin gesucht",
    "deine aufgaben",
    "ihre aufgaben",
    "wir bieten",
    "das bieten wir",
    "benefits:",
    "corporate benefits",
    "join our team",
    "we are hiring",
]

# Candidate signals (person seeking job, NOT company hiring)
CANDIDATE_PATTERNS: List[str] = [
    "ich suche",
    "suche job",
    "suche arbeit",
    "suche stelle",
    "stellengesuch",
    "biete mich an",
    "bin auf der suche",
    "auf jobsuche",
    "arbeitslos",
    "arbeitssuchend",
    "gekündigt",
    "freigestellt",
    "wechselwillig",
    "open to work",
    "#opentowork",
    "verfügbar ab",
    "ab sofort verfügbar",
    "neue herausforderung",
    "quereinstieg",
]

# HR/Recruiting page patterns
HR_PATTERNS: List[str] = [
    "personalabteilung",
    "personalreferent",
    "human resources",
    "hr manager",
    "hr-manager",
    "recruiting team",
    "karriere bei uns",
    "karriereseite",
    "bewerbungen richten sie an",
    "jetzt bewerben",
    "online bewerben",
    "bewerbungsformular",
    "ihre bewerbung an",
    "bewerben sie sich jetzt",
]

# Generic contact patterns (not personal contact)
GENERIC_CONTACT_PATTERNS: List[str] = [
    "impressum",
    "kontakt aufnehmen",
    "kontaktieren sie uns",
    "schreiben sie uns",
    "rufen sie uns an",
    "unser team erreichen sie",
    "servicenummer",
    "kundenservice",
    "support@",
    "info@",
    "kontakt@",
    "office@",
    "zentrale",
    "empfang",
    "sekretariat",
]

# News/Blog patterns
NEWS_PATTERNS: List[str] = [
    "/news/",
    "/blog/",
    "/artikel/",
    "/article/",
    "/pressemitteilung/",
    "/press-release/",
    "/aktuelles/",
    "/magazin/",
    "veröffentlicht am",
    "published on",
    "autor:",
    "by admin",
    "pressekontakt",
]

# Aggregator domains to exclude
AGGREGATOR_DOMAINS: List[str] = [
    "stepstone.de",
    "indeed.com",
    "indeed.de",
    "monster.de",
    "monster.com",
    "glassdoor.de",
    "glassdoor.com",
    "linkedin.com/jobs",
    "xing.com/jobs",
    "jobware.de",
    "jobboerse.de",
    "meinestadt.de/jobs",
    "arbeitsagentur.de",
    "jobbörse",
    "jobboerse",
]

# Privacy/Legal pages (never relevant for leads)
PRIVACY_PATTERNS: List[str] = [
    "/datenschutz",
    "/privacy",
    "/agb",
    "/terms",
    "/impressum",
    "/legal",
    "/rechtliches",
]

# High-quality portal patterns (candidate listings)
QUALITY_PORTAL_PATTERNS: List[str] = [
    "kleinanzeigen.de/s-stellengesuche",
    "kleinanzeigen.de/s-anzeige",
    "quoka.de/stellengesuche",
    "markt.de/stellengesuche",
    "kalaydo.de/stellengesuche",
]


# ========================================
# DECISION CONFIGURATION
# ========================================

@dataclass
class LeadRulesConfig:
    """Configuration for lead inclusion/exclusion rules."""
    
    # Score thresholds
    high_value_threshold: int = 8       # Automatic include if score >= this
    low_score_threshold: int = 2        # Automatic exclude if score < this
    review_threshold: int = 4           # Below this, needs review
    
    # Required signals for borderline leads
    min_candidate_signals: int = 1      # Min candidate signals to include
    min_job_offer_override: int = 2     # Job offers needed to override candidate
    
    # Contact requirements
    require_phone_for_include: bool = True  # Must have phone to include
    require_phone_or_email: bool = True     # Must have phone OR email


# Default configuration
DEFAULT_RULES_CONFIG = LeadRulesConfig()


# ========================================
# CSV FIELD DEFINITIONS
# ========================================

@dataclass
class LeadCSVFields:
    """Standard CSV fields for lead export."""
    
    # Required fields
    name: str = ""                      # Contact person name
    rolle: str = ""                     # Role/context (Vertrieb, etc.)
    quelle: str = ""                    # Source URL
    telefon: str = ""                   # Phone number (normalized +49)
    email: str = ""                     # Email address
    region: str = ""                    # Region (NRW city/area)
    score: int = 0                      # Lead score (0-100 or points)
    lead_type: str = ""                 # Type: candidate, prospect, etc.
    
    # Optional fields
    firma: str = ""                     # Company (if known)
    branche: str = ""                   # Industry
    verfuegbarkeit: str = ""            # Availability (ab sofort, etc.)
    whatsapp: str = ""                  # WhatsApp link/number
    confidence: float = 0.0             # Confidence score (0-1)
    tags: str = ""                      # Comma-separated tags
    classification: str = ""            # HIGH, MEDIUM, LOW
    phone_type: str = ""                # mobile, landline
    extraction_date: str = ""           # When extracted
    
    # Metadata
    inclusion_reason: str = ""          # Why included
    sales_keywords: str = ""            # Found sales keywords
    job_signals: str = ""               # Found job-seeking signals


# CSV header order
CSV_HEADERS: List[str] = [
    "name",
    "rolle",
    "quelle",
    "telefon",
    "email",
    "region",
    "score",
    "lead_type",
    "classification",
    "firma",
    "branche",
    "verfuegbarkeit",
    "whatsapp",
    "phone_type",
    "confidence",
    "tags",
    "inclusion_reason",
    "sales_keywords",
    "job_signals",
    "extraction_date",
]


# ========================================
# DECISION FUNCTIONS
# ========================================

@dataclass
class LeadDecisionResult:
    """Result of lead inclusion/exclusion decision."""
    
    decision: LeadDecision = LeadDecision.EXCLUDE
    reason: str = ""
    reason_code: Optional[str] = None
    score: int = 0
    
    # Details for debugging
    candidate_signals_found: List[str] = field(default_factory=list)
    job_offer_signals_found: List[str] = field(default_factory=list)
    exclusion_patterns_found: List[str] = field(default_factory=list)
    
    # Should this go to CSV?
    include_in_csv: bool = False


def evaluate_lead_for_csv(
    text: str,
    url: str,
    score: int,
    has_phone: bool = False,
    has_mobile: bool = False,
    has_email: bool = False,
    has_whatsapp: bool = False,
    is_nrw: bool = False,
    config: Optional[LeadRulesConfig] = None,
) -> LeadDecisionResult:
    """
    Evaluate whether a lead should be included in CSV export.
    
    Decision Logic:
    1. Check for automatic EXCLUSION patterns
    2. Check for automatic INCLUSION patterns  
    3. Apply score-based rules
    4. Return REVIEW for borderline cases
    
    Args:
        text: Lead text content
        url: Source URL
        score: Lead score
        has_phone: Whether phone was found
        has_mobile: Whether it's a mobile number
        has_email: Whether email was found
        has_whatsapp: Whether WhatsApp was found
        is_nrw: Whether NRW region was detected
        config: Rules configuration
        
    Returns:
        LeadDecisionResult with decision and reasoning
    """
    if config is None:
        config = DEFAULT_RULES_CONFIG
    
    result = LeadDecisionResult(score=score)
    text_lower = (text or "").lower()
    url_lower = (url or "").lower()
    
    # ========================================
    # 1. CHECK AUTOMATIC EXCLUSIONS
    # ========================================
    
    # Check for privacy/legal pages
    for pattern in PRIVACY_PATTERNS:
        if pattern in url_lower:
            result.decision = LeadDecision.EXCLUDE
            result.reason = f"Privacy/legal page: {pattern}"
            result.reason_code = ExclusionReason.PRIVACY_PAGE.value
            result.exclusion_patterns_found.append(pattern)
            return result
    
    # Check for aggregator domains
    for domain in AGGREGATOR_DOMAINS:
        if domain in url_lower:
            result.decision = LeadDecision.EXCLUDE
            result.reason = f"Job aggregator site: {domain}"
            result.reason_code = ExclusionReason.AGGREGATOR.value
            result.exclusion_patterns_found.append(domain)
            return result
    
    # Check for news/blog content
    for pattern in NEWS_PATTERNS:
        if pattern in text_lower or pattern in url_lower:
            result.decision = LeadDecision.EXCLUDE
            result.reason = f"News/blog content: {pattern}"
            result.reason_code = ExclusionReason.NEWS_ARTICLE.value
            result.exclusion_patterns_found.append(pattern)
            return result
    
    # Check for low score
    if score < config.low_score_threshold:
        result.decision = LeadDecision.EXCLUDE
        result.reason = f"Score too low: {score} < {config.low_score_threshold}"
        result.reason_code = ExclusionReason.LOW_SCORE.value
        return result
    
    # Check for no contact info
    if config.require_phone_or_email and not has_phone and not has_email:
        result.decision = LeadDecision.EXCLUDE
        result.reason = "No contact information (phone or email)"
        result.reason_code = ExclusionReason.NO_CONTACT_INFO.value
        return result
    
    # ========================================
    # 2. DETECT SIGNALS
    # ========================================
    
    # Find candidate signals
    for pattern in CANDIDATE_PATTERNS:
        if pattern in text_lower:
            result.candidate_signals_found.append(pattern)
    
    # Find job offer signals
    for pattern in JOB_OFFER_PATTERNS:
        if pattern in text_lower:
            result.job_offer_signals_found.append(pattern)
    
    # ========================================
    # 3. JOB OFFER VS CANDIDATE LOGIC
    # ========================================
    
    has_candidate_signal = len(result.candidate_signals_found) >= config.min_candidate_signals
    has_job_offer_signal = len(result.job_offer_signals_found) > 0
    job_offer_override = len(result.job_offer_signals_found) >= config.min_job_offer_override
    
    # Pure job offer (company hiring, no candidate signals)
    if has_job_offer_signal and not has_candidate_signal:
        # Check for HR patterns
        is_hr_page = any(pattern in text_lower for pattern in HR_PATTERNS)
        
        if is_hr_page or job_offer_override:
            result.decision = LeadDecision.EXCLUDE
            result.reason = "Job offer page (company hiring, not candidate seeking)"
            result.reason_code = ExclusionReason.JOB_OFFER_ONLY.value
            return result
    
    # Check for generic contact page
    generic_contact_count = sum(1 for p in GENERIC_CONTACT_PATTERNS if p in text_lower)
    if generic_contact_count >= 2 and not has_candidate_signal:
        result.decision = LeadDecision.EXCLUDE
        result.reason = "Generic company contact page"
        result.reason_code = ExclusionReason.GENERIC_CONTACT.value
        return result
    
    # ========================================
    # 4. CHECK AUTOMATIC INCLUSIONS
    # ========================================
    
    # High score = automatic include
    if score >= config.high_value_threshold:
        result.decision = LeadDecision.INCLUDE
        result.reason = f"High-value score: {score}"
        result.reason_code = InclusionReason.HIGH_VALUE_SCORE.value
        result.include_in_csv = True
        return result
    
    # WhatsApp contact = automatic include
    if has_whatsapp:
        result.decision = LeadDecision.INCLUDE
        result.reason = "WhatsApp contact found"
        result.reason_code = InclusionReason.WHATSAPP_CONTACT.value
        result.include_in_csv = True
        return result
    
    # Vertrieb + Handy + NRW = high priority include
    is_sales = any(kw in text_lower for kw in ["vertrieb", "sales", "außendienst", "verkauf"])
    if is_sales and has_mobile and is_nrw:
        result.decision = LeadDecision.INCLUDE
        result.reason = "Sales + Mobile + NRW pattern"
        result.reason_code = InclusionReason.SALES_MOBILE_NRW.value
        result.include_in_csv = True
        return result
    
    # Quality portal source
    for portal in QUALITY_PORTAL_PATTERNS:
        if portal in url_lower:
            result.decision = LeadDecision.INCLUDE
            result.reason = f"Quality portal: {portal}"
            result.reason_code = InclusionReason.QUALITY_PORTAL.value
            result.include_in_csv = True
            return result
    
    # Phone + candidate signal = include
    if has_phone and has_candidate_signal:
        result.decision = LeadDecision.INCLUDE
        result.reason = "Phone number with job-seeking signal"
        result.reason_code = InclusionReason.PHONE_WITH_SIGNAL.value
        result.include_in_csv = True
        return result
    
    # Phone + sales context = include
    if has_phone and is_sales:
        result.decision = LeadDecision.INCLUDE
        result.reason = "Phone number with sales context"
        result.reason_code = InclusionReason.PHONE_WITH_SIGNAL.value
        result.include_in_csv = True
        return result
    
    # ========================================
    # 5. BORDERLINE CASES -> REVIEW
    # ========================================
    
    if score >= config.review_threshold:
        if has_phone or has_email:
            result.decision = LeadDecision.REVIEW
            result.reason = f"Borderline case: score {score}, has contact info"
            result.include_in_csv = True  # Include but mark for review
            return result
    
    # Default: exclude
    result.decision = LeadDecision.EXCLUDE
    result.reason = f"Does not meet inclusion criteria (score: {score})"
    result.reason_code = ExclusionReason.LOW_SCORE.value
    return result


def build_csv_row(
    lead_data: Dict[str, Any],
    decision_result: LeadDecisionResult,
) -> Dict[str, Any]:
    """
    Build a CSV row dictionary from lead data.
    
    Args:
        lead_data: Raw lead data dictionary
        decision_result: Result from evaluate_lead_for_csv
        
    Returns:
        Dictionary with standardized CSV fields
    """
    row = {}
    
    # Map standard fields
    row["name"] = lead_data.get("name", "")
    row["rolle"] = lead_data.get("rolle", lead_data.get("role", ""))
    row["quelle"] = lead_data.get("quelle", lead_data.get("url", ""))
    row["telefon"] = lead_data.get("telefon", lead_data.get("phone", ""))
    row["email"] = lead_data.get("email", "")
    row["region"] = lead_data.get("region", lead_data.get("location", ""))
    row["score"] = decision_result.score
    row["lead_type"] = lead_data.get("lead_type", "candidate")
    
    # Optional fields
    row["classification"] = lead_data.get("classification", "")
    row["firma"] = lead_data.get("firma", lead_data.get("company", ""))
    row["branche"] = lead_data.get("branche", lead_data.get("industry", ""))
    row["verfuegbarkeit"] = lead_data.get("verfuegbarkeit", lead_data.get("availability", ""))
    row["whatsapp"] = lead_data.get("whatsapp", lead_data.get("whatsapp_link", ""))
    row["phone_type"] = lead_data.get("phone_type", "")
    row["confidence"] = lead_data.get("confidence", lead_data.get("confidence_score", 0.0))
    row["tags"] = lead_data.get("tags", "")
    
    # Decision metadata
    row["inclusion_reason"] = decision_result.reason_code or decision_result.reason
    row["sales_keywords"] = ""  # Would be populated by sales_context module
    row["job_signals"] = ", ".join(decision_result.candidate_signals_found[:5])
    row["extraction_date"] = lead_data.get("extraction_date", lead_data.get("last_updated", ""))
    
    return row


def filter_leads_for_csv(
    leads: List[Dict[str, Any]],
    config: Optional[LeadRulesConfig] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Filter a list of leads for CSV export.
    
    Args:
        leads: List of lead dictionaries
        config: Rules configuration
        
    Returns:
        Tuple of:
        - included_leads: Leads to include in CSV
        - excluded_leads: Leads that were excluded
        - stats: Statistics about the filtering
    """
    if config is None:
        config = DEFAULT_RULES_CONFIG
    
    included = []
    excluded = []
    stats = {
        "total": len(leads),
        "included": 0,
        "excluded": 0,
        "reviewed": 0,
    }
    
    # Track exclusion reasons
    exclusion_reasons: Dict[str, int] = {}
    
    for lead in leads:
        text = lead.get("text", lead.get("fulltext", ""))
        url = lead.get("quelle", lead.get("url", ""))
        score = lead.get("score", 0)
        
        result = evaluate_lead_for_csv(
            text=text,
            url=url,
            score=score,
            has_phone=bool(lead.get("telefon", lead.get("phone"))),
            has_mobile=lead.get("phone_type") == "mobile",
            has_email=bool(lead.get("email")),
            has_whatsapp=bool(lead.get("whatsapp", lead.get("whatsapp_link"))),
            is_nrw=bool(lead.get("region", "").lower() in ["nrw", "nordrhein-westfalen"]),
            config=config,
        )
        
        if result.include_in_csv:
            included.append(build_csv_row(lead, result))
            stats["included"] += 1
            if result.decision == LeadDecision.REVIEW:
                stats["reviewed"] += 1
        else:
            excluded.append(lead)
            stats["excluded"] += 1
            reason = result.reason_code or "unknown"
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
    
    stats["exclusion_reasons"] = exclusion_reasons
    
    return included, excluded, stats


# ========================================
# EXPORTS
# ========================================

__all__ = [
    # Enums
    "LeadDecision",
    "ExclusionReason",
    "InclusionReason",
    # Pattern lists
    "JOB_OFFER_PATTERNS",
    "CANDIDATE_PATTERNS",
    "HR_PATTERNS",
    "GENERIC_CONTACT_PATTERNS",
    "NEWS_PATTERNS",
    "AGGREGATOR_DOMAINS",
    "PRIVACY_PATTERNS",
    "QUALITY_PORTAL_PATTERNS",
    # Configuration
    "LeadRulesConfig",
    "DEFAULT_RULES_CONFIG",
    # CSV definitions
    "LeadCSVFields",
    "CSV_HEADERS",
    # Result classes
    "LeadDecisionResult",
    # Functions
    "evaluate_lead_for_csv",
    "build_csv_row",
    "filter_leads_for_csv",
]
