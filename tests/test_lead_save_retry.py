"""
Unit tests for lead save retry logic
=====================================
Tests to verify that lead save operations retry on transient errors.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from luca_scraper.repository import upsert_lead_sqlite


class TestLeadSaveRetry:
    """Test retry logic for lead saving operations."""
    
    def test_retry_on_database_locked_error(self):
        """Test that upsert retries on database locked errors."""
        # Mock the db connection to simulate lock errors
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        
        # Simulate database locked error on first two attempts, success on third
        call_count = 0
        def side_effect_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("database is locked")
            # On success, return nothing (successful execute)
            return None
        
        mock_cursor.execute.side_effect = side_effect_execute
        mock_cursor.fetchone.return_value = None  # No existing lead
        mock_cursor.lastrowid = 1
        
        with patch("luca_scraper.repository.db", mock_db):
            data = {
                'name': 'Test Lead',
                'email': 'test@example.com',
                'score': 80,
            }
            
            start_time = time.time()
            lead_id, created = upsert_lead_sqlite(data, max_retries=3, retry_delay=0.01)
            elapsed = time.time() - start_time
            
            # Should succeed after retries
            assert lead_id == 1
            assert created is True
            
            # Should have taken some time due to retries (at least 2 delays)
            # First retry: 0.01s, second retry: 0.02s = 0.03s minimum
            assert elapsed >= 0.03
            
            # Should have attempted 3 times
            assert call_count == 3
    
    def test_retry_with_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        
        # Simulate database locked error on all attempts
        mock_cursor.execute.side_effect = Exception("database is locked")
        
        with patch("luca_scraper.repository.db", mock_db):
            data = {
                'name': 'Test Lead',
                'email': 'test@example.com',
                'score': 80,
            }
            
            start_time = time.time()
            
            # Should fail after max retries
            with pytest.raises(Exception, match="database is locked"):
                upsert_lead_sqlite(data, max_retries=3, retry_delay=0.01)
            
            elapsed = time.time() - start_time
            
            # With exponential backoff:
            # Attempt 1: fail immediately
            # Attempt 2: wait 0.01s (0.01 * 2^0), then fail
            # Attempt 3: wait 0.02s (0.01 * 2^1), then fail
            # Total minimum wait time: 0.01s + 0.02s = 0.03s
            assert elapsed >= 0.03
    
    def test_no_retry_on_non_transient_error(self):
        """Test that non-transient errors are not retried."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        
        # Simulate a non-transient error (e.g., constraint violation)
        call_count = 0
        def side_effect_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("UNIQUE constraint failed")
        
        mock_cursor.execute.side_effect = side_effect_execute
        
        with patch("luca_scraper.repository.db", mock_db):
            data = {
                'name': 'Test Lead',
                'email': 'test@example.com',
                'score': 80,
            }
            
            # Should fail immediately without retries
            with pytest.raises(Exception, match="UNIQUE constraint failed"):
                upsert_lead_sqlite(data, max_retries=3, retry_delay=0.01)
            
            # Should have attempted only once (no retries)
            assert call_count == 1
    
    def test_successful_save_without_retry(self):
        """Test that successful save completes immediately without retries."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        
        # Simulate successful execution
        call_count = 0
        def side_effect_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return None
        
        mock_cursor.execute.side_effect = side_effect_execute
        mock_cursor.fetchone.return_value = None  # No existing lead
        mock_cursor.lastrowid = 42
        
        with patch("luca_scraper.repository.db", mock_db):
            data = {
                'name': 'Test Lead',
                'email': 'test@example.com',
                'score': 80,
            }
            
            start_time = time.time()
            lead_id, created = upsert_lead_sqlite(data, max_retries=3, retry_delay=0.01)
            elapsed = time.time() - start_time
            
            # Should succeed immediately
            assert lead_id == 42
            assert created is True
            
            # Should complete quickly (no retries)
            assert elapsed < 0.1
            
            # Should have executed queries only once
            assert call_count >= 1  # At least one for the insert


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
