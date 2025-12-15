# -*- coding: utf-8 -*-
"""
Wasserfall (waterfall) phase-based throttling system.
Manages conservative/moderate/aggressive modes with adaptive transitions.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from metrics import MetricsStore


@dataclass
class WasserfallMode:
    """Configuration for a Wasserfall mode."""
    name: str
    ddg_bucket_rate: int  # Requests per minute for DDG
    google_bucket_rate: int = 4  # Fixed at 4/min
    dork_slots_min: int = 6
    dork_slots_max: int = 8
    explore_rate: float = 0.15
    worker_parallelism: int = 35
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "name": self.name,
            "ddg_bucket_rate": self.ddg_bucket_rate,
            "google_bucket_rate": self.google_bucket_rate,
            "dork_slots": f"{self.dork_slots_min}-{self.dork_slots_max}",
            "explore_rate": f"{self.explore_rate*100:.0f}%",
            "worker_parallelism": self.worker_parallelism,
        }


# Mode definitions
MODE_CONSERVATIVE = WasserfallMode(
    name="conservative",
    ddg_bucket_rate=15,
    dork_slots_min=6,
    dork_slots_max=8,
    explore_rate=0.20,  # 20% explore
    worker_parallelism=35,
)

MODE_MODERATE = WasserfallMode(
    name="moderate",
    ddg_bucket_rate=30,
    dork_slots_min=6,
    dork_slots_max=8,
    explore_rate=0.15,  # 15% explore
    worker_parallelism=35,
)

MODE_AGGRESSIVE = WasserfallMode(
    name="aggressive",
    ddg_bucket_rate=50,
    dork_slots_min=8,
    dork_slots_max=10,
    explore_rate=0.10,  # 10% explore
    worker_parallelism=50,  # Higher parallelism
)


class WasserfallManager:
    """
    Manages Wasserfall mode transitions based on metrics.
    """
    
    def __init__(
        self,
        metrics_store: MetricsStore,
        initial_mode: str = "conservative",
        phone_find_rate_threshold: float = 0.25,  # 25%
        min_runs_for_transition: int = 3,
    ):
        self.metrics = metrics_store
        self.current_mode = self._get_mode(initial_mode)
        self.phone_find_rate_threshold = phone_find_rate_threshold
        self.min_runs = min_runs_for_transition
        self.run_count = 0
        self.mode_history: List[Dict] = []
    
    def _get_mode(self, name: str) -> WasserfallMode:
        """Get mode by name."""
        modes = {
            "conservative": MODE_CONSERVATIVE,
            "moderate": MODE_MODERATE,
            "aggressive": MODE_AGGRESSIVE,
        }
        return modes.get(name, MODE_CONSERVATIVE)
    
    def get_current_mode(self) -> WasserfallMode:
        """Get current active mode."""
        return self.current_mode
    
    def should_transition_up(self) -> bool:
        """Check if should transition to more aggressive mode."""
        if self.run_count < self.min_runs:
            return False
        
        # Check phone find rate
        phone_rate = self.metrics.calculate_phone_find_rate()
        if phone_rate < self.phone_find_rate_threshold:
            return False
        
        # Check block/error rate (simplified: check if backoff hosts are low)
        backedoff = len(self.metrics.get_backedoff_hosts())
        total_hosts = len(self.metrics.host_cache)
        
        if total_hosts > 0:
            backoff_rate = backedoff / total_hosts
            if backoff_rate > 0.2:  # More than 20% hosts backed off
                return False
        
        return True
    
    def should_transition_down(self) -> bool:
        """Check if should transition to more conservative mode."""
        if self.run_count < 2:  # Quick downgrade if issues
            return False
        
        # Check phone find rate
        phone_rate = self.metrics.calculate_phone_find_rate()
        if phone_rate < self.phone_find_rate_threshold * 0.5:  # Dropped below 50% of threshold
            return True
        
        # Check block/error rate
        backedoff = len(self.metrics.get_backedoff_hosts())
        total_hosts = len(self.metrics.host_cache)
        
        if total_hosts > 0:
            backoff_rate = backedoff / total_hosts
            if backoff_rate > 0.3:  # More than 30% hosts backed off
                return True
        
        return False
    
    def transition_mode(self, direction: str, reason: str = "") -> Optional[WasserfallMode]:
        """
        Transition to a different mode.
        
        Args:
            direction: "up" or "down"
            reason: Human-readable reason for transition
        
        Returns:
            New mode if transitioned, None if at boundary
        """
        current_name = self.current_mode.name
        
        if direction == "up":
            if current_name == "conservative":
                new_mode = MODE_MODERATE
            elif current_name == "moderate":
                new_mode = MODE_AGGRESSIVE
            else:  # Already aggressive
                return None
        elif direction == "down":
            if current_name == "aggressive":
                new_mode = MODE_MODERATE
            elif current_name == "moderate":
                new_mode = MODE_CONSERVATIVE
            else:  # Already conservative
                return None
        else:
            return None
        
        # Log transition
        transition_info = {
            "timestamp": time.time(),
            "from_mode": current_name,
            "to_mode": new_mode.name,
            "direction": direction,
            "reason": reason,
            "run_count": self.run_count,
            "phone_find_rate": self.metrics.calculate_phone_find_rate(),
            "backedoff_hosts": len(self.metrics.get_backedoff_hosts()),
        }
        self.mode_history.append(transition_info)
        
        self.current_mode = new_mode
        self.run_count = 0  # Reset run count after transition
        
        return new_mode
    
    def check_and_transition(self) -> Optional[Dict]:
        """
        Check if should transition and do it.
        Returns transition info if transitioned, None otherwise.
        """
        if self.should_transition_up():
            new_mode = self.transition_mode(
                "up",
                f"Phone find rate >= {self.phone_find_rate_threshold*100:.0f}%, low errors"
            )
            if new_mode:
                return self.mode_history[-1]
        
        elif self.should_transition_down():
            new_mode = self.transition_mode(
                "down",
                f"Phone find rate dropped or high error rate"
            )
            if new_mode:
                return self.mode_history[-1]
        
        return None
    
    def increment_run(self):
        """Increment run counter."""
        self.run_count += 1
    
    def get_status(self) -> Dict:
        """Get current status."""
        return {
            "current_mode": self.current_mode.to_dict(),
            "run_count": self.run_count,
            "phone_find_rate": self.metrics.calculate_phone_find_rate(),
            "backedoff_hosts": len(self.metrics.get_backedoff_hosts()),
            "transitions_count": len(self.mode_history),
        }
