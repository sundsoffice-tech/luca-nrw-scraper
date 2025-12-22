# -*- coding: utf-8 -*-
"""Tests for the learning engine module."""

import pytest
import os
import sqlite3
import tempfile
from learning_engine import LearningEngine, is_mobile_number, is_job_posting


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


class TestMobileNumberDetection:
    """Tests for mobile number detection."""
    
    def test_german_mobile_numbers(self):
        """Test detection of German mobile numbers."""
        # Valid German mobile numbers
        assert is_mobile_number("+491761234567") is True
        assert is_mobile_number("01761234567") is True
        assert is_mobile_number("+49 176 1234567") is True
        assert is_mobile_number("0176 1234567") is True
        
        assert is_mobile_number("+491501234567") is True
        assert is_mobile_number("01501234567") is True
        
        assert is_mobile_number("+491621234567") is True
        assert is_mobile_number("01621234567") is True
        
        assert is_mobile_number("+491701234567") is True
        assert is_mobile_number("01701234567") is True
    
    def test_german_landline_numbers(self):
        """Test that German landline numbers are rejected."""
        # German landline numbers should return False
        assert is_mobile_number("+49211123456") is False
        assert is_mobile_number("0211123456") is False
        assert is_mobile_number("+49 211 123456") is False
        assert is_mobile_number("0211 123 456") is False
    
    def test_austrian_mobile_numbers(self):
        """Test detection of Austrian mobile numbers."""
        assert is_mobile_number("+436601234567") is True
        assert is_mobile_number("+436701234567") is True
        assert is_mobile_number("+436801234567") is True
    
    def test_swiss_mobile_numbers(self):
        """Test detection of Swiss mobile numbers."""
        assert is_mobile_number("+41761234567") is True
        assert is_mobile_number("+41771234567") is True
        assert is_mobile_number("+41781234567") is True
        assert is_mobile_number("+41791234567") is True
    
    def test_invalid_numbers(self):
        """Test that invalid numbers are rejected."""
        assert is_mobile_number("") is False
        assert is_mobile_number(None) is False
        assert is_mobile_number("123") is False
        assert is_mobile_number("abc") is False


class TestJobPostingDetection:
    """Tests for job posting detection."""
    
    def test_job_posting_url_patterns(self):
        """Test detection via URL patterns."""
        assert is_job_posting(url="https://example.com/jobs/sales-manager") is True
        assert is_job_posting(url="https://example.com/karriere/vertrieb") is True
        assert is_job_posting(url="https://example.com/stellenangebot/123") is True
        assert is_job_posting(url="https://example.com/career/sales") is True
        assert is_job_posting(url="https://example.com/vacancy/manager") is True
    
    def test_job_posting_title_patterns(self):
        """Test detection via title patterns."""
        assert is_job_posting(title="Vertriebsmitarbeiter gesucht") is True
        assert is_job_posting(title="Wir suchen Sales Manager (m/w/d)") is True
        assert is_job_posting(title="Stellenangebot: Account Manager") is True
        assert is_job_posting(title="Job bei Top Company") is True
    
    def test_job_posting_content_signals(self):
        """Test detection via content signals."""
        # Multiple job signals
        content = """
        Wir suchen einen Vertriebsmitarbeiter (m/w/d) in Vollzeit.
        Ihre Aufgaben: Kaltakquise, Kundenbetreuung
        Wir bieten: Firmenwagen, unbefristete Anstellung
        Bewerben Sie sich jetzt!
        """
        assert is_job_posting(content=content) is True
        
        # Strong single indicator
        assert is_job_posting(content="Stellenanzeige: Sales Manager") is True
        assert is_job_posting(content="Job-ID: 12345 - Apply now") is True
    
    def test_not_job_posting(self):
        """Test that non-job content is not flagged."""
        # Personal profile
        assert is_job_posting(
            title="Max Mustermann - Vertriebsleiter",
            content="Ich bin Vertriebsleiter mit 10 Jahren Erfahrung"
        ) is False
        
        # Company about page
        assert is_job_posting(
            url="https://example.com/ueber-uns",
            title="Über uns",
            content="Unser Team besteht aus erfahrenen Vertriebsmitarbeitern"
        ) is False
        
        # Contact page
        assert is_job_posting(
            url="https://example.com/kontakt",
            content="Kontaktieren Sie uns telefonisch oder per E-Mail"
        ) is False
    
    def test_job_seeking_not_job_posting(self):
        """Test that job seeking posts are not flagged as job postings."""
        # These are people looking for jobs, not companies hiring
        assert is_job_posting(
            content="Ich suche eine neue Herausforderung im Vertrieb"
        ) is False
        
        assert is_job_posting(
            title="Suche Job im Vertrieb NRW",
            content="Suche Stelle als Vertriebsmitarbeiter"
        ) is False


class TestLearningEngine:
    """Tests for the LearningEngine class."""
    
    def test_initialization(self, learning_engine, temp_db):
        """Test that learning engine initializes correctly."""
        # Check that table was created
        con = sqlite3.connect(temp_db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='success_patterns'")
        result = cur.fetchone()
        con.close()
        
        assert result is not None
        assert result[0] == "success_patterns"
    
    def test_learn_from_success(self, learning_engine):
        """Test learning from successful leads."""
        lead_data = {
            "quelle": "https://example.com/kontakt/team",
            "telefon": "+491761234567",
            "tags": "vertrieb,sales,mobile",
            "score": 95,
            "lead_type": "candidate"
        }
        
        learning_engine.learn_from_success(lead_data, query="vertrieb handynummer NRW")
        
        # Check that patterns were recorded
        domains = learning_engine.get_top_patterns("domain", min_confidence=0.0, min_successes=1)
        assert len(domains) > 0
        assert any("example.com" in d[0] for d in domains)
        
        terms = learning_engine.get_top_patterns("query_term", min_confidence=0.0, min_successes=1)
        assert len(terms) > 0
        assert any("vertrieb" in t[0] for t in terms)
    
    def test_get_top_patterns(self, learning_engine):
        """Test retrieving top patterns."""
        # Add multiple successful patterns
        for i in range(5):
            lead_data = {
                "quelle": f"https://example{i}.com/team",
                "telefon": "+491761234567",
                "tags": "vertrieb",
                "score": 90
            }
            learning_engine.learn_from_success(lead_data, query="vertrieb")
        
        # Get top domains
        top_domains = learning_engine.get_top_patterns("domain", min_confidence=0.0, min_successes=1, limit=10)
        assert len(top_domains) <= 10
        
        # Check structure of results
        for pattern_value, confidence, success_count in top_domains:
            assert isinstance(pattern_value, str)
            assert 0.0 <= confidence <= 1.0
            assert success_count >= 1
    
    def test_confidence_scoring(self, learning_engine):
        """Test that confidence scores are calculated correctly."""
        lead_data = {
            "quelle": "https://testdomain.com/page",
            "telefon": "+491761234567",
            "tags": "test",
            "score": 90
        }
        
        # Record success
        learning_engine.learn_from_success(lead_data)
        
        patterns = learning_engine.get_top_patterns("domain", min_confidence=0.0, min_successes=1)
        domain_pattern = next((p for p in patterns if "testdomain.com" in p[0]), None)
        
        assert domain_pattern is not None
        _, confidence, success_count = domain_pattern
        assert success_count >= 1
        assert confidence > 0.0
    
    def test_generate_optimized_queries(self, learning_engine):
        """Test query optimization based on learned patterns."""
        # Add some successful patterns
        for i in range(3):
            lead_data = {
                "quelle": f"https://gooddomain{i}.com/kontakt",
                "telefon": "+491761234567",
                "tags": "vertrieb",
                "score": 90
            }
            learning_engine.learn_from_success(lead_data, query="vertrieb handy kontakt")
        
        base_queries = ["vertrieb NRW", "sales manager"]
        optimized = learning_engine.generate_optimized_queries(base_queries)
        
        # Should include base queries plus learned patterns
        assert len(optimized) >= len(base_queries)
        assert "vertrieb NRW" in optimized
        assert "sales manager" in optimized
    
    def test_get_pattern_stats(self, learning_engine):
        """Test getting statistics about learned patterns."""
        # Add some test data
        lead_data = {
            "quelle": "https://example.com/team",
            "telefon": "+491761234567",
            "tags": "vertrieb,mobile",
            "score": 90
        }
        learning_engine.learn_from_success(lead_data, query="vertrieb kontakt")
        
        stats = learning_engine.get_pattern_stats()
        
        # Check stats structure
        assert "domain" in stats
        assert "query_term" in stats
        assert "url_path" in stats
        assert "content_signal" in stats
        
        # Check that we have some successes recorded
        total_successes = sum(s["total_successes"] for s in stats.values())
        assert total_successes > 0


class TestAILearningFeatures:
    """Tests for new AI learning features."""
    
    def test_new_tables_created(self, learning_engine, temp_db):
        """Test that new AI learning tables are created."""
        con = sqlite3.connect(temp_db)
        cur = con.cursor()
        
        # Check for new tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        
        assert 'extraction_patterns' in tables
        assert 'failed_extractions' in tables
        assert 'phone_patterns' in tables
        assert 'domain_performance' in tables
        assert 'ai_improvements' in tables
        
        con.close()
    
    def test_learn_from_failure(self, learning_engine):
        """Test recording extraction failures."""
        learning_engine.learn_from_failure(
            url="https://example.com/test",
            html_content="<html><body>Test</body></html>",
            reason="no_mobile_found",
            visible_phones=["0211123456"]  # Landline, not mobile
        )
        
        # Verify failure was recorded
        con = sqlite3.connect(learning_engine.db_path)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM failed_extractions")
        count = cur.fetchone()[0]
        assert count == 1
        con.close()
    
    def test_record_extraction_pattern(self, learning_engine):
        """Test recording successful extraction patterns."""
        learning_engine.record_extraction_pattern(
            pattern_type="phone_regex",
            pattern=r"\+49\s*1[567]\d{9}",
            description="Standard mobile pattern"
        )
        
        # Verify pattern was recorded
        con = sqlite3.connect(learning_engine.db_path)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM extraction_patterns")
        count = cur.fetchone()[0]
        assert count == 1
        con.close()
    
    def test_record_phone_pattern(self, learning_engine):
        """Test recording phone number patterns."""
        learning_engine.record_phone_pattern(
            pattern=r"0\s*1\s*7\s*6",
            pattern_type="spaced",
            example="0 1 7 6 1234567"
        )
        
        # Verify pattern was recorded
        con = sqlite3.connect(learning_engine.db_path)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM phone_patterns")
        count = cur.fetchone()[0]
        assert count == 1
        con.close()
    
    def test_update_domain_performance(self, learning_engine):
        """Test tracking domain performance."""
        # Record success
        learning_engine.update_domain_performance(
            domain="kleinanzeigen.de",
            success=True,
            rate_limited=False
        )
        
        # Record failure
        learning_engine.update_domain_performance(
            domain="kleinanzeigen.de",
            success=False,
            rate_limited=False
        )
        
        # Record rate limit
        learning_engine.update_domain_performance(
            domain="quoka.de",
            success=False,
            rate_limited=True
        )
        
        # Verify performance was tracked
        con = sqlite3.connect(learning_engine.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM domain_performance WHERE domain = ?", ("kleinanzeigen.de",))
        row = cur.fetchone()
        assert row is not None
        assert row['total_requests'] == 2
        assert row['successful_requests'] == 1
        assert row['success_rate'] == 0.5
        
        cur.execute("SELECT * FROM domain_performance WHERE domain = ?", ("quoka.de",))
        row = cur.fetchone()
        assert row is not None
        assert row['rate_limit_detected'] == 1
        
        con.close()
    
    def test_generate_improved_patterns(self, learning_engine):
        """Test generating improved patterns."""
        # Add some patterns first
        learning_engine.record_phone_pattern(
            pattern=r"0\s*1\s*[567]",
            pattern_type="spaced",
            example="0 1 7 6"
        )
        learning_engine.record_phone_pattern(
            pattern=r"0\s*1\s*[567]",
            pattern_type="spaced",
            example="0 1 6 2"
        )
        
        learning_engine.record_extraction_pattern(
            pattern_type="css_selector",
            pattern=".phone-number",
            description="Phone number class"
        )
        learning_engine.record_extraction_pattern(
            pattern_type="css_selector",
            pattern=".phone-number",
            description="Phone number class"
        )
        learning_engine.record_extraction_pattern(
            pattern_type="css_selector",
            pattern=".phone-number",
            description="Phone number class"
        )
        
        # Generate improvements
        improvements = learning_engine.generate_improved_patterns()
        
        assert isinstance(improvements, list)
        assert len(improvements) >= 1
        
        # Check structure
        for imp in improvements:
            assert 'type' in imp
            assert 'pattern' in imp
            assert 'description' in imp
    
    def test_optimize_portal_config(self, learning_engine):
        """Test portal configuration optimization."""
        # Add some portal performance data
        for i in range(15):
            learning_engine.update_domain_performance(
                domain="meinestadt.de",
                success=False,
                rate_limited=False
            )
        
        for i in range(10):
            learning_engine.update_domain_performance(
                domain="kleinanzeigen.de",
                success=True if i < 3 else False,
                rate_limited=False
            )
        
        # Get recommendations
        recommendations = learning_engine.optimize_portal_config()
        
        assert 'disable' in recommendations
        assert 'delay_increase' in recommendations
        assert 'prioritize' in recommendations
        
        # meinestadt should be recommended for disabling (0% success)
        disabled_domains = [r['domain'] for r in recommendations['disable']]
        assert 'meinestadt.de' in disabled_domains
    
    def test_get_ai_learning_stats(self, learning_engine):
        """Test getting comprehensive AI learning stats."""
        # Add some data
        learning_engine.record_phone_pattern(
            pattern=r"test",
            pattern_type="test",
            example="test"
        )
        learning_engine.learn_from_failure(
            url="https://test.com",
            html_content="test",
            reason="test"
        )
        learning_engine.update_domain_performance(
            domain="test.de",
            success=True,
            rate_limited=False
        )
        
        # Get stats
        stats = learning_engine.get_ai_learning_stats()
        
        assert 'phone_patterns_learned' in stats
        assert 'extraction_patterns' in stats
        assert 'failures_logged' in stats
        assert 'portals_tracked' in stats
        assert 'avg_portal_success_rate' in stats
        assert 'ai_improvements_generated' in stats
        
        assert stats['phone_patterns_learned'] >= 1
        assert stats['failures_logged'] >= 1
        assert stats['portals_tracked'] >= 1

