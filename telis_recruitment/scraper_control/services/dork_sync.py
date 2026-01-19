# -*- coding: utf-8 -*-
"""
DorkSyncService - Synchronizes AI learning metrics with Django CRM.

This service bridges the SQLite-based AI learning system with the Django SearchDork model,
enabling continuous learning from real results and automatic tracking of success rates.

Features:
- Syncs dork performance metrics from SQLite to Django SearchDork model
- Tracks successful extraction patterns per dork
- Records top-performing domains for each dork
- Enables dashboard visibility of AI learning results
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DorkSyncService:
    """
    Service to synchronize AI learning metrics between SQLite and Django CRM.
    
    The AI learning system uses SQLite for fast, local metric tracking during scraping.
    This service syncs those metrics to Django's SearchDork model for:
    - Dashboard visibility
    - Persistent storage across deployments
    - Integration with CRM workflows
    """
    
    def __init__(self, sqlite_db_path: str = "scraper.db"):
        """
        Initialize the DorkSyncService.
        
        Args:
            sqlite_db_path: Path to the SQLite database used by AI learning engine
        """
        self.sqlite_db_path = sqlite_db_path
    
    def get_sqlite_dork_metrics(self) -> List[Dict[str, Any]]:
        """
        Fetch all dork metrics from the SQLite learning database.
        
        Returns:
            List of dork metric dictionaries with:
            - dork: The search query
            - times_used: Number of times used
            - total_results: Total search results returned
            - leads_found: Number of leads found
            - leads_with_phone: Number of leads with phone numbers
            - score: Calculated success score
            - pool: 'core' or 'explore'
            - last_used: Timestamp of last use
        """
        metrics = []
        try:
            with sqlite3.connect(self.sqlite_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT dork, times_used, total_results, leads_found, 
                           leads_with_phone, score, pool, last_used
                    FROM learning_dork_performance
                    ORDER BY score DESC, leads_with_phone DESC
                """)
                for row in cursor.fetchall():
                    metrics.append({
                        'dork': row['dork'],
                        'times_used': row['times_used'] or 0,
                        'total_results': row['total_results'] or 0,
                        'leads_found': row['leads_found'] or 0,
                        'leads_with_phone': row['leads_with_phone'] or 0,
                        'score': row['score'] or 0.0,
                        'pool': row['pool'] or 'explore',
                        'last_used': row['last_used'],
                    })
        except Exception as e:
            logger.warning(f"Could not fetch SQLite dork metrics: {e}")
        
        return metrics
    
    def sync_dork_to_django(self, dork_query: str, metrics: Dict[str, Any],
                            create_if_missing: bool = False,
                            extraction_patterns: Optional[List[str]] = None,
                            top_domains: Optional[List[str]] = None,
                            phone_patterns: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Sync a single dork's metrics to Django SearchDork model.
        
        Args:
            dork_query: The search query string
            metrics: Dictionary with dork metrics
            create_if_missing: If True, create new SearchDork if not found
            extraction_patterns: List of successful extraction patterns
            top_domains: List of top-performing domains
            phone_patterns: List of successful phone patterns
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            from telis_recruitment.scraper_control.models import SearchDork
            from django.utils import timezone
            
            try:
                search_dork = SearchDork.objects.get(query=dork_query)
            except SearchDork.DoesNotExist:
                if create_if_missing:
                    # Create new SearchDork with AI-generated flag
                    search_dork = SearchDork.objects.create(
                        query=dork_query,
                        category='custom',
                        description=f"Auto-synced from AI learning ({metrics.get('pool', 'explore')} pool)",
                        is_active=True,
                        ai_generated=True,
                    )
                    logger.info(f"Created new SearchDork from AI learning: {dork_query[:50]}...")
                else:
                    return False, f"SearchDork not found: {dork_query[:50]}..."
            
            # Update metrics using the model method
            search_dork.update_from_learning_metrics(
                times_used=metrics.get('times_used', 0),
                total_results=metrics.get('total_results', 0),
                leads_found=metrics.get('leads_found', 0),
                leads_with_phone=metrics.get('leads_with_phone', 0),
                score=metrics.get('score', 0.0),
            )
            
            # Update pattern data if provided
            if extraction_patterns:
                # Merge with existing patterns, keeping unique ones
                existing = search_dork.extraction_patterns or []
                merged = list(set(existing + extraction_patterns))[:50]  # Limit to 50
                search_dork.extraction_patterns = merged
            
            if top_domains:
                existing = search_dork.top_domains or []
                merged = list(set(existing + top_domains))[:20]  # Limit to 20
                search_dork.top_domains = merged
            
            if phone_patterns:
                existing = search_dork.phone_patterns or []
                merged = list(set(existing + phone_patterns))[:30]  # Limit to 30
                search_dork.phone_patterns = merged
            
            search_dork.save()
            return True, f"Synced: {dork_query[:50]}..."
            
        except ImportError as e:
            return False, f"Django not available: {e}"
        except Exception as e:
            logger.error(f"Error syncing dork to Django: {e}")
            return False, f"Error: {e}"
    
    def sync_all_dorks(self, create_successful: bool = True, 
                       min_times_used: int = 2,
                       min_leads_with_phone: int = 1) -> Dict[str, Any]:
        """
        Sync all qualifying dorks from SQLite to Django.
        
        Args:
            create_successful: If True, create new SearchDork entries for successful dorks
            min_times_used: Minimum times a dork must be used to be synced
            min_leads_with_phone: Minimum leads with phone required to create new entries
        
        Returns:
            Summary dictionary with sync statistics
        """
        summary = {
            'total_processed': 0,
            'updated': 0,
            'created': 0,
            'skipped': 0,
            'errors': [],
        }
        
        metrics = self.get_sqlite_dork_metrics()
        
        for dork_metrics in metrics:
            summary['total_processed'] += 1
            
            # Skip dorks that haven't been used enough
            if dork_metrics['times_used'] < min_times_used:
                summary['skipped'] += 1
                continue
            
            # Only auto-create for successful dorks
            should_create = (
                create_successful and 
                dork_metrics['leads_with_phone'] >= min_leads_with_phone and
                dork_metrics['pool'] == 'core'
            )
            
            success, message = self.sync_dork_to_django(
                dork_query=dork_metrics['dork'],
                metrics=dork_metrics,
                create_if_missing=should_create,
            )
            
            if success:
                if "Created" in message:
                    summary['created'] += 1
                else:
                    summary['updated'] += 1
            else:
                if "not found" in message.lower():
                    summary['skipped'] += 1
                else:
                    summary['errors'].append(message)
        
        logger.info(f"Dork sync complete: {summary['updated']} updated, "
                   f"{summary['created']} created, {summary['skipped']} skipped")
        
        return summary
    
    def get_top_performing_domains_for_dork(self, dork: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing domains for a specific dork from learning data.
        
        This analyzes which domains yield the best results for a given search query,
        enabling domain-specific optimization.
        
        Args:
            dork: The search query
            limit: Maximum number of domains to return
        
        Returns:
            List of domain performance dictionaries
        """
        # This would require cross-referencing with domain_performance table
        # For now, return empty list - can be enhanced with more sophisticated tracking
        return []
    
    def record_dork_result_with_sync(self, dork: str, results: int, 
                                     leads_found: int, leads_with_phone: int,
                                     domains: Optional[List[str]] = None,
                                     extraction_patterns: Optional[List[str]] = None,
                                     sync_to_django: bool = True) -> bool:
        """
        Record a dork result to both SQLite and optionally sync to Django.
        
        This is a convenience method that:
        1. Records metrics to SQLite for fast local tracking
        2. Optionally syncs to Django for CRM visibility
        
        Args:
            dork: The search query
            results: Number of search results
            leads_found: Number of leads found
            leads_with_phone: Number of leads with phone
            domains: List of domains found (for tracking top domains)
            extraction_patterns: List of extraction patterns used
            sync_to_django: Whether to sync to Django (default: True)
        
        Returns:
            True if recording was successful
        """
        try:
            # Record to SQLite first
            score = leads_with_phone / max(1, leads_found) if leads_found > 0 else 0.0
            pool = 'core' if leads_with_phone > 0 else 'explore'
            
            with sqlite3.connect(self.sqlite_db_path) as conn:
                # Check if dork exists
                cursor = conn.execute(
                    "SELECT times_used, total_results, leads_found, leads_with_phone "
                    "FROM learning_dork_performance WHERE dork = ?", 
                    (dork,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    new_times = existing[0] + 1
                    new_total_results = existing[1] + results
                    new_leads = existing[2] + leads_found
                    new_phone_leads = existing[3] + leads_with_phone
                    new_score = new_phone_leads / max(1, new_leads)
                    
                    conn.execute("""
                        UPDATE learning_dork_performance 
                        SET times_used = ?, total_results = ?, leads_found = ?, 
                            leads_with_phone = ?, score = ?, last_used = datetime('now'), 
                            pool = ?
                        WHERE dork = ?
                    """, (new_times, new_total_results, new_leads, new_phone_leads, 
                          new_score, pool, dork))
                    
                    metrics = {
                        'times_used': new_times,
                        'total_results': new_total_results,
                        'leads_found': new_leads,
                        'leads_with_phone': new_phone_leads,
                        'score': new_score,
                        'pool': pool,
                    }
                else:
                    conn.execute("""
                        INSERT INTO learning_dork_performance 
                        (dork, times_used, total_results, leads_found, leads_with_phone, 
                         score, last_used, pool)
                        VALUES (?, 1, ?, ?, ?, ?, datetime('now'), ?)
                    """, (dork, results, leads_found, leads_with_phone, score, pool))
                    
                    metrics = {
                        'times_used': 1,
                        'total_results': results,
                        'leads_found': leads_found,
                        'leads_with_phone': leads_with_phone,
                        'score': score,
                        'pool': pool,
                    }
                
                conn.commit()
            
            # Sync to Django if requested and dork was successful
            if sync_to_django and leads_with_phone > 0:
                self.sync_dork_to_django(
                    dork_query=dork,
                    metrics=metrics,
                    create_if_missing=True,  # Create new SearchDork for successful dorks
                    top_domains=domains,
                    extraction_patterns=extraction_patterns,
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording dork result: {e}")
            return False


# Convenience function for easy import
def get_dork_sync_service(sqlite_db_path: str = "scraper.db") -> DorkSyncService:
    """
    Get a DorkSyncService instance.
    
    Args:
        sqlite_db_path: Path to SQLite database
    
    Returns:
        DorkSyncService instance
    """
    return DorkSyncService(sqlite_db_path=sqlite_db_path)
