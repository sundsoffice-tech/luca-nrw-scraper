import os
from stream3_scoring_layer.scoring_enhanced import (
    compute_score_v2,
    apply_dynamic_threshold,
    score_and_filter_leads,
)
from stream3_scoring_layer.quality_metrics import track_quality_metrics


def test_compute_score_v2_good_vs_bad():
    base_good_lead = {
        "name": "Max Mustermann",
        "rolle": "Vertriebsleiter",
        "email": "max@agentur-nrw.de",
        "telefon": "+491711234567",
        "phone_type": "mobile",
        "whatsapp_link": "yes",
        "industry": "versicherung",
        "region": "NRW",
        "tags": "nrw,whatsapp,vertrieb",
        "recency_indicator": "aktuell",
    }
    good_lead = {
        **base_good_lead,
        "private_address": "Musterstr. 1, 12345 Köln",
        "social_profile_url": "https://www.linkedin.com/in/testperson",
    }
    without_bonus = {
        **base_good_lead,
        "private_address": "",
        "social_profile_url": "",
    }
    score_good = compute_score_v2("", "https://example.com/kontakt", good_lead)
    score_without_bonus = compute_score_v2("", "https://example.com/kontakt", without_bonus)
    assert score_good >= 80
    assert score_good >= score_without_bonus

    bonus_probe = {
        "name": "Julia",
        "rolle": "Sales",
        "email": "julia@gmail.com",
        "telefon": "",
        "industry": "",
        "region": "",
        "private_address": "Bahnhofstr. 12, 50667 Köln",
        "social_profile_url": "https://www.linkedin.com/in/julia-probe",
    }
    bonus_probe_without = {**bonus_probe, "private_address": "", "social_profile_url": ""}
    assert compute_score_v2("", "https://example.com", bonus_probe) - compute_score_v2("", "https://example.com", bonus_probe_without) >= 30

    bad_lead = {
        "name": "Foo",
        "email": "",
        "telefon": "",
        "industry": "",
        "region": "",
    }
    score_bad = compute_score_v2("", "https://example.com/datenschutz", bad_lead)
    assert score_bad < score_good
    assert 0 <= score_bad <= 100


def test_apply_dynamic_threshold_removes_bottom_quartile():
    leads = [{"score": s} for s in [10, 20, 30, 40, 50, 60, 70, 80]]

    filtered, info = apply_dynamic_threshold(leads, percentile=0.25)

    assert info["threshold"] >= 10
    assert len(filtered) < len(leads)
    assert all(int(l.get("score", 0)) >= info["threshold"] for l in filtered)


def test_track_quality_metrics_basic():
    leads = [
        {"score": 80, "confidence_score": 90, "email": "a@example.com", "telefon": "+491234", "name": "A"},
        {"score": 60, "confidence_score": 70, "email": "", "telefon": "", "name": ""},
    ]

    stats = track_quality_metrics(leads, run_id=1, metrics_file="metrics_test.csv", write_csv=False)

    assert stats["total_leads"] == 2
    assert stats["leads_with_email"] == 1
    assert stats["avg_score"] >= 60
    assert "avg_confidence" in stats


def test_score_and_filter_leads_pipeline():
    leads = [
        {
            "name": "Max",
            "rolle": "Vertrieb",
            "email": "max@firma.de",
            "telefon": "+491711234567",
            "phone_type": "mobile",
            "whatsapp_link": "yes",
            "industry": "versicherung",
            "region": "NRW",
            "tags": "nrw,whatsapp,vertrieb",
            "recency_indicator": "aktuell",
        },
        {
            "name": "NoContact",
            "email": "",
            "telefon": "",
            "industry": "",
            "region": "",
        },
    ]

    filtered, summary = score_and_filter_leads(leads, run_id=123, base_min_score=0, verbose=False)

    assert isinstance(summary.threshold, int)
    assert summary.start == len(leads)
    assert summary.end == len(filtered)
    assert all(0 <= l.get("score", 0) <= 100 for l in filtered)
    assert len(filtered) >= 1
