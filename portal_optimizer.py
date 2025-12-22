# -*- coding: utf-8 -*-
"""
Portal optimization module - automatic configuration based on performance.

This module analyzes portal performance and generates optimized configurations
to maximize lead generation while minimizing wasted requests.
"""

import sqlite3
from typing import Dict, Any, List
from learning_engine import LearningEngine


class PortalOptimizer:
    """
    Optimizes portal configuration based on learned performance data.
    """
    
    def __init__(self, learning_engine: LearningEngine):
        """
        Initialize portal optimizer.
        
        Args:
            learning_engine: Learning engine instance
        """
        self.learning_engine = learning_engine
    
    def analyze_portal_performance(self) -> Dict[str, Any]:
        """
        Analyze performance of all portals.
        
        Returns:
            Dictionary with portal analysis
        """
        recommendations = self.learning_engine.optimize_portal_config()
        
        analysis = {
            "summary": {
                "low_performing": len(recommendations["disable"]),
                "rate_limited": len(recommendations["delay_increase"]),
                "high_performing": len(recommendations["prioritize"])
            },
            "disable_recommendations": recommendations["disable"],
            "delay_recommendations": recommendations["delay_increase"],
            "prioritize_recommendations": recommendations["prioritize"]
        }
        
        return analysis
    
    def generate_portal_config(self, current_config: Dict[str, bool],
                               current_delays: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate optimized portal configuration.
        
        Args:
            current_config: Current DIRECT_CRAWL_SOURCES config
            current_delays: Current PORTAL_DELAYS config
        
        Returns:
            Optimized configuration
        """
        recommendations = self.learning_engine.optimize_portal_config()
        
        new_config = current_config.copy()
        new_delays = current_delays.copy()
        changes = []
        
        # Disable low-performing portals
        for rec in recommendations["disable"]:
            domain = rec["domain"]
            # Map domain to portal key
            portal_key = self._domain_to_portal_key(domain)
            if portal_key and new_config.get(portal_key, False):
                new_config[portal_key] = False
                changes.append(f"Disabled {portal_key}: {rec['reason']}")
        
        # Increase delays for rate-limited portals
        for rec in recommendations["delay_increase"]:
            domain = rec["domain"]
            portal_key = self._domain_to_portal_key(domain)
            if portal_key:
                old_delay = new_delays.get(portal_key, 3.0)
                new_delay = rec.get("suggested_delay", old_delay * 2)
                new_delays[portal_key] = new_delay
                changes.append(f"Increased {portal_key} delay: {old_delay}s → {new_delay}s")
        
        return {
            "config": new_config,
            "delays": new_delays,
            "changes": changes,
            "recommendations": recommendations
        }
    
    def _domain_to_portal_key(self, domain: str) -> str:
        """
        Map domain name to portal configuration key.
        
        Args:
            domain: Domain name (e.g., "kleinanzeigen.de")
        
        Returns:
            Portal key (e.g., "kleinanzeigen")
        """
        # Mapping of domain names to portal keys
        domain_mapping = {
            "kleinanzeigen.de": "kleinanzeigen",
            "markt.de": "markt_de",
            "quoka.de": "quoka",
            "kalaydo.de": "kalaydo",
            "meinestadt.de": "meinestadt",
            "dhd24.com": "dhd24",
            "freelancermap.de": "freelancermap",
            "freelance.de": "freelance_de",
        }
        
        return domain_mapping.get(domain, None)
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get human-readable optimization suggestions.
        
        Returns:
            List of suggestions with priority and description
        """
        recommendations = self.learning_engine.optimize_portal_config()
        suggestions = []
        
        # High priority: Disable useless portals
        for rec in recommendations["disable"]:
            suggestions.append({
                "priority": "HIGH",
                "type": "disable_portal",
                "portal": rec["domain"],
                "reason": rec["reason"],
                "action": f"Set DIRECT_CRAWL_SOURCES['{self._domain_to_portal_key(rec['domain'])}'] = False"
            })
        
        # Medium priority: Increase delays for rate-limited portals
        for rec in recommendations["delay_increase"]:
            portal_key = self._domain_to_portal_key(rec["domain"])
            suggestions.append({
                "priority": "MEDIUM",
                "type": "increase_delay",
                "portal": rec["domain"],
                "reason": rec["reason"],
                "action": f"Set PORTAL_DELAYS['{portal_key}'] = {rec.get('suggested_delay', 8.0)}"
            })
        
        # Low priority: Prioritize high performers
        for rec in recommendations["prioritize"]:
            suggestions.append({
                "priority": "LOW",
                "type": "prioritize",
                "portal": rec["domain"],
                "reason": f"High success rate: {rec['success_rate']:.1%}",
                "action": f"Focus more resources on {rec['domain']}"
            })
        
        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        suggestions.sort(key=lambda x: priority_order[x["priority"]])
        
        return suggestions
    
    def get_portal_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive portal health report.
        
        Returns:
            Health report with scores and recommendations
        """
        con = sqlite3.connect(self.learning_engine.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        try:
            # Get all portal stats
            cur.execute("""
                SELECT domain, success_rate, total_requests, 
                       successful_requests, rate_limit_detected, enabled
                FROM domain_performance
                ORDER BY success_rate DESC
            """)
            
            portals = []
            health_score = 0
            total_portals = 0
            
            for row in cur.fetchall():
                portal_info = {
                    "domain": row["domain"],
                    "health": "unknown",
                    "success_rate": row["success_rate"],
                    "total_requests": row["total_requests"],
                    "successful_requests": row["successful_requests"],
                    "rate_limited": bool(row["rate_limit_detected"]),
                    "enabled": bool(row.get("enabled", 1))
                }
                
                # Determine health
                if row["success_rate"] >= 0.2:
                    portal_info["health"] = "excellent"
                    health_score += 100
                elif row["success_rate"] >= 0.1:
                    portal_info["health"] = "good"
                    health_score += 70
                elif row["success_rate"] >= 0.05:
                    portal_info["health"] = "fair"
                    health_score += 40
                elif row["success_rate"] >= 0.01:
                    portal_info["health"] = "poor"
                    health_score += 20
                else:
                    portal_info["health"] = "critical"
                    health_score += 0
                
                portals.append(portal_info)
                total_portals += 1
            
            avg_health = health_score / total_portals if total_portals > 0 else 0
            
            return {
                "overall_health": round(avg_health, 1),
                "health_grade": self._health_to_grade(avg_health),
                "portals": portals,
                "total_portals": total_portals,
                "recommendations": self.get_optimization_suggestions()
            }
        finally:
            con.close()
    
    def _health_to_grade(self, health_score: float) -> str:
        """Convert health score to letter grade."""
        if health_score >= 90:
            return "A"
        elif health_score >= 80:
            return "B"
        elif health_score >= 70:
            return "C"
        elif health_score >= 60:
            return "D"
        else:
            return "F"


def get_portal_optimizer(db_path: str) -> PortalOptimizer:
    """
    Get a portal optimizer instance.
    
    Args:
        db_path: Path to database
    
    Returns:
        PortalOptimizer instance
    """
    learning_engine = LearningEngine(db_path)
    return PortalOptimizer(learning_engine)
