#!/usr/bin/env python3
"""
Learning Dashboard - Zeigt den Status des Self-Learning Systems
Aufruf: python dashboard.py
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = "scraper.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def print_header():
    print("=" * 65)
    print("           🧠 SELF-LEARNING DASHBOARD")
    print("           " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 65)

def show_leads_stats():
    print("\n📈 LEADS ÜBERSICHT")
    print("-" * 65)
    try:
        conn = get_connection()
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        with_phone = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE telefon != '' AND telefon IS NOT NULL"
        ).fetchone()[0]
        pct = round(with_phone / max(1, total) * 100)
        print(f"  Total: {total} Leads")
        print(f"  Mit Telefon: {with_phone} ({pct}%)")
        
        # Letzte 5 Leads
        print("\n  Letzte 5 Leads:")
        for row in conn.execute(
            "SELECT name, telefon, quelle FROM leads ORDER BY id DESC LIMIT 5"
        ):
            name = (row[0] or "?")[:25]
            phone = row[1] or "-"
            print(f"    • {name}: {phone}")
        conn.close()
    except Exception as e:
        print(f"  Fehler: {e}")

def show_portal_performance():
    print("\n🏢 PORTAL PERFORMANCE (Learning)")
    print("-" * 65)
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT portal, 
                   SUM(leads_with_phone) as total_leads,
                   ROUND(AVG(success_rate) * 100, 1) as avg_success,
                   COUNT(*) as runs,
                   SUM(urls_crawled) as total_urls
            FROM learning_portal_metrics 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY portal 
            ORDER BY avg_success DESC
        """).fetchall()
        
        if rows:
            print(f"  {'Portal':<20} {'Leads':>6} {'Erfolg':>8} {'Runs':>6} {'URLs':>8}")
            print(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*6} {'-'*8}")
            for row in rows:
                portal = row[0][:20] if row[0] else "?"
                leads = row[1] or 0
                success = row[2] or 0
                runs = row[3] or 0
                urls = row[4] or 0
                status = "✅" if success > 1 else "❌"
                print(f"  {status} {portal:<18} {leads:>6} {success:>7}% {runs:>6} {urls:>8}")
        else:
            print("  Noch keine Portal-Daten (starte Scraper mit Learning)")
        conn.close()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("  ⚠️  Learning-Tabellen existieren noch nicht")
            print("  → Starte: python scriptname.py --once --industry candidates")
        else:
            print(f"  Fehler: {e}")

def show_top_dorks():
    print("\n🔍 TOP DORKS (erfolgreichste Suchanfragen)")
    print("-" * 65)
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT dork, leads_with_phone, pool, 
                   ROUND(score * 100, 1) as score_pct,
                   times_used
            FROM learning_dork_performance 
            WHERE leads_with_phone > 0 
            ORDER BY leads_with_phone DESC, score DESC 
            LIMIT 5
        """).fetchall()
        
        if rows:
            for i, row in enumerate(rows, 1):
                dork = (row[0] or "?")[:50]
                leads = row[1] or 0
                pool = (row[2] or "?")[:4]
                score = row[3] or 0
                used = row[4] or 0
                print(f"  {i}. [{pool}] {leads} Leads ({score}%, {used}x)")
                print(f"     {dork}...")
        else:
            print("  Noch keine erfolgreichen Dorks")
        conn.close()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("  ⚠️  Learning-Tabellen existieren noch nicht")
        else:
            print(f"  Fehler: {e}")

def show_phone_patterns():
    print("\n📞 GELERNTE TELEFON-PATTERNS")
    print("-" * 65)
    try:
        conn = get_connection()
        count = conn.execute(
            "SELECT COUNT(*) FROM learning_phone_patterns"
        ).fetchone()[0]
        print(f"  {count} Patterns gelernt")
        
        if count > 0:
            print("\n  Top 5 Patterns:")
            for row in conn.execute("""
                SELECT pattern, times_matched, source_portal 
                FROM learning_phone_patterns 
                ORDER BY times_matched DESC 
                LIMIT 5
            """):
                pattern = (row[0] or "?")[:30]
                matches = row[1] or 0
                portal = (row[2] or "?")[:15]
                print(f"    {matches:>4}x: {pattern} (von {portal})")
        conn.close()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("  ⚠️  Learning-Tabellen existieren noch nicht")
        else:
            print(f"  Fehler: {e}")

def show_host_backoff():
    print("\n🚫 HOST BACKOFF (blockierte Hosts)")
    print("-" * 65)
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT host, failures, reason, backoff_until 
            FROM learning_host_backoff 
            WHERE backoff_until > datetime('now')
            ORDER BY failures DESC
            LIMIT 5
        """).fetchall()
        
        if rows:
            for row in rows:
                host = (row[0] or "?")[:35]
                failures = row[1] or 0
                reason = (row[2] or "?")[:15]
                until = row[3] or "?"
                print(f"  ⏸️  {host}")
                print(f"      {failures} Fehler ({reason}) bis {until}")
        else:
            print("  ✅ Keine Hosts blockiert")
        conn.close()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("  ⚠️  Learning-Tabellen existieren noch nicht")
        else:
            print(f"  Fehler: {e}")

def show_disabled_portals():
    print("\n🔴 DEAKTIVIERTE PORTALE (durch Learning)")
    print("-" * 65)
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT portal, disabled_reason, last_updated 
            FROM learning_portal_config 
            WHERE enabled = 0
        """).fetchall()
        
        if rows:
            for row in rows:
                portal = row[0] or "?"
                reason = row[1] or "Unbekannt"
                updated = row[2] or "?"
                print(f"  ❌ {portal}: {reason}")
                print(f"     (seit {updated})")
        else:
            print("  ✅ Alle Portale aktiv")
        conn.close()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("  Portale werden automatisch deaktiviert wenn Learning aktiv ist")
        else:
            print(f"  Fehler: {e}")

def show_run_history():
    print("\n📊 LETZTE RUNS")
    print("-" * 65)
    try:
        conn = get_connection()
        # Versuche aus learning_portal_metrics die letzten Runs zu bekommen
        rows = conn.execute("""
            SELECT DATE(timestamp) as date, 
                   COUNT(DISTINCT run_id) as runs,
                   SUM(leads_with_phone) as leads
            FROM learning_portal_metrics
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 5
        """).fetchall()
        
        if rows:
            print(f"  {'Datum':<12} {'Runs':>6} {'Leads':>8}")
            print(f"  {'-'*12} {'-'*6} {'-'*8}")
            for row in rows:
                date = row[0] or "?"
                runs = row[1] or 0
                leads = row[2] or 0
                print(f"  {date:<12} {runs:>6} {leads:>8}")
        else:
            print("  Noch keine Run-Historie")
        conn.close()
    except sqlite3.OperationalError:
        print("  Noch keine Run-Historie")

def main():
    print_header()
    show_leads_stats()
    show_portal_performance()
    show_top_dorks()
    show_phone_patterns()
    show_host_backoff()
    show_disabled_portals()
    show_run_history()
    print("\n" + "=" * 65)
    print("  Tipp: Starte mit 'python dashboard.py' jederzeit neu")
    print("  Live: while($true) { cls; python dashboard.py; Start-Sleep 30 }")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
