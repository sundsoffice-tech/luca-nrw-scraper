# -*- coding: utf-8 -*-
"""
Self-learning system for lead generation optimization.

This module tracks successful patterns (domains, query terms, URL paths, content signals)
and uses this data to optimize future searches and improve lead quality.

Integrates with Django ai_config app when available for DB-driven AI configuration.
Falls back gracefully to default constants when Django is not available.

CONSOLIDATED: Uses luca_scraper.learning_db for unified database layer.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import urllib.parse
import re
import logging
import hashlib
import os
import sys

# CRITICAL: Ensure Django is initialized before importing luca_scraper modules
# This prevents AppRegistryNotReady errors when Django models are accessed
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')
    try:
        import django
        django.setup()
    except Exception as e:
        logging.warning(f"Django setup failed in learning_engine: {e}")
        # Continue anyway - some functionality may work without Django

# Import unified learning database adapter
try:
    from cache import get_domain_rating_cache
except ImportError:
    _root = os.path.dirname(os.path.abspath(__file__))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from cache import get_domain_rating_cache

from luca_scraper import learning_db

# Import thread-safe database utilities
try:
    from luca_scraper.db_utils import (
        get_db_connection,
        with_db_retry,
        configure_connection,
        ensure_db_initialized
    )
    DB_UTILS_AVAILABLE = True
except ImportError:
    logging.warning("db_utils not available, using basic SQLite without retry logic")
    DB_UTILS_AVAILABLE = False

# Optional Django ai_config integration
# Falls back gracefully when Django is not available or configured
try:
    from telis_recruitment.ai_config.loader import (
        get_ai_config,
        get_prompt,
        log_usage,
        check_budget
    )
    AI_CONFIG_AVAILABLE = True
except (ImportError, Exception):
    AI_CONFIG_AVAILABLE = False
    # Fallback defaults when ai_config is not available
    def get_ai_config():
        return {
            'temperature': 0.3,
            'top_p': 1.0,
            'max_tokens': 4000,
            'learning_rate': 0.01,
            'daily_budget': 5.0,
            'monthly_budget': 150.0,
            'confidence_threshold': 0.35,
            'retry_limit': 2,
            'timeout_seconds': 30,
            'default_provider': 'OpenAI',
            'default_model': 'gpt-4o-mini',
        }

    def get_prompt(slug: str):
        return None

    def log_usage(*args, **kwargs):
        pass

    def check_budget():
        return True, {
            'daily_spent': 0.0,
            'daily_budget': 5.0,
            'daily_remaining': 5.0,
            'monthly_spent': 0.0,
            'monthly_budget': 150.0,
            'monthly_remaining': 150.0,
        }


_DOMAIN_RATING_CACHE = get_domain_rating_cache()


def _normalize_domain(domain: str) -> str:
    """Normalize host names for consistent caching."""
    if not domain:
        return ""
    domain = domain.lower()
    if domain.startswith("www."):
        return domain[4:]
    return domain

logger = logging.getLogger(__name__)


class LearningEngine:
    """Self-learning engine that tracks and optimizes lead generation patterns.
    
    Integrates with Django ai_config app when available for configuration management.
    """
    
    def __init__(self, db_path: str):
        """Initialize the learning engine with database path.
        
        Args:
            db_path: Path to SQLite database for storing learning data
        """
        self.db_path = db_path
        
        # Load AI configuration with fallback (defense in depth)
        # Catches any errors from get_ai_config() including Django configuration issues
        try:
            self.ai_config = get_ai_config()
            if AI_CONFIG_AVAILABLE:
                logger.info(f"AI config loaded from Django DB: provider={self.ai_config.get('default_provider')}, "
                           f"model={self.ai_config.get('default_model')}")
            else:
                logger.info("AI config using fallback defaults (Django not available)")
        except Exception as e:
            # Fallback if get_ai_config() fails for any reason
            # This provides an additional safety layer beyond the loader.py handling
            # Catches: ImportError, django.core.exceptions.ImproperlyConfigured, etc.
            logger.warning(f"Failed to load AI config, using defaults: {e}")
            self.ai_config = {
                'temperature': 0.3,
                'top_p': 1.0,
                'max_tokens': 4000,
                'learning_rate': 0.01,
                'daily_budget': 5.0,
                'monthly_budget': 150.0,
                'confidence_threshold': 0.35,
                'retry_limit': 2,
                'timeout_seconds': 30,
                'default_provider': 'OpenAI',
                'default_model': 'gpt-4o-mini',
            }
        
        self._ensure_learning_tables()
    
    def _ensure_learning_tables(self) -> None:
        """Create success_patterns table and additional learning tables if they don't exist (thread-safe)."""
        def _init_tables(con):
            """Initialize tables - called by ensure_db_initialized."""
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
            
            # Extraction Patterns table - tracks successful extraction patterns
            cur.execute("""
                CREATE TABLE IF NOT EXISTS extraction_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    description TEXT,
                    success_count INTEGER DEFAULT 0,
                    last_success TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pattern_type, pattern)
                )
            """)
            
            # Failed Extractions table - learn from failures
            cur.execute("""
                CREATE TABLE IF NOT EXISTS failed_extractions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    failure_reason TEXT,
                    html_snippet TEXT,
                    visible_phone_numbers TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Phone Patterns table - discovered phone number formats
            cur.execute("""
                CREATE TABLE IF NOT EXISTS phone_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL UNIQUE,
                    pattern_type TEXT,
                    success_count INTEGER DEFAULT 0,
                    example_matches TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Domain Performance table - detailed portal tracking
            cur.execute("""
                CREATE TABLE IF NOT EXISTS domain_performance (
                    domain TEXT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT 1,
                    priority INTEGER DEFAULT 2,
                    delay_seconds REAL DEFAULT 3.0,
                    success_rate REAL DEFAULT 0.0,
                    total_requests INTEGER DEFAULT 0,
                    successful_requests INTEGER DEFAULT 0,
                    rate_limit_detected BOOLEAN DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            """)
            
            # AI Improvements table - track AI-generated improvements
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ai_improvements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    improvement_type TEXT NOT NULL,
                    description TEXT,
                    implementation_status TEXT DEFAULT 'pending',
                    impact_estimate TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied_at TIMESTAMP
                )
            """)
            
            # Active Learning: Portal/Run Metrics
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learning_portal_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    portal TEXT,
                    urls_crawled INTEGER DEFAULT 0,
                    leads_found INTEGER DEFAULT 0,
                    leads_with_phone INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    errors INTEGER DEFAULT 0
                )
            """)
            
            # Active Learning: Dork/Query Performance
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learning_dork_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dork TEXT UNIQUE,
                    times_used INTEGER DEFAULT 0,
                    total_results INTEGER DEFAULT 0,
                    leads_found INTEGER DEFAULT 0,
                    leads_with_phone INTEGER DEFAULT 0,
                    score REAL DEFAULT 0.0,
                    last_used TEXT,
                    pool TEXT DEFAULT 'explore'
                )
            """)
            
            # Active Learning: Phone Patterns Learned
            cur.execute("""
                CREATE TABLE IF NOT EXISTS phone_patterns_learned (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT UNIQUE,
                    times_matched INTEGER DEFAULT 0,
                    source_portal TEXT,
                    discovered_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Active Learning: Host Backoff
            cur.execute("""
                CREATE TABLE IF NOT EXISTS host_backoff (
                    host TEXT PRIMARY KEY,
                    failures INTEGER DEFAULT 0,
                    last_failure TEXT,
                    backoff_until TEXT,
                    reason TEXT
                )
            """)
            
            con.commit()
            
            # Create indexes for better query performance (after commit)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_portal_metrics_run ON learning_portal_metrics(run_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_portal_metrics_portal ON learning_portal_metrics(portal)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_portal_metrics_timestamp ON learning_portal_metrics(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_dork_performance_score ON learning_dork_performance(score DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_dork_performance_pool ON learning_dork_performance(pool)")
            
            con.commit()
        
        if DB_UTILS_AVAILABLE:
            ensure_db_initialized(self.db_path, _init_tables)
        else:
            # Fallback without thread-safety
            con = sqlite3.connect(self.db_path)
            _init_tables(con)
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
        """
        Increment success count for a pattern and update confidence score (thread-safe with retry).
        Uses unified learning_db adapter.
        """
        if not pattern_value:
            return
        
        # Use unified learning database adapter
        learning_db.record_pattern_success(
            pattern_type=pattern_type,
            pattern_value=pattern_value,
            metadata={
                "last_lead_type": metadata.get("lead_type", ""),
                "last_tags": metadata.get("tags", "")[:200],  # Truncate
                "last_score": metadata.get("score", 0)
            },
            db_path=self.db_path
        )
        
        # Also maintain legacy success_patterns table for compatibility
        @with_db_retry()
        def _update_pattern():
            # Convert metadata to JSON (store only essential info)
            meta_json = json.dumps({
                "last_lead_type": metadata.get("lead_type", ""),
                "last_tags": metadata.get("tags", "")[:200],  # Truncate
                "last_score": metadata.get("score", 0)
            })
            
            if DB_UTILS_AVAILABLE:
                with get_db_connection(self.db_path) as con:
                    cur = con.cursor()
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
            else:
                # Fallback without db_utils
                con = sqlite3.connect(self.db_path)
                cur = con.cursor()
                try:
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
        
        try:
            _update_pattern()
        except Exception:
            # Silent fail - don't break lead processing if learning fails
            pass
    
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
    
    def record_domain_success(self, domain: str, leads_found: int, quality: float = 0.5, has_phone: bool = False) -> None:
        """
        Update domain score after a successful crawl.
        Uses unified learning_db adapter.
        
        Args:
            domain: Domain name
            leads_found: Number of leads found from this domain
            quality: Quality score (0.0-1.0)
            has_phone: Whether leads have phone numbers
        """
        normalized_domain = _normalize_domain(domain)
        if not normalized_domain:
            return
        
        # Use unified learning database adapter
        learning_db.record_source_hit(
            domain=normalized_domain,
            leads_found=leads_found,
            has_phone=has_phone,
            quality=quality,
                db_path=self.db_path
            )
        
        # Also maintain legacy learning_domains table for compatibility
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
                    avg_quality = (avg_quality * total_visits + ?) / (total_visits + 1),
                    last_visit = CURRENT_TIMESTAMP,
                    score = MIN(1.0, score + ?)
            """, (
                normalized_domain,
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
            # Refresh cache after a successful update
            cur.execute("SELECT score FROM learning_domains WHERE domain = ?", (normalized_domain,))
            row = cur.fetchone()
            if row:
                _DOMAIN_RATING_CACHE.set(normalized_domain, row[0])
        except Exception:
            pass
        finally:
            con.close()
    
    def record_query_performance(self, query: str, leads_found: int, phone_leads: int = 0) -> None:
        """
        Record query performance for optimization.
        Uses unified learning_db adapter.
        
        Args:
            query: The search query
            leads_found: Number of leads generated by this query
            phone_leads: Number of leads with phone numbers (optional)
        """
        if not query:
            return

        # Use unified learning database adapter
        try:
            learning_db.record_dork_usage(
                query=query,
                leads_found=leads_found,
                phone_leads=phone_leads,
                results=leads_found,  # Approximate results as leads for success rate
                db_path=self.db_path
            )
        except Exception:
            pass

        query_hash = hashlib.sha256(query.encode()).hexdigest()
        
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
        normalized_domain = _normalize_domain(domain)
        if not normalized_domain:
            return 0.5

        cached_score = _DOMAIN_RATING_CACHE.get(normalized_domain)
        if cached_score is not None:
            return cached_score

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            cur.execute("SELECT score FROM learning_domains WHERE domain = ?", (normalized_domain,))
            row = cur.fetchone()
            score = row[0] if row else 0.5
            _DOMAIN_RATING_CACHE.set(normalized_domain, score)
            return score
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
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            scored_queries = []
            for q in queries:
                query_hash = hashlib.sha256(q.encode()).hexdigest()
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


    def learn_from_failure(self, url: str, html_content: str, reason: str, 
                          visible_phones: Optional[List[str]] = None) -> None:
        """
        Learn from extraction failures to improve future attempts.
        
        Args:
            url: URL where extraction failed
            html_content: HTML content (will be truncated to snippet)
            reason: Why extraction failed
            visible_phones: Any phone numbers visible in HTML (for learning)
        """
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            # Store HTML snippet (first 2000 chars)
            html_snippet = html_content[:2000] if html_content else ""
            visible_phones_str = json.dumps(visible_phones) if visible_phones else None
            
            cur.execute("""
                INSERT INTO failed_extractions 
                (url, failure_reason, html_snippet, visible_phone_numbers, timestamp)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (url, reason, html_snippet, visible_phones_str))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def record_extraction_pattern(self, pattern_type: str, pattern: str, 
                                  description: str = "") -> None:
        """
        Record a successful extraction pattern for future use.
        
        Args:
            pattern_type: Type of pattern (e.g., 'phone_regex', 'css_selector', 'whatsapp_link')
            pattern: The actual pattern/selector
            description: Human-readable description
        """
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            cur.execute("""
                INSERT INTO extraction_patterns 
                (pattern_type, pattern, description, success_count, last_success)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(pattern_type, pattern) DO UPDATE SET
                    success_count = success_count + 1,
                    last_success = CURRENT_TIMESTAMP
            """, (pattern_type, pattern, description))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def record_phone_pattern(self, pattern: str, pattern_type: str, 
                            example: str = "") -> None:
        """
        Record a discovered phone number pattern.
        
        Args:
            pattern: Regex pattern for phone number
            pattern_type: Type of pattern (e.g., 'spaced', 'obfuscated', 'whatsapp')
            example: Example phone number that matches
        """
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            cur.execute("""
                INSERT INTO phone_patterns 
                (pattern, pattern_type, success_count, example_matches)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(pattern) DO UPDATE SET
                    success_count = success_count + 1,
                    example_matches = example_matches || ', ' || ?
            """, (pattern, pattern_type, example, example))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def update_domain_performance(self, domain: str, success: bool, 
                                  rate_limited: bool = False) -> None:
        """
        Update portal/domain performance metrics.
        
        Args:
            domain: Domain name
            success: Whether the request was successful
            rate_limited: Whether rate limiting was detected
        """
        if not domain:
            return
        
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            cur.execute("""
                INSERT INTO domain_performance 
                (domain, total_requests, successful_requests, rate_limit_detected, last_updated)
                VALUES (?, 1, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(domain) DO UPDATE SET
                    total_requests = total_requests + 1,
                    successful_requests = successful_requests + ?,
                    success_rate = CAST(successful_requests AS REAL) / total_requests,
                    rate_limit_detected = rate_limit_detected OR ?,
                    last_updated = CURRENT_TIMESTAMP
            """, (
                domain, 
                1 if success else 0, 
                1 if rate_limited else 0,
                1 if success else 0,
                1 if rate_limited else 0
            ))
            
            con.commit()
        except Exception:
            pass
        finally:
            con.close()
    
    def generate_improved_patterns(self) -> List[Dict[str, str]]:
        """
        Generate improved extraction patterns based on learning data.
        
        Returns:
            List of pattern improvements with type, pattern, and description
        """
        improvements = []
        
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        try:
            # Get successful phone patterns
            cur.execute("""
                SELECT pattern, pattern_type, success_count 
                FROM phone_patterns 
                WHERE success_count >= 2
                ORDER BY success_count DESC
                LIMIT 10
            """)
            
            for row in cur.fetchall():
                improvements.append({
                    "type": "phone_pattern",
                    "pattern": row["pattern"],
                    "description": f"Phone pattern ({row['pattern_type']}) with {row['success_count']} successes"
                })
            
            # Get successful extraction patterns
            cur.execute("""
                SELECT pattern_type, pattern, description, success_count 
                FROM extraction_patterns 
                WHERE success_count >= 3
                ORDER BY success_count DESC
                LIMIT 10
            """)
            
            for row in cur.fetchall():
                improvements.append({
                    "type": row["pattern_type"],
                    "pattern": row["pattern"],
                    "description": f"{row['description']} ({row['success_count']} successes)"
                })
            
            return improvements
        finally:
            con.close()
    
    def optimize_portal_config(self) -> Dict[str, Any]:
        """
        Generate optimized portal configuration based on performance data.
        
        Returns:
            Dictionary with portal recommendations
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        recommendations = {
            "disable": [],
            "delay_increase": [],
            "prioritize": []
        }
        
        try:
            # Find portals to disable (low success rate, many attempts)
            cur.execute("""
                SELECT domain, success_rate, total_requests, rate_limit_detected
                FROM domain_performance
                WHERE total_requests >= 10
                ORDER BY success_rate ASC
                LIMIT 10
            """)
            
            for row in cur.fetchall():
                if row["success_rate"] < 0.05:  # Less than 5% success
                    recommendations["disable"].append({
                        "domain": row["domain"],
                        "reason": f"Low success rate: {row['success_rate']:.1%} ({row['total_requests']} attempts)",
                        "success_rate": row["success_rate"]
                    })
                elif row["rate_limit_detected"]:
                    recommendations["delay_increase"].append({
                        "domain": row["domain"],
                        "reason": "Rate limiting detected",
                        "suggested_delay": 8.0
                    })
            
            # Find high-performing portals to prioritize
            cur.execute("""
                SELECT domain, success_rate, total_requests
                FROM domain_performance
                WHERE total_requests >= 5 AND success_rate >= 0.2
                ORDER BY success_rate DESC
                LIMIT 5
            """)
            
            for row in cur.fetchall():
                recommendations["prioritize"].append({
                    "domain": row["domain"],
                    "success_rate": row["success_rate"],
                    "requests": row["total_requests"]
                })
            
            return recommendations
        finally:
            con.close()
    
    def get_ai_learning_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive AI learning statistics.
        
        Returns:
            Dictionary with learning statistics
        """
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        try:
            stats = {}
            
            # Phone patterns learned
            cur.execute("SELECT COUNT(*) FROM phone_patterns")
            stats["phone_patterns_learned"] = cur.fetchone()[0]
            
            # Extraction patterns
            cur.execute("SELECT COUNT(*) FROM extraction_patterns")
            stats["extraction_patterns"] = cur.fetchone()[0]
            
            # Failed extractions (for learning)
            cur.execute("SELECT COUNT(*) FROM failed_extractions")
            stats["failures_logged"] = cur.fetchone()[0]
            
            # Portal performance
            cur.execute("""
                SELECT 
                    COUNT(*) as total_portals,
                    AVG(success_rate) as avg_success_rate,
                    SUM(CASE WHEN rate_limit_detected = 1 THEN 1 ELSE 0 END) as rate_limited_portals
                FROM domain_performance
            """)
            perf = cur.fetchone()
            stats["portals_tracked"] = perf[0]
            stats["avg_portal_success_rate"] = round(perf[1] or 0, 3)
            stats["rate_limited_portals"] = perf[2]
            
            # AI improvements
            cur.execute("SELECT COUNT(*) FROM ai_improvements")
            stats["ai_improvements_generated"] = cur.fetchone()[0]
            
            return stats
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


def extract_competitor_intel(url: str = "", title: str = "", snippet: str = "", content: str = "") -> Optional[Dict[str, Any]]:
    """
    Extract competitive intelligence from job postings instead of discarding them.
    
    Job postings reveal:
    - Which companies are hiring (potential sources for unhappy salespeople)
    - What conditions they offer
    - HR contacts for referrals
    
    Args:
        url: Page URL
        title: Page or snippet title
        snippet: Search result snippet
        content: Full page content
    
    Returns:
        Dict with competitor intelligence or None if not a job posting
    """
    if not is_job_posting(url, title, snippet, content):
        return None
    
    intel = {
        "type": "competitor_intel",
        "url": url,
        "title": title,
        "is_job_posting": True,
    }
    
    # Extract company name from URL or title
    from urllib.parse import urlparse
    domain = urlparse(url).netloc if url else ""
    intel["company_domain"] = domain
    
    # Extract salary/benefits hints
    combined = ' '.join([title or '', snippet or '', content[:1000] if content else ''])
    combined_lower = combined.lower()
    
    if any(term in combined_lower for term in ["gehalt", "vergütung", "€", "eur", "provision"]):
        intel["has_salary_info"] = True
    
    if any(term in combined_lower for term in ["firmenwagen", "dienstwagen", "homeoffice"]):
        intel["has_benefits"] = True
    
    # Extract HR contact hints
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    emails = re.findall(email_pattern, combined)
    if emails:
        intel["hr_emails"] = emails[:3]  # Keep first 3
    
    return intel


def is_job_posting(url: str = "", title: str = "", snippet: str = "", content: str = "") -> bool:
    """
    Detect if content is a job posting/advertisement.
    
    NOTE: In talent_hunt mode, job postings are used for competitive intelligence
    rather than being completely filtered out.
    
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
        'vollzeit', 'teilzeit', 'bewerben sie sich',
        'ihr profil', 'ihre aufgaben', 'wir bieten', 'benefits',
        'firmenwagen', 'unbefristete', 'befristete',
        'karrierestufe', 'anstellungsart',
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
    
    # Increased threshold to 4+ to be less aggressive (was 3)
    if signal_count >= 4:
        return True
    
    # Special case: very strong single indicators
    strong_indicators = [
        'stellenanzeige', 'job-id:', 'bewerben sie sich jetzt',
        'online bewerben', 'bewerbungsformular'
    ]
    if any(indicator in combined for indicator in strong_indicators):
        return True
    
    return False


class ActiveLearningEngine:
    """
    Active self-learning system that tracks portal performance, query effectiveness,
    and phone patterns to optimize future scraping runs.
    """
    
    def __init__(self, db_path: str = "scraper.db"):
        self.db_path = db_path
        self.current_run_metrics = {}
    
    def record_portal_result(self, portal: str, urls_crawled: int, leads_found: int, 
                            leads_with_phone: int, run_id: int = None, errors: int = 0) -> None:
        """
        Record results after each portal crawl.
        
        Args:
            portal: Portal name (e.g., 'kleinanzeigen', 'markt_de')
            urls_crawled: Number of URLs crawled from this portal
            leads_found: Total leads found
            leads_with_phone: Leads with valid phone numbers
            run_id: Current run ID (optional)
            errors: Number of errors encountered (optional)
        """
        success_rate = leads_with_phone / max(1, urls_crawled)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO learning_portal_metrics 
                    (run_id, portal, urls_crawled, leads_found, leads_with_phone, success_rate, errors)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (run_id, portal, urls_crawled, leads_found, leads_with_phone, success_rate, errors))
                conn.commit()
            
            # Check if portal should be automatically disabled
            if self._get_portal_avg_success(portal, last_n=5) < 0.01:
                # Log warning (using print as fallback since learning_engine has no dependency on log())
                import sys
                print(f"[LEARNING] Portal {portal} has <1% success rate - consider disabling", file=sys.stderr)
        except Exception as e:
            # Silent fail - don't break the scraping run if learning fails
            pass
    
    def _get_portal_avg_success(self, portal: str, last_n: int = 5) -> float:
        """
        Get average success rate for a portal over the last N runs.
        
        Args:
            portal: Portal name
            last_n: Number of recent runs to average
            
        Returns:
            Average success rate (0.0-1.0)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("""
                    SELECT AVG(success_rate) FROM (
                        SELECT success_rate FROM learning_portal_metrics 
                        WHERE portal = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    )
                """, (portal, last_n))
                result = cur.fetchone()
                return result[0] if result and result[0] is not None else 0.5
        except Exception:
            return 0.5
    
    def record_dork_result(self, dork: str, results: int, leads_found: int, leads_with_phone: int) -> None:
        """
        Record performance of a search query (dork).
        
        Args:
            dork: The search query/dork used
            results: Total number of search results returned
            leads_found: Number of leads found with this query
            leads_with_phone: Number of leads with valid phone numbers
        """
        try:
            # Use max(leads_found, leads_with_phone) to handle edge cases where
            # leads_with_phone > leads_found (data inconsistency)
            # Then divide by max(1, ...) to prevent division by zero
            actual_leads = max(leads_found, leads_with_phone)
            score = leads_with_phone / max(1, actual_leads)
            pool = 'core' if leads_with_phone > 0 else 'explore'
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if dork exists
                cur = conn.execute("SELECT times_used, total_results, leads_found, leads_with_phone FROM learning_dork_performance WHERE dork = ?", (dork,))
                existing = cur.fetchone()
                
                if existing:
                    new_times = existing[0] + 1
                    new_total_results = existing[1] + results
                    new_leads = existing[2] + leads_found
                    new_phone_leads = existing[3] + leads_with_phone
                    # Handle edge case where new_phone_leads > new_leads
                    actual_new_leads = max(new_leads, new_phone_leads)
                    new_score = new_phone_leads / max(1, actual_new_leads)
                    
                    conn.execute("""
                        UPDATE learning_dork_performance 
                        SET times_used = ?, total_results = ?, leads_found = ?, leads_with_phone = ?, 
                            score = ?, last_used = datetime('now'), pool = ?
                        WHERE dork = ?
                    """, (new_times, new_total_results, new_leads, new_phone_leads, new_score, pool, dork))
                else:
                    conn.execute("""
                        INSERT INTO learning_dork_performance 
                        (dork, times_used, total_results, leads_found, leads_with_phone, score, last_used, pool)
                        VALUES (?, 1, ?, ?, ?, ?, datetime('now'), ?)
                    """, (dork, results, leads_found, leads_with_phone, score, pool))
                
                conn.commit()
        except Exception:
            # Silent fail - don't break the scraping run if learning fails
            pass
    
    def learn_phone_pattern(self, raw_phone: str, normalized: str, portal: str) -> None:
        """
        Learn from a successfully extracted phone number pattern.
        
        Args:
            raw_phone: Raw phone number as found in HTML
            normalized: Normalized phone number
            portal: Portal where this was found
        """
        try:
            # Extract pattern (e.g., "0171 - 123 456" -> "XXXX - XXX XXX")
            pattern = self._extract_pattern(raw_phone)
            
            if pattern:
                with sqlite3.connect(self.db_path) as conn:
                    cur = conn.execute(
                        "SELECT times_matched FROM phone_patterns_learned WHERE pattern = ?", 
                        (pattern,)
                    )
                    existing = cur.fetchone()
                    
                    if existing:
                        conn.execute("""
                            UPDATE phone_patterns_learned 
                            SET times_matched = times_matched + 1 
                            WHERE pattern = ?
                        """, (pattern,))
                    else:
                        conn.execute("""
                            INSERT INTO phone_patterns_learned 
                            (pattern, times_matched, source_portal)
                            VALUES (?, 1, ?)
                        """, (pattern, portal))
                    
                    conn.commit()
        except Exception:
            # Silent fail - don't break the scraping run if learning fails
            pass
    
    def _extract_pattern(self, phone: str) -> str:
        """
        Extract pattern from a phone number.
        
        Args:
            phone: Phone number string
            
        Returns:
            Pattern representation
        """
        if not phone:
            return ""
        
        # Replace digits with X, keep structure
        pattern = re.sub(r'\d', 'X', phone)
        return pattern[:50]  # Limit length
    
    def get_best_dorks(self, n: int = 10) -> List[str]:
        """
        Get the best performing search queries.
        
        Args:
            n: Number of dorks to return
            
        Returns:
            List of best dork strings
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("""
                    SELECT dork FROM learning_dork_performance 
                    WHERE pool = 'core' AND times_used > 2
                    ORDER BY score DESC, leads_with_phone DESC
                    LIMIT ?
                """, (n,))
                return [row[0] for row in cur.fetchall()]
        except Exception:
            return []
    
    def should_skip_portal(self, portal: str) -> bool:
        """
        Determine if a portal should be skipped based on historical performance.
        
        Note: This is a simplified version that returns only bool.
        The ai_learning_engine.ActiveLearningEngine returns Tuple[bool, str] with a reason.
        scriptname.py uses the ai_learning_engine version.
        
        Returns False (don't skip) if:
        - No data exists for the portal
        - Less than 5 runs recorded
        
        Returns True (skip) only if:
        - At least 5 runs recorded AND success rate < 10%
        
        Args:
            portal: Portal name
            
        Returns:
            True if portal should be skipped, False otherwise
        """
        # Get metrics for last 5 runs
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("""
                    SELECT COUNT(*), AVG(success_rate) FROM (
                        SELECT success_rate FROM learning_portal_metrics 
                        WHERE portal = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 5
                    )
                """, (portal,))
                result = cur.fetchone()
                
                if result and result[0] is not None:
                    num_runs = result[0]
                    avg_success = result[1] if result[1] is not None else 1.0
                    
                    # Only skip if we have enough data (5+ runs) AND poor performance (<10%)
                    if num_runs >= 5 and avg_success < 0.10:
                        return True
                
                # Default: don't skip (test new portals or those with insufficient data)
                return False
        except Exception:
            # On error, don't skip (safer to test than to miss opportunities)
            return False
    
    def get_learned_phone_patterns(self) -> List[str]:
        """
        Get learned phone patterns that have been successful multiple times.
        
        Returns:
            List of phone patterns
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("""
                    SELECT pattern FROM phone_patterns_learned 
                    WHERE times_matched > 2
                    ORDER BY times_matched DESC
                """)
                return [row[0] for row in cur.fetchall()]
        except Exception:
            return []
    
    def record_host_failure(self, host: str, reason: str, backoff_hours: int = 1) -> None:
        """
        Record a host failure and set backoff period.
        
        Args:
            host: Host/domain that failed
            reason: Reason for failure
            backoff_hours: Hours to back off
        """
        try:
            backoff_until = (datetime.now(timezone.utc) + 
                           timedelta(hours=backoff_hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("SELECT failures FROM host_backoff WHERE host = ?", (host,))
                existing = cur.fetchone()
                
                if existing:
                    new_failures = existing[0] + 1
                    conn.execute("""
                        UPDATE host_backoff 
                        SET failures = ?, last_failure = datetime('now'), 
                            backoff_until = ?, reason = ?
                        WHERE host = ?
                    """, (new_failures, backoff_until, reason, host))
                else:
                    conn.execute("""
                        INSERT INTO host_backoff 
                        (host, failures, last_failure, backoff_until, reason)
                        VALUES (?, 1, datetime('now'), ?, ?)
                    """, (host, backoff_until, reason))
                
                conn.commit()
        except Exception:
            # Silent fail - don't break the scraping run if learning fails
            pass
    
    def should_backoff_host(self, host: str) -> bool:
        """
        Check if we should back off from a host.
        
        Args:
            host: Host to check
            
        Returns:
            True if we should back off, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("""
                    SELECT backoff_until FROM host_backoff 
                    WHERE host = ?
                """, (host,))
                result = cur.fetchone()
                
                if result and result[0]:
                    backoff_until = datetime.fromisoformat(result[0])
                    return datetime.now(timezone.utc) < backoff_until
        except Exception:
            pass
        
        return False
    
    def get_portal_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all portals.
        
        Returns:
            Dictionary with portal statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("""
                    SELECT 
                        portal,
                        COUNT(*) as runs,
                        SUM(urls_crawled) as total_urls,
                        SUM(leads_found) as total_leads,
                        SUM(leads_with_phone) as total_with_phone,
                        AVG(success_rate) as avg_success_rate
                    FROM learning_portal_metrics
                    GROUP BY portal
                    ORDER BY avg_success_rate DESC
                """)
                
                stats = {}
                for row in cur.fetchall():
                    stats[row['portal']] = {
                        'runs': row['runs'],
                        'total_urls': row['total_urls'],
                        'total_leads': row['total_leads'],
                        'total_with_phone': row['total_with_phone'],
                        'avg_success_rate': round(row['avg_success_rate'] or 0, 4)
                    }
                
                return stats
        except Exception:
            # Silent fail - return empty dict if stats retrieval fails
            return {}
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """
        Get a summary of what the system has learned.
        
        Returns:
            Dictionary with learning summary
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                summary = {}
                
                # Total metrics tracked
                cur = conn.execute("SELECT COUNT(*) FROM learning_portal_metrics")
                summary['total_portal_runs'] = cur.fetchone()[0]
                
                # Dork statistics
                cur = conn.execute("""
                    SELECT COUNT(*), 
                           SUM(CASE WHEN pool = 'core' THEN 1 ELSE 0 END) as core_count
                    FROM learning_dork_performance
                """)
                result = cur.fetchone()
                summary['total_dorks_tracked'] = result[0]
                summary['core_dorks'] = result[1]
                
                # Phone patterns learned
                cur = conn.execute("SELECT COUNT(*) FROM phone_patterns_learned")
                summary['phone_patterns_learned'] = cur.fetchone()[0]
                
                # Hosts in backoff
                cur = conn.execute("""
                    SELECT COUNT(*) FROM host_backoff 
                    WHERE backoff_until > datetime('now')
                """)
                summary['hosts_in_backoff'] = cur.fetchone()[0]
                
                return summary
        except Exception:
            # Silent fail - return empty dict if summary retrieval fails
            return {}
