# -*- coding: utf-8 -*-
"""
Perplexity Learning Engine

This module tracks and learns from Perplexity search results to optimize future queries.

Features:
- Records successful queries and their results
- Analyzes which sources provide the best leads
- Generates optimized queries based on historical success
- Provides learning reports for analysis

Usage:
    from perplexity_learning import PerplexityLearning
    
    pplx = PerplexityLearning()
    pplx.record_perplexity_result(query, citations, leads)
    best_sources = pplx.get_best_sources()
    optimized_queries = pplx.generate_optimized_queries(["vertrieb", "sales"])
"""

import sqlite3
import json
import re
from datetime import datetime
from typing import List, Dict, Optional


class PerplexityLearning:
    """
    Learning engine for Perplexity search optimization.
    
    Tracks:
    - Query success rates
    - Source domain performance
    - Optimal query patterns
    """
    
    def __init__(self, db_path: str = "scraper.db"):
        """
        Initialize the learning engine.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Create learning tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS perplexity_queries (
                id INTEGER PRIMARY KEY,
                query TEXT,
                citations_count INTEGER,
                leads_found INTEGER,
                leads_with_phone INTEGER,
                success_rate REAL,
                timestamp TEXT,
                citations_json TEXT
            );
            
            CREATE TABLE IF NOT EXISTS perplexity_sources (
                id INTEGER PRIMARY KEY,
                domain TEXT UNIQUE,
                total_leads INTEGER DEFAULT 0,
                leads_with_phone INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                last_success TEXT,
                query_patterns TEXT
            );
            
            CREATE TABLE IF NOT EXISTS learned_query_patterns (
                id INTEGER PRIMARY KEY,
                pattern TEXT,
                success_count INTEGER DEFAULT 0,
                avg_leads REAL DEFAULT 0,
                best_sources TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_pplx_queries_timestamp 
                ON perplexity_queries(timestamp);
            CREATE INDEX IF NOT EXISTS idx_pplx_sources_success 
                ON perplexity_sources(success_rate DESC);
        """)
        conn.commit()
        conn.close()
    
    def record_perplexity_result(self, query: str, citations: List[str], leads: List[Dict]):
        """
        Record a Perplexity search result for analysis.
        
        Args:
            query: Search query used
            citations: List of citation URLs
            leads: List of leads found from this query
        """
        conn = sqlite3.connect(self.db_path)
        
        leads_with_phone = sum(1 for l in leads if l.get("telefon"))
        success_rate = leads_with_phone / len(leads) if leads else 0
        
        conn.execute("""
            INSERT INTO perplexity_queries 
            (query, citations_count, leads_found, leads_with_phone, success_rate, timestamp, citations_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (query, len(citations), len(leads), leads_with_phone, success_rate, 
              datetime.now().isoformat(), json.dumps(citations)))
        
        # Update source statistics
        for citation in citations:
            domain = self._extract_domain(citation)
            if domain:
                self._update_source_stats(conn, domain, leads)
        
        conn.commit()
        conn.close()
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name or empty string
        """
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else ""
    
    def _update_source_stats(self, conn, domain: str, leads: List[Dict]):
        """
        Update statistics for a source domain.
        
        Args:
            conn: Database connection
            domain: Domain name
            leads: Leads associated with this domain
        """
        # Find leads from this domain
        leads_from_domain = [l for l in leads if domain in l.get("quelle", "")]
        if not leads_from_domain:
            return
        
        with_phone = sum(1 for l in leads_from_domain if l.get("telefon"))
        success_rate = with_phone / len(leads_from_domain) if leads_from_domain else 0
        
        conn.execute("""
            INSERT INTO perplexity_sources (domain, total_leads, leads_with_phone, success_rate, last_success)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                total_leads = total_leads + excluded.total_leads,
                leads_with_phone = leads_with_phone + excluded.leads_with_phone,
                success_rate = (leads_with_phone + excluded.leads_with_phone) * 1.0 / 
                               (total_leads + excluded.total_leads),
                last_success = excluded.last_success
        """, (domain, len(leads_from_domain), with_phone, success_rate,
              datetime.now().isoformat()))
    
    def get_best_sources(self, min_leads: int = 5) -> List[Dict]:
        """
        Get the most successful source domains.
        
        Args:
            min_leads: Minimum number of leads to consider a source
            
        Returns:
            List of dicts with domain stats, sorted by success rate
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("""
            SELECT domain, total_leads, leads_with_phone, success_rate
            FROM perplexity_sources
            WHERE total_leads >= ?
            ORDER BY success_rate DESC, total_leads DESC
            LIMIT 20
        """, (min_leads,))
        
        results = [
            {"domain": r[0], "total": r[1], "with_phone": r[2], "success_rate": r[3]}
            for r in cur.fetchall()
        ]
        conn.close()
        return results
    
    def generate_optimized_queries(self, base_keywords: List[str]) -> List[str]:
        """
        Generate optimized search queries based on learning.
        
        Combines base keywords with successful source domains to create
        targeted queries.
        
        Args:
            base_keywords: Keywords to combine with sources
            
        Returns:
            List of optimized query strings
        """
        best_sources = self.get_best_sources(min_leads=3)
        
        queries = []
        for source in best_sources[:10]:  # Top 10 sources
            domain = source["domain"]
            for keyword in base_keywords:
                queries.append(f'site:{domain} "{keyword}" telefon')
                queries.append(f'site:{domain} "{keyword}" kontakt mobil')
        
        return queries
    
    def get_learning_report(self) -> Dict:
        """
        Generate a comprehensive learning report.
        
        Returns:
            Dict with learning statistics and insights
        """
        conn = sqlite3.connect(self.db_path)
        
        report = {
            "best_sources": self.get_best_sources(),
            "total_queries": conn.execute("SELECT COUNT(*) FROM perplexity_queries").fetchone()[0],
            "avg_success_rate": 0,
            "top_patterns": []
        }
        
        # Calculate average success rate
        result = conn.execute(
            "SELECT AVG(success_rate) FROM perplexity_queries WHERE leads_found > 0"
        ).fetchone()
        report["avg_success_rate"] = result[0] if result[0] else 0
        
        # Get top query patterns
        cur = conn.execute("""
            SELECT query, success_rate, leads_with_phone
            FROM perplexity_queries
            WHERE leads_with_phone > 0
            ORDER BY success_rate DESC, leads_with_phone DESC
            LIMIT 10
        """)
        report["top_patterns"] = [
            {"query": r[0][:80], "success_rate": r[1], "leads": r[2]}
            for r in cur.fetchall()
        ]
        
        conn.close()
        return report
    
    def get_query_stats(self) -> Dict:
        """
        Get summary statistics for all queries.
        
        Returns:
            Dict with query statistics
        """
        conn = sqlite3.connect(self.db_path)
        
        stats = {
            "total": 0,
            "with_results": 0,
            "avg_leads_per_query": 0,
            "total_leads": 0,
        }
        
        cur = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN leads_found > 0 THEN 1 ELSE 0 END) as with_results,
                AVG(leads_found) as avg_leads,
                SUM(leads_found) as total_leads
            FROM perplexity_queries
        """)
        
        row = cur.fetchone()
        if row:
            stats["total"] = row[0]
            stats["with_results"] = row[1]
            stats["avg_leads_per_query"] = row[2] if row[2] else 0
            stats["total_leads"] = row[3] if row[3] else 0
        
        conn.close()
        return stats


if __name__ == "__main__":
    # Demo/test mode
    print("Perplexity Learning Engine")
    print("=" * 50)
    
    pplx = PerplexityLearning()
    
    # Get stats
    stats = pplx.get_query_stats()
    print(f"Total queries tracked: {stats['total']}")
    print(f"Queries with results: {stats['with_results']}")
    print(f"Average leads per query: {stats['avg_leads_per_query']:.2f}")
    
    # Get best sources
    best_sources = pplx.get_best_sources(min_leads=1)
    if best_sources:
        print("\nTop performing sources:")
        for i, source in enumerate(best_sources[:5], 1):
            print(f"{i}. {source['domain']}: {source['with_phone']}/{source['total']} "
                  f"({source['success_rate']*100:.1f}% success)")
    else:
        print("\nNo sources tracked yet.")
    
    # Generate optimized queries
    optimized = pplx.generate_optimized_queries(["vertrieb", "sales"])
    if optimized:
        print(f"\nGenerated {len(optimized)} optimized queries")
        print("Sample queries:")
        for query in optimized[:3]:
            print(f"  - {query}")
