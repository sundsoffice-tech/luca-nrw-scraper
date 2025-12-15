# -*- coding: utf-8 -*-
"""
Reporting module for generating weekly summaries and analytics.
"""

import csv
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from metrics import MetricsStore


class ReportGenerator:
    """Generate comprehensive reports for the scraping system."""
    
    def __init__(self, metrics_store: MetricsStore):
        self.metrics = metrics_store
    
    def generate_weekly_report(
        self,
        output_format: str = "json",
        output_path: Optional[str] = None,
    ) -> Dict:
        """
        Generate a weekly report with key metrics.
        
        Args:
            output_format: "json" or "csv"
            output_path: Optional path to save report
        
        Returns:
            Report data as dictionary
        """
        # Get top and flop dorks
        top_dorks = self.metrics.get_top_dorks(n=5)
        flop_dorks = self.metrics.get_flop_dorks(n=5)
        
        # Get phone find rate
        phone_find_rate = self.metrics.calculate_phone_find_rate()
        
        # Get backed-off hosts
        backedoff_hosts = self.metrics.get_backedoff_hosts()
        
        # Get drop reasons summary
        drop_reasons = self.metrics.get_drop_reasons_summary()
        
        # Aggregate statistics
        total_queries = sum(d.queries_total for d in self.metrics.dork_cache.values())
        total_fetched = sum(d.urls_fetched for d in self.metrics.dork_cache.values())
        total_leads = sum(d.leads_found for d in self.metrics.dork_cache.values())
        total_kept = sum(d.leads_kept for d in self.metrics.dork_cache.values())
        total_accepted = sum(d.accepted_leads for d in self.metrics.dork_cache.values())
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "weekly",
            "summary": {
                "total_queries": total_queries,
                "total_urls_fetched": total_fetched,
                "total_leads_found": total_leads,
                "total_leads_kept": total_kept,
                "total_accepted_leads": total_accepted,
                "phone_find_rate": f"{phone_find_rate * 100:.2f}%",
                "acceptance_rate": f"{(total_accepted / max(1, total_leads)) * 100:.2f}%",
            },
            "top_dorks": [
                {
                    "dork": d.dork,
                    "score": d.score(),
                    "queries": d.queries_total,
                    "accepted": d.accepted_leads,
                    "kept": d.leads_kept,
                }
                for d in top_dorks
            ],
            "flop_dorks": [
                {
                    "dork": d.dork,
                    "score": d.score(),
                    "queries": d.queries_total,
                    "accepted": d.accepted_leads,
                    "kept": d.leads_kept,
                }
                for d in flop_dorks
            ],
            "backedoff_hosts": [
                {
                    "host": h.host,
                    "drop_rate": f"{h.drop_rate() * 100:.2f}%",
                    "backoff_until": datetime.fromtimestamp(h.backoff_until).isoformat(),
                    "top_reasons": dict(sorted(
                        h.drops_by_reason.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:3]),
                }
                for h in backedoff_hosts
            ],
            "drop_reasons": drop_reasons,
        }
        
        # Save to file if requested
        if output_path:
            if output_format == "json":
                self._save_json_report(report, output_path)
            elif output_format == "csv":
                self._save_csv_report(report, output_path)
        
        return report
    
    def _save_json_report(self, report: Dict, path: str):
        """Save report as JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def _save_csv_report(self, report: Dict, path: str):
        """Save report as CSV (summary format)."""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write summary
            writer.writerow(['Section', 'Metric', 'Value'])
            writer.writerow(['Summary', 'Generated At', report['generated_at']])
            for key, value in report['summary'].items():
                writer.writerow(['Summary', key, value])
            
            writer.writerow([])  # Empty row
            
            # Write top dorks
            writer.writerow(['Top Dorks', 'Dork', 'Score', 'Queries', 'Accepted', 'Kept'])
            for d in report['top_dorks']:
                writer.writerow([
                    'Top Dorks',
                    d['dork'][:50],  # Truncate long dorks
                    d['score'],
                    d['queries'],
                    d['accepted'],
                    d['kept'],
                ])
            
            writer.writerow([])  # Empty row
            
            # Write flop dorks
            writer.writerow(['Flop Dorks', 'Dork', 'Score', 'Queries', 'Accepted', 'Kept'])
            for d in report['flop_dorks']:
                writer.writerow([
                    'Flop Dorks',
                    d['dork'][:50],
                    d['score'],
                    d['queries'],
                    d['accepted'],
                    d['kept'],
                ])
            
            writer.writerow([])  # Empty row
            
            # Write drop reasons
            writer.writerow(['Drop Reasons', 'Reason', 'Count'])
            for reason, count in sorted(
                report['drop_reasons'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                writer.writerow(['Drop Reasons', reason, count])
            
            writer.writerow([])  # Empty row
            
            # Write backed-off hosts
            writer.writerow(['Backed-off Hosts', 'Host', 'Drop Rate', 'Backoff Until'])
            for h in report['backedoff_hosts']:
                writer.writerow([
                    'Backed-off Hosts',
                    h['host'],
                    h['drop_rate'],
                    h['backoff_until'],
                ])
    
    def log_dork_selection(
        self,
        selected_dorks: List[Dict],
        mode: str,
        log_file: str = "dork_selection_log.jsonl",
    ):
        """
        Log selected dorks for this run.
        
        Args:
            selected_dorks: List of dork selection info
            mode: Current Wasserfall mode
            log_file: Path to log file (JSONL format)
        """
        log_entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "mode": mode,
            "num_dorks": len(selected_dorks),
            "dorks": selected_dorks,
        }
        
        # Append to JSONL file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def generate_dork_performance_summary(self) -> List[Dict]:
        """
        Generate a summary of all dork performances.
        
        Returns:
            List of dork performance data
        """
        performances = []
        
        for dork, metrics in self.metrics.dork_cache.items():
            if metrics.queries_total == 0:
                continue
            
            performances.append({
                "dork": dork,
                "score": metrics.score(),
                "queries_total": metrics.queries_total,
                "serp_hits": metrics.serp_hits,
                "urls_fetched": metrics.urls_fetched,
                "leads_found": metrics.leads_found,
                "leads_kept": metrics.leads_kept,
                "accepted_leads": metrics.accepted_leads,
                "conversion_rate": (
                    metrics.accepted_leads / max(1, metrics.urls_fetched)
                ),
            })
        
        # Sort by score
        performances.sort(key=lambda x: x["score"], reverse=True)
        
        return performances
    
    def generate_host_analysis(self) -> List[Dict]:
        """
        Generate analysis of host performance.
        
        Returns:
            List of host analysis data
        """
        analyses = []
        
        for host, metrics in self.metrics.host_cache.items():
            if metrics.hits_total == 0:
                continue
            
            analyses.append({
                "host": host,
                "hits_total": metrics.hits_total,
                "drop_rate": metrics.drop_rate(),
                "is_backedoff": metrics.is_backedoff(),
                "top_drop_reasons": dict(sorted(
                    metrics.drops_by_reason.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]),
            })
        
        # Sort by hits (most active first)
        analyses.sort(key=lambda x: x["hits_total"], reverse=True)
        
        return analyses
