# -*- coding: utf-8 -*-
"""
Stats API - Provides KPI metrics for the dashboard
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def get_stats(db_path: str) -> Dict[str, Any]:
    """
    Get dashboard statistics/KPIs.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dictionary containing KPI metrics
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        # Leads total
        cur.execute("SELECT COUNT(*) as count FROM leads")
        leads_total = cur.fetchone()['count']
        
        # Leads with mobile phone
        cur.execute("""
            SELECT COUNT(*) as count FROM leads 
            WHERE telefon IS NOT NULL AND telefon != ''
        """)
        leads_with_mobile = cur.fetchone()['count']
        
        # Success rate
        success_rate = (leads_with_mobile / leads_total * 100) if leads_total > 0 else 0.0
        
        # Leads today
        cur.execute("""
            SELECT COUNT(*) as count FROM leads 
            WHERE DATE(last_updated) = DATE('now')
        """)
        leads_today = cur.fetchone()['count']
        
        # API costs today
        cur.execute("""
            SELECT COALESCE(SUM(cost_eur), 0.0) as cost 
            FROM api_costs 
            WHERE DATE(timestamp) = DATE('now')
        """)
        cost_today = cur.fetchone()['cost']
        
        # API costs total
        cur.execute("""
            SELECT COALESCE(SUM(cost_eur), 0.0) as cost 
            FROM api_costs
        """)
        cost_total = cur.fetchone()['cost']
        
        # Budget remaining
        cur.execute("""
            SELECT value FROM dashboard_settings 
            WHERE key = 'budget_limit_eur'
        """)
        budget_row = cur.fetchone()
        budget_limit = float(budget_row['value']) if budget_row else 1000.0
        
        # Get cost for current month
        cur.execute("""
            SELECT COALESCE(SUM(cost_eur), 0.0) as cost 
            FROM api_costs 
            WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
        """)
        cost_month = cur.fetchone()['cost']
        budget_remaining = budget_limit - cost_month
        
        # Total runs
        cur.execute("SELECT COUNT(*) as count FROM runs")
        runs_total = cur.fetchone()['count']
        
        # Last run info
        cur.execute("""
            SELECT id, started_at, finished_at, status, links_checked, leads_new 
            FROM runs 
            ORDER BY id DESC 
            LIMIT 1
        """)
        last_run_row = cur.fetchone()
        last_run = dict(last_run_row) if last_run_row else None
        
        return {
            'leads_total': leads_total,
            'leads_today': leads_today,
            'leads_with_mobile': leads_with_mobile,
            'success_rate': round(success_rate, 2),
            'cost_today_eur': round(cost_today, 4),
            'cost_total_eur': round(cost_total, 4),
            'cost_month_eur': round(cost_month, 4),
            'budget_limit_eur': budget_limit,
            'budget_remaining_eur': round(budget_remaining, 2),
            'runs_total': runs_total,
            'last_run': last_run
        }
    finally:
        con.close()


def get_leads_history(db_path: str, days: int = 7) -> Dict[str, Any]:
    """
    Get lead count history for the last N days.
    
    Args:
        db_path: Path to SQLite database
        days: Number of days to retrieve (default: 7)
        
    Returns:
        Dictionary with dates and lead counts
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute("""
            SELECT 
                DATE(last_updated) as date,
                COUNT(*) as count
            FROM leads
            WHERE last_updated IS NOT NULL 
                AND DATE(last_updated) >= DATE('now', ? || ' days')
            GROUP BY DATE(last_updated)
            ORDER BY date ASC
        """, (f'-{days}',))
        
        rows = cur.fetchall()
        
        return {
            'labels': [row['date'] for row in rows],
            'data': [row['count'] for row in rows]
        }
    finally:
        con.close()


def get_top_sources(db_path: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get top performing domains/sources.
    
    Args:
        db_path: Path to SQLite database
        limit: Maximum number of sources to return
        
    Returns:
        Dictionary with source names and counts
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        # Try to get from success_patterns table first
        cur.execute("""
            SELECT pattern_value as source, success_count as count
            FROM success_patterns
            WHERE pattern_type = 'domain'
            ORDER BY success_count DESC
            LIMIT ?
        """, (limit,))
        
        rows = cur.fetchall()
        
        if not rows:
            # Fallback: extract domain from quelle in leads table
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN quelle LIKE 'http%' THEN 
                            substr(quelle, instr(quelle, '://') + 3,
                                instr(substr(quelle, instr(quelle, '://') + 3), '/') - 1)
                        ELSE quelle
                    END as source,
                    COUNT(*) as count
                FROM leads
                WHERE quelle IS NOT NULL
                GROUP BY source
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
        
        return {
            'labels': [row['source'] if row['source'] else 'Unknown' for row in rows],
            'data': [row['count'] for row in rows]
        }
    finally:
        con.close()
