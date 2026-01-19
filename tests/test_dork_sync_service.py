# -*- coding: utf-8 -*-
"""
Tests for DorkSyncService - AI Learning to CRM Integration.

These tests verify the synchronization of AI learning metrics from SQLite
to Django's SearchDork model.
"""

import pytest
import sqlite3
import os
import tempfile
from unittest.mock import patch, MagicMock

# Check if Django is available
try:
    import django
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

# Import the sync service
from telis_recruitment.scraper_control.services.dork_sync import DorkSyncService, get_dork_sync_service


@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database with learning tables."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Create the learning tables
    conn = sqlite3.connect(path)
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
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sync_service(temp_sqlite_db):
    """Create a DorkSyncService with temporary database."""
    return DorkSyncService(sqlite_db_path=temp_sqlite_db)


@pytest.fixture
def populated_sqlite_db(temp_sqlite_db):
    """Populate SQLite database with test dork metrics."""
    conn = sqlite3.connect(temp_sqlite_db)
    
    # Insert test dorks with varying performance
    test_dorks = [
        ("site:example.com Vertrieb", 5, 50, 10, 5, 0.5, "core"),
        ("Handynummer Ansprechpartner", 10, 100, 20, 8, 0.4, "core"),
        ("test explore dork", 1, 5, 0, 0, 0.0, "explore"),
        ("successful new dork", 3, 30, 6, 3, 0.5, "core"),
    ]
    
    for dork, times, results, leads, phone, score, pool in test_dorks:
        conn.execute('''
            INSERT INTO learning_dork_performance 
            (dork, times_used, total_results, leads_found, leads_with_phone, score, pool, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (dork, times, results, leads, phone, score, pool))
    
    conn.commit()
    conn.close()
    
    return temp_sqlite_db


class TestDorkSyncServiceInit:
    """Tests for DorkSyncService initialization."""
    
    def test_init_with_default_path(self):
        """Test service initializes with default database path."""
        service = DorkSyncService()
        assert service.sqlite_db_path == "scraper.db"
    
    def test_init_with_custom_path(self, temp_sqlite_db):
        """Test service initializes with custom database path."""
        service = DorkSyncService(sqlite_db_path=temp_sqlite_db)
        assert service.sqlite_db_path == temp_sqlite_db


class TestGetSqliteMetrics:
    """Tests for fetching metrics from SQLite."""
    
    def test_get_empty_metrics(self, sync_service):
        """Test getting metrics from empty database."""
        metrics = sync_service.get_sqlite_dork_metrics()
        assert metrics == []
    
    def test_get_populated_metrics(self, populated_sqlite_db):
        """Test getting metrics from populated database."""
        service = DorkSyncService(sqlite_db_path=populated_sqlite_db)
        metrics = service.get_sqlite_dork_metrics()
        
        assert len(metrics) == 4
        # Should be sorted by score DESC
        assert metrics[0]['score'] >= metrics[-1]['score']
        
        # Check first metric has all fields
        first = metrics[0]
        assert 'dork' in first
        assert 'times_used' in first
        assert 'total_results' in first
        assert 'leads_found' in first
        assert 'leads_with_phone' in first
        assert 'score' in first
        assert 'pool' in first
    
    def test_metrics_handle_missing_db(self):
        """Test graceful handling of missing database."""
        service = DorkSyncService(sqlite_db_path="/nonexistent/path.db")
        metrics = service.get_sqlite_dork_metrics()
        assert metrics == []


class TestRecordDorkResultWithSync:
    """Tests for recording dork results with CRM sync."""
    
    def test_record_new_dork(self, sync_service, temp_sqlite_db):
        """Test recording a new dork result."""
        result = sync_service.record_dork_result_with_sync(
            dork="new test dork",
            results=10,
            leads_found=5,
            leads_with_phone=3,
            sync_to_django=False,  # Don't try to sync to Django in unit tests
        )
        
        assert result is True
        
        # Verify stored in SQLite
        conn = sqlite3.connect(temp_sqlite_db)
        cursor = conn.execute(
            "SELECT times_used, leads_found, leads_with_phone, score, pool "
            "FROM learning_dork_performance WHERE dork = ?",
            ("new test dork",)
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[0] == 1  # times_used
        assert row[1] == 5  # leads_found
        assert row[2] == 3  # leads_with_phone
        assert row[3] == 0.6  # score (3/5)
        assert row[4] == "core"  # pool (has phone leads)
    
    def test_record_updates_existing_dork(self, sync_service, temp_sqlite_db):
        """Test recording updates existing dork metrics."""
        # First record
        sync_service.record_dork_result_with_sync(
            dork="update test dork",
            results=10,
            leads_found=5,
            leads_with_phone=2,
            sync_to_django=False,
        )
        
        # Second record
        sync_service.record_dork_result_with_sync(
            dork="update test dork",
            results=20,
            leads_found=8,
            leads_with_phone=4,
            sync_to_django=False,
        )
        
        # Verify cumulative metrics
        conn = sqlite3.connect(temp_sqlite_db)
        cursor = conn.execute(
            "SELECT times_used, total_results, leads_found, leads_with_phone "
            "FROM learning_dork_performance WHERE dork = ?",
            ("update test dork",)
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] == 2  # times_used
        assert row[1] == 30  # total_results (10 + 20)
        assert row[2] == 13  # leads_found (5 + 8)
        assert row[3] == 6  # leads_with_phone (2 + 4)
    
    def test_record_explore_pool_for_no_phone_leads(self, sync_service, temp_sqlite_db):
        """Test dork goes to explore pool when no phone leads."""
        sync_service.record_dork_result_with_sync(
            dork="no phone dork",
            results=10,
            leads_found=5,
            leads_with_phone=0,
            sync_to_django=False,
        )
        
        conn = sqlite3.connect(temp_sqlite_db)
        cursor = conn.execute(
            "SELECT pool FROM learning_dork_performance WHERE dork = ?",
            ("no phone dork",)
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] == "explore"


class TestSyncAllDorks:
    """Tests for bulk sync functionality."""
    
    @patch('telis_recruitment.scraper_control.services.dork_sync.DorkSyncService.sync_dork_to_django')
    def test_sync_all_filters_by_min_uses(self, mock_sync, populated_sqlite_db):
        """Test sync_all_dorks respects min_times_used filter."""
        mock_sync.return_value = (True, "Synced")
        
        service = DorkSyncService(sqlite_db_path=populated_sqlite_db)
        summary = service.sync_all_dorks(
            create_successful=False,
            min_times_used=5,  # Only dorks used 5+ times
            min_leads_with_phone=1,
        )
        
        # Should process all 4 but skip 2 (times_used < 5)
        assert summary['total_processed'] == 4
        assert summary['skipped'] >= 2  # At least 2 don't meet min_times_used
    
    def test_sync_all_returns_summary(self, populated_sqlite_db):
        """Test sync_all_dorks returns proper summary dict."""
        service = DorkSyncService(sqlite_db_path=populated_sqlite_db)
        
        with patch.object(service, 'sync_dork_to_django') as mock_sync:
            mock_sync.return_value = (False, "SearchDork not found")
            
            summary = service.sync_all_dorks(
                create_successful=False,
                min_times_used=1,
            )
        
        assert 'total_processed' in summary
        assert 'updated' in summary
        assert 'created' in summary
        assert 'skipped' in summary
        assert 'errors' in summary
        assert isinstance(summary['errors'], list)


class TestGetDorkSyncServiceHelper:
    """Tests for the convenience function."""
    
    def test_get_dork_sync_service_returns_instance(self):
        """Test helper function returns DorkSyncService instance."""
        service = get_dork_sync_service()
        assert isinstance(service, DorkSyncService)
    
    def test_get_dork_sync_service_with_custom_path(self, temp_sqlite_db):
        """Test helper accepts custom database path."""
        service = get_dork_sync_service(sqlite_db_path=temp_sqlite_db)
        assert service.sqlite_db_path == temp_sqlite_db


class TestDorkSyncServiceIntegration:
    """Integration tests for DorkSyncService (require Django)."""
    
    @pytest.mark.django_db
    @pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not available")
    def test_sync_to_existing_searchdork(self, populated_sqlite_db):
        """Test syncing to an existing SearchDork model."""
        from telis_recruitment.scraper_control.models import SearchDork
        
        # Create a SearchDork that matches one of our test dorks
        SearchDork.objects.create(
            query="site:example.com Vertrieb",
            category="default",
            is_active=True,
        )
        
        service = DorkSyncService(sqlite_db_path=populated_sqlite_db)
        metrics = {
            'times_used': 5,
            'total_results': 50,
            'leads_found': 10,
            'leads_with_phone': 5,
            'score': 0.5,
            'pool': 'core',
        }
        
        success, message = service.sync_dork_to_django(
            dork_query="site:example.com Vertrieb",
            metrics=metrics,
            create_if_missing=False,
        )
        
        assert success is True
        
        # Verify the SearchDork was updated
        dork = SearchDork.objects.get(query="site:example.com Vertrieb")
        assert dork.times_used == 5
        assert dork.leads_found == 10
        assert dork.leads_with_phone == 5
        assert dork.success_rate == 0.5
        assert dork.last_synced_at is not None
    
    @pytest.mark.django_db
    @pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not available")
    def test_sync_creates_new_searchdork(self, populated_sqlite_db):
        """Test syncing creates new SearchDork when create_if_missing=True."""
        from telis_recruitment.scraper_control.models import SearchDork
        
        service = DorkSyncService(sqlite_db_path=populated_sqlite_db)
        metrics = {
            'times_used': 3,
            'total_results': 30,
            'leads_found': 6,
            'leads_with_phone': 3,
            'score': 0.5,
            'pool': 'core',
        }
        
        success, message = service.sync_dork_to_django(
            dork_query="brand new ai dork",
            metrics=metrics,
            create_if_missing=True,
        )
        
        assert success is True
        assert "Created" in message or "Synced" in message
        
        # Verify the new SearchDork was created
        dork = SearchDork.objects.get(query="brand new ai dork")
        assert dork.ai_generated is True
        assert dork.times_used == 3
        assert dork.leads_with_phone == 3
    
    @pytest.mark.django_db
    @pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not available")
    def test_sync_adds_extraction_patterns(self, populated_sqlite_db):
        """Test syncing adds extraction patterns to SearchDork."""
        from telis_recruitment.scraper_control.models import SearchDork
        
        SearchDork.objects.create(
            query="pattern test dork",
            category="default",
            is_active=True,
        )
        
        service = DorkSyncService(sqlite_db_path=populated_sqlite_db)
        metrics = {'times_used': 1, 'total_results': 10, 'leads_found': 2, 
                   'leads_with_phone': 1, 'score': 0.5, 'pool': 'core'}
        
        success, _ = service.sync_dork_to_django(
            dork_query="pattern test dork",
            metrics=metrics,
            extraction_patterns=["div.contact-phone", "span.mobile"],
            top_domains=["example.com", "test.de"],
        )
        
        assert success is True
        
        dork = SearchDork.objects.get(query="pattern test dork")
        assert "div.contact-phone" in dork.extraction_patterns
        assert "example.com" in dork.top_domains
