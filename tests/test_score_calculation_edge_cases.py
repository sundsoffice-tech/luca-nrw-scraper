# -*- coding: utf-8 -*-
"""
Tests for score calculation edge cases in record_dork_result.

This test file specifically addresses the issue where:
- leads_found=0 and leads_with_phone>0 (data inconsistency)
- The score calculation should handle these edge cases correctly
"""

import pytest
import os
import sqlite3
import tempfile
from learning_engine import ActiveLearningEngine


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def active_learning(temp_db):
    """Create an active learning engine instance."""
    from learning_engine import LearningEngine
    # First initialize the base learning engine to create tables
    base_engine = LearningEngine(temp_db)
    return ActiveLearningEngine(temp_db)


class TestScoreCalculationEdgeCases:
    """Tests for edge cases in score calculation."""
    
    def test_edge_case_leads_found_zero_but_leads_with_phone_positive(self, active_learning, temp_db):
        """
        Test the specific edge case mentioned in the issue:
        leads_found=0 and leads_with_phone=1 should result in score=1.0, not 0.0
        """
        dork = "edge case test dork"
        
        # This is the edge case: leads_found=0 but leads_with_phone=1
        # (shouldn't normally happen but could due to data inconsistency)
        active_learning.record_dork_result(
            dork=dork,
            results=10,
            leads_found=0,
            leads_with_phone=1
        )
        
        # Verify data was recorded correctly
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row['leads_found'] == 0
        assert row['leads_with_phone'] == 1
        # The score should be 1.0 (1 phone lead out of max(0, 1) = 1 lead)
        assert row['score'] == 1.0, f"Expected score 1.0 but got {row['score']}"
        assert row['pool'] == 'core'  # Should be in core pool since we have phone leads
    
    def test_normal_case_leads_with_phone_less_than_leads_found(self, active_learning, temp_db):
        """Test normal case where leads_with_phone < leads_found."""
        dork = "normal test dork"
        
        active_learning.record_dork_result(
            dork=dork,
            results=100,
            leads_found=10,
            leads_with_phone=3
        )
        
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row['leads_found'] == 10
        assert row['leads_with_phone'] == 3
        # Score should be 3/10 = 0.3
        assert abs(row['score'] - 0.3) < 0.001
        assert row['pool'] == 'core'
    
    def test_edge_case_both_zero(self, active_learning, temp_db):
        """Test edge case where both leads_found and leads_with_phone are 0."""
        dork = "zero dork"
        
        active_learning.record_dork_result(
            dork=dork,
            results=50,
            leads_found=0,
            leads_with_phone=0
        )
        
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row['leads_found'] == 0
        assert row['leads_with_phone'] == 0
        # Score should be 0 / max(1, max(0, 0)) = 0 / 1 = 0.0
        assert row['score'] == 0.0
        assert row['pool'] == 'explore'  # Should be in explore pool
    
    def test_edge_case_leads_with_phone_exceeds_leads_found(self, active_learning, temp_db):
        """Test edge case where leads_with_phone > leads_found (data inconsistency)."""
        dork = "inconsistent data dork"
        
        # Another data inconsistency: more phone leads than total leads
        active_learning.record_dork_result(
            dork=dork,
            results=20,
            leads_found=5,
            leads_with_phone=8  # More phone leads than total leads
        )
        
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row['leads_found'] == 5
        assert row['leads_with_phone'] == 8
        # Score should be 8 / max(1, max(5, 8)) = 8 / 8 = 1.0
        assert row['score'] == 1.0, f"Expected score 1.0 but got {row['score']}"
        assert row['pool'] == 'core'
    
    def test_cumulative_edge_case_handling(self, active_learning, temp_db):
        """Test that cumulative updates also handle edge cases correctly."""
        dork = "cumulative edge case dork"
        
        # First record: normal data
        active_learning.record_dork_result(
            dork=dork,
            results=10,
            leads_found=5,
            leads_with_phone=2
        )
        
        # Second record: edge case with leads_found=0 but leads_with_phone=3
        active_learning.record_dork_result(
            dork=dork,
            results=15,
            leads_found=0,
            leads_with_phone=3
        )
        
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row['times_used'] == 2
        assert row['leads_found'] == 5  # 5 + 0
        assert row['leads_with_phone'] == 5  # 2 + 3
        # Cumulative score: 5 phone leads / max(1, max(5 total, 5 phone)) = 5 / 5 = 1.0
        assert row['score'] == 1.0, f"Expected score 1.0 but got {row['score']}"
    
    def test_negative_values_handled_gracefully(self, active_learning, temp_db):
        """Test that negative values are handled gracefully (shouldn't happen but defensive)."""
        dork = "negative value dork"
        
        # Test with negative leads_found (shouldn't happen in practice)
        # The max() function should handle this
        active_learning.record_dork_result(
            dork=dork,
            results=10,
            leads_found=-1,  # Invalid but testing robustness
            leads_with_phone=2
        )
        
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        # Score should be 2 / max(1, max(-1, 2)) = 2 / 2 = 1.0
        assert row['score'] == 1.0
        assert row['pool'] == 'core'
    
    def test_perfect_score_scenario(self, active_learning, temp_db):
        """Test scenario where all leads have phone numbers."""
        dork = "perfect score dork"
        
        active_learning.record_dork_result(
            dork=dork,
            results=50,
            leads_found=10,
            leads_with_phone=10  # All leads have phones
        )
        
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row['leads_found'] == 10
        assert row['leads_with_phone'] == 10
        # Score should be perfect: 10 / 10 = 1.0
        assert row['score'] == 1.0
        assert row['pool'] == 'core'
    
    def test_very_low_success_rate(self, active_learning, temp_db):
        """Test with very low success rate."""
        dork = "low success dork"
        
        active_learning.record_dork_result(
            dork=dork,
            results=200,
            leads_found=100,
            leads_with_phone=1  # Only 1% have phone
        )
        
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM learning_dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row['leads_found'] == 100
        assert row['leads_with_phone'] == 1
        # Score should be 1 / 100 = 0.01
        assert abs(row['score'] - 0.01) < 0.001
        assert row['pool'] == 'core'  # Still core because has at least one phone
