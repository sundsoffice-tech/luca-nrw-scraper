# -*- coding: utf-8 -*-
"""
Costs API - Provides API cost metrics for the dashboard
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List


def get_costs(db_path: str) -> Dict[str, Any]:
    """
    Get API cost breakdown.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dictionary containing cost data for various time periods
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        return {
            'today': get_daily_costs(cur, days=1),
            'week': get_daily_costs(cur, days=7),
            'month': get_daily_costs(cur, days=30),
            'by_provider': get_costs_by_provider(cur),
            'by_endpoint': get_costs_by_endpoint(cur)
        }
    finally:
        con.close()


def get_daily_costs(cur: sqlite3.Cursor, days: int = 7) -> List[Dict[str, Any]]:
    """
    Get daily cost breakdown for the last N days.
    
    Args:
        cur: SQLite cursor
        days: Number of days to retrieve
        
    Returns:
        List of daily cost records
    """
    cur.execute("""
        SELECT 
            DATE(timestamp) as date,
            provider,
            SUM(tokens_input) as tokens_in,
            SUM(tokens_output) as tokens_out,
            SUM(cost_eur) as cost
        FROM api_costs
        WHERE DATE(timestamp) >= DATE('now', ? || ' days')
        GROUP BY DATE(timestamp), provider
        ORDER BY date DESC, provider
    """, (f'-{days}',))
    
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_costs_by_provider(cur: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """
    Get cost breakdown by provider.
    
    Args:
        cur: SQLite cursor
        
    Returns:
        List of provider cost records
    """
    cur.execute("""
        SELECT 
            provider,
            SUM(tokens_input) as tokens_in,
            SUM(tokens_output) as tokens_out,
            SUM(cost_eur) as cost,
            COUNT(*) as call_count
        FROM api_costs
        GROUP BY provider
        ORDER BY cost DESC
    """)
    
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_costs_by_endpoint(cur: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """
    Get cost breakdown by endpoint.
    
    Args:
        cur: SQLite cursor
        
    Returns:
        List of endpoint cost records
    """
    cur.execute("""
        SELECT 
            endpoint,
            provider,
            SUM(tokens_input) as tokens_in,
            SUM(tokens_output) as tokens_out,
            SUM(cost_eur) as cost,
            COUNT(*) as call_count
        FROM api_costs
        WHERE endpoint IS NOT NULL
        GROUP BY endpoint, provider
        ORDER BY cost DESC
        LIMIT 20
    """)
    
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_cost_chart_data(db_path: str, days: int = 7) -> Dict[str, Any]:
    """
    Get cost data formatted for charts.
    
    Args:
        db_path: Path to SQLite database
        days: Number of days to retrieve
        
    Returns:
        Dictionary with labels and datasets for Chart.js
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        # Get all dates in range
        cur.execute("""
            SELECT DISTINCT DATE(timestamp) as date
            FROM api_costs
            WHERE DATE(timestamp) >= DATE('now', ? || ' days')
            ORDER BY date ASC
        """, (f'-{days}',))
        
        dates = [row['date'] for row in cur.fetchall()]
        
        # Get providers
        cur.execute("SELECT DISTINCT provider FROM api_costs")
        providers = [row['provider'] for row in cur.fetchall()]
        
        # Build datasets
        datasets = []
        colors = {
            'openai': 'rgb(75, 192, 192)',
            'google_cse': 'rgb(255, 159, 64)',
            'bing': 'rgb(153, 102, 255)'
        }
        
        for provider in providers:
            cur.execute("""
                SELECT DATE(timestamp) as date, SUM(cost_eur) as cost
                FROM api_costs
                WHERE provider = ? AND DATE(timestamp) >= DATE('now', ? || ' days')
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """, (provider, f'-{days}'))
            
            cost_map = {row['date']: row['cost'] for row in cur.fetchall()}
            data = [cost_map.get(date, 0) for date in dates]
            
            datasets.append({
                'label': provider,
                'data': data,
                'borderColor': colors.get(provider, 'rgb(201, 203, 207)'),
                'backgroundColor': colors.get(provider, 'rgba(201, 203, 207, 0.2)')
            })
        
        return {
            'labels': dates,
            'datasets': datasets
        }
    finally:
        con.close()
