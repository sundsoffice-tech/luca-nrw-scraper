# -*- coding: utf-8 -*-
"""
Self-learning system for lead generation optimization.

This module tracks successful patterns (domains, query terms, URL paths, content signals)
and uses this data to optimize future searches and improve lead quality.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import urllib.parse
import re


class LearningEngine:
    """Self-learning engine that tracks and optimizes lead generation patterns."""
    
    def __init__(self, db_path: str):
        """Initialize the learning engine with database path."""
        self.db_path = db_path
        self._ensure_learning_tables()
    
    def _ensure_learning_tables(self) -> None:
        """Create success_patterns table and additional learning tables if they don't exist."""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # Success Patterns table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS success_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                last_success TIMESTAMP,
                confidence_score REAL DEFAULT 0.0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_value)
            )
        """)
        
        # Create indexes for faster queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_success_patterns_type_confidence 
            ON success_patterns(pattern_type, confidence_score DESC)
        """)
        
        # Domain Learning table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS learning_domains (
                domain TEXT PRIMARY KEY,
                total_visits INTEGER DEFAULT 0,
                successful_extractions INTEGER DEFAULT 0,
                leads_found INTEGER DEFAULT 0,
                avg_quality REAL DEFAULT 0.0,
                last_visit TIMESTAMP,
                score REAL DEFAULT 0.5
            )
        """)
        
        # Query Performance table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS learning_queries (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT,
                times_used INTEGER DEFAULT 0,
                leads_generated INTEGER DEFAULT 0,
                avg_leads_per_run REAL DEFAULT 0.0,
                last_used TIMESTAMP,
                effectiveness_score REAL DEFAULT 0.5
            )
        """)
        
        con.commit()
        con.close()
    
    def learn_from_success(self, lead_data: Dict[str, Any], query: str = "") -> None:
        """
        Learn from a successful lead (one with a mobile number).
        
        Tracks:
        - Domain of the lead source
        - Query terms that led to the lead
        - URL path patterns
        - Content signals that indicated quality
        
        Args:
            lead_data: Dictionary containing lead information (must have 'quelle' URL and 'telefon')
            query: The search query that led to this lead
        """
        source_url = lead_data.get("quelle", "")
        if not source_url:
            return
        
        # Extract domain
        try:
            parsed = urllib.parse.urlparse(source_url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Track domain success
            self._increment_pattern("domain", domain, lead_data)
            
            # Track URL path pattern
            path = parsed.path.lower()
            if path and path != "/":
                # Extract meaningful path segments
                path_segments = [seg for seg in path.split("/") if seg and len(seg) > 2]
                for segment in path_segments[:3]:  # Track first 3 segments
                    self._increment_pattern("url_path", segment, lead_data)
            
            # Track query terms
            if query:
                # Extract meaningful terms from query (ignore operators)
                query_terms = re.findall(r'\b[a-zäöüß]{4,}\b', query.lower())
                for term in set(query_terms):
                    if term not in {"site", "oder", "und", "mit", "von", "für", "bei"}:
                        self._increment_pattern("query_term", term, lead_data)
            
            # Track content signals from tags
            tags = lead_data.get("tags", "")
            if tags:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                for tag in tag_list:
                    if tag and len(tag) > 2:
                        self._increment_pattern("content_signal", tag.lower(), lead_data)
        
        except Exception as e:
            # Don't fail lead processing if learning fails
            pass
    
    def _increment_pattern(self, pattern_type: str, pattern_value: str, metadata: Dict[str, Any]) -> None:
        """Increment success count for a pattern and update confidence score."""
        if not pattern_value:
            return
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        # Convert metadata to JSON (store only essential info)
        meta_json = json.dumps({
            "last_lead_type": metadata.get("lead_type", ""),
            "last_tags": metadata.get("tags", "")[:200],  # Truncate
            "last_score": metadata.get("score", 0)
        })
        
        try:
            # Try to insert or update
            cur.execute("""
                INSERT INTO success_patterns 
                (pattern_type, pattern_value, success_count, last_success, metadata)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(pattern_type, pattern_value) DO UPDATE SET
                    success_count = success_count + 1,
                    last_success = ?,
                    metadata = ?
            """, (pattern_type, pattern_value, datetime.now(timezone.utc).isoformat(), 
                  meta_json, datetime.now(timezone.utc).isoformat(), meta_json))
            
            # Update confidence score
            cur.execute("""
                UPDATE success_patterns
                SET confidence_score = CAST(success_count AS REAL) / 
                                      (success_count + fail_count + 1.0)
                WHERE pattern_type = ? AND pattern_value = ?
            """, (pattern_type, pattern_value))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def increment_fail(self, pattern_type: str, pattern_value: str) -> None:
        """Increment fail count for a pattern (when URL doesn't yield a lead)."""
        if not pattern_value:
            return
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            cur.execute("""
                INSERT INTO success_patterns 
                (pattern_type, pattern_value, fail_count)
                VALUES (?, ?, 1)
                ON CONFLICT(pattern_type, pattern_value) DO UPDATE SET
                    fail_count = fail_count + 1
            """, (pattern_type, pattern_value))
            
            # Update confidence score
            cur.execute("""
                UPDATE success_patterns
                SET confidence_score = CAST(success_count AS REAL) / 
                                      (success_count + fail_count + 1.0)
                WHERE pattern_type = ? AND pattern_value = ?
            """, (pattern_type, pattern_value))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def get_top_patterns(self, pattern_type: str, min_confidence: float = 0.3, 
                         min_successes: int = 2, limit: int = 20) -> List[Tuple[str, float, int]]:
        """
        Get top performing patterns of a given type.
        
        Args:
            pattern_type: Type of pattern ('domain', 'query_term', 'url_path', 'content_signal')
            min_confidence: Minimum confidence score (0.0-1.0)
            min_successes: Minimum number of successes required
            limit: Maximum number of patterns to return
        
        Returns:
            List of tuples: (pattern_value, confidence_score, success_count)
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        try:
            cur.execute("""
                SELECT pattern_value, confidence_score, success_count
                FROM success_patterns
                WHERE pattern_type = ? 
                  AND confidence_score >= ?
                  AND success_count >= ?
                ORDER BY confidence_score DESC, success_count DESC
                LIMIT ?
            """, (pattern_type, min_confidence, min_successes, limit))
            
            results = [(row["pattern_value"], row["confidence_score"], row["success_count"]) 
                      for row in cur.fetchall()]
            return results
        finally:
            con.close()
    
    def generate_optimized_queries(self, base_queries: List[str], industry: str = "") -> List[str]:
        """
        Generate optimized queries based on learned patterns.
        
        Args:
            base_queries: Base queries to enhance
            industry: Industry context for query generation
        
        Returns:
            List of optimized queries combining learned patterns
        """
        optimized = []
        
        # Get top performing patterns
        top_domains = self.get_top_patterns("domain", min_confidence=0.4, min_successes=3, limit=5)
        top_terms = self.get_top_patterns("query_term", min_confidence=0.3, min_successes=2, limit=10)
        
        # Site-specific queries for successful domains
        for domain, confidence, count in top_domains:
            optimized.append(f'site:{domain} Vertrieb Kontakt Handy')
            optimized.append(f'site:{domain} Ansprechpartner Mobil')
        
        # Term-enhanced queries
        for term, confidence, count in top_terms[:5]:
            optimized.append(f'{term} Handynummer Ansprechpartner NRW')
            optimized.append(f'{term} Vertrieb Mobil Kontakt')
        
        # Combine with base queries
        optimized.extend(base_queries)
        
        return optimized
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about learned patterns."""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        try:
            stats = {}
            for pattern_type in ["domain", "query_term", "url_path", "content_signal"]:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_patterns,
                        SUM(success_count) as total_successes,
                        AVG(confidence_score) as avg_confidence,
                        MAX(confidence_score) as max_confidence
                    FROM success_patterns
                    WHERE pattern_type = ?
                """, (pattern_type,))
                
                row = cur.fetchone()
                stats[pattern_type] = {
                    "total_patterns": row["total_patterns"] or 0,
                    "total_successes": row["total_successes"] or 0,
                    "avg_confidence": round(row["avg_confidence"] or 0, 3),
                    "max_confidence": round(row["max_confidence"] or 0, 3)
                }
            
            return stats
        finally:
            con.close()
    
    def record_domain_success(self, domain: str, leads_found: int, quality: float = 0.5) -> None:
        """
        Update domain score after a successful crawl.
        
        Args:
            domain: Domain name
            leads_found: Number of leads found from this domain
            quality: Quality score (0.0-1.0)
        """
        if not domain:
            return
        
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            # Calculate initial score
            initial_score = min(1.0, 0.5 + (leads_found * 0.1))
            score_boost = leads_found * 0.1
            
            cur.execute("""
                INSERT INTO learning_domains 
                (domain, total_visits, successful_extractions, leads_found, avg_quality, last_visit, score)
                VALUES (?, 1, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    total_visits = total_visits + 1,
                    successful_extractions = successful_extractions + ?,
                    leads_found = leads_found + ?,
                    avg_quality = (avg_quality * (total_visits - 1) + ?) / total_visits,
                    last_visit = CURRENT_TIMESTAMP,
                    score = MIN(1.0, score + ?)
            """, (
                domain, 
                1 if leads_found > 0 else 0, 
                leads_found, 
                quality, 
                initial_score,
                1 if leads_found > 0 else 0,
                leads_found,
                quality,
                score_boost
            ))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def record_query_performance(self, query: str, leads_found: int) -> None:
        """
        Record query performance for optimization.
        
        Args:
            query: The search query
            leads_found: Number of leads generated by this query
        """
        if not query:
            return
        
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            # Calculate initial effectiveness score
            initial_effectiveness = min(1.0, leads_found * 0.2)
            
            cur.execute("""
                INSERT INTO learning_queries 
                (query_hash, query_text, times_used, leads_generated, last_used, effectiveness_score)
                VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(query_hash) DO UPDATE SET
                    times_used = times_used + 1,
                    leads_generated = leads_generated + ?,
                    avg_leads_per_run = CAST(leads_generated + ? AS REAL) / (times_used + 1),
                    last_used = CURRENT_TIMESTAMP,
                    effectiveness_score = MIN(1.0, CAST(leads_generated + ? AS REAL) / (times_used + 1) * 0.2)
            """, (
                query_hash, 
                query, 
                leads_found, 
                initial_effectiveness,
                leads_found,
                leads_found,
                leads_found
            ))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def get_domain_priority(self, domain: str) -> float:
        """
        Get priority score for a domain (0.0 - 1.0).
        
        Args:
            domain: Domain name
        
        Returns:
            Priority score (higher is better), defaults to 0.5 for unknown domains
        """
        if not domain:
            return 0.5
        
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            cur.execute("SELECT score FROM learning_domains WHERE domain = ?", (domain,))
            row = cur.fetchone()
            return row[0] if row else 0.5
        finally:
            con.close()
    
    def get_top_domains(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the most successful domains.
        
        Args:
            limit: Maximum number of domains to return
        
        Returns:
            List of domain dictionaries with stats
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        try:
            cur.execute("""
                SELECT domain, score, leads_found, total_visits 
                FROM learning_domains 
                ORDER BY score DESC, leads_found DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cur.fetchall()
            return [
                {
                    "domain": row["domain"], 
                    "score": row["score"], 
                    "leads": row["leads_found"], 
                    "visits": row["total_visits"]
                } 
                for row in rows
            ]
        finally:
            con.close()
    
    def should_skip_domain(self, domain: str) -> bool:
        """
        Check if a domain should be skipped (too many failures).
        
        Args:
            domain: Domain name
        
        Returns:
            True if domain should be skipped, False otherwise
        """
        if not domain:
            return False
        
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            cur.execute("""
                SELECT total_visits, successful_extractions, score 
                FROM learning_domains WHERE domain = ?
            """, (domain,))
            row = cur.fetchone()
            
            if not row:
                return False
            
            visits, successes, score = row
            
            # Skip if >10 visits but <10% success rate
            if visits > 10 and successes / visits < 0.1:
                return True
            
            # Skip if score very low
            if score < 0.1:
                return True
            
            return False
        finally:
            con.close()
    
    def optimize_query_order(self, queries: List[str]) -> List[str]:
        """
        Sort queries by effectiveness score (highest first).
        
        Args:
            queries: List of queries to optimize
        
        Returns:
            Sorted list of queries
        """
        if not queries:
            return []
        
        import hashlib
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            scored_queries = []
            for q in queries:
                query_hash = hashlib.md5(q.encode()).hexdigest()[:16]
                cur.execute(
                    "SELECT effectiveness_score FROM learning_queries WHERE query_hash = ?", 
                    (query_hash,)
                )
                row = cur.fetchone()
                score = row[0] if row else 0.5
                scored_queries.append((q, score))
            
            # Sort by score (highest first)
            scored_queries.sort(key=lambda x: x[1], reverse=True)
            return [q[0] for q in scored_queries]
        finally:
            con.close()
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get overall learning statistics.
        
        Returns:
            Dictionary with learning statistics
        """
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            # Pattern stats
            cur.execute("SELECT COUNT(*), AVG(confidence_score) FROM success_patterns")
            patterns = cur.fetchone()
            
            # Domain stats
            cur.execute("SELECT COUNT(*), AVG(score), SUM(leads_found) FROM learning_domains")
            domains = cur.fetchone()
            
            # Query stats
            cur.execute("SELECT COUNT(*), AVG(effectiveness_score), SUM(leads_generated) FROM learning_queries")
            queries = cur.fetchone()
            
            return {
                "patterns": {
                    "count": patterns[0] or 0, 
                    "avg_confidence": round(patterns[1] or 0, 2)
                },
                "domains": {
                    "count": domains[0] or 0, 
                    "avg_score": round(domains[1] or 0, 2), 
                    "total_leads": domains[2] or 0
                },
                "queries": {
                    "count": queries[0] or 0, 
                    "avg_effectiveness": round(queries[1] or 0, 2), 
                    "total_leads": queries[2] or 0
                }
            }
        finally:
            con.close()


def is_mobile_number(phone: str) -> bool:
    """
    Check if a phone number is a mobile number (DE, AT, CH).
    
    Only mobile numbers qualify as valid lead phone numbers.
    
    Args:
        phone: Phone number in any format
    
    Returns:
        True if it's a mobile number, False otherwise
    """
    if not phone:
        return False
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # German mobile prefixes (015x, 016x, 017x - complete list)
    MOBILE_PREFIXES_DE = ['150', '151', '152', '155', '156', '157', '159',
                          '160', '162', '163', '170', '171', '172', '173',
                          '174', '175', '176', '177', '178', '179']
    
    # Austrian mobile prefixes  
    MOBILE_PREFIXES_AT = ['660', '661', '662', '663', '664', '665', '666', '667',
                          '668', '669', '670', '676', '677', '678', '679',
                          '680', '681', '688', '689']
    
    # Swiss mobile prefixes
    MOBILE_PREFIXES_CH = ['760', '761', '762', '763', '764', '765', '766', '767',
                          '768', '769', '770', '771', '772', '773', '774', '775',
                          '776', '777', '778', '779', '780', '781', '782', '783',
                          '784', '785', '786', '787', '788', '789', '790', '791',
                          '792', '793', '794', '795', '796', '797', '798', '799']
    
    # Check German numbers
    if cleaned.startswith('+49'):
        # Extract prefix after country code (next 3 digits)
        rest = cleaned[3:]  # Everything after +49
        if len(rest) >= 3:
            prefix = rest[:3]
            return prefix in MOBILE_PREFIXES_DE
    elif cleaned.startswith('0049'):
        # Extract prefix after country code
        rest = cleaned[4:]  # Everything after 0049
        if len(rest) >= 3:
            prefix = rest[:3]
            return prefix in MOBILE_PREFIXES_DE
    elif cleaned.startswith('0') and not cleaned.startswith('00'):
        # National format (0176...)
        if len(cleaned) >= 4:
            prefix = cleaned[1:4]  # Skip the leading 0, get next 3 digits
            return prefix in MOBILE_PREFIXES_DE
    
    # Check Austrian numbers
    elif cleaned.startswith('+43'):
        rest = cleaned[3:]
        if len(rest) >= 3:
            prefix = rest[:3]
            return prefix in MOBILE_PREFIXES_AT
    elif cleaned.startswith('0043'):
        rest = cleaned[4:]
        if len(rest) >= 3:
            prefix = rest[:3]
            return prefix in MOBILE_PREFIXES_AT
    
    # Check Swiss numbers
    elif cleaned.startswith('+41'):
        rest = cleaned[3:]
        if len(rest) >= 3:
            prefix = rest[:3]
            return prefix in MOBILE_PREFIXES_CH
    elif cleaned.startswith('0041'):
        rest = cleaned[4:]
        if len(rest) >= 3:
            prefix = rest[:3]
            return prefix in MOBILE_PREFIXES_CH
    
    return False


def is_job_posting(url: str = "", title: str = "", snippet: str = "", content: str = "") -> bool:
    """
    Detect if content is a job posting/advertisement.
    
    Job postings should NEVER be saved as leads, even if they contain mobile numbers.
    This is a critical filter that must be applied before lead saving.
    
    Args:
        url: Page URL
        title: Page or snippet title
        snippet: Search result snippet
        content: Full page content
    
    Returns:
        True if this is a job posting, False otherwise
    """
    # Job posting URL patterns
    JOB_URL_PATTERNS = [
        '/jobs/', '/karriere/', '/stellenangebot/', '/stellenangebote/',
        '/vacancy/', '/vacancies/', '/career/', '/careers/', '/job-',
        '/jobboerse/', '/jobangebot/', '/joboffers/', '/positions/',
        '/bewerbung/', '/apply/', '/recruitment/', '/stellen/',
        '/offene-stellen/', '/job_', '/jobs_', '-job-', '-jobs-'
    ]
    
    # Job posting content signals
    JOB_CONTENT_SIGNALS = [
        # German
        'wir suchen', 'stellenanzeige', 'bewerbung', 'job-id', 
        'arbeitsort', 'eintrittsdatum', '(m/w/d)', '(w/m/d)', '(d/m/w)',
        'vollzeit', 'teilzeit', 'ab sofort', 'bewerben sie sich',
        'ihr profil', 'ihre aufgaben', 'wir bieten', 'benefits',
        'firmenwagen', 'unbefristete', 'befristete', 'gehalt',
        'karrierestufe', 'berufserfahrung', 'anstellungsart',
        'online bewerben', 'jetzt bewerben', 'bewerbungsunterlagen',
        'anschreiben', 'lebenslauf einreichen', 'bewerber',
        # English
        'we are hiring', 'apply now', 'job description', 'job requirements',
        'your responsibilities', 'what we offer', 'work location',
        'employment type', 'submit application', 'applicant',
        # Common job board indicators
        'stepstone', 'indeed', 'monster', 'linkedin jobs', 'xing stellenmarkt',
        'jobware', 'jobvector', 'stellenwerk', 'meinestadt.de/jobs'
    ]
    
    # Job posting title patterns
    JOB_TITLE_PATTERNS = [
        ' sucht ', ' gesucht', 'stellenangebot', 'job bei ',
        'karriere bei ', ' hiring ', ' wanted', ' vacancy',
        'mitarbeiter (m/w/d)', 'sales manager (m/w/d)',
        'vertriebsmitarbeiter gesucht'
    ]
    
    # Combine all text for analysis
    combined = ' '.join([
        url.lower() if url else '',
        title.lower() if title else '',
        snippet.lower() if snippet else '',
        content[:2000].lower() if content else ''  # Check first 2000 chars
    ])
    
    if not combined.strip():
        return False
    
    # Check URL patterns
    if url:
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in JOB_URL_PATTERNS):
            return True
    
    # Check title patterns
    if title:
        title_lower = title.lower()
        if any(pattern in title_lower for pattern in JOB_TITLE_PATTERNS):
            return True
    
    # Check content signals (need multiple hits to be sure)
    signal_count = sum(1 for signal in JOB_CONTENT_SIGNALS if signal in combined)
    
    # If we find 3+ job signals, it's likely a job posting
    if signal_count >= 3:
        return True
    
    # Special case: very strong single indicators
    strong_indicators = [
        'stellenanzeige', 'job-id:', 'bewerben sie sich jetzt',
        'online bewerben', 'jetzt bewerben', 'apply now',
        'submit application', 'bewerbungsformular'
    ]
    if any(indicator in combined for indicator in strong_indicators):
        return True
    
    return False
