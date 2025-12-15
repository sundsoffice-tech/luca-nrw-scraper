import pytest

import scriptname
from stream3_scoring_layer import scoring_enhanced as se


@pytest.fixture(autouse=True)
def reset_pdf_flag(monkeypatch):
    monkeypatch.setattr(scriptname, "ALLOW_PDF_NON_CV", False)


def test_drop_without_phone():
    lead = {"email": "someone@example.com", "telefon": ""}

    drop, reason = scriptname.should_drop_lead(lead, "https://example.com/profile", "Kontakt per E-Mail")

    assert drop is True
    assert reason == "no_phone"


def test_drop_on_portal_email_domain():
    lead = {"email": "person@stepstone.de", "telefon": "+49 123"}

    drop, reason = scriptname.should_drop_lead(lead, "https://example.com/profile", "profile text")

    assert drop is True
    assert reason == "portal_domain"


def test_pdf_dropped_without_cv_hint(monkeypatch):
    monkeypatch.setattr(scriptname, "ALLOW_PDF_NON_CV", False)
    lead = {"email": "user@example.com", "telefon": "+49 123"}

    drop, reason = scriptname.should_drop_lead(lead, "https://example.com/brochure.pdf", "Produktuebersicht")

    assert drop is True
    assert reason == "pdf_without_cv_hint"


def test_pdf_kept_with_cv_hint(monkeypatch):
    monkeypatch.setattr(scriptname, "ALLOW_PDF_NON_CV", False)
    lead = {"email": "user@example.com", "telefon": "+49 123"}

    drop, reason = scriptname.should_drop_lead(lead, "https://example.com/cv.pdf", "Lebenslauf Sales")

    assert drop is False
    assert reason == ""


def test_scoring_email_ordering():
    text = "Sales profile"
    url = "https://example.com/profile"
    base_lead = {"telefon": "+49 123"}

    corp = dict(base_lead, email="alice@company.com")
    free = dict(base_lead, email="bob@gmail.com")
    generic = dict(base_lead, email="info@company.com")
    portal = dict(base_lead, email="carol@stepstone.de")

    score_corp = se.compute_score_v2(text, url, corp)
    score_free = se.compute_score_v2(text, url, free)
    score_generic = se.compute_score_v2(text, url, generic)
    score_portal = se.compute_score_v2(text, url, portal)

    assert score_corp > score_free > score_generic > score_portal


def test_dynamic_threshold_median_and_removed_reason(monkeypatch):
    scores = [10, 20, 30, 40, 50]

    def fake_compute(text, url, lead):
        return scores.pop(0)

    monkeypatch.setattr(se, "compute_score_v2", fake_compute)
    leads = [{"quelle": f"https://example.com/{i}", "telefon": "+49 123"} for i in range(5)]

    filtered, summary = se.score_and_filter_leads(leads, run_id=0, base_min_score=0, verbose=False)

    assert summary.threshold == 30
    assert summary.meta.get("removed_reason") == "below_dynamic"
    assert [l["score"] for l in filtered] == [30, 40, 50]
