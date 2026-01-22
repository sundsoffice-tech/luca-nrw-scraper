"""
LUCA NRW Scraper - Scoring Module
==================================
Lead scoring and validation functions.
Phase 3 der Modularisierung.
"""

from .validation import (
    # Pattern constants
    EMAIL_RE,
    PHONE_RE,
    MOBILE_RE,
    SALES_RE,
    PROVISION_HINT,
    D2D_HINT,
    CALLCENTER_HINT,
    B2C_HINT,
    JOBSEEKER_RE,
    CANDIDATE_TEXT_RE,
    EMPLOYER_TEXT_RE,
    RECRUITER_RE,
    WHATSAPP_RE,
    WA_LINK_RE,
    WHATS_RE,
    WHATSAPP_PHRASE_RE,
    TELEGRAM_LINK_RE,
    CITY_RE,
    NAME_RE,
    SALES_WINDOW,
    JOBSEEKER_WINDOW,
    
    # Signal lists
    CANDIDATE_POSITIVE_SIGNALS,
    JOB_OFFER_SIGNALS,
    STRICT_JOB_AD_MARKERS,
    MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE,
    CANDIDATE_KEYWORDS,
    IGNORE_KEYWORDS,
    JOB_AD_MARKERS,
    HIRING_INDICATORS,
    SOLO_BIZ_INDICATORS,
    AGENT_FINGERPRINTS,
    RETAIL_ROLES,
    
    # Validation functions
    is_candidate_seeking_job,
    is_job_advertisement,
    classify_lead,
    is_garbage_context,
    should_drop_lead,
    should_skip_url_prefetch,
)

from .enrichment import (
    # Enrichment functions
    get_cached_telefonbuch_result,
    cache_telefonbuch_result,
    query_dasoertliche,
    should_accept_enrichment,
    enrich_phone_from_telefonbuch,
    enrich_leads_with_telefonbuch,
)

from .quality import (
    # Scoring & Quality functions
    compute_score,
    etld1,
    _dedup_run,
    deduplicate_parallel_leads,
    detect_recency,
    is_commercial_agent,
)

# New modules for enhanced phone extraction and lead scoring
from .german_patterns import (
    # Phone patterns
    PHONE_PATTERNS_COMPILED,
    PHONE_LABELS,
    LABEL_PATTERN,
    GERMAN_MOBILE_PREFIXES,
    PHONE_BLACKLIST,
    # Normalization functions
    normalize_german_phone,
    validate_german_mobile,
    validate_german_landline,
    # Extraction functions
    extract_german_phones,
    extract_phone_with_label,
    is_blacklisted_phone,
)

from .sales_context import (
    # Keyword lists
    SALES_KEYWORDS_PRIMARY,
    SALES_KEYWORDS_SECONDARY,
    HIGH_VALUE_INDUSTRIES,
    JOB_SEEKING_SIGNALS_STRONG,
    JOB_SEEKING_SIGNALS_MODERATE,
    NRW_INDICATORS,
    # Configuration
    ScoringConfig,
    DEFAULT_SCORING_CONFIG,
    # Data classes
    LeadScore,
    # Functions
    score_lead,
    is_sales_context,
    is_job_seeker,
    is_nrw_region,
)

from .lead_rules import (
    # Enums
    LeadDecision,
    ExclusionReason,
    InclusionReason,
    # Pattern lists
    JOB_OFFER_PATTERNS,
    CANDIDATE_PATTERNS,
    HR_PATTERNS,
    GENERIC_CONTACT_PATTERNS,
    NEWS_PATTERNS,
    AGGREGATOR_DOMAINS,
    PRIVACY_PATTERNS,
    QUALITY_PORTAL_PATTERNS,
    # Configuration
    LeadRulesConfig,
    DEFAULT_RULES_CONFIG,
    # CSV definitions
    LeadCSVFields,
    CSV_HEADERS,
    # Result classes
    LeadDecisionResult,
    # Functions
    evaluate_lead_for_csv,
    build_csv_row,
    filter_leads_for_csv,
)

__all__ = [
    # Patterns
    "EMAIL_RE",
    "PHONE_RE",
    "MOBILE_RE",
    "SALES_RE",
    "PROVISION_HINT",
    "D2D_HINT",
    "CALLCENTER_HINT",
    "B2C_HINT",
    "JOBSEEKER_RE",
    "CANDIDATE_TEXT_RE",
    "EMPLOYER_TEXT_RE",
    "RECRUITER_RE",
    "WHATSAPP_RE",
    "WA_LINK_RE",
    "WHATS_RE",
    "WHATSAPP_PHRASE_RE",
    "TELEGRAM_LINK_RE",
    "CITY_RE",
    "NAME_RE",
    "SALES_WINDOW",
    "JOBSEEKER_WINDOW",
    
    # Signals
    "CANDIDATE_POSITIVE_SIGNALS",
    "JOB_OFFER_SIGNALS",
    "STRICT_JOB_AD_MARKERS",
    "MIN_JOB_OFFER_SIGNALS_TO_OVERRIDE",
    "CANDIDATE_KEYWORDS",
    "IGNORE_KEYWORDS",
    "JOB_AD_MARKERS",
    "HIRING_INDICATORS",
    "SOLO_BIZ_INDICATORS",
    "AGENT_FINGERPRINTS",
    "RETAIL_ROLES",
    
    # Validation Functions
    "is_candidate_seeking_job",
    "is_job_advertisement",
    "classify_lead",
    "is_garbage_context",
    "should_drop_lead",
    "should_skip_url_prefetch",
    
    # Enrichment Functions
    "get_cached_telefonbuch_result",
    "cache_telefonbuch_result",
    "query_dasoertliche",
    "should_accept_enrichment",
    "enrich_phone_from_telefonbuch",
    "enrich_leads_with_telefonbuch",
    
    # Scoring & Quality Functions
    "compute_score",
    "etld1",
    "_dedup_run",
    "deduplicate_parallel_leads",
    "detect_recency",
    "is_commercial_agent",
    
    # German Phone Patterns (new)
    "PHONE_PATTERNS_COMPILED",
    "PHONE_LABELS",
    "LABEL_PATTERN",
    "GERMAN_MOBILE_PREFIXES",
    "PHONE_BLACKLIST",
    "normalize_german_phone",
    "validate_german_mobile",
    "validate_german_landline",
    "extract_german_phones",
    "extract_phone_with_label",
    "is_blacklisted_phone",
    
    # Sales Context Detection (new)
    "SALES_KEYWORDS_PRIMARY",
    "SALES_KEYWORDS_SECONDARY",
    "HIGH_VALUE_INDUSTRIES",
    "JOB_SEEKING_SIGNALS_STRONG",
    "JOB_SEEKING_SIGNALS_MODERATE",
    "NRW_INDICATORS",
    "ScoringConfig",
    "DEFAULT_SCORING_CONFIG",
    "LeadScore",
    "score_lead",
    "is_sales_context",
    "is_job_seeker",
    "is_nrw_region",
    
    # Lead CSV Rules (new)
    "LeadDecision",
    "ExclusionReason",
    "InclusionReason",
    "JOB_OFFER_PATTERNS",
    "CANDIDATE_PATTERNS",
    "HR_PATTERNS",
    "GENERIC_CONTACT_PATTERNS",
    "NEWS_PATTERNS",
    "AGGREGATOR_DOMAINS",
    "PRIVACY_PATTERNS",
    "QUALITY_PORTAL_PATTERNS",
    "LeadRulesConfig",
    "DEFAULT_RULES_CONFIG",
    "LeadCSVFields",
    "CSV_HEADERS",
    "LeadDecisionResult",
    "evaluate_lead_for_csv",
    "build_csv_row",
    "filter_leads_for_csv",
]
