# -*- coding: utf-8 -*-
"""
Metrics tracking module for adaptive search system.
Tracks per-dork and per-host metrics using SQLite backend.
"""

import json
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DorkMetrics:
    """Metrics for a single dork query."""
    dork: str
    queries_total: int = 0
    serp_hits: int = 0
    urls_fetched: int = 0
    leads_found: int = 0
    leads_kept: int = 0
    accepted_leads: int = 0
    last_used: float = 0.0
    
    def score(self) -> float:
        """Calculate dork score: accepted_leads / max(1, queries_total), fallback to leads_kept."""
        if self.queries_total == 0:
            return 0.0
        if self.accepted_leads > 0:
            return self.accepted_leads / max(1, self.queries_total)
        # Fallback to leads_kept if no accepted leads yet
        return self.leads_kept / max(1, self.queries_total)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dork": self.dork,
            "queries_total": self.queries_total,
            "serp_hits": self.serp_hits,
            "urls_fetched": self.urls_fetched,
            "leads_found": self.leads_found,
            "leads_kept": self.leads_kept,
            "accepted_leads": self.accepted_leads,
            "last_used": self.last_used,
            "score": self.score(),
        }


@dataclass
class HostMetrics:
    """Metrics for a single host."""
    host: str
    hits_total: int = 0
    drops_by_reason: Dict[str, int] = field(default_factory=dict)
    backoff_until: float = 0.0  # Unix timestamp
    
    def drop_rate(self) -> float:
        """Calculate total drop rate."""
        total_drops = sum(self.drops_by_reason.values())
        if self.hits_total == 0:
            return 0.0
        return total_drops / self.hits_total
    
    def is_backedoff(self) -> bool:
        """Check if host is currently in backoff period."""
        return time.time() < self.backoff_until
    
    def should_backoff(self, threshold: float = 0.8) -> bool:
        """Check if host should be put in backoff based on drop rate."""
        if self.hits_total < 5:  # Minimum hits before backoff
            return False
        
        # Check if specific bad reasons exceed threshold
        bad_reasons = {"no_phone", "portal_domain", "job_ad", "blacklist_host"}
        bad_drops = sum(self.drops_by_reason.get(r, 0) for r in bad_reasons)
        
        if self.hits_total > 0 and (bad_drops / self.hits_total) > threshold:
            return True
        
        return self.drop_rate() > threshold
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "hits_total": self.hits_total,
            "drops_by_reason": dict(self.drops_by_reason),
            "backoff_until": self.backoff_until,
            "drop_rate": self.drop_rate(),
            "is_backedoff": self.is_backedoff(),
        }


class MetricsStore:
    """SQLite-backed metrics storage."""
    
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self.dork_cache: Dict[str, DorkMetrics] = {}
        self.host_cache: Dict[str, HostMetrics] = {}
        self._init_db()
        self._load_metrics()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Dork metrics table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dork_metrics (
                dork TEXT PRIMARY KEY,
                queries_total INTEGER DEFAULT 0,
                serp_hits INTEGER DEFAULT 0,
                urls_fetched INTEGER DEFAULT 0,
                leads_found INTEGER DEFAULT 0,
                leads_kept INTEGER DEFAULT 0,
                accepted_leads INTEGER DEFAULT 0,
                last_used REAL DEFAULT 0.0,
                updated_at REAL DEFAULT 0.0
            )
        """)
        
        # Host metrics table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS host_metrics (
                host TEXT PRIMARY KEY,
                hits_total INTEGER DEFAULT 0,
                drops_by_reason TEXT DEFAULT '{}',
                backoff_until REAL DEFAULT 0.0,
                updated_at REAL DEFAULT 0.0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_metrics(self):
        """Load metrics from database into cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Load dork metrics
            cur.execute("SELECT * FROM dork_metrics")
            for row in cur.fetchall():
                self.dork_cache[row["dork"]] = DorkMetrics(
                    dork=row["dork"],
                    queries_total=row["queries_total"],
                    serp_hits=row["serp_hits"],
                    urls_fetched=row["urls_fetched"],
                    leads_found=row["leads_found"],
                    leads_kept=row["leads_kept"],
                    accepted_leads=row["accepted_leads"],
                    last_used=row["last_used"],
                )
            
            # Load host metrics
            cur.execute("SELECT * FROM host_metrics")
            for row in cur.fetchall():
                drops = json.loads(row["drops_by_reason"])
                self.host_cache[row["host"]] = HostMetrics(
                    host=row["host"],
                    hits_total=row["hits_total"],
                    drops_by_reason=defaultdict(int, drops),
                    backoff_until=row["backoff_until"],
                )
            
            conn.close()
        except sqlite3.OperationalError:
            # Tables don't exist yet, skip loading
            pass
    
    def persist(self):
        """Persist all metrics to database."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now = time.time()
        
        try:
            # Persist dork metrics
            for dork, metrics in self.dork_cache.items():
                cur.execute("""
                    INSERT OR REPLACE INTO dork_metrics 
                    (dork, queries_total, serp_hits, urls_fetched, leads_found, 
                     leads_kept, accepted_leads, last_used, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dork, metrics.queries_total, metrics.serp_hits,
                    metrics.urls_fetched, metrics.leads_found, metrics.leads_kept,
                    metrics.accepted_leads, metrics.last_used, now
                ))
            
            # Persist host metrics
            for host, metrics in self.host_cache.items():
                drops_json = json.dumps(dict(metrics.drops_by_reason))
                cur.execute("""
                    INSERT OR REPLACE INTO host_metrics 
                    (host, hits_total, drops_by_reason, backoff_until, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (host, metrics.hits_total, drops_json, metrics.backoff_until, now))
            
            conn.commit()
        except sqlite3.OperationalError as e:
            # If tables don't exist, reinitialize
            if "no such table" in str(e):
                conn.close()
                self._init_db()
                # Retry persist
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                for dork, metrics in self.dork_cache.items():
                    cur.execute("""
                        INSERT OR REPLACE INTO dork_metrics 
                        (dork, queries_total, serp_hits, urls_fetched, leads_found, 
                         leads_kept, accepted_leads, last_used, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        dork, metrics.queries_total, metrics.serp_hits,
                        metrics.urls_fetched, metrics.leads_found, metrics.leads_kept,
                        metrics.accepted_leads, metrics.last_used, now
                    ))
                for host, metrics in self.host_cache.items():
                    drops_json = json.dumps(dict(metrics.drops_by_reason))
                    cur.execute("""
                        INSERT OR REPLACE INTO host_metrics 
                        (host, hits_total, drops_by_reason, backoff_until, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (host, metrics.hits_total, drops_json, metrics.backoff_until, now))
                conn.commit()
            else:
                raise
        finally:
            conn.close()
    
    def get_dork_metrics(self, dork: str) -> DorkMetrics:
        """Get or create dork metrics."""
        if dork not in self.dork_cache:
            self.dork_cache[dork] = DorkMetrics(dork=dork)
        return self.dork_cache[dork]
    
    def get_host_metrics(self, host: str) -> HostMetrics:
        """Get or create host metrics."""
        if not host:
            return HostMetrics(host="", drops_by_reason=defaultdict(int))
        if host not in self.host_cache:
            self.host_cache[host] = HostMetrics(host=host, drops_by_reason=defaultdict(int))
        return self.host_cache[host]
    
    def record_query(self, dork: str):
        """Record a query execution."""
        m = self.get_dork_metrics(dork)
        m.queries_total += 1
        m.last_used = time.time()
    
    def record_serp_hits(self, dork: str, count: int):
        """Record SERP hits for a dork."""
        m = self.get_dork_metrics(dork)
        m.serp_hits += count
    
    def record_url_fetch(self, dork: str, host: str):
        """Record a URL fetch."""
        m = self.get_dork_metrics(dork)
        m.urls_fetched += 1
        
        h = self.get_host_metrics(host)
        h.hits_total += 1
    
    def record_lead_found(self, dork: str):
        """Record a lead found."""
        m = self.get_dork_metrics(dork)
        m.leads_found += 1
    
    def record_lead_kept(self, dork: str):
        """Record a lead kept after dropper."""
        m = self.get_dork_metrics(dork)
        m.leads_kept += 1
    
    def record_accepted_lead(self, dork: str):
        """Record a lead accepted (final)."""
        m = self.get_dork_metrics(dork)
        m.accepted_leads += 1
    
    def record_drop(self, host: str, reason: str):
        """Record a lead drop."""
        h = self.get_host_metrics(host)
        h.drops_by_reason[reason] += 1
    
    def set_host_backoff(self, host: str, duration_seconds: int = 604800):
        """Set host backoff (default 7 days)."""
        h = self.get_host_metrics(host)
        h.backoff_until = time.time() + duration_seconds
    
    def get_top_dorks(self, n: int = 10) -> List[DorkMetrics]:
        """Get top N dorks by score."""
        dorks = list(self.dork_cache.values())
        dorks.sort(key=lambda d: d.score(), reverse=True)
        return dorks[:n]
    
    def get_flop_dorks(self, n: int = 10) -> List[DorkMetrics]:
        """Get bottom N dorks by score (that have been tried)."""
        dorks = [d for d in self.dork_cache.values() if d.queries_total > 0]
        dorks.sort(key=lambda d: d.score())
        return dorks[:n]
    
    def get_backedoff_hosts(self) -> List[HostMetrics]:
        """Get all currently backed-off hosts."""
        return [h for h in self.host_cache.values() if h.is_backedoff()]
    
    def get_drop_reasons_summary(self) -> Dict[str, int]:
        """Get summary of all drop reasons."""
        summary = defaultdict(int)
        for host_metrics in self.host_cache.values():
            for reason, count in host_metrics.drops_by_reason.items():
                summary[reason] += count
        return dict(summary)
    
    def calculate_phone_find_rate(self) -> float:
        """Calculate overall phone find rate."""
        total_fetched = sum(d.urls_fetched for d in self.dork_cache.values())
        total_leads = sum(d.leads_found for d in self.dork_cache.values())
        
        if total_fetched == 0:
            return 0.0
        
        return total_leads / total_fetched


# Global metrics store instance
_METRICS_STORE: Optional[MetricsStore] = None


def get_metrics_store(db_path: str = "metrics.db") -> MetricsStore:
    """Get or create global metrics store."""
    global _METRICS_STORE
    if _METRICS_STORE is None:
        _METRICS_STORE = MetricsStore(db_path)
    return _METRICS_STORE
