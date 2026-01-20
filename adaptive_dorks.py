# -*- coding: utf-8 -*-
"""
Adaptive dork selection using bandit-light algorithm.
"""

import random
from typing import Callable, Dict, List, Tuple, Union

from metrics import MetricsStore, DorkMetrics


class AdaptiveDorkSelector:
    """
    Bandit-light algorithm for adaptive dork selection.
    Maintains core_dorks (top performers) and explore_dorks (new/experimental).
    """
    
    def __init__(
        self,
        metrics_store: MetricsStore,
        all_dorks: Union[List[str], Callable[[], List[str]]],
        explore_rate: float = 0.15,
        min_core: int = 4,
        max_core: int = 6,
    ):
        self.metrics = metrics_store
        self._dork_loader = all_dorks
        self._dorks_loaded = False
        self.all_dorks: List[str] = []
        self.explore_rate = explore_rate
        self.min_core = min_core
        self.max_core = max_core
        self.core_dorks: List[str] = []
        self.explore_dorks: List[str] = []
        # Pools will be initialized lazily when needed
   
    def _load_all_dorks(self):
        """Load all dorks only once, supporting callables."""
        if self._dorks_loaded:
            return
        loader = self._dork_loader
        try:
            if callable(loader):
                loaded = loader() or []
            else:
                loaded = loader or []
            self.all_dorks = list(loaded)
        except Exception:
            self.all_dorks = []
        self._dorks_loaded = True
    def _update_pools(self):
        """Update core and explore pools based on metrics."""
        self._load_all_dorks()
        # Get all dork metrics
        dork_metrics = [self.metrics.get_dork_metrics(d) for d in self.all_dorks]
        
        # Sort by score (best first)
        dork_metrics.sort(key=lambda d: d.score(), reverse=True)
        
        # Core dorks: top performers with at least 1 query tried
        tried_dorks = [d for d in dork_metrics if d.queries_total > 0]
        self.core_dorks = [d.dork for d in tried_dorks[:self.max_core]]
        
        # If not enough tried dorks, add untried ones to core
        if len(self.core_dorks) < self.min_core:
            untried = [d.dork for d in dork_metrics if d.queries_total == 0]
            needed = self.min_core - len(self.core_dorks)
            self.core_dorks.extend(untried[:needed])
        
        # Explore dorks: new or low-performing dorks
        core_set = set(self.core_dorks)
        self.explore_dorks = [d for d in self.all_dorks if d not in core_set]
    
    def select_dorks(
        self,
        num_dorks: int = 8,
        google_ratio: float = 0.25,
        force_update: bool = False,
    ) -> List[Dict[str, str]]:
        """
        Select dorks for this run using ε-greedy strategy.
        
        Args:
            num_dorks: Total number of dorks to select (6-10)
            google_ratio: Ratio of dorks to send to Google (0.25 = 25%)
            force_update: Force pool update before selection
        
        Returns:
            List of dork info dicts with keys: dork, pool, source, score
        """
        if force_update or not self.core_dorks:
            self._update_pools()
        
        # Calculate explore count (ε-greedy)
        num_explore = int(num_dorks * self.explore_rate)
        num_core = num_dorks - num_explore
        
        # Ensure we have enough dorks
        num_core = min(num_core, len(self.core_dorks))
        num_explore = min(num_explore, len(self.explore_dorks))
        
        # If we don't have enough, adjust
        if num_core + num_explore < num_dorks:
            deficit = num_dorks - (num_core + num_explore)
            if len(self.core_dorks) > num_core:
                num_core += deficit
            elif len(self.explore_dorks) > num_explore:
                num_explore += deficit
        
        selected = []
        
        # Select core dorks (best first)
        core_selected = self.core_dorks[:num_core]
        for dork in core_selected:
            m = self.metrics.get_dork_metrics(dork)
            selected.append({
                "dork": dork,
                "pool": "core",
                "source": "",  # Will be set below
                "score": m.score(),
            })
        
        # Select explore dorks (random)
        if self.explore_dorks and num_explore > 0:
            explore_selected = random.sample(
                self.explore_dorks,
                min(num_explore, len(self.explore_dorks))
            )
            for dork in explore_selected:
                m = self.metrics.get_dork_metrics(dork)
                selected.append({
                    "dork": dork,
                    "pool": "explore",
                    "source": "",  # Will be set below
                    "score": m.score(),
                })
        
        # Shuffle to mix core and explore
        random.shuffle(selected)
        
        # Assign sources: 25% Google, 75% DDG
        num_google = int(len(selected) * google_ratio)
        num_google = min(num_google, len(selected))
        
        for i, item in enumerate(selected):
            if i < num_google:
                item["source"] = "google"
            else:
                item["source"] = "ddg"
        
        return selected
    
    def promote_to_core(self, dork: str):
        """Manually promote a dork to core pool."""
        self._update_pools()
        if dork in self.explore_dorks:
            self.explore_dorks.remove(dork)
            if dork not in self.core_dorks:
                self.core_dorks.append(dork)
    
    def demote_to_explore(self, dork: str):
        """Manually demote a dork to explore pool."""
        self._update_pools()
        if dork in self.core_dorks:
            self.core_dorks.remove(dork)
            if dork not in self.explore_dorks:
                self.explore_dorks.append(dork)
    
    def get_pool_info(self) -> Dict[str, any]:
        """Get information about current pools."""
        self._update_pools()
        return {
            "core_dorks": len(self.core_dorks),
            "explore_dorks": len(self.explore_dorks),
            "total_dorks": len(self.all_dorks),
            "explore_rate": self.explore_rate,
            "core_top_scores": [
                self.metrics.get_dork_metrics(d).score()
                for d in self.core_dorks[:5]
            ],
        }
