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
    # NEU: always_crawl Support
    _is_always_crawl_url,
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
    # NEU: always_crawl Support
    "_is_always_crawl_url",
    
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
]
