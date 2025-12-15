from __future__ import annotations

import statistics
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .quality_metrics import track_quality_metrics

Lead = Dict[str, Any]
ScoreConfig = Dict[str, int]

DEFAULT_SCORE_CONFIG: ScoreConfig = {
    "email_bonus": 30,
    "corporate_email_bonus": 10,
    "phone_bonus": 20,
    "mobile_bonus": 10,
    "whatsapp_bonus": 15,
    "private_address_bonus": 15,
    "social_profile_bonus": 15,
    "sales_keywords_bonus": 35,
    "jobseeker_bonus": 15,
    "industry_bonus": 20,
    "nrw_bonus": 10,
    "fresh_bonus": 10,
}

FREE_MAILS = {"gmail.com", "outlook.com", "hotmail.com", "gmx.de", "web.de", "yahoo.com"}
GENERIC_MAILBOXES = {
    "info",
    "kontakt",
    "contact",
    "support",
    "service",
    "privacy",
    "datenschutz",
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "jobs",
    "karriere",
    "sales",
}
PORTAL_DOMAINS = {
    "stepstone.de",
    "indeed.com",
    "heyjobs.de",
    "heyjobs.co",
    "softgarden.io",
    "jobijoba.de",
    "jobijoba.com",
    "jobware.de",
    "monster.de",
    "kununu.com",
    "ok.ru",
    "tiktok.com",
    "patents.google.com",
    "linkedin.com",
    "xing.com",
}


@dataclass
class ScoreSummary:
    start: int = 0
    eligible: int = 0
    end: int = 0
    threshold: int = 0
    pass_rate: float = 0.0
    meta: Dict[str, Any] = None


def compute_score_v2(
    text: str,
    url: str,
    lead: Lead,
    config: Optional[ScoreConfig] = None,
) -> int:
    """Berechnet einen Score 0–100 für einen einzelnen Lead (v2-Scoring)."""
    config = dict(DEFAULT_SCORE_CONFIG if config is None else config)

    email = (lead.get("email") or "").strip().lower()
    telefon = (lead.get("telefon") or "").strip()
    phone_type = (lead.get("phone_type") or "").strip().lower()
    region = (lead.get("region") or "").strip().upper()
    industry = (lead.get("industry") or "").strip().lower()
    tags = (lead.get("tags") or "").lower()
    recency = (lead.get("recency_indicator") or "").lower()
    whatsapp = (lead.get("whatsapp_link") or "").lower()

    score = 0

    if not telefon:
        score -= 100

    if email:
        score += config["email_bonus"]
        domain = email.split("@", 1)[1] if "@" in email else ""
        local = email.split("@", 1)[0]
        domain_is_portal = domain and any(domain == d or domain.endswith("." + d) for d in PORTAL_DOMAINS)
        domain_is_free = domain in FREE_MAILS
        local_is_generic = local in GENERIC_MAILBOXES

        if domain_is_portal:
            score -= 15
        elif local_is_generic:
            score -= 5
        elif domain_is_free:
            score += 5
        elif domain and not domain_is_free:
            score += 10

    if telefon:
        score += config["phone_bonus"]

    if phone_type == "mobile":
        score += config["mobile_bonus"]

    text_low = (text or "").lower()
    url_value = url or ""
    parsed = urllib.parse.urlparse(url_value)
    host = parsed.netloc.lower()
    host_is_portal = any(host == d or host.endswith("." + d) for d in PORTAL_DOMAINS)

    has_wa = (
        ("whatsapp" in tags)
        or (whatsapp in {"1", "yes", "true"})
        or ("wa.me" in text_low)
        or ("wa.me" in url_value.lower())
        or ("api.whatsapp.com" in url_value.lower())
    )
    if has_wa:
        score += config["whatsapp_bonus"]

    sales_keywords = [
        "vertrieb",
        "sales",
        "verkauf",
        "telesales",
        "callcenter",
        "call center",
        "outbound",
        "d2d",
        "door to door",
        "haustür",
        "haustuer",
    ]
    sales_hits = sum(text_low.count(k) for k in sales_keywords)
    if sales_hits > 0:
        score += min(sales_hits * 3, config["sales_keywords_bonus"])

    job_keywords = ["jobsuche", "stellensuche", "arbeitslos", "bewerbung", "lebenslauf", "cv"]
    job_hits = sum(text_low.count(k) for k in job_keywords)
    if job_hits > 0:
        score += min(job_hits * 2, config["jobseeker_bonus"])

    if industry in {"versicherung", "energie", "telekom", "bau", "ecommerce", "household"}:
        score += config["industry_bonus"]

    if region == "NRW" or "nrw" in tags:
        score += config["nrw_bonus"]

    if recency in {"aktuell", "sofort"}:
        score += config["fresh_bonus"]

    if lead.get("private_address"):
        score += config["private_address_bonus"]

    if lead.get("social_profile_url"):
        score += config["social_profile_bonus"]

    if "jobs." in url_value or "/jobs" in url_value or "/karriere" in url_value:
        score -= 15

    if any(token in url_value for token in ["/datenschutz", "/privacy", "/agb", "/impressum"]):
        score -= 20

    if host_is_portal:
        score -= 25

    score_int = int(round(score))
    score_int = max(0, min(100, score_int))
    return score_int


def apply_dynamic_threshold(
    leads: List[Lead],
    percentile: float = 0.25,
) -> Tuple[List[Lead], Dict[str, Any]]:
    """
    Entfernt z.B. das schlechteste Quartil nach Score.
    Gibt (gefilterte_leads, info_dict) zurück.
    """
    if not leads:
        return [], {"threshold": 0, "passed": 0, "removed": 0, "pass_rate": "0.0%"}

    scores = [max(0, min(100, int(l.get("score", 0)))) for l in leads]

    if sum(scores) == 0:
        threshold = 0
        filtered = list(leads)
    else:
        if len(scores) < 8:
            threshold = statistics.median(scores)
        else:
            q = statistics.quantiles(scores, n=4)
            threshold = int(round(q[0] + 5))

        threshold = max(0, min(100, threshold))
        filtered = [l for l in leads if int(l.get("score", 0)) >= threshold]

    total = len(leads)
    passed = len(filtered)
    removed = total - passed
    pass_rate = f"{(passed / total * 100.0):.1f}%" if total else "0.0%"

    info = {
        "threshold": threshold,
        "passed": passed,
        "removed": removed,
        "pass_rate": pass_rate,
    }
    return filtered, info


def score_and_filter_leads(
    leads: List[Lead],
    run_id: int,
    *,
    base_min_score: Optional[int] = None,
    verbose: bool = False,
) -> Tuple[List[Lead], ScoreSummary]:
    """
    Komplette Scoring-Pipeline:
    1. compute_score_v2() für alle Leads
    2. apply_dynamic_threshold() mit optionaler Untergrenze base_min_score
    3. Quality-Metriken loggen (wird in S4 verdrahtet)
    """
    all_leads = list(leads or [])
    if not all_leads:
        summary = ScoreSummary(start=0, eligible=0, end=0, threshold=0, pass_rate=0.0, meta={})
        return [], summary

    min_floor = 0 if base_min_score is None else int(base_min_score)

    for lead in all_leads:
        text = lead.get("fulltext") or lead.get("text") or ""
        url = lead.get("quelle") or ""
        score = compute_score_v2(text, url, lead)
        lead["score"] = score

    eligible = [l for l in all_leads if int(l.get("score", 0)) >= min_floor]

    if not eligible:
        summary = ScoreSummary(
            start=len(all_leads),
            eligible=0,
            end=0,
            threshold=min_floor,
            pass_rate=0.0,
            meta={"reason": "below_base_min_score", "removed_reason": "below_floor"},
        )
        return [], summary

    filtered, thresh_info = apply_dynamic_threshold(eligible, percentile=0.25)

    metrics: Dict[str, Any] = {}
    try:
        metrics = track_quality_metrics(filtered, run_id, metrics_file="metrics_log.csv", write_csv=True)
    except Exception:
        metrics = {}

    start = len(all_leads)
    elig = len(eligible)
    end = len(filtered)
    threshold = int(thresh_info.get("threshold", min_floor))
    pass_rate_str = thresh_info.get("pass_rate", "0.0%")
    try:
        pass_rate_val = float(pass_rate_str.rstrip("%")) if isinstance(pass_rate_str, str) else float(pass_rate_str)
    except Exception:
        pass_rate_val = 0.0

    removed_reason = None
    if len(filtered) < len(eligible):
        removed_reason = "below_dynamic"
    elif len(eligible) < len(all_leads):
        removed_reason = "below_floor"

    meta = {
        "threshold_info": thresh_info,
        "metrics": metrics,
    }
    if removed_reason:
        meta["removed_reason"] = removed_reason

    summary = ScoreSummary(
        start=start,
        eligible=elig,
        end=end,
        threshold=threshold,
        pass_rate=pass_rate_val,
        meta=meta,
    )
    return filtered, summary


__all__ = ["ScoreSummary", "compute_score_v2", "apply_dynamic_threshold", "score_and_filter_leads"]


if __name__ == "__main__":
    demo_leads: List[Lead] = [
        {"id": 1, "text": "Demo lead A", "url": "https://example.com/a"},
        {"id": 2, "text": "Demo lead B", "url": "https://example.com/b"},
    ]
    score_and_filter_leads(demo_leads, run_id=0, base_min_score=None, verbose=True)
    print("scoring_enhanced stub ok")
