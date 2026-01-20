# -*- coding: utf-8 -*-
"""
Unified Learning Database Adapter
==================================

This module provides a unified interface for learning data that automatically
detects Django availability and falls back to SQLite when Django is not available.

All learning engines (learning_engine, ai_learning_engine, perplexity_learning)
should use these functions instead of directly creating SQLite tables.

Features:
- Auto-detection of Django availability
- Seamless fallback to SQLite
- Consistent API across both backends
- Performance optimization via caching
"""

import sqlite3
import json
import hashlib
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Detect Django availability
DJANGO_AVAILABLE = False
try:
    import django
    from django.conf import settings
    from django.utils import timezone
    if settings.configured:
        from telis_recruitment.ai_config.models import (
            DorkPerformance,
            SourcePerformance,
            PatternSuccess,
            TelefonbuchCache
        )
        DJANGO_AVAILABLE = True
        logger.info("Django learning models available - using Django ORM")
except (ImportError, Exception) as e:
    logger.info(f"Django not available, using SQLite fallback: {e}")

# Default SQLite path
DEFAULT_SQLITE_PATH = "scraper.db"


def _get_db_path() -> str:
    """Get the SQLite database path (fallback mode)"""
    return DEFAULT_SQLITE_PATH


def _ensure_sqlite_tables(db_path: str) -> None:
    """Ensure SQLite tables exist (fallback mode only)"""
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS learning_dork_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            query_hash TEXT UNIQUE NOT NULL,
            times_used INTEGER DEFAULT 0,
            leads_found INTEGER DEFAULT 0,
            phone_leads INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            pool TEXT DEFAULT 'explore',
            last_used TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS learning_source_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            leads_found INTEGER DEFAULT 0,
            leads_with_phone INTEGER DEFAULT 0,
            avg_quality REAL DEFAULT 0.5,
            is_blocked INTEGER DEFAULT 0,
            blocked_reason TEXT DEFAULT '',
            total_visits INTEGER DEFAULT 0,
            last_visit TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS learning_pattern_success (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            pattern_value TEXT NOT NULL,
            pattern_hash TEXT NOT NULL,
            occurrences INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0.0,
            metadata TEXT DEFAULT '{}',
            last_success TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(pattern_type, pattern_hash)
        );
        
        CREATE TABLE IF NOT EXISTS learning_telefonbuch_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT UNIQUE NOT NULL,
            query_text TEXT NOT NULL,
            results_json TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            hits INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_dork_perf_success ON learning_dork_performance(success_rate DESC, phone_leads DESC);
        CREATE INDEX IF NOT EXISTS idx_dork_perf_pool ON learning_dork_performance(pool, success_rate DESC);
        CREATE INDEX IF NOT EXISTS idx_source_perf_quality ON learning_source_performance(avg_quality DESC, leads_with_phone DESC);
        CREATE INDEX IF NOT EXISTS idx_source_perf_blocked ON learning_source_performance(is_blocked);
        CREATE INDEX IF NOT EXISTS idx_pattern_type_conf ON learning_pattern_success(pattern_type, confidence DESC);
        CREATE INDEX IF NOT EXISTS idx_cache_expires ON learning_telefonbuch_cache(expires_at);
    """)
    conn.commit()
    conn.close()


def _hash_query(query: str) -> str:
    """Generate a hash for a query string"""
    return hashlib.md5(query.encode('utf-8')).hexdigest()


def _hash_pattern(pattern_type: str, pattern_value: str) -> str:
    """Generate a hash for a pattern"""
    combined = f"{pattern_type}:{pattern_value}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()


# ==================== DORK PERFORMANCE ====================

def record_dork_usage(
    query: str,
    leads_found: int = 0,
    phone_leads: int = 0,
    results: int = 0,
    db_path: Optional[str] = None
) -> None:
    """
    Record or update dork/query performance.
    
    Args:
        query: The search query
        leads_found: Number of leads found
        phone_leads: Number of leads with phone numbers
        results: Total search results (for success rate calculation)
        db_path: SQLite database path (fallback mode only)
    """
    query_hash = _hash_query(query)
    success_rate = phone_leads / max(1, results) if results > 0 else 0.0
    pool = 'core' if phone_leads > 0 else 'explore'
    
    if DJANGO_AVAILABLE:
        try:
            dork, created = DorkPerformance.objects.get_or_create(
                query_hash=query_hash,
                defaults={
                    'query': query,
                    'times_used': 0,
                    'leads_found': 0,
                    'phone_leads': 0,
                    'success_rate': 0.0,
                    'pool': pool,
                }
            )
            
            # Update metrics
            dork.times_used += 1
            dork.leads_found += leads_found
            dork.phone_leads += phone_leads
            dork.success_rate = dork.phone_leads / max(1, dork.leads_found)
            dork.pool = 'core' if dork.phone_leads > 0 else 'explore'
            dork.last_used = timezone.now()
            dork.save()
            
        except Exception as e:
            logger.error(f"Failed to record dork usage in Django: {e}")
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("""
                INSERT INTO learning_dork_performance 
                (query, query_hash, times_used, leads_found, phone_leads, success_rate, pool, last_used)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?)
                ON CONFLICT(query_hash) DO UPDATE SET
                    times_used = times_used + 1,
                    leads_found = leads_found + excluded.leads_found,
                    phone_leads = phone_leads + excluded.phone_leads,
                    success_rate = CAST(phone_leads + excluded.phone_leads AS REAL) / 
                                   MAX(1, leads_found + excluded.leads_found),
                    pool = CASE WHEN phone_leads + excluded.phone_leads > 0 THEN 'core' ELSE pool END,
                    last_used = excluded.last_used,
                    updated_at = CURRENT_TIMESTAMP
            """, (query, query_hash, leads_found, phone_leads, success_rate, pool, 
                  datetime.now(dt_timezone.utc).isoformat()))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to record dork usage in SQLite: {e}")
        finally:
            conn.close()


def get_top_dorks(
    limit: int = 10,
    pool: Optional[str] = None,
    min_uses: int = 2,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get top performing dorks/queries.
    
    Args:
        limit: Maximum number of dorks to return
        pool: Filter by pool ('core', 'explore', or None for all)
        min_uses: Minimum number of uses required
        db_path: SQLite database path (fallback mode only)
    
    Returns:
        List of dork dictionaries with metrics
    """
    if DJANGO_AVAILABLE:
        try:
            queryset = DorkPerformance.objects.filter(times_used__gte=min_uses)
            if pool:
                queryset = queryset.filter(pool=pool)
            
            queryset = queryset.order_by('-success_rate', '-phone_leads')[:limit]
            
            return [
                {
                    'query': d.query,
                    'times_used': d.times_used,
                    'leads_found': d.leads_found,
                    'phone_leads': d.phone_leads,
                    'success_rate': d.success_rate,
                    'pool': d.pool,
                    'last_used': d.last_used.isoformat() if d.last_used else None,
                }
                for d in queryset
            ]
        except Exception as e:
            logger.error(f"Failed to get top dorks from Django: {e}")
            return []
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            if pool:
                cursor = conn.execute("""
                    SELECT query, times_used, leads_found, phone_leads, success_rate, pool, last_used
                    FROM learning_dork_performance
                    WHERE times_used >= ? AND pool = ?
                    ORDER BY success_rate DESC, phone_leads DESC
                    LIMIT ?
                """, (min_uses, pool, limit))
            else:
                cursor = conn.execute("""
                    SELECT query, times_used, leads_found, phone_leads, success_rate, pool, last_used
                    FROM learning_dork_performance
                    WHERE times_used >= ?
                    ORDER BY success_rate DESC, phone_leads DESC
                    LIMIT ?
                """, (min_uses, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get top dorks from SQLite: {e}")
            return []
        finally:
            conn.close()


# ==================== SOURCE PERFORMANCE ====================

def record_source_hit(
    domain: str,
    leads_found: int = 1,
    has_phone: bool = False,
    quality: float = 0.5,
    is_blocked: bool = False,
    blocked_reason: str = "",
    db_path: Optional[str] = None
) -> None:
    """
    Record a hit on a source/domain.
    
    Args:
        domain: Domain name
        leads_found: Number of leads found from this source
        has_phone: Whether the lead has a phone number
        quality: Quality score (0.0-1.0)
        is_blocked: Whether the source is blocked
        blocked_reason: Reason for blocking (if blocked)
        db_path: SQLite database path (fallback mode only)
    """
    if not domain:
        return
    
    # Normalize domain (remove www.)
    if domain.startswith('www.'):
        domain = domain[4:]
    
    phone_leads = 1 if has_phone else 0
    
    if DJANGO_AVAILABLE:
        try:
            source, created = SourcePerformance.objects.get_or_create(
                domain=domain,
                defaults={
                    'leads_found': 0,
                    'leads_with_phone': 0,
                    'avg_quality': 0.5,
                    'is_blocked': False,
                    'total_visits': 0,
                }
            )
            
            # Update metrics
            source.total_visits += 1
            source.leads_found += leads_found
            source.leads_with_phone += phone_leads
            
            # Update average quality (moving average)
            source.avg_quality = (
                (source.avg_quality * (source.total_visits - 1) + quality) / 
                source.total_visits
            )
            
            if is_blocked:
                source.is_blocked = True
                source.blocked_reason = blocked_reason
            
            source.last_visit = timezone.now()
            source.save()
            
        except Exception as e:
            logger.error(f"Failed to record source hit in Django: {e}")
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("""
                INSERT INTO learning_source_performance 
                (domain, leads_found, leads_with_phone, avg_quality, is_blocked, 
                 blocked_reason, total_visits, last_visit)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    total_visits = total_visits + 1,
                    leads_found = leads_found + excluded.leads_found,
                    leads_with_phone = leads_with_phone + excluded.leads_with_phone,
                    avg_quality = (avg_quality * total_visits + excluded.avg_quality) / (total_visits + 1),
                    is_blocked = CASE WHEN excluded.is_blocked = 1 THEN 1 ELSE is_blocked END,
                    blocked_reason = CASE WHEN excluded.is_blocked = 1 THEN excluded.blocked_reason ELSE blocked_reason END,
                    last_visit = excluded.last_visit,
                    updated_at = CURRENT_TIMESTAMP
            """, (domain, leads_found, phone_leads, quality, 1 if is_blocked else 0,
                  blocked_reason, datetime.now(dt_timezone.utc).isoformat()))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to record source hit in SQLite: {e}")
        finally:
            conn.close()


def get_best_sources(
    limit: int = 20,
    min_leads: int = 5,
    exclude_blocked: bool = True,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get best performing sources/domains.
    
    Args:
        limit: Maximum number of sources to return
        min_leads: Minimum number of leads required
        exclude_blocked: Whether to exclude blocked sources
        db_path: SQLite database path (fallback mode only)
    
    Returns:
        List of source dictionaries with metrics
    """
    if DJANGO_AVAILABLE:
        try:
            queryset = SourcePerformance.objects.filter(leads_found__gte=min_leads)
            if exclude_blocked:
                queryset = queryset.filter(is_blocked=False)
            
            queryset = queryset.order_by('-avg_quality', '-leads_with_phone')[:limit]
            
            return [
                {
                    'domain': s.domain,
                    'leads_found': s.leads_found,
                    'leads_with_phone': s.leads_with_phone,
                    'avg_quality': s.avg_quality,
                    'is_blocked': s.is_blocked,
                    'total_visits': s.total_visits,
                    'last_visit': s.last_visit.isoformat() if s.last_visit else None,
                }
                for s in queryset
            ]
        except Exception as e:
            logger.error(f"Failed to get best sources from Django: {e}")
            return []
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            if exclude_blocked:
                cursor = conn.execute("""
                    SELECT domain, leads_found, leads_with_phone, avg_quality, 
                           is_blocked, total_visits, last_visit
                    FROM learning_source_performance
                    WHERE leads_found >= ? AND is_blocked = 0
                    ORDER BY avg_quality DESC, leads_with_phone DESC
                    LIMIT ?
                """, (min_leads, limit))
            else:
                cursor = conn.execute("""
                    SELECT domain, leads_found, leads_with_phone, avg_quality, 
                           is_blocked, total_visits, last_visit
                    FROM learning_source_performance
                    WHERE leads_found >= ?
                    ORDER BY avg_quality DESC, leads_with_phone DESC
                    LIMIT ?
                """, (min_leads, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get best sources from SQLite: {e}")
            return []
        finally:
            conn.close()


# ==================== PATTERN SUCCESS ====================

def record_pattern_success(
    pattern_type: str,
    pattern_value: str,
    metadata: Optional[Dict] = None,
    db_path: Optional[str] = None
) -> None:
    """
    Record a successful pattern.
    
    Args:
        pattern_type: Type of pattern ('phone', 'domain', 'query_term', etc.)
        pattern_value: The pattern value
        metadata: Additional metadata (optional)
        db_path: SQLite database path (fallback mode only)
    """
    if not pattern_value:
        return
    
    pattern_hash = _hash_pattern(pattern_type, pattern_value)
    metadata = metadata or {}
    
    if DJANGO_AVAILABLE:
        try:
            pattern, created = PatternSuccess.objects.get_or_create(
                pattern_type=pattern_type,
                pattern_hash=pattern_hash,
                defaults={
                    'pattern_value': pattern_value,
                    'occurrences': 0,
                    'confidence': 0.0,
                    'metadata': metadata,
                }
            )
            
            # Update metrics
            pattern.occurrences += 1
            pattern.confidence = min(1.0, pattern.occurrences / (pattern.occurrences + 10.0))
            pattern.metadata = metadata
            pattern.last_success = timezone.now()
            pattern.save()
            
        except Exception as e:
            logger.error(f"Failed to record pattern success in Django: {e}")
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("""
                INSERT INTO learning_pattern_success 
                (pattern_type, pattern_value, pattern_hash, occurrences, confidence, metadata, last_success)
                VALUES (?, ?, ?, 1, 0.0, ?, ?)
                ON CONFLICT(pattern_type, pattern_hash) DO UPDATE SET
                    occurrences = occurrences + 1,
                    confidence = CAST(occurrences + 1 AS REAL) / (occurrences + 11),
                    metadata = excluded.metadata,
                    last_success = excluded.last_success,
                    updated_at = CURRENT_TIMESTAMP
            """, (pattern_type, pattern_value, pattern_hash, json.dumps(metadata),
                  datetime.now(dt_timezone.utc).isoformat()))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to record pattern success in SQLite: {e}")
        finally:
            conn.close()


def get_top_patterns(
    pattern_type: str,
    limit: int = 20,
    min_confidence: float = 0.3,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get top patterns of a given type.
    
    Args:
        pattern_type: Type of pattern to retrieve
        limit: Maximum number of patterns to return
        min_confidence: Minimum confidence score
        db_path: SQLite database path (fallback mode only)
    
    Returns:
        List of pattern dictionaries
    """
    if DJANGO_AVAILABLE:
        try:
            queryset = PatternSuccess.objects.filter(
                pattern_type=pattern_type,
                confidence__gte=min_confidence
            ).order_by('-confidence', '-occurrences')[:limit]
            
            return [
                {
                    'pattern_type': p.pattern_type,
                    'pattern_value': p.pattern_value,
                    'occurrences': p.occurrences,
                    'confidence': p.confidence,
                    'metadata': p.metadata,
                    'last_success': p.last_success.isoformat() if p.last_success else None,
                }
                for p in queryset
            ]
        except Exception as e:
            logger.error(f"Failed to get top patterns from Django: {e}")
            return []
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("""
                SELECT pattern_type, pattern_value, occurrences, confidence, metadata, last_success
                FROM learning_pattern_success
                WHERE pattern_type = ? AND confidence >= ?
                ORDER BY confidence DESC, occurrences DESC
                LIMIT ?
            """, (pattern_type, min_confidence, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Failed to get top patterns from SQLite: {e}")
            return []
        finally:
            conn.close()


# ==================== TELEFONBUCH CACHE ====================

def get_phonebook_cache(
    query: str,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get cached phonebook lookup results.
    
    Args:
        query: Lookup query
        db_path: SQLite database path (fallback mode only)
    
    Returns:
        Cached results dict or None if not found/expired
    """
    query_hash = _hash_query(query)
    now = datetime.now(dt_timezone.utc)
    
    if DJANGO_AVAILABLE:
        try:
            cache = TelefonbuchCache.objects.filter(
                query_hash=query_hash,
                expires_at__gt=timezone.now()
            ).first()
            
            if cache:
                cache.hits += 1
                cache.save()
                return cache.results_json
            
            return None
        except Exception as e:
            logger.error(f"Failed to get phonebook cache from Django: {e}")
            return None
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("""
                SELECT results_json, expires_at, hits
                FROM learning_telefonbuch_cache
                WHERE query_hash = ? AND expires_at > ?
            """, (query_hash, now.isoformat()))
            
            row = cursor.fetchone()
            if row:
                # Update hit counter
                conn.execute("""
                    UPDATE learning_telefonbuch_cache
                    SET hits = hits + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE query_hash = ?
                """, (query_hash,))
                conn.commit()
                
                return json.loads(row['results_json'])
            
            return None
        except Exception as e:
            logger.error(f"Failed to get phonebook cache from SQLite: {e}")
            return None
        finally:
            conn.close()


def set_phonebook_cache(
    query: str,
    results: Dict[str, Any],
    ttl_hours: int = 24,
    db_path: Optional[str] = None
) -> None:
    """
    Set phonebook lookup cache.
    
    Args:
        query: Lookup query
        results: Results to cache
        ttl_hours: Time to live in hours
        db_path: SQLite database path (fallback mode only)
    """
    query_hash = _hash_query(query)
    now = datetime.now(dt_timezone.utc)
    expires_at = now + timedelta(hours=ttl_hours)
    
    if DJANGO_AVAILABLE:
        try:
            cache, created = TelefonbuchCache.objects.update_or_create(
                query_hash=query_hash,
                defaults={
                    'query_text': query,
                    'results_json': results,
                    'expires_at': expires_at,
                    'hits': 0,
                }
            )
        except Exception as e:
            logger.error(f"Failed to set phonebook cache in Django: {e}")
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("""
                INSERT INTO learning_telefonbuch_cache 
                (query_hash, query_text, results_json, expires_at, hits)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(query_hash) DO UPDATE SET
                    query_text = excluded.query_text,
                    results_json = excluded.results_json,
                    expires_at = excluded.expires_at,
                    hits = 0,
                    updated_at = CURRENT_TIMESTAMP
            """, (query_hash, query, json.dumps(results), expires_at.isoformat()))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to set phonebook cache in SQLite: {e}")
        finally:
            conn.close()


def cleanup_expired_cache(db_path: Optional[str] = None) -> int:
    """
    Clean up expired cache entries.
    
    Args:
        db_path: SQLite database path (fallback mode only)
    
    Returns:
        Number of entries deleted
    """
    now = datetime.now(dt_timezone.utc)
    
    if DJANGO_AVAILABLE:
        try:
            count, _ = TelefonbuchCache.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache in Django: {e}")
            return 0
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute("""
                DELETE FROM learning_telefonbuch_cache
                WHERE expires_at < ?
            """, (now.isoformat(),))
            count = cursor.rowcount
            conn.commit()
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache in SQLite: {e}")
            return 0
        finally:
            conn.close()


# ==================== UTILITY FUNCTIONS ====================

def get_learning_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get overall learning statistics.
    
    Args:
        db_path: SQLite database path (fallback mode only)
    
    Returns:
        Dictionary with learning statistics
    """
    if DJANGO_AVAILABLE:
        try:
            return {
                'backend': 'django',
                'dorks_tracked': DorkPerformance.objects.count(),
                'core_dorks': DorkPerformance.objects.filter(pool='core').count(),
                'sources_tracked': SourcePerformance.objects.count(),
                'blocked_sources': SourcePerformance.objects.filter(is_blocked=True).count(),
                'patterns_learned': PatternSuccess.objects.count(),
                'cache_entries': TelefonbuchCache.objects.count(),
                'cache_hits': sum(c.hits for c in TelefonbuchCache.objects.all()),
            }
        except Exception as e:
            logger.error(f"Failed to get learning stats from Django: {e}")
            return {'backend': 'django', 'error': str(e)}
    else:
        # SQLite fallback
        db_path = db_path or _get_db_path()
        _ensure_sqlite_tables(db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            stats = {'backend': 'sqlite'}
            
            cursor = conn.execute("SELECT COUNT(*) FROM learning_dork_performance")
            stats['dorks_tracked'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM learning_dork_performance WHERE pool = 'core'")
            stats['core_dorks'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM learning_source_performance")
            stats['sources_tracked'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM learning_source_performance WHERE is_blocked = 1")
            stats['blocked_sources'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM learning_pattern_success")
            stats['patterns_learned'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*), SUM(hits) FROM learning_telefonbuch_cache")
            row = cursor.fetchone()
            stats['cache_entries'] = row[0] if row[0] else 0
            stats['cache_hits'] = row[1] if row[1] else 0
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get learning stats from SQLite: {e}")
            return {'backend': 'sqlite', 'error': str(e)}
        finally:
            conn.close()
