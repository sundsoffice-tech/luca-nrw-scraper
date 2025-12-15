from fallbacks import should_use_fallbacks


def test_fallback_triggers_on_429_even_with_results():
    assert should_use_fallbacks(link_count=10, had_429=True) is True


def test_fallback_triggers_when_results_are_sparse():
    assert should_use_fallbacks(link_count=2, had_429=False) is True


def test_fallback_skips_when_results_are_sufficient_and_no_429():
    assert should_use_fallbacks(link_count=5, had_429=False) is False
