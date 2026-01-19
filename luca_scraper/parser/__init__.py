"""Parser module for extracting and validating contact information, names, and context."""

from .contacts import (
    email_quality,
    is_employer_email,
    same_org_domain,
    deobfuscate_text_for_emails,
)

from .names import (
    is_likely_human_name,
    looks_like_company,
    _validate_name_heuristic,
    _looks_like_company_name,
)

from .context import (
    analyze_wir_suchen_context,
    detect_hidden_gem,
    is_candidate_seeking_job,
)

__all__ = [
    # Contact parsing
    "email_quality",
    "is_employer_email",
    "same_org_domain",
    "deobfuscate_text_for_emails",
    
    # Name validation
    "is_likely_human_name",
    "looks_like_company",
    "_validate_name_heuristic",
    "_looks_like_company_name",
    
    # Context analysis
    "analyze_wir_suchen_context",
    "detect_hidden_gem",
    "is_candidate_seeking_job",
]
