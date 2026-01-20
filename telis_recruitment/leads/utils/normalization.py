"""Normalization helpers for lead contact fields."""

from typing import Optional


def normalize_email(value: Optional[str]) -> Optional[str]:
    """Lower-case and trim emails for normalized comparison."""
    if not value:
        return None
    return value.strip().lower()


def normalize_phone(value: Optional[str]) -> Optional[str]:
    """Keep only digits when normalizing phone numbers."""
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or None
