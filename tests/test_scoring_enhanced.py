import pytest

from stream3_scoring_layer import scoring_enhanced as se


def test_portal_mail_scores_lower_than_corporate():
    text = "Sales profile with phone"
    url = "https://example.com/profile"
    corp = {"email": "person@corp.com", "telefon": "+4912345"}
    portal = {"email": "user@stepstone.de", "telefon": "+4912345"}

    corp_score = se.compute_score_v2(text, url, corp)
    portal_score = se.compute_score_v2(text, url, portal)

    assert portal_score < corp_score


def test_small_sample_uses_median_threshold():
    leads = [{"score": s} for s in [10, 20, 30, 40, 50]]

    filtered, info = se.apply_dynamic_threshold(leads)

    assert info["threshold"] == 30
    assert len(filtered) == 3  # 30, 40, 50


def test_removed_reason_set_when_dynamic_filter_applies(monkeypatch):
    scores = iter([10, 20, 90])

    monkeypatch.setattr(se, "compute_score_v2", lambda *args, **kwargs: next(scores))

    leads = [{"fulltext": "", "quelle": ""} for _ in range(3)]
    filtered, summary = se.score_and_filter_leads(leads, run_id=1, base_min_score=0)

    assert len(filtered) == 2
    assert summary.meta.get("removed_reason") == "below_dynamic"
