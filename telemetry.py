import json
import os
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_THRESHOLDS: Dict[str, float] = {
    "title_guard_score": 1.0,
    "ai_filter_min_score": 40.0,
    "garbage_block_confidence": 0.5,
    "max_negative_keywords": 1.0,
}


class TelemetryStore:
    """
    Lightweight telemetry with persistence and adaptive thresholds.
    """

    def __init__(
        self,
        path: Path | str = ".run_state/telemetry.json",
        status_path: Path | str | None = None,
        thresholds_path: Path | str | None = None,
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.status_path = Path(status_path) if status_path else self.path.parent / "status.json"
        self.thresholds_path = Path(thresholds_path) if thresholds_path else self.path.parent / "thresholds.json"
        self._lock = threading.Lock()
        self.run_id: int | None = None
        self.start_ts: float = time.time()
        self.counters: Dict[str, int] = defaultdict(int)
        self.reasons: Dict[str, int] = defaultdict(int)
        self.strategy_stats: Dict[str, Dict[str, int]] = {}
        self.thresholds: Dict[str, float] = dict(DEFAULT_THRESHOLDS)
        self.target_success_per_min = float(os.getenv("TARGET_SUCCESS_PER_MIN", "0.5"))
        self.target_success_rate = float(os.getenv("ADAPT_TARGET_RATE", "0.2"))
        self.window_size = int(os.getenv("ADAPT_WINDOW", "50"))
        self.recent_outcomes: deque[str] = deque(maxlen=self.window_size)
        self._load_last_thresholds()

    def _load_last_thresholds(self) -> None:
        loaded = False
        if self.thresholds_path.exists():
            try:
                data = json.loads(self.thresholds_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.thresholds.update({k: float(v) for k, v in data.items() if isinstance(v, (int, float))})
                    loaded = True
            except Exception:
                pass
        if loaded:
            return
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                last = data[-1]
                if isinstance(last, dict) and isinstance(last.get("thresholds"), dict):
                    self.thresholds.update(
                        {k: float(v) for k, v in last["thresholds"].items() if isinstance(v, (int, float))}
                    )
        except Exception:
            pass

    def start_run(self, run_id: int | None = None) -> None:
        with self._lock:
            self.run_id = run_id
            self.start_ts = time.time()
            self.counters = defaultdict(int)
            self.reasons = defaultdict(int)
            self.strategy_stats = {}
            self.recent_outcomes = deque(maxlen=self.window_size)
        self.update_thresholds(self.thresholds)

    def inc(self, key: str, amount: int = 1, reason: str | None = None) -> None:
        with self._lock:
            self.counters[key] += amount
            if reason:
                self.reasons[reason] += amount

    def record_strategy(self, name: str, fetched: int = 0, success: int = 0) -> None:
        with self._lock:
            st = self.strategy_stats.setdefault(name, {"fetched": 0, "success": 0})
            st["fetched"] += max(0, fetched)
            st["success"] += max(0, success)

    def record_outcome(self, outcome: str) -> None:
        if outcome not in {"success", "garbage", "blocked", "low_quality"}:
            outcome = "blocked"
        with self._lock:
            self.recent_outcomes.append(outcome)
            self._adaptive_rebalance()

    def log_decision(self, url: str, decision: str, reason_codes: List[str], scores: Dict[str, Any]) -> None:
        rc_key = f"decision:{decision}"
        with self._lock:
            self.reasons[rc_key] += 1
            for r in reason_codes:
                self.reasons[f"rc:{r}"] += 1

    def update_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        with self._lock:
            for key, val in new_thresholds.items():
                if key in DEFAULT_THRESHOLDS:
                    self.thresholds[key] = float(val)
            try:
                self.thresholds_path.parent.mkdir(parents=True, exist_ok=True)
                self.thresholds_path.write_text(json.dumps(self.thresholds, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

    def _block_counts(self) -> int:
        keys = [
            "blocked_by_title_guard",
            "blocked_by_garbage",
            "blocked_by_ai_filter",
            "rejected_quality_gate",
        ]
        return sum(self.counters.get(k, 0) for k in keys)

    def snapshot(self) -> Dict[str, Any]:
        elapsed = max(time.time() - self.start_ts, 1.0)
        fetched = max(self.counters.get("fetched_urls_total", 0), 1)
        block_rate = min(1.0, self._block_counts() / fetched)
        success_per_min = self.counters.get("success_candidates", 0) / (elapsed / 60.0)
        success_rate = 0.0
        if self.recent_outcomes:
            success_rate = sum(1 for o in self.recent_outcomes if o == "success") / len(self.recent_outcomes)
        return {
            "run_id": self.run_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "duration_s": elapsed,
            "counters": dict(self.counters),
            "reasons": dict(self.reasons),
            "strategy_stats": dict(self.strategy_stats),
            "thresholds": dict(self.thresholds),
            "block_rate": round(block_rate, 4),
            "success_per_min": round(success_per_min, 4),
            "target_success_per_min": self.target_success_per_min,
            "success_rate_recent": round(success_rate, 4),
            "target_success_rate": self.target_success_rate,
        }

    def top_blockers(self, limit: int = 5) -> List[Tuple[str, int]]:
        return sorted(self.reasons.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    def persist_run(self, status: str = "ok", meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        snap = self.snapshot()
        payload = {
            **snap,
            "status": status,
            "meta": meta or {},
            "top_blockers": [{"reason": r, "count": c} for r, c in self.top_blockers()],
        }
        data: List[Dict[str, Any]] = []
        if self.path.exists():
            try:
                data_raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data_raw, list):
                    data = data_raw
            except Exception:
                data = []
        data.append(payload)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
        self._write_status_file(payload)
        return payload

    def _write_status_file(self, payload: Dict[str, Any]) -> None:
        status = {
            "run_id": payload.get("run_id"),
            "timestamp": payload.get("timestamp"),
            "thresholds": payload.get("thresholds", {}),
            "block_rate": payload.get("block_rate"),
            "success_per_min": payload.get("success_per_min"),
            "target_success_per_min": payload.get("target_success_per_min"),
            "success_rate_recent": payload.get("success_rate_recent"),
            "target_success_rate": payload.get("target_success_rate"),
            "top_blockers": payload.get("top_blockers", []),
            "counters": payload.get("counters", {}),
        }
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    def _adaptive_rebalance(self) -> None:
        if not self.recent_outcomes:
            return
        successes = sum(1 for o in self.recent_outcomes if o == "success")
        garbage = sum(1 for o in self.recent_outcomes if o in {"garbage", "low_quality"})
        total = len(self.recent_outcomes)
        success_rate = successes / total if total else 0.0
        garbage_rate = garbage / total if total else 0.0

        changed = False
        title_guard = self.thresholds.get("title_guard_score", DEFAULT_THRESHOLDS["title_guard_score"])
        ai_min = self.thresholds.get("ai_filter_min_score", DEFAULT_THRESHOLDS["ai_filter_min_score"])

        if success_rate < self.target_success_rate:
            title_guard = max(0.1, round(title_guard - 0.05, 3))
            ai_min = max(15.0, round(ai_min - 0.05, 3))
            changed = True
        elif garbage_rate > (1.0 - self.target_success_rate):
            title_guard = min(2.0, round(title_guard + 0.05, 3))
            ai_min = min(90.0, round(ai_min + 0.05, 3))
            changed = True

        if changed:
            self.update_thresholds(
                {
                    "title_guard_score": title_guard,
                    "ai_filter_min_score": ai_min,
                    "garbage_block_confidence": self.thresholds.get("garbage_block_confidence", DEFAULT_THRESHOLDS["garbage_block_confidence"]),
                    "max_negative_keywords": self.thresholds.get("max_negative_keywords", DEFAULT_THRESHOLDS["max_negative_keywords"]),
                }
            )


_TELEMETRY_SINGLETON: TelemetryStore | None = None


def get_telemetry() -> TelemetryStore:
    global _TELEMETRY_SINGLETON
    if _TELEMETRY_SINGLETON is None:
        _TELEMETRY_SINGLETON = TelemetryStore()
    return _TELEMETRY_SINGLETON


def maybe_adjust_thresholds(metrics: Dict[str, Any], thresholds: Dict[str, float] | None = None) -> Tuple[Dict[str, float], bool]:
    """
    Loosen guards if we are over-blocking and under-performing.
    """
    thresholds = dict(thresholds or DEFAULT_THRESHOLDS)
    success_per_min = float(metrics.get("success_per_min", 0.0) or 0.0)
    target = float(metrics.get("target_success_per_min", 0.5) or 0.5)
    block_rate = float(metrics.get("block_rate", 0.0) or 0.0)
    changed = False
    if success_per_min < target and block_rate > 0.7:
        thresholds["title_guard_score"] = max(0.0, thresholds.get("title_guard_score", 1.0) - 0.25)
        thresholds["ai_filter_min_score"] = max(20.0, thresholds.get("ai_filter_min_score", 40.0) - 5.0)
        thresholds["garbage_block_confidence"] = min(0.95, thresholds.get("garbage_block_confidence", 0.5) + 0.1)
        changed = True
    return thresholds, changed
