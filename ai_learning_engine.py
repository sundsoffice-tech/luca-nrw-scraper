# -*- coding: utf-8 -*-
"""
Aktives Self-Learning System für Lead-Extraktion.
Lernt aus Erfolgen und Fehlern, optimiert sich automatisch.
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


class ActiveLearningEngine:
    """
    Selbstlernendes System das:
    - Portal-Performance trackt und schlechte Portale deaktiviert
    - Erfolgreiche Dorks priorisiert
    - Neue Telefon-Patterns automatisch lernt
    - Host-Backoff bei Fehlern verwaltet
    """
    
    def __init__(self, db_path: str = "scraper.db"):
        self.db_path = db_path
        self._init_learning_tables()
        self._load_learned_patterns()
    
    def _init_learning_tables(self):
        """Erstellt Learning-Tabellen falls nicht vorhanden"""
        with sqlite3.connect(self.db_path) as conn:
            # Portal Performance Tracking
            conn.execute('''CREATE TABLE IF NOT EXISTS learning_portal_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                portal TEXT NOT NULL,
                urls_crawled INTEGER DEFAULT 0,
                leads_found INTEGER DEFAULT 0,
                leads_with_phone INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                errors INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0.0
            )''')
            
            # Dork Performance Tracking
            conn.execute('''CREATE TABLE IF NOT EXISTS learning_dork_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dork TEXT UNIQUE NOT NULL,
                times_used INTEGER DEFAULT 0,
                total_results INTEGER DEFAULT 0,
                leads_found INTEGER DEFAULT 0,
                leads_with_phone INTEGER DEFAULT 0,
                score REAL DEFAULT 0.0,
                pool TEXT DEFAULT 'explore',
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Gelernte Telefon-Patterns
            conn.execute('''CREATE TABLE IF NOT EXISTS learning_phone_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE NOT NULL,
                regex TEXT NOT NULL,
                times_matched INTEGER DEFAULT 0,
                source_portal TEXT,
                example_raw TEXT,
                example_normalized TEXT,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Host Backoff (für Rate-Limits etc.)
            conn.execute('''CREATE TABLE IF NOT EXISTS learning_host_backoff (
                host TEXT PRIMARY KEY,
                failures INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                last_failure TEXT,
                backoff_until TEXT,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Portal Config (gelernte Einstellungen)
            conn.execute('''CREATE TABLE IF NOT EXISTS learning_portal_config (
                portal TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 5,
                delay_seconds REAL DEFAULT 2.0,
                disabled_reason TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            conn.commit()
    
    def _load_learned_patterns(self):
        """Lädt gelernte Patterns beim Start"""
        self.learned_phone_patterns = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT regex FROM learning_phone_patterns 
                    WHERE times_matched >= 2
                    ORDER BY times_matched DESC
                ''')
                self.learned_phone_patterns = [row[0] for row in cursor.fetchall()]
        except Exception:
            pass
    
    # ==================== PORTAL LEARNING ====================
    
    def record_portal_result(self, portal: str, urls_crawled: int, 
                            leads_found: int, leads_with_phone: int,
                            errors: int = 0, run_id: int = 0):
        """Speichert Portal-Ergebnis für Lernen"""
        success_rate = leads_with_phone / max(1, urls_crawled)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO learning_portal_metrics 
                (run_id, portal, urls_crawled, leads_found, leads_with_phone, success_rate, errors)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (run_id, portal, urls_crawled, leads_found, leads_with_phone, success_rate, errors))
            conn.commit()
        
        # Automatisch deaktivieren wenn dauerhaft erfolglos
        self._evaluate_portal(portal)
    
    def _evaluate_portal(self, portal: str):
        """Bewertet Portal und deaktiviert bei schlechter Performance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT AVG(success_rate), SUM(leads_with_phone), COUNT(*), SUM(errors)
                FROM learning_portal_metrics 
                WHERE portal = ? 
                AND timestamp > datetime('now', '-7 days')
            ''', (portal,))
            row = cursor.fetchone()
            
            if row and row[2] >= 3:  # Mindestens 3 Runs
                avg_success, total_leads, runs, total_errors = row
                
                # Deaktivieren wenn: 0% Erfolg ODER >50% Fehler
                if avg_success < 0.01 or (total_errors and total_errors / runs > 0.5):
                    reason = "0% Erfolgsrate" if avg_success < 0.01 else "Zu viele Fehler"
                    conn.execute('''
                        INSERT OR REPLACE INTO learning_portal_config 
                        (portal, enabled, disabled_reason, last_updated)
                        VALUES (?, 0, ?, datetime('now'))
                    ''', (portal, reason))
                    conn.commit()
    
    def should_skip_portal(self, portal: str) -> Tuple[bool, str]:
        """Prüft ob Portal übersprungen werden soll"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT enabled, disabled_reason FROM learning_portal_config 
                WHERE portal = ?
            ''', (portal,))
            row = cursor.fetchone()
            
            if row and row[0] == 0:
                return True, row[1] or "Deaktiviert durch Learning"
        
        return False, ""
    
    def get_portal_stats(self) -> Dict:
        """Gibt Portal-Statistiken zurück"""
        stats = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT portal, 
                       AVG(success_rate) as avg_success,
                       SUM(leads_with_phone) as total_leads,
                       COUNT(*) as runs
                FROM learning_portal_metrics 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY portal
                ORDER BY avg_success DESC
            ''')
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'avg_success': round(row[1] * 100, 1),
                    'total_leads': row[2],
                    'runs': row[3]
                }
        return stats
    
    # ==================== DORK LEARNING ====================
    
    def record_dork_result(self, dork: str, results: int, 
                          leads_found: int, leads_with_phone: int):
        """Speichert Dork-Ergebnis für Lernen"""
        score = leads_with_phone / max(1, results) if results > 0 else 0
        pool = 'core' if leads_with_phone > 0 else 'explore'
        
        with sqlite3.connect(self.db_path) as conn:
            # Upsert
            conn.execute('''
                INSERT INTO learning_dork_performance 
                (dork, times_used, total_results, leads_found, leads_with_phone, score, pool, last_used)
                VALUES (?, 1, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(dork) DO UPDATE SET
                    times_used = times_used + 1,
                    total_results = total_results + excluded.total_results,
                    leads_found = leads_found + excluded.leads_found,
                    leads_with_phone = leads_with_phone + excluded.leads_with_phone,
                    score = (leads_with_phone + excluded.leads_with_phone) * 1.0 / 
                            MAX(1, total_results + excluded.total_results),
                    pool = CASE WHEN leads_with_phone + excluded.leads_with_phone > 0 
                           THEN 'core' ELSE pool END,
                    last_used = datetime('now')
            ''', (dork, results, leads_found, leads_with_phone, score, pool))
            conn.commit()
    
    def get_best_dorks(self, n: int = 10, include_explore: bool = True) -> List[str]:
        """Gibt die besten Dorks zurück"""
        with sqlite3.connect(self.db_path) as conn:
            # Core Dorks (bewährt)
            cursor = conn.execute('''
                SELECT dork FROM learning_dork_performance 
                WHERE pool = 'core' AND times_used >= 2
                ORDER BY score DESC, leads_with_phone DESC
                LIMIT ?
            ''', (n - 2 if include_explore else n,))
            core_dorks = [row[0] for row in cursor.fetchall()]
            
            if include_explore:
                # 2 Explore Dorks (zum Testen)
                cursor = conn.execute('''
                    SELECT dork FROM learning_dork_performance 
                    WHERE pool = 'explore' 
                    AND (times_used < 3 OR last_used < datetime('now', '-3 days'))
                    ORDER BY RANDOM()
                    LIMIT 2
                ''')
                explore_dorks = [row[0] for row in cursor.fetchall()]
                return core_dorks + explore_dorks
            
            return core_dorks
    
    # ==================== PHONE PATTERN LEARNING ====================
    
    def learn_phone_pattern(self, raw_phone: str, normalized: str, portal: str):
        """Lernt neues Telefon-Pattern aus erfolgreichem Match"""
        # Generiere Regex-Pattern aus raw_phone
        pattern_key = self._generate_pattern_key(raw_phone)
        regex = self._generate_regex(raw_phone)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO learning_phone_patterns 
                (pattern, regex, times_matched, source_portal, example_raw, example_normalized)
                VALUES (?, ?, 1, ?, ?, ?)
                ON CONFLICT(pattern) DO UPDATE SET
                    times_matched = times_matched + 1,
                    source_portal = excluded.source_portal
            ''', (pattern_key, regex, portal, raw_phone, normalized))
            conn.commit()
        
        # Pattern zur Runtime-Liste hinzufügen
        if regex not in self.learned_phone_patterns:
            self.learned_phone_patterns.append(regex)
    
    def _generate_pattern_key(self, raw: str) -> str:
        """
        Generiert Pattern-Key (z.B. '0XXX-XXXXXXX')
        Konvertiert Ziffern zu 'X' und behält nur Separatoren ( -/.())
        Andere Zeichen (inkl. '+') werden herausgefiltert
        """
        result = []
        for c in raw:
            if c.isdigit():
                result.append('X')
            elif c in ' -/.()':
                result.append(c)
            # Andere Zeichen werden ignoriert (z.B. '+')
        return ''.join(result)
    
    def _generate_regex(self, raw: str) -> str:
        """
        Generiert Regex aus Beispiel-Nummer
        Ersetzt alle Ziffern durch \\d, behält Separatoren
        """
        # Escape special regex characters
        pattern = re.escape(raw)
        # Replace escaped digits with \d pattern
        pattern = re.sub(r'\\\d', r'\\d', pattern)
        return pattern
    
    def get_learned_phone_patterns(self) -> List[str]:
        """Gibt gelernte Phone-Patterns zurück"""
        return self.learned_phone_patterns
    
    # ==================== HOST BACKOFF ====================
    
    def record_host_failure(self, host: str, reason: str = "error"):
        """Speichert Host-Fehler"""
        backoff_minutes = 30  # Standard: 30 Minuten Backoff
        
        if reason == "429":
            backoff_minutes = 90  # Rate-Limit: 90 Minuten
        elif reason == "blocked":
            backoff_minutes = 1440  # Blockiert: 24 Stunden
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO learning_host_backoff 
                (host, failures, total_requests, last_failure, backoff_until, reason)
                VALUES (?, 1, 1, datetime('now'), datetime('now', '+' || ? || ' minutes'), ?)
                ON CONFLICT(host) DO UPDATE SET
                    failures = failures + 1,
                    total_requests = total_requests + 1,
                    last_failure = datetime('now'),
                    backoff_until = datetime('now', '+' || ? || ' minutes'),
                    reason = excluded.reason
            ''', (host, backoff_minutes, reason, backoff_minutes))
            conn.commit()
    
    def is_host_backed_off(self, host: str) -> Tuple[bool, str]:
        """Prüft ob Host im Backoff ist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT backoff_until, reason FROM learning_host_backoff 
                WHERE host = ? AND backoff_until > datetime('now')
            ''', (host,))
            row = cursor.fetchone()
            
            if row:
                return True, f"Backoff bis {row[0]} ({row[1]})"
        
        return False, ""
    
    # ==================== SUMMARY & REPORTING ====================
    
    def get_learning_summary(self) -> Dict:
        """Gibt Zusammenfassung des Lernens zurück"""
        return {
            'portal_stats': self.get_portal_stats(),
            'best_dorks': self.get_best_dorks(5),
            'learned_patterns': len(self.learned_phone_patterns),
            'disabled_portals': self._get_disabled_portals()
        }
    
    def _get_disabled_portals(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT portal, disabled_reason FROM learning_portal_config 
                WHERE enabled = 0
            ''')
            return [f"{row[0]} ({row[1]})" for row in cursor.fetchall()]
