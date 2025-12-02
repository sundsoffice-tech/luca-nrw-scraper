from __future__ import annotations

from typing import Any, Dict, List
import statistics
from datetime import datetime
import csv

Lead = Dict[str, Any]


def track_quality_metrics(
    leads: List[Lead],
    run_id: int,
    metrics_file: str = "metrics_log.csv",
    *,
    write_csv: bool = True,
) -> Dict[str, Any]:
    """
    Aggregiert Qualitäts-Metriken (Score, Confidence etc.) pro Run.
    Optional CSV-Append, aber hier noch keine Logik.
    """
    if not leads:
        return {}

    total = len(leads)
    leads_with_email = sum(1 for l in leads if l.get("email"))
    leads_with_phone = sum(1 for l in leads if l.get("telefon"))
    leads_with_name = sum(1 for l in leads if l.get("name"))
    avg_score = statistics.mean(int(l.get("score", 0)) for l in leads)
    avg_confidence = statistics.mean(float(l.get("confidence_score", 0)) for l in leads)

    stats: Dict[str, Any] = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total_leads": total,
        "leads_with_email": leads_with_email,
        "leads_with_phone": leads_with_phone,
        "leads_with_name": leads_with_name,
        "avg_score": round(avg_score, 1),
        "avg_confidence": round(avg_confidence, 1),
    }

    if write_csv:
        try:
            with open(metrics_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(stats.keys()))
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerow(stats)
        except Exception:
            pass

    return stats


__all__ = ["track_quality_metrics"]
