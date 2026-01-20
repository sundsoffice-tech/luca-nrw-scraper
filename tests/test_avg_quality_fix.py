#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for avg_quality calculation fix in learning_engine.py
This test validates the off-by-one error fix in record_domain_success.
"""

import os
import sqlite3
import tempfile
import pytest
from learning_engine import LearningEngine


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def learning_engine(temp_db):
    """Create a learning engine instance with temp database."""
    return LearningEngine(temp_db)


def test_avg_quality_calculation_single_update(learning_engine, temp_db):
    """Test that avg_quality is calculated correctly on a single update.
    
    This is the exact scenario from the problem statement:
    - Entry with total_visits=1 and avg_quality=0.5
    - Call record_domain_success with quality=1.0
    - Expected new avg_quality: 0.75
    """
    domain = "test-domain.com"
    
    # Manually insert initial entry with total_visits=1, avg_quality=0.5
    con = sqlite3.connect(temp_db)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO learning_domains 
        (domain, total_visits, successful_extractions, leads_found, avg_quality, last_visit, score)
        VALUES (?, 1, 1, 1, 0.5, CURRENT_TIMESTAMP, 0.5)
    """, (domain,))
    con.commit()
    con.close()
    
    # Now call record_domain_success with quality=1.0
    learning_engine.record_domain_success(
        domain=domain,
        leads_found=1,
        quality=1.0,
        has_phone=True
    )
    
    # Check that avg_quality is now 0.75
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM learning_domains WHERE domain = ?", (domain,))
    row = cur.fetchone()
    con.close()
    
    assert row is not None, f"Domain {domain} not found in database"
    assert row['total_visits'] == 2, f"Expected total_visits=2, got {row['total_visits']}"
    
    # The expected avg_quality is (0.5 * 1 + 1.0) / 2 = 1.5 / 2 = 0.75
    expected_avg = 0.75
    actual_avg = row['avg_quality']
    
    assert abs(actual_avg - expected_avg) < 0.001, \
        f"Expected avg_quality={expected_avg}, got {actual_avg}"


def test_avg_quality_calculation_multiple_updates(learning_engine, temp_db):
    """Test that avg_quality is calculated correctly over multiple updates."""
    domain = "multi-test.com"
    
    # First insert
    learning_engine.record_domain_success(
        domain=domain,
        leads_found=1,
        quality=0.5,
        has_phone=True
    )
    
    # Check first insert
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM learning_domains WHERE domain = ?", (domain,))
    row = cur.fetchone()
    con.close()
    
    assert row['total_visits'] == 1
    assert abs(row['avg_quality'] - 0.5) < 0.001
    
    # Second update with quality=1.0
    learning_engine.record_domain_success(
        domain=domain,
        leads_found=1,
        quality=1.0,
        has_phone=True
    )
    
    # Check second update: avg should be (0.5 + 1.0) / 2 = 0.75
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM learning_domains WHERE domain = ?", (domain,))
    row = cur.fetchone()
    con.close()
    
    assert row['total_visits'] == 2
    assert abs(row['avg_quality'] - 0.75) < 0.001
    
    # Third update with quality=0.6
    learning_engine.record_domain_success(
        domain=domain,
        leads_found=1,
        quality=0.6,
        has_phone=True
    )
    
    # Check third update: avg should be (0.5 + 1.0 + 0.6) / 3 = 0.7
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM learning_domains WHERE domain = ?", (domain,))
    row = cur.fetchone()
    con.close()
    
    assert row['total_visits'] == 3
    assert abs(row['avg_quality'] - 0.7) < 0.001


def test_email_regex_pattern():
    """Test that the email regex pattern correctly matches valid email addresses."""
    import re
    from learning_engine import extract_competitor_intel
    
    # Test that extract_competitor_intel correctly extracts emails
    test_content = """
    Contact us at hr@example.com for job opportunities.
    You can also reach recruiting@test-company.de
    or sales@subdomain.example.org
    """
    
    intel = extract_competitor_intel(
        url="https://example.com/jobs",
        title="Job Posting",
        snippet="",
        content=test_content
    )
    
    assert "hr_emails" in intel
    emails = intel["hr_emails"]
    
    # Should have extracted the email addresses
    assert len(emails) >= 2
    assert "hr@example.com" in emails or "hr@example.com" in ' '.join(emails)
    assert "recruiting@test-company.de" in emails or "test-company.de" in ' '.join(emails)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
