import random
import time
from typing import Dict, List, Optional, Tuple


class HostPolicy:
    """
    Per-host policy: exponential backoff with jitter, UA rotation, circuit breaker with decay.
    """

    def __init__(
        self,
        ua_pool: List[str],
        base_penalty: float = 60.0,
        max_penalty: float = 900.0,
        max_retries: int = 3,
    ):
        self.ua_pool = ua_pool or []
        self.base_penalty = base_penalty
        self.max_penalty = max_penalty
        self.max_retries = max_retries
        self.state: Dict[str, Dict[str, float]] = {}

    def _init_state(self, host: str) -> Dict[str, float]:
        return self.state.setdefault(
            host,
            {"penalty_s": self.base_penalty, "penalty_until": 0.0, "retries": 0, "ua_idx": 0},
        )

    def next_user_agent(self, host: str) -> Optional[str]:
        st = self._init_state(host)
        if not self.ua_pool:
            return None
        ua = self.ua_pool[int(st["ua_idx"]) % len(self.ua_pool)]
        st["ua_idx"] = (st["ua_idx"] + 1) % max(1, len(self.ua_pool))
        return ua

    def pre_request(self, host: str) -> Tuple[float, Optional[str], bool]:
        st = self._init_state(host)
        now = time.time()
        ua = self.next_user_agent(host)
        delay = max(0.0, st["penalty_until"] - now)
        if delay > 0:
            delay *= random.uniform(0.8, 1.2)
        if st["retries"] >= self.max_retries and delay > 0:
            return delay, ua, False
        return delay, ua, True

    def record_result(self, host: str, status: int) -> None:
        st = self._init_state(host)
        now = time.time()
        if status in (403, 429):
            st["retries"] += 1
            penalty = st.get("penalty_s", self.base_penalty)
            if now < st.get("penalty_until", 0.0):
                penalty = min(self.max_penalty, penalty * 2)
            penalty = max(self.base_penalty, penalty)
            st["penalty_s"] = penalty
            jitter = random.uniform(0.8, 1.4)
            st["penalty_until"] = now + penalty * jitter
        elif 200 <= status < 300:
            st["retries"] = 0
            penalty = st.get("penalty_s", self.base_penalty)
            st["penalty_s"] = max(self.base_penalty * 0.5, penalty * 0.5)
            st["penalty_until"] = 0.0
        else:
            st["retries"] = max(0, st.get("retries", 0) - 1)
            st["penalty_s"] = max(self.base_penalty * 0.5, st.get("penalty_s", self.base_penalty) * 0.9)
