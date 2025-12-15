from __future__ import annotations


def should_use_fallbacks(link_count: int, had_429: bool) -> bool:
    """
    Decides if alternative search providers should be used.

    We trigger fallbacks when Google signaled rate limiting (had_429)
    or when we have too few links from the primary search.
    """
    return had_429 or link_count < 3


__all__ = ["should_use_fallbacks"]
