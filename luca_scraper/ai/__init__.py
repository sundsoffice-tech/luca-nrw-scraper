"""
AI Integration Module for LUCA NRW Scraper
===========================================

This module provides AI-powered functionality for:
- Contact extraction (OpenAI)
- Content analysis and scoring
- Name validation
- Smart search query generation (Perplexity)
- Dynamic query expansion with Query Fan-Out (DynamicQueryGenerator)

All functions handle missing API keys gracefully.
"""

from .openai_integration import (
    openai_extract_contacts,
    validate_real_name_with_ai,
    analyze_content_async,
    extract_contacts_with_ai,
)

from .perplexity import (
    search_perplexity_async,
    generate_smart_dorks,
)

from .query_generator import (
    DynamicQueryGenerator,
)

__all__ = [
    "openai_extract_contacts",
    "validate_real_name_with_ai",
    "analyze_content_async",
    "extract_contacts_with_ai",
    "search_perplexity_async",
    "generate_smart_dorks",
    "DynamicQueryGenerator",
]
