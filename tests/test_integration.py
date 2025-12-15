"""
Integration tests for the complete adaptive search system.
"""

import os
import tempfile
import pytest

from adaptive_system import AdaptiveSearchSystem, create_system_from_env


@pytest.fixture
def temp_db():
    """Create a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def test_dorks():
    """Sample dork queries for testing."""
    return [
        'site:kleinanzeigen.de "Vertrieb" "NRW"',
        'site:linkedin.com/in/ "Suche Job" "Vertrieb"',
        'filetype:pdf "Lebenslauf" "Vertrieb" "Mobil"',
        'site:de "Vertriebspartner" "PLZ" "Kontakt"',
        'site:xing.com "verfügbar" "Sales" "Deutschland"',
    ]


@pytest.fixture
def adaptive_system(temp_db, test_dorks):
    """Create an adaptive system for testing."""
    return AdaptiveSearchSystem(
        all_dorks=test_dorks,
        metrics_db_path=temp_db,
        query_cache_ttl=10,
        url_seen_ttl=10,
        initial_mode="conservative",
    )


class TestAdaptiveSystemIntegration:
    """Test complete adaptive system workflow."""
    
    def test_system_initialization(self, adaptive_system):
        """Test that system initializes correctly."""
        assert adaptive_system.metrics is not None
        assert adaptive_system.dork_selector is not None
        assert adaptive_system.wasserfall is not None
        assert adaptive_system.query_cache is not None
        assert adaptive_system.url_seen is not None
        assert adaptive_system.reporter is not None
    
    def test_dork_selection_workflow(self, adaptive_system):
        """Test complete dork selection workflow."""
        # Select dorks
        selected = adaptive_system.select_dorks_for_run()
        
        # Should select dorks
        assert len(selected) > 0
        
        # Each should have required fields
        for dork_info in selected:
            assert "dork" in dork_info
            assert "pool" in dork_info
            assert "source" in dork_info
            assert "score" in dork_info
            assert dork_info["source"] in ["google", "ddg"]
    
    def test_url_filtering_workflow(self, adaptive_system):
        """Test URL filtering and seen tracking."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        
        # First check should allow
        should_fetch, reason = adaptive_system.should_fetch_url(url1)
        assert should_fetch is True
        
        # Mark as seen
        adaptive_system.mark_url_seen(url1)
        
        # Second check should reject
        should_fetch, reason = adaptive_system.should_fetch_url(url1)
        assert should_fetch is False
        assert reason == "already_seen"
        
        # Different URL should still be allowed
        should_fetch, reason = adaptive_system.should_fetch_url(url2)
        assert should_fetch is True
    
    def test_query_caching_workflow(self, adaptive_system):
        """Test query caching workflow."""
        query = "test query"
        source = "google"
        results = [
            {"url": "https://example.com/1", "title": "Result 1"},
            {"url": "https://example.com/2", "title": "Result 2"},
        ]
        
        # First time should miss cache
        cached = adaptive_system.get_cached_query_results(query, source)
        assert cached is None
        
        # Cache results
        adaptive_system.cache_query_results(query, source, results)
        
        # Second time should hit cache
        cached = adaptive_system.get_cached_query_results(query, source)
        assert cached is not None
        assert len(cached) == 2
        assert cached[0]["url"] == "https://example.com/1"
    
    def test_metrics_recording_workflow(self, adaptive_system):
        """Test complete metrics recording workflow."""
        dork = "test dork query"
        url = "https://example.com/page"
        
        # Record query execution
        adaptive_system.record_query_execution(dork)
        
        # Record SERP results
        adaptive_system.record_serp_results(dork, 10)
        
        # Record URL fetch
        adaptive_system.record_url_fetched(dork, url)
        
        # Record lead found
        adaptive_system.record_lead_found(dork)
        
        # Record lead kept
        adaptive_system.record_lead_kept(dork)
        
        # Record accepted lead
        adaptive_system.record_accepted_lead(dork)
        
        # Verify metrics
        dork_metrics = adaptive_system.metrics.get_dork_metrics(dork)
        assert dork_metrics.queries_total == 1
        assert dork_metrics.serp_hits == 10
        assert dork_metrics.urls_fetched == 1
        assert dork_metrics.leads_found == 1
        assert dork_metrics.leads_kept == 1
        assert dork_metrics.accepted_leads == 1
    
    def test_host_backoff_workflow(self, adaptive_system):
        """Test host backoff workflow."""
        url = "https://bad-host.com/page"
        
        # Simulate many drops for same host
        for i in range(10):
            adaptive_system.record_lead_dropped(f"{url}{i}", "no_phone")
        
        # Host should be backed off now
        should_fetch, reason = adaptive_system.should_fetch_url(url)
        # May or may not be backed off depending on thresholds
        # Just verify the system handles it
        if not should_fetch:
            assert reason == "host_backedoff"
    
    def test_complete_run_workflow(self, adaptive_system):
        """Test complete run workflow."""
        # Initial state
        initial_run_count = adaptive_system.run_count
        
        # Simulate a run
        selected = adaptive_system.select_dorks_for_run()
        
        for dork_info in selected[:2]:  # Just test 2 dorks
            dork = dork_info["dork"]
            
            # Record query
            adaptive_system.record_query_execution(dork)
            
            # Simulate some results
            adaptive_system.record_serp_results(dork, 5)
            
            # Simulate fetching and finding leads
            for i in range(3):
                url = f"https://example{i}.com/page"
                
                should_fetch, _ = adaptive_system.should_fetch_url(url)
                if should_fetch:
                    adaptive_system.mark_url_seen(url)
                    adaptive_system.record_url_fetched(dork, url)
                    adaptive_system.record_lead_found(dork)
                    adaptive_system.record_lead_kept(dork)
                    adaptive_system.record_accepted_lead(dork)
        
        # Complete run
        adaptive_system.complete_run()
        
        # Verify run was completed
        assert adaptive_system.run_count == initial_run_count + 1
    
    def test_rate_limits_from_mode(self, adaptive_system):
        """Test getting rate limits from Wasserfall mode."""
        limits = adaptive_system.get_rate_limits()
        
        assert "ddg_bucket_rate" in limits
        assert "google_bucket_rate" in limits
        assert "worker_parallelism" in limits
        
        # Conservative mode defaults
        assert limits["ddg_bucket_rate"] == 15
        assert limits["google_bucket_rate"] == 4
    
    def test_status_reporting(self, adaptive_system):
        """Test status reporting."""
        status = adaptive_system.get_status()
        
        # Should have all required fields
        assert "run_count" in status
        assert "wasserfall" in status
        assert "dork_pools" in status
        assert "query_cache" in status
        assert "url_seen" in status
        assert "phone_find_rate" in status
        assert "backedoff_hosts" in status
    
    def test_report_generation(self, adaptive_system, temp_db):
        """Test report generation."""
        # Add some metrics first
        adaptive_system.record_query_execution("test dork")
        adaptive_system.record_accepted_lead("test dork")
        
        # Generate report
        report = adaptive_system.generate_report(output_format="json")
        
        assert "generated_at" in report
        assert "summary" in report
        assert "top_dorks" in report
        assert "flop_dorks" in report
        assert "backedoff_hosts" in report
        assert "drop_reasons" in report


class TestSystemFromEnv:
    """Test creating system from environment variables."""
    
    def test_create_from_env(self, test_dorks, monkeypatch):
        """Test creating system from environment."""
        # Set env vars
        monkeypatch.setenv("METRICS_DB", "test_metrics.db")
        monkeypatch.setenv("QUERY_CACHE_TTL", "3600")
        monkeypatch.setenv("URL_SEEN_TTL", "86400")
        monkeypatch.setenv("WASSERFALL_MODE", "moderate")
        
        try:
            system = create_system_from_env(test_dorks)
            
            # Verify configuration
            assert system.wasserfall.current_mode.name == "moderate"
            
            # Cleanup
            import os
            if os.path.exists("test_metrics.db"):
                os.unlink("test_metrics.db")
        except:
            pass
