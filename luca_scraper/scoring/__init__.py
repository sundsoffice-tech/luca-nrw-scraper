# -*- coding: utf-8 -*-
"""
Scoring Module

This module provides lead scoring and validation functionality.
It includes functions for:
- Computing lead quality scores based on various signals
- Validating leads against quality criteria
- Detecting job advertisements vs. candidate profiles
- Analyzing context and extracting metadata
"""

# Lead scoring functions
from luca_scraper.scoring.lead_scorer import (
    compute_score,
    detect_company_size,
    detect_industry,
    detect_recency,
    estimate_hiring_volume,
    detect_hidden_gem,
    analyze_wir_suchen_context,
    tags_from,
    is_commercial_agent,
)

# Validation functions
from luca_scraper.scoring.validation import (
    should_drop_lead,
    is_job_advertisement,
    is_candidate_seeking_job,
    has_nrw_signal,
    email_quality,
    is_likely_human_name,
    same_org_domain,
)

__all__ = [
    # Scoring functions
    "compute_score",
    "detect_company_size",
    "detect_industry",
    "detect_recency",
    "estimate_hiring_volume",
    "detect_hidden_gem",
    "analyze_wir_suchen_context",
    "tags_from",
    "is_commercial_agent",
    # Validation functions
    "should_drop_lead",
    "is_job_advertisement",
    "is_candidate_seeking_job",
    "has_nrw_signal",
    "email_quality",
    "is_likely_human_name",
    "same_org_domain",
]
