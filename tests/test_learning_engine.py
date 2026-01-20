# -*- coding: utf-8 -*-
"""Tests for the learning engine module."""

import pytest
import os
import sqlite3
import tempfile
from learning_engine import LearningEngine, ActiveLearningEngine, is_mobile_number, is_job_posting


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


class TestActiveLearningEngine:
    """Tests for the ActiveLearningEngine class."""
    
    @pytest.fixture
    def active_learning(self, temp_db):
        """Create an active learning engine instance."""
        # First initialize the base learning engine to create tables
        base_engine = LearningEngine(temp_db)
        return ActiveLearningEngine(temp_db)
    
    def test_initialization(self, active_learning, temp_db):
        """Test that active learning engine initializes correctly."""
        # Check that new tables were created
        con = sqlite3.connect(temp_db)
        cur = con.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        
        assert 'learning_metrics' in tables
        assert 'dork_performance' in tables
        assert 'phone_patterns_learned' in tables
        assert 'host_backoff' in tables
        
        con.close()
    
    def test_record_portal_result(self, active_learning):
        """Test recording portal performance."""
        active_learning.record_portal_result(
            portal="kleinanzeigen",
            urls_crawled=100,
            leads_found=20,
            leads_with_phone=5,
            run_id=1
        )
        
        # Verify data was recorded
        con = sqlite3.connect(active_learning.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM learning_metrics WHERE portal = ?", ("kleinanzeigen",))
        row = cur.fetchone()
        
        assert row is not None
        assert row['urls_crawled'] == 100
        assert row['leads_found'] == 20
        assert row['leads_with_phone'] == 5
        assert row['success_rate'] == 0.05  # 5/100
        
        con.close()
    
    def test_should_skip_portal_good_performance(self, active_learning):
        """Test that good performing portals are not skipped."""
        # Record good performance
        for i in range(5):
            active_learning.record_portal_result(
                portal="kleinanzeigen",
                urls_crawled=100,
                leads_found=50,
                leads_with_phone=10,
                run_id=i
            )
        
        # Should NOT skip
        assert active_learning.should_skip_portal("kleinanzeigen") is False
    
    def test_should_skip_portal_poor_performance(self, active_learning):
        """Test that poor performing portals are skipped."""
        # Record poor performance (0% success rate)
        for i in range(5):
            active_learning.record_portal_result(
                portal="meinestadt",
                urls_crawled=100,
                leads_found=0,
                leads_with_phone=0,
                run_id=i
            )
        
        # Should skip
        assert active_learning.should_skip_portal("meinestadt") is True
    
    def test_should_skip_portal_no_data(self, active_learning):
        """Test that portals with no data are NOT skipped (should be tested)."""
        # Don't record any data for this portal
        # Should NOT skip (need to test new portals)
        assert active_learning.should_skip_portal("new_portal") is False
    
    def test_should_skip_portal_insufficient_runs(self, active_learning):
        """Test that portals with < 5 runs are NOT skipped even with poor performance."""
        # Record only 3 runs with 0% success rate
        for i in range(3):
            active_learning.record_portal_result(
                portal="test_portal",
                urls_crawled=100,
                leads_found=0,
                leads_with_phone=0,
                run_id=i
            )
        
        # Should NOT skip (need at least 5 runs)
        assert active_learning.should_skip_portal("test_portal") is False
    
    def test_should_skip_portal_marginal_performance(self, active_learning):
        """Test that portals with 5-10% success rate are skipped."""
        # Record 5 runs with 8% success rate
        for i in range(5):
            active_learning.record_portal_result(
                portal="marginal_portal",
                urls_crawled=100,
                leads_found=8,
                leads_with_phone=8,
                run_id=i
            )
        
        # Should skip (8% < 10% threshold)
        assert active_learning.should_skip_portal("marginal_portal") is True
    
    def test_should_skip_portal_good_enough_performance(self, active_learning):
        """Test that portals with >= 10% success rate are NOT skipped."""
        # Record 5 runs with 12% success rate
        for i in range(5):
            active_learning.record_portal_result(
                portal="decent_portal",
                urls_crawled=100,
                leads_found=12,
                leads_with_phone=12,
                run_id=i
            )
        
        # Should NOT skip (12% >= 10% threshold)
        assert active_learning.should_skip_portal("decent_portal") is False
    
    def test_record_dork_result(self, active_learning):
        """Test recording dork/query performance."""
        dork = "site:kleinanzeigen.de vertrieb NRW"
        
        active_learning.record_dork_result(
            dork=dork,
            leads_found=10,
            leads_with_phone=3
        )
        
        # Verify data was recorded
        con = sqlite3.connect(active_learning.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        
        assert row is not None
        assert row['times_used'] == 1
        assert row['leads_found'] == 10
        assert row['leads_with_phone'] == 3
        assert row['score'] == 0.3  # 3/10
        assert row['pool'] == 'core'  # Has phone leads
        
        con.close()
    
    def test_record_dork_result_multiple_times(self, active_learning):
        """Test that dork results accumulate correctly."""
        dork = "vertrieb handy NRW"
        
        # Record multiple times
        active_learning.record_dork_result(dork, leads_found=5, leads_with_phone=2)
        active_learning.record_dork_result(dork, leads_found=8, leads_with_phone=4)
        active_learning.record_dork_result(dork, leads_found=3, leads_with_phone=1)
        
        # Verify accumulated data
        con = sqlite3.connect(active_learning.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM dork_performance WHERE dork = ?", (dork,))
        row = cur.fetchone()
        
        assert row is not None
        assert row['times_used'] == 3
        assert row['leads_found'] == 16  # 5+8+3
        assert row['leads_with_phone'] == 7  # 2+4+1
        assert abs(row['score'] - (7/16)) < 0.01  # 7/16 ≈ 0.4375
        
        con.close()
    
    def test_get_best_dorks(self, active_learning):
        """Test retrieving best performing dorks."""
        # Record various dorks with different performance
        dorks_data = [
            ("excellent dork", 10, 8),  # 80% success
            ("good dork", 10, 5),       # 50% success
            ("mediocre dork", 10, 2),   # 20% success
            ("poor dork", 10, 0),       # 0% success
        ]
        
        for dork, leads, with_phone in dorks_data:
            for _ in range(3):  # Use each 3 times to pass times_used > 2 filter
                active_learning.record_dork_result(dork, leads, with_phone)
        
        # Get best dorks
        best = active_learning.get_best_dorks(n=2)
        
        assert len(best) <= 2
        assert "excellent dork" in best
        # Should be ordered by score
        if len(best) == 2:
            assert best[0] == "excellent dork"
    
    def test_learn_phone_pattern(self, active_learning):
        """Test learning phone patterns."""
        active_learning.learn_phone_pattern(
            raw_phone="0171 - 123 456",
            normalized="+491711234567",
            portal="kleinanzeigen"
        )
        
        # Verify pattern was learned
        con = sqlite3.connect(active_learning.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM phone_patterns_learned")
        row = cur.fetchone()
        
        assert row is not None
        assert row['pattern'] == "XXXX - XXX XXX"  # Digits replaced with X
        assert row['times_matched'] == 1
        assert row['source_portal'] == "kleinanzeigen"
        
        con.close()
    
    def test_learn_phone_pattern_multiple_times(self, active_learning):
        """Test that phone patterns accumulate correctly."""
        pattern_phone = "0176 123 456"
        
        # Learn same pattern multiple times
        for _ in range(5):
            active_learning.learn_phone_pattern(
                raw_phone=pattern_phone,
                normalized="+491761234567",
                portal="kleinanzeigen"
            )
        
        # Verify times_matched increased
        con = sqlite3.connect(active_learning.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM phone_patterns_learned WHERE pattern = ?", ("XXXX XXX XXX",))
        row = cur.fetchone()
        
        assert row is not None
        assert row['times_matched'] == 5
        
        con.close()
    
    def test_get_learned_phone_patterns(self, active_learning):
        """Test retrieving learned phone patterns."""
        # Learn various patterns
        patterns = [
            ("0171 123456", 5),   # Learn 5 times
            ("0162-123-456", 3),  # Learn 3 times
            ("0150 12 34 56", 1), # Learn 1 time (should be filtered)
        ]
        
        for phone, times in patterns:
            for _ in range(times):
                active_learning.learn_phone_pattern(
                    raw_phone=phone,
                    normalized="+49...",
                    portal="test"
                )
        
        # Get patterns (min 2 matches)
        learned = active_learning.get_learned_phone_patterns()
        
        # Should only return patterns with > 2 matches
        assert len(learned) == 2
        assert "XXXX XXXXXX" in learned      # 0171 123456 pattern, 5 times
        assert "XXXX-XXX-XXX" in learned    # 0162-123-456 pattern, 3 times
    
    def test_record_host_failure(self, active_learning):
        """Test recording host failures."""
        active_learning.record_host_failure(
            host="dhd24.com",
            reason="HTTP 403 Forbidden",
            backoff_hours=2
        )
        
        # Verify failure was recorded
        con = sqlite3.connect(active_learning.db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM host_backoff WHERE host = ?", ("dhd24.com",))
        row = cur.fetchone()
        
        assert row is not None
        assert row['failures'] == 1
        assert row['reason'] == "HTTP 403 Forbidden"
        assert row['backoff_until'] is not None
        
        con.close()
    
    def test_should_backoff_host_active(self, active_learning):
        """Test that hosts in backoff period are detected."""
        active_learning.record_host_failure(
            host="blocked.com",
            reason="Rate limited",
            backoff_hours=1
        )
        
        # Should be in backoff
        assert active_learning.should_backoff_host("blocked.com") is True
    
    def test_should_backoff_host_expired(self, active_learning):
        """Test that expired backoff periods are detected."""
        # This would require time manipulation or a very short backoff
        # For now, just test that non-existent hosts don't backoff
        assert active_learning.should_backoff_host("never-failed.com") is False
    
    def test_get_portal_stats(self, active_learning):
        """Test getting portal statistics."""
        # Record data for multiple portals
        active_learning.record_portal_result("kleinanzeigen", 100, 20, 5, 1)
        active_learning.record_portal_result("kleinanzeigen", 100, 15, 3, 2)
        active_learning.record_portal_result("markt_de", 50, 10, 2, 1)
        
        stats = active_learning.get_portal_stats()
        
        assert "kleinanzeigen" in stats
        assert "markt_de" in stats
        
        kl_stats = stats["kleinanzeigen"]
        assert kl_stats['runs'] == 2
        assert kl_stats['total_urls'] == 200
        assert kl_stats['total_leads'] == 35
        assert kl_stats['total_with_phone'] == 8
    
    def test_get_learning_summary(self, active_learning):
        """Test getting overall learning summary."""
        # Add some data
        active_learning.record_portal_result("test", 100, 10, 2, 1)
        active_learning.record_dork_result("test dork", 5, 1)
        active_learning.learn_phone_pattern("0171 123", "+49171123", "test")
        
        summary = active_learning.get_learning_summary()
        
        assert 'total_portal_runs' in summary
        assert 'total_dorks_tracked' in summary
        assert 'core_dorks' in summary
        assert 'phone_patterns_learned' in summary
        assert 'hosts_in_backoff' in summary
        
        assert summary['total_portal_runs'] >= 1
        assert summary['total_dorks_tracked'] >= 1
        assert summary['phone_patterns_learned'] >= 1


class TestAvgQualityCalculation:
    """Tests for avg_quality calculation fix."""
    
    def test_avg_quality_calculation_single_update(self, learning_engine, temp_db):
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
    
    def test_avg_quality_calculation_multiple_updates(self, learning_engine, temp_db):
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


class TestEmailRegex:
    """Tests for email regex pattern fix."""
    
    def test_email_regex_pattern(self):
        """Test that the email regex pattern correctly matches valid email addresses."""
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
        assert "hr@example.com" in emails
        assert "recruiting@test-company.de" in emails


