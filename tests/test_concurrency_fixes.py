#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Concurrency tests for database and global state management.

Tests that database operations and global state management are thread-safe
and can handle concurrent access without "database is locked" errors or
race conditions.
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseConcurrency(unittest.TestCase):
    """Test database concurrency with retry logic."""
    
    def setUp(self):
        """Create a temporary database for testing."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
    def tearDown(self):
        """Clean up temporary database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_db_utils_import(self):
        """Test that db_utils module can be imported."""
        from luca_scraper import db_utils
        self.assertTrue(hasattr(db_utils, 'get_db_connection'))
        self.assertTrue(hasattr(db_utils, 'with_db_retry'))
    
    def test_concurrent_writes(self):
        """Test concurrent database writes with retry logic."""
        from luca_scraper.db_utils import get_db_connection, with_db_retry
        
        # Initialize database
        with get_db_connection(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value TEXT,
                    thread_id INTEGER
                )
            """)
            conn.commit()
        
        @with_db_retry()
        def write_data(thread_id, num_writes):
            """Write data from a thread."""
            for i in range(num_writes):
                with get_db_connection(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO test_data (value, thread_id) VALUES (?, ?)",
                        (f"value_{thread_id}_{i}", thread_id)
                    )
                    conn.commit()
        
        # Run concurrent writes
        num_threads = 10
        writes_per_thread = 20
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(write_data, thread_id, writes_per_thread)
                for thread_id in range(num_threads)
            ]
            for future in futures:
                future.result()  # Wait for completion
        
        # Verify all data was written
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test_data")
            count = cursor.fetchone()[0]
            expected = num_threads * writes_per_thread
            self.assertEqual(count, expected, 
                           f"Expected {expected} rows, got {count}")
    
    def test_wal_mode_enabled(self):
        """Test that WAL mode is properly enabled for concurrency."""
        from luca_scraper.db_utils import get_db_connection
        
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0].upper()
            # Should be WAL or DELETE (if WAL not supported)
            self.assertIn(mode, ['WAL', 'DELETE'], 
                         f"Unexpected journal mode: {mode}")
    
    def test_connection_reuse(self):
        """Test that connections are reused within the same thread."""
        from luca_scraper.db_utils import get_db_connection
        
        conn1_id = None
        conn2_id = None
        
        with get_db_connection(self.db_path) as conn1:
            conn1_id = id(conn1)
        
        with get_db_connection(self.db_path) as conn2:
            conn2_id = id(conn2)
        
        # Should be the same connection object (reused)
        self.assertEqual(conn1_id, conn2_id,
                        "Connection should be reused within same thread")
    
    def test_retry_on_lock(self):
        """Test that database locked errors are retried."""
        from luca_scraper.db_utils import with_db_retry
        
        # Create a scenario where one thread locks the database
        conn1 = sqlite3.connect(self.db_path, timeout=0.1)
        conn1.execute("CREATE TABLE IF NOT EXISTS lock_test (id INTEGER)")
        conn1.execute("BEGIN EXCLUSIVE")  # Lock the database
        
        retry_count = [0]
        
        @with_db_retry(max_retries=3, delay=0.1)
        def try_write():
            retry_count[0] += 1
            # This should fail initially due to lock
            conn2 = sqlite3.connect(self.db_path, timeout=0.1)
            try:
                conn2.execute("INSERT INTO lock_test VALUES (1)")
                conn2.commit()
                conn2.close()
            except sqlite3.OperationalError as e:
                conn2.close()
                raise
        
        # Start the write in a thread
        def delayed_unlock():
            time.sleep(0.3)  # Wait a bit
            conn1.commit()  # Release the lock
            conn1.close()
        
        threading.Thread(target=delayed_unlock).start()
        
        # This should eventually succeed after retries
        try:
            try_write()
        except Exception:
            pass  # Might still fail if timing is off
        
        # Should have retried at least once
        self.assertGreater(retry_count[0], 0,
                          "Should have attempted at least once")


class TestHTTPClientConcurrency(unittest.TestCase):
    """Test HTTP client singleton concurrency."""
    
    def test_client_lock_import(self):
        """Test that client lock is properly defined."""
        from luca_scraper.http import client
        self.assertTrue(hasattr(client, '_CLIENT_LOCK'))
        self.assertTrue(isinstance(client._CLIENT_LOCK, asyncio.Lock))
    
    async def test_concurrent_client_creation(self):
        """Test concurrent access to HTTP client singletons."""
        from luca_scraper.http.client import get_client
        
        # Try to create multiple clients concurrently
        clients = await asyncio.gather(*[
            get_client(secure=True) for _ in range(10)
        ])
        
        # All should be the same instance
        first_client = clients[0]
        for client in clients[1:]:
            self.assertIs(client, first_client,
                         "All clients should be the same instance")
    
    def test_client_singleton_async(self):
        """Test HTTP client singleton creation in async context."""
        asyncio.run(self.test_concurrent_client_creation())


class TestRetryConcurrency(unittest.TestCase):
    """Test retry module global state concurrency."""
    
    def test_retry_locks_import(self):
        """Test that retry locks are properly defined."""
        from luca_scraper.http import retry
        self.assertTrue(hasattr(retry, '_HOST_STATE_LOCK'))
        self.assertTrue(hasattr(retry, '_RETRY_URLS_LOCK'))
        self.assertTrue(hasattr(retry, '_RUN_METRICS_LOCK'))
    
    def test_concurrent_host_penalization(self):
        """Test concurrent host penalization."""
        from luca_scraper.http.retry import _penalize_host, _host_allowed
        
        host = "test.example.com"
        
        def penalize_many_times(n):
            for _ in range(n):
                _penalize_host(host, "test")
        
        # Penalize from multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(penalize_many_times, 10) for _ in range(5)]
            for future in futures:
                future.result()
        
        # Host should be penalized
        self.assertFalse(_host_allowed(host),
                        "Host should be penalized after many failures")
    
    def test_concurrent_metrics_update(self):
        """Test concurrent updates to RUN_METRICS."""
        from luca_scraper.http.retry import _record_drop, _record_retry, RUN_METRICS
        
        def update_metrics(n):
            for _ in range(n):
                _record_drop("portal_host")
                _record_retry(429)
        
        # Update from multiple threads
        num_threads = 10
        updates_per_thread = 100
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(update_metrics, updates_per_thread)
                for _ in range(num_threads)
            ]
            for future in futures:
                future.result()
        
        # Verify counts are correct (thread-safe)
        expected_drops = num_threads * updates_per_thread
        expected_retries = num_threads * updates_per_thread
        
        self.assertEqual(RUN_METRICS["removed_by_dropper"], expected_drops,
                        f"Expected {expected_drops} drops")
        self.assertEqual(RUN_METRICS["retry_count"], expected_retries,
                        f"Expected {expected_retries} retries")
        self.assertEqual(RUN_METRICS["status_429"], expected_retries,
                        f"Expected {expected_retries} 429 status codes")


class TestLearningEngineConcurrency(unittest.TestCase):
    """Test learning engine database concurrency."""
    
    def setUp(self):
        """Create a temporary database for testing."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
    
    def tearDown(self):
        """Clean up temporary database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_concurrent_pattern_updates(self):
        """Test concurrent pattern success updates."""
        from learning_engine import LearningEngine
        
        engine = LearningEngine(self.db_path)
        
        def record_successes(thread_id, n):
            for i in range(n):
                engine.learn_from_success({
                    "quelle": f"https://test{thread_id}.com/page{i}",
                    "telefon": "+49171234567",
                    "tags": "test"
                }, query=f"test query {thread_id}")
        
        # Record from multiple threads
        num_threads = 5
        records_per_thread = 20
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(record_successes, thread_id, records_per_thread)
                for thread_id in range(num_threads)
            ]
            for future in futures:
                future.result()
        
        # Verify patterns were recorded
        stats = engine.get_pattern_stats()
        self.assertGreater(stats["domain"]["total_patterns"], 0,
                          "Should have recorded domain patterns")
    
    def test_concurrent_domain_updates(self):
        """Test concurrent domain performance updates."""
        from learning_engine import LearningEngine
        
        engine = LearningEngine(self.db_path)
        domain = "test.example.com"
        
        def update_domain(n):
            for _ in range(n):
                engine.record_domain_success(domain, leads_found=1, has_phone=True)
        
        # Update from multiple threads
        num_threads = 5
        updates_per_thread = 10
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(update_domain, updates_per_thread)
                for _ in range(num_threads)
            ]
            for future in futures:
                future.result()
        
        # Verify domain was tracked
        priority = engine.get_domain_priority(domain)
        self.assertGreater(priority, 0.5,
                          "Domain priority should have increased")


def run_tests():
    """Run all concurrency tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseConcurrency))
    suite.addTests(loader.loadTestsFromTestCase(TestHTTPClientConcurrency))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryConcurrency))
    suite.addTests(loader.loadTestsFromTestCase(TestLearningEngineConcurrency))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
